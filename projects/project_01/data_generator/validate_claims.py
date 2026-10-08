"""
Project 01 - Healthcare Payer Data Platform
Module: validate_claims.py

Purpose
-------
Performs comprehensive business, referential, temporal, clinical, and
financial validation of generated Claim Header and Claim Line data.

What This Module Validates
--------------------------
Claim Line validation includes:

- Unique Claim Line identifiers.
- Parent Claim Header existence.
- Line numbering.
- Service-date validity.
- Service Category / Procedure relationships.
- Revenue-code behavior.
- Diagnosis code/category relationships.
- Units and Claim Line status.
- Billed, allowed, paid, and member-responsibility amounts.

Claim Header validation includes:

- Unique Claim identifiers.
- Member relationship.
- Exact Eligibility relationship.
- Claim service dates.
- Member birth/death constraints.
- Eligibility coverage on the service date.
- Practitioner Role relationship and effective period.
- Practitioner, Supplier, and Supplier Location relationships.
- Benefit Plan relationship.
- Claim Type / Place-of-Service behavior.
- Admission/discharge rules for institutional claims.
- Primary diagnosis.
- Claim status.
- Financial ordering and consistency.
- Claim Header totals versus aggregated Claim Lines.

The validator also checks configured global row counts and produces
distribution/error summaries.

Inputs
------
- member/*.csv
- eligibility/*.csv
- practitioner/*.csv
- practitioner_role/*.csv
- supplier/*.csv
- supplier_location/*.csv
- benefit_plan/*.csv
- claim_header/*.csv
- claim_line/*.csv
- config.py
- reference_data.py

Output
------
Prints distributions, categorized error counts, sample errors, and a
final PASS or FAIL result.

Execution
---------
Example:

    python validate_claims.py --scale medium

Important Notes
---------------
This validator is read-only and is intended to identify source-data
problems before downstream Bronze/Silver processing.
"""




import argparse
import csv
from collections import Counter, defaultdict
from datetime import date
from decimal import Decimal, InvalidOperation
from pathlib import Path

from config import (
    DATA_END_DATE,
    get_scale,
)

from reference_data import (
    CLAIM_DIAGNOSIS_CODES,
    CLAIM_PROCEDURE_PROFILES,
)


PROJECT_ROOT = (
    Path(__file__)
    .resolve()
    .parents[1]
)


# ---------------------------------------------------------
# Generic helpers
# ---------------------------------------------------------

def load_rows(
    data_root: Path,
    folder_name: str,
    pattern: str,
):

    rows = []

    folder = (
        data_root
        / folder_name
    )

    files = sorted(
        folder.glob(pattern)
    )

    if not files:

        raise FileNotFoundError(
            f"No files matching "
            f"'{pattern}' found in "
            f"{folder}."
        )

    for file_path in files:

        with file_path.open(
            mode="r",
            newline="",
            encoding="utf-8",
        ) as handle:

            rows.extend(
                csv.DictReader(handle)
            )

    return rows


def parse_date(
    value: str,
):

    if not value:
        return None

    return date.fromisoformat(
        value[:10]
    )


def parse_money(
    value: str,
):

    try:

        return Decimal(
            value or "0"
        )

    except InvalidOperation:

        return None


def date_in_span(
    target_date: date,
    effective_date: date,
    termination_date,
):

    if target_date < effective_date:
        return False

    if (
        termination_date
        and target_date
        > termination_date
    ):
        return False

    return True


def expected_claim_status(
    line_statuses: list,
):

    if all(
        status == "DENIED"
        for status in line_statuses
    ):
        return "DENIED"

    if any(
        status in [
            "DENIED",
            "ADJUSTED",
        ]
        for status in line_statuses
    ):
        return "ADJUSTED"

    return "PAID"


# ---------------------------------------------------------
# Main validation
# ---------------------------------------------------------

def main():

    parser = argparse.ArgumentParser(
        description=(
            "Validate synthetic healthcare "
            "Claim Header and Claim Line data."
        )
    )

    parser.add_argument(
        "--scale",
        choices=[
            "smoke",
            "medium",
            "full",
        ],
        default="smoke",
    )

    args = parser.parse_args()

    scale_config = get_scale(
        args.scale
    )

    data_root = (
        PROJECT_ROOT
        / "generated_data"
        / args.scale
    )

    # -----------------------------------------------------
    # Load parent datasets
    # -----------------------------------------------------

    members = load_rows(
        data_root,
        "member",
        "member_*.csv",
    )

    eligibility = load_rows(
        data_root,
        "eligibility",
        "eligibility_*.csv",
    )

    practitioners = load_rows(
        data_root,
        "practitioner",
        "practitioner_*.csv",
    )

    practitioner_roles = load_rows(
        data_root,
        "practitioner_role",
        "practitioner_role_*.csv",
    )

    suppliers = load_rows(
        data_root,
        "supplier",
        "supplier_*.csv",
    )

    supplier_locations = load_rows(
        data_root,
        "supplier_location",
        "supplier_location_*.csv",
    )

    benefit_plans = load_rows(
        data_root,
        "benefit_plan",
        "benefit_plan_*.csv",
    )

    claim_headers = load_rows(
        data_root,
        "claim_header",
        "claim_header_*.csv",
    )

    claim_lines = load_rows(
        data_root,
        "claim_line",
        "claim_line_*.csv",
    )

    # -----------------------------------------------------
    # Build lookups
    # -----------------------------------------------------

    member_lookup = {
        row["member_id"]: row
        for row in members
    }

    eligibility_lookup = {
        row["eligibility_id"]: row
        for row in eligibility
    }

    practitioner_lookup = {
        row["practitioner_id"]: row
        for row in practitioners
    }

    role_lookup = {
        row["practitioner_role_id"]: row
        for row in practitioner_roles
    }

    supplier_lookup = {
        row["supplier_id"]: row
        for row in suppliers
    }

    location_lookup = {
        row["supplier_location_id"]: row
        for row in supplier_locations
    }

    plan_lookup = {
        row["benefit_plan_id"]: row
        for row in benefit_plans
    }

    header_lookup = {
        row["claim_id"]: row
        for row in claim_headers
    }

    diagnosis_category_by_code = {}

    for (
        category,
        codes,
    ) in CLAIM_DIAGNOSIS_CODES.items():

        for code in codes:

            diagnosis_category_by_code[
                code
            ] = category

    # -----------------------------------------------------
    # Error collection
    # -----------------------------------------------------

    errors = []

    error_counts = Counter()

    error_examples = defaultdict(
        list
    )

    def add_error(
        category: str,
        message: str,
    ):

        errors.append(
            (
                category,
                message,
            )
        )

        error_counts[
            category
        ] += 1

        if (
            len(
                error_examples[
                    category
                ]
            )
            < 5
        ):

            error_examples[
                category
            ].append(
                message
            )

    # -----------------------------------------------------
    # Distributions for reporting
    # -----------------------------------------------------

    claim_type_counts = Counter()
    claim_status_counts = Counter()
    line_status_counts = Counter()
    service_category_counts = Counter()

    # -----------------------------------------------------
    # LINE VALIDATION + HEADER AGGREGATES
    # -----------------------------------------------------

    line_ids = set()
    line_source_keys = set()

    line_aggregates = defaultdict(
        lambda: {
            "count": 0,
            "billed": Decimal("0"),
            "allowed": Decimal("0"),
            "paid": Decimal("0"),
            "member": Decimal("0"),
            "statuses": [],
            "line_numbers": [],
        }
    )

    for line in claim_lines:

        claim_line_id = (
            line["claim_line_id"]
        )

        claim_id = (
            line["claim_id"]
        )

        # -------------------------------------------------
        # Unique identifiers
        # -------------------------------------------------

        if (
            claim_line_id
            in line_ids
        ):

            add_error(
                "DUPLICATE_CLAIM_LINE_ID",
                claim_line_id,
            )

        line_ids.add(
            claim_line_id
        )

        source_key = (
            line[
                "source_claim_line_key"
            ]
        )

        if (
            source_key
            in line_source_keys
        ):

            add_error(
                "DUPLICATE_CLAIM_LINE_SOURCE_KEY",
                source_key,
            )

        line_source_keys.add(
            source_key
        )

        # -------------------------------------------------
        # Parent Claim Header
        # -------------------------------------------------

        header = (
            header_lookup.get(
                claim_id
            )
        )

        if not header:

            add_error(
                "ORPHAN_CLAIM_LINE",
                (
                    f"{claim_line_id}: "
                    f"Claim {claim_id} "
                    f"does not exist"
                ),
            )

            continue

        # -------------------------------------------------
        # Line sequence
        # -------------------------------------------------

        try:

            line_number = int(
                line["line_number"]
            )

        except ValueError:

            add_error(
                "INVALID_LINE_NUMBER",
                claim_line_id,
            )

            continue

        if line_number <= 0:

            add_error(
                "INVALID_LINE_NUMBER",
                (
                    f"{claim_line_id}: "
                    f"{line_number}"
                ),
            )

        # -------------------------------------------------
        # Service dates
        # -------------------------------------------------

        line_service_date = (
            parse_date(
                line[
                    "service_date"
                ]
            )
        )

        header_from = (
            parse_date(
                header[
                    "service_from_date"
                ]
            )
        )

        header_to = (
            parse_date(
                header[
                    "service_to_date"
                ]
            )
        )

        if (
            not line_service_date
            or not header_from
            or not header_to
        ):

            add_error(
                "MISSING_SERVICE_DATE",
                claim_line_id,
            )

        elif not (
            header_from
            <= line_service_date
            <= header_to
        ):

            add_error(
                "LINE_SERVICE_DATE_OUTSIDE_HEADER",
                (
                    f"{claim_line_id}: "
                    f"line={line_service_date}, "
                    f"header="
                    f"{header_from}..{header_to}"
                ),
            )

        # -------------------------------------------------
        # Service category / procedure relationship
        # -------------------------------------------------

        service_category = (
            line[
                "service_category"
            ]
        )

        service_category_counts[
            service_category
        ] += 1

        profile = (
            CLAIM_PROCEDURE_PROFILES.get(
                service_category
            )
        )

        if not profile:

            add_error(
                "INVALID_SERVICE_CATEGORY",
                (
                    f"{claim_line_id}: "
                    f"{service_category}"
                ),
            )

        else:

            if (
                line[
                    "procedure_code"
                ]
                not in profile[
                    "codes"
                ]
            ):

                add_error(
                    "PROCEDURE_CATEGORY_MISMATCH",
                    (
                        f"{claim_line_id}: "
                        f"{line['procedure_code']} "
                        f"not valid for "
                        f"{service_category}"
                    ),
                )

            expected_revenue_code = (
                profile[
                    "revenue_code"
                ]
            )

            # Professional claims usually do not use
            # revenue codes except our LAB / IMAGING
            # examples.
            if (
                header[
                    "claim_type"
                ]
                == "PROFESSIONAL"
                and service_category
                not in [
                    "LAB",
                    "IMAGING",
                ]
            ):

                expected_revenue_code = ""

            if (
                line["revenue_code"]
                != expected_revenue_code
            ):

                add_error(
                    "REVENUE_CODE_MISMATCH",
                    (
                        f"{claim_line_id}: "
                        f"actual="
                        f"{line['revenue_code']}, "
                        f"expected="
                        f"{expected_revenue_code}"
                    ),
                )

        # -------------------------------------------------
        # Diagnosis relationship
        # -------------------------------------------------

        diagnosis_code = (
            line[
                "diagnosis_code"
            ]
        )

        diagnosis_category = (
            line[
                "diagnosis_category"
            ]
        )

        expected_diagnosis_category = (
            diagnosis_category_by_code.get(
                diagnosis_code
            )
        )

        if (
            expected_diagnosis_category
            is None
        ):

            add_error(
                "UNKNOWN_DIAGNOSIS_CODE",
                (
                    f"{claim_line_id}: "
                    f"{diagnosis_code}"
                ),
            )

        elif (
            diagnosis_category
            != expected_diagnosis_category
        ):

            add_error(
                "DIAGNOSIS_CATEGORY_MISMATCH",
                claim_line_id,
            )

        if (
            diagnosis_category
            != header[
                "primary_diagnosis_category"
            ]
        ):

            add_error(
                "LINE_HEADER_DIAGNOSIS_CATEGORY_MISMATCH",
                claim_line_id,
            )

        # -------------------------------------------------
        # Units
        # -------------------------------------------------

        try:

            units = int(
                line["units"]
            )

        except ValueError:

            units = 0

        if units <= 0:

            add_error(
                "INVALID_UNITS",
                claim_line_id,
            )

        # -------------------------------------------------
        # Line status
        # -------------------------------------------------

        line_status = (
            line["line_status"]
        )

        line_status_counts[
            line_status
        ] += 1

        if (
            line_status
            not in [
                "PAID",
                "ADJUSTED",
                "DENIED",
            ]
        ):

            add_error(
                "INVALID_LINE_STATUS",
                (
                    f"{claim_line_id}: "
                    f"{line_status}"
                ),
            )

        # -------------------------------------------------
        # Financial values
        # -------------------------------------------------

        billed = parse_money(
            line[
                "billed_amount"
            ]
        )

        allowed = parse_money(
            line[
                "allowed_amount"
            ]
        )

        paid = parse_money(
            line[
                "paid_amount"
            ]
        )

        member = parse_money(
            line[
                "member_responsibility_amount"
            ]
        )

        if None in [
            billed,
            allowed,
            paid,
            member,
        ]:

            add_error(
                "INVALID_LINE_MONEY",
                claim_line_id,
            )

            continue

        if (
            billed < 0
            or allowed < 0
            or paid < 0
            or member < 0
        ):

            add_error(
                "NEGATIVE_LINE_AMOUNT",
                claim_line_id,
            )

        if allowed > billed:

            add_error(
                "ALLOWED_EXCEEDS_BILLED",
                claim_line_id,
            )

        if paid > allowed:

            add_error(
                "PAID_EXCEEDS_ALLOWED",
                claim_line_id,
            )

        if (
            paid + member
            != allowed
        ):

            add_error(
                "LINE_FINANCIAL_EQUATION_ERROR",
                (
                    f"{claim_line_id}: "
                    f"allowed={allowed}, "
                    f"paid={paid}, "
                    f"member={member}"
                ),
            )

        if (
            line_status == "DENIED"
            and (
                allowed != 0
                or paid != 0
                or member != 0
            )
        ):

            add_error(
                "DENIED_LINE_HAS_PAYMENT",
                claim_line_id,
            )

        # -------------------------------------------------
        # Aggregate toward Claim Header
        # -------------------------------------------------

        aggregate = (
            line_aggregates[
                claim_id
            ]
        )

        aggregate["count"] += 1

        aggregate["billed"] += (
            billed
        )

        aggregate["allowed"] += (
            allowed
        )

        aggregate["paid"] += (
            paid
        )

        aggregate["member"] += (
            member
        )

        aggregate[
            "statuses"
        ].append(
            line_status
        )

        aggregate[
            "line_numbers"
        ].append(
            line_number
        )

    # -----------------------------------------------------
    # HEADER VALIDATION
    # -----------------------------------------------------

    claim_ids = set()
    claim_source_keys = set()

    for header in claim_headers:

        claim_id = (
            header["claim_id"]
        )

        claim_type = (
            header[
                "claim_type"
            ]
        )

        claim_status = (
            header[
                "claim_status"
            ]
        )

        claim_type_counts[
            claim_type
        ] += 1

        claim_status_counts[
            claim_status
        ] += 1

        # -------------------------------------------------
        # Unique claim identifiers
        # -------------------------------------------------

        if claim_id in claim_ids:

            add_error(
                "DUPLICATE_CLAIM_ID",
                claim_id,
            )

        claim_ids.add(
            claim_id
        )

        source_claim_key = (
            header[
                "source_claim_key"
            ]
        )

        if (
            source_claim_key
            in claim_source_keys
        ):

            add_error(
                "DUPLICATE_CLAIM_SOURCE_KEY",
                source_claim_key,
            )

        claim_source_keys.add(
            source_claim_key
        )

        # -------------------------------------------------
        # Member
        # -------------------------------------------------

        member = (
            member_lookup.get(
                header["member_id"]
            )
        )

        if not member:

            add_error(
                "MISSING_CLAIM_MEMBER",
                claim_id,
            )

        # -------------------------------------------------
        # Eligibility
        # -------------------------------------------------

        eligibility_row = (
            eligibility_lookup.get(
                header[
                    "eligibility_id"
                ]
            )
        )

        if not eligibility_row:

            add_error(
                "MISSING_CLAIM_ELIGIBILITY",
                claim_id,
            )

        else:

            expected_fields = [
                "member_id",
                "subscriber_id",
                "family_id",
                "group_id",
                "subgroup_id",
                "product_id",
                "benefit_plan_id",
                "line_of_business",
                "product_type",
                "network_id",
            ]

            for field_name in (
                expected_fields
            ):

                if (
                    header[field_name]
                    != eligibility_row[
                        field_name
                    ]
                ):

                    add_error(
                        "CLAIM_ELIGIBILITY_FIELD_MISMATCH",
                        (
                            f"{claim_id}: "
                            f"{field_name}"
                        ),
                    )

            if (
                header[
                    "eligibility_record_version"
                ]
                != eligibility_row[
                    "record_version"
                ]
            ):

                add_error(
                    "ELIGIBILITY_VERSION_MISMATCH",
                    claim_id,
                )

        # -------------------------------------------------
        # Header service dates
        # -------------------------------------------------

        service_from = parse_date(
            header[
                "service_from_date"
            ]
        )

        service_to = parse_date(
            header[
                "service_to_date"
            ]
        )

        received_date = parse_date(
            header[
                "received_date"
            ]
        )

        adjudication_date = (
            parse_date(
                header[
                    "adjudication_date"
                ]
            )
        )

        if (
            not service_from
            or not service_to
            or not received_date
            or not adjudication_date
        ):

            add_error(
                "MISSING_CLAIM_DATE",
                claim_id,
            )

            continue

        if (
            service_from
            > service_to
        ):

            add_error(
                "INVALID_SERVICE_DATE_RANGE",
                claim_id,
            )

        if (
            service_to
            > DATA_END_DATE
        ):

            add_error(
                "CLAIM_SERVICE_AFTER_DATA_END",
                claim_id,
            )

        if (
            received_date
            < service_to
        ):

            add_error(
                "CLAIM_RECEIVED_BEFORE_SERVICE",
                claim_id,
            )

        if (
            adjudication_date
            < received_date
        ):

            add_error(
                "CLAIM_ADJUDICATED_BEFORE_RECEIPT",
                claim_id,
            )

        if (
            received_date
            > DATA_END_DATE
            or adjudication_date
            > DATA_END_DATE
        ):

            add_error(
                "CLAIM_PROCESSING_AFTER_DATA_END",
                claim_id,
            )

        # -------------------------------------------------
        # Member DOB / death
        # -------------------------------------------------

        if member:

            dob = parse_date(
                member[
                    "date_of_birth"
                ]
            )

            death_date = parse_date(
                member[
                    "death_date"
                ]
            )

            if (
                dob
                and service_from
                < dob
            ):

                add_error(
                    "CLAIM_BEFORE_MEMBER_BIRTH",
                    claim_id,
                )

            if (
                death_date
                and service_to
                > death_date
            ):

                add_error(
                    "CLAIM_AFTER_MEMBER_DEATH",
                    (
                        f"{claim_id}: "
                        f"service_to="
                        f"{service_to}, "
                        f"death={death_date}"
                    ),
                )

        # -------------------------------------------------
        # Eligibility on service date
        # -------------------------------------------------

        if eligibility_row:

            coverage_start = (
                parse_date(
                    eligibility_row[
                        "coverage_start_date"
                    ]
                )
            )

            coverage_end = (
                parse_date(
                    eligibility_row[
                        "coverage_end_date"
                    ]
                )
                or DATA_END_DATE
            )

            if (
                service_from
                < coverage_start
                or service_to
                > coverage_end
            ):

                add_error(
                    "CLAIM_OUTSIDE_ELIGIBILITY",
                    (
                        f"{claim_id}: "
                        f"service="
                        f"{service_from}.."
                        f"{service_to}, "
                        f"coverage="
                        f"{coverage_start}.."
                        f"{coverage_end}"
                    ),
                )

            if (
                eligibility_row[
                    "eligibility_status"
                ]
                == "FUTURE"
            ):

                add_error(
                    "CLAIM_USES_FUTURE_ELIGIBILITY",
                    claim_id,
                )

        # -------------------------------------------------
        # Practitioner Role
        # -------------------------------------------------

        role = role_lookup.get(
            header[
                "practitioner_role_id"
            ]
        )

        if not role:

            add_error(
                "MISSING_PRACTITIONER_ROLE",
                claim_id,
            )

        else:

            for field_name in [
                "practitioner_id",
                "supplier_id",
                "supplier_location_id",
            ]:

                if (
                    header[field_name]
                    != role[field_name]
                ):

                    add_error(
                        "CLAIM_ROLE_FIELD_MISMATCH",
                        (
                            f"{claim_id}: "
                            f"{field_name}"
                        ),
                    )

            if (
                header[
                    "network_status"
                ]
                != role[
                    "network_status"
                ]
            ):

                add_error(
                    "CLAIM_NETWORK_STATUS_MISMATCH",
                    claim_id,
                )

            if (
                header[
                    "network_tier"
                ]
                != role[
                    "network_tier"
                ]
            ):

                add_error(
                    "CLAIM_NETWORK_TIER_MISMATCH",
                    claim_id,
                )

            role_start = parse_date(
                role[
                    "effective_date"
                ]
            )

            role_end = parse_date(
                role[
                    "termination_date"
                ]
            )

            if not date_in_span(
                service_from,
                role_start,
                role_end,
            ):

                add_error(
                    "CLAIM_OUTSIDE_ROLE_DATES",
                    claim_id,
                )

            if not date_in_span(
                service_to,
                role_start,
                role_end,
            ):

                add_error(
                    "CLAIM_OUTSIDE_ROLE_DATES",
                    claim_id,
                )

        # -------------------------------------------------
        # Practitioner Master
        # -------------------------------------------------

        practitioner = (
            practitioner_lookup.get(
                header[
                    "practitioner_id"
                ]
            )
        )

        if not practitioner:

            add_error(
                "MISSING_PRACTITIONER",
                claim_id,
            )

        else:

            practitioner_start = (
                parse_date(
                    practitioner[
                        "effective_date"
                    ]
                )
            )

            practitioner_end = (
                parse_date(
                    practitioner[
                        "termination_date"
                    ]
                )
            )

            if not date_in_span(
                service_from,
                practitioner_start,
                practitioner_end,
            ):

                add_error(
                    "CLAIM_OUTSIDE_PRACTITIONER_DATES",
                    claim_id,
                )

            if not date_in_span(
                service_to,
                practitioner_start,
                practitioner_end,
            ):

                add_error(
                    "CLAIM_OUTSIDE_PRACTITIONER_DATES",
                    claim_id,
                )

        # -------------------------------------------------
        # Supplier
        # -------------------------------------------------

        if (
            header["supplier_id"]
            not in supplier_lookup
        ):

            add_error(
                "MISSING_SUPPLIER",
                claim_id,
            )

        # -------------------------------------------------
        # Supplier Location
        # -------------------------------------------------

        location = (
            location_lookup.get(
                header[
                    "supplier_location_id"
                ]
            )
        )

        if not location:

            add_error(
                "MISSING_SUPPLIER_LOCATION",
                claim_id,
            )

        else:

            if (
                location[
                    "supplier_id"
                ]
                != header[
                    "supplier_id"
                ]
            ):

                add_error(
                    "LOCATION_SUPPLIER_MISMATCH",
                    claim_id,
                )

            if (
                location[
                    "place_of_service_code"
                ]
                != header[
                    "place_of_service_code"
                ]
            ):

                add_error(
                    "PLACE_OF_SERVICE_MISMATCH",
                    claim_id,
                )

            if (
                location[
                    "network_status"
                ]
                != header[
                    "network_status"
                ]
            ):

                add_error(
                    "LOCATION_NETWORK_STATUS_MISMATCH",
                    claim_id,
                )

            if (
                location[
                    "network_tier"
                ]
                != header[
                    "network_tier"
                ]
            ):

                add_error(
                    "LOCATION_NETWORK_TIER_MISMATCH",
                    claim_id,
                )

            location_start = parse_date(
                location[
                    "effective_date"
                ]
            )

            location_end = parse_date(
                location[
                    "termination_date"
                ]
            )

            if not date_in_span(
                service_from,
                location_start,
                location_end,
            ):

                add_error(
                    "CLAIM_OUTSIDE_LOCATION_DATES",
                    claim_id,
                )

            if not date_in_span(
                service_to,
                location_start,
                location_end,
            ):

                add_error(
                    "CLAIM_OUTSIDE_LOCATION_DATES",
                    claim_id,
                )

        # -------------------------------------------------
        # Benefit Plan
        # -------------------------------------------------

        plan = (
            plan_lookup.get(
                header[
                    "benefit_plan_id"
                ]
            )
        )

        if not plan:

            add_error(
                "MISSING_CLAIM_BENEFIT_PLAN",
                claim_id,
            )

        elif (
            header[
                "network_id"
            ]
            != plan[
                "network_id"
            ]
        ):

            add_error(
                "CLAIM_PLAN_NETWORK_MISMATCH",
                claim_id,
            )

        # -------------------------------------------------
        # Claim Type / Place of Service
        # -------------------------------------------------

        pos = (
            header[
                "place_of_service_code"
            ]
        )

        if (
            claim_type
            == "INSTITUTIONAL_INPATIENT"
            and pos != "21"
        ):

            add_error(
                "INPATIENT_INVALID_POS",
                (
                    f"{claim_id}: "
                    f"POS={pos}"
                ),
            )

        if (
            claim_type
            == "INSTITUTIONAL_OUTPATIENT"
            and pos
            not in [
                "19",
                "22",
                "23",
                "24",
                "49",
                "81",
            ]
        ):

            add_error(
                "OUTPATIENT_INVALID_POS",
                (
                    f"{claim_id}: "
                    f"POS={pos}"
                ),
            )

        # -------------------------------------------------
        # Admission / discharge
        # -------------------------------------------------

        admission_date = (
            parse_date(
                header[
                    "admission_date"
                ]
            )
        )

        discharge_date = (
            parse_date(
                header[
                    "discharge_date"
                ]
            )
        )

        if (
            claim_type
            == "INSTITUTIONAL_INPATIENT"
        ):

            if (
                admission_date
                != service_from
            ):

                add_error(
                    "INPATIENT_ADMISSION_DATE_ERROR",
                    claim_id,
                )

            if (
                discharge_date
                != service_to
            ):

                add_error(
                    "INPATIENT_DISCHARGE_DATE_ERROR",
                    claim_id,
                )

        else:

            if (
                admission_date
                or discharge_date
            ):

                add_error(
                    "NON_INPATIENT_HAS_ADMISSION_DATES",
                    claim_id,
                )

        # -------------------------------------------------
        # Primary diagnosis
        # -------------------------------------------------

        primary_code = (
            header[
                "primary_diagnosis_code"
            ]
        )

        primary_category = (
            header[
                "primary_diagnosis_category"
            ]
        )

        expected_category = (
            diagnosis_category_by_code.get(
                primary_code
            )
        )

        if expected_category is None:

            add_error(
                "UNKNOWN_PRIMARY_DIAGNOSIS",
                claim_id,
            )

        elif (
            expected_category
            != primary_category
        ):

            add_error(
                "PRIMARY_DIAGNOSIS_CATEGORY_MISMATCH",
                claim_id,
            )

        # -------------------------------------------------
        # Claim status
        # -------------------------------------------------

        if (
            claim_status
            not in [
                "PAID",
                "ADJUSTED",
                "DENIED",
            ]
        ):

            add_error(
                "INVALID_CLAIM_STATUS",
                claim_id,
            )

        # -------------------------------------------------
        # Header financial amounts
        # -------------------------------------------------

        header_billed = parse_money(
            header[
                "total_billed_amount"
            ]
        )

        header_allowed = parse_money(
            header[
                "total_allowed_amount"
            ]
        )

        header_paid = parse_money(
            header[
                "total_paid_amount"
            ]
        )

        header_member = parse_money(
            header[
                "member_responsibility_amount"
            ]
        )

        if None in [
            header_billed,
            header_allowed,
            header_paid,
            header_member,
        ]:

            add_error(
                "INVALID_HEADER_MONEY",
                claim_id,
            )

            continue

        if (
            header_billed < 0
            or header_allowed < 0
            or header_paid < 0
            or header_member < 0
        ):

            add_error(
                "NEGATIVE_HEADER_AMOUNT",
                claim_id,
            )

        if (
            header_allowed
            > header_billed
        ):

            add_error(
                "HEADER_ALLOWED_EXCEEDS_BILLED",
                claim_id,
            )

        if (
            header_paid
            > header_allowed
        ):

            add_error(
                "HEADER_PAID_EXCEEDS_ALLOWED",
                claim_id,
            )

        if (
            header_paid
            + header_member
            != header_allowed
        ):

            add_error(
                "HEADER_FINANCIAL_EQUATION_ERROR",
                claim_id,
            )

        # -------------------------------------------------
        # Header vs Claim Lines
        # -------------------------------------------------

        aggregate = (
            line_aggregates.get(
                claim_id
            )
        )

        if not aggregate:

            add_error(
                "CLAIM_HAS_NO_LINES",
                claim_id,
            )

            continue

        expected_line_count = int(
            header[
                "claim_line_count"
            ]
        )

        if (
            aggregate["count"]
            != expected_line_count
        ):

            add_error(
                "CLAIM_LINE_COUNT_MISMATCH",
                (
                    f"{claim_id}: "
                    f"header="
                    f"{expected_line_count}, "
                    f"actual="
                    f"{aggregate['count']}"
                ),
            )

        expected_line_numbers = list(
            range(
                1,
                aggregate["count"] + 1,
            )
        )

        actual_line_numbers = sorted(
            aggregate[
                "line_numbers"
            ]
        )

        if (
            actual_line_numbers
            != expected_line_numbers
        ):

            add_error(
                "CLAIM_LINE_SEQUENCE_ERROR",
                (
                    f"{claim_id}: "
                    f"{actual_line_numbers}"
                ),
            )

        if (
            aggregate["billed"]
            != header_billed
        ):

            add_error(
                "HEADER_BILLED_TOTAL_MISMATCH",
                claim_id,
            )

        if (
            aggregate["allowed"]
            != header_allowed
        ):

            add_error(
                "HEADER_ALLOWED_TOTAL_MISMATCH",
                claim_id,
            )

        if (
            aggregate["paid"]
            != header_paid
        ):

            add_error(
                "HEADER_PAID_TOTAL_MISMATCH",
                claim_id,
            )

        if (
            aggregate["member"]
            != header_member
        ):

            add_error(
                "HEADER_MEMBER_TOTAL_MISMATCH",
                claim_id,
            )

        expected_status = (
            expected_claim_status(
                aggregate[
                    "statuses"
                ]
            )
        )

        if (
            claim_status
            != expected_status
        ):

            add_error(
                "CLAIM_STATUS_LINE_STATUS_MISMATCH",
                (
                    f"{claim_id}: "
                    f"header="
                    f"{claim_status}, "
                    f"expected="
                    f"{expected_status}"
                ),
            )

    # -----------------------------------------------------
    # GLOBAL COUNT VALIDATION
    # -----------------------------------------------------

    if (
        len(claim_headers)
        != scale_config.claim_headers
    ):

        add_error(
            "CLAIM_HEADER_ROW_COUNT_ERROR",
            (
                f"Expected "
                f"{scale_config.claim_headers:,}; "
                f"found "
                f"{len(claim_headers):,}"
            ),
        )

    if (
        len(claim_lines)
        != scale_config.claim_lines
    ):

        add_error(
            "CLAIM_LINE_ROW_COUNT_ERROR",
            (
                f"Expected "
                f"{scale_config.claim_lines:,}; "
                f"found "
                f"{len(claim_lines):,}"
            ),
        )

    # -----------------------------------------------------
    # REPORT
    # -----------------------------------------------------

    print()
    print("=" * 85)
    print(
        "ENHANCED CLAIMS VALIDATION"
    )
    print("=" * 85)

    print(
        f"Scale             : "
        f"{args.scale}"
    )

    print(
        f"Claim Headers     : "
        f"{len(claim_headers):,}"
    )

    print(
        f"Claim Lines       : "
        f"{len(claim_lines):,}"
    )

    print(
        f"Members           : "
        f"{len(members):,}"
    )

    print(
        f"Eligibility Rows  : "
        f"{len(eligibility):,}"
    )

    print(
        f"Practitioner Roles: "
        f"{len(practitioner_roles):,}"
    )

    print(
        f"Validation errors : "
        f"{len(errors):,}"
    )

    print()
    print(
        "CLAIM TYPE DISTRIBUTION"
    )
    print("-" * 85)

    for (
        claim_type,
        count,
    ) in claim_type_counts.most_common():

        print(
            f"{claim_type:40}"
            f"{count:>12,}"
        )

    print()
    print(
        "CLAIM STATUS DISTRIBUTION"
    )
    print("-" * 85)

    for (
        claim_status,
        count,
    ) in claim_status_counts.most_common():

        print(
            f"{claim_status:40}"
            f"{count:>12,}"
        )

    print()
    print(
        "CLAIM LINE STATUS DISTRIBUTION"
    )
    print("-" * 85)

    for (
        line_status,
        count,
    ) in line_status_counts.most_common():

        print(
            f"{line_status:40}"
            f"{count:>12,}"
        )

    print()
    print(
        "SERVICE CATEGORY DISTRIBUTION"
    )
    print("-" * 85)

    for (
        service_category,
        count,
    ) in service_category_counts.most_common():

        print(
            f"{service_category:40}"
            f"{count:>12,}"
        )

    if errors:

        print()
        print(
            "ERROR SUMMARY"
        )
        print("-" * 85)

        for (
            category,
            count,
        ) in error_counts.most_common():

            print(
                f"{category:55}"
                f"{count:>12,}"
            )

        print()
        print(
            "SAMPLE ERRORS BY CATEGORY"
        )
        print("-" * 85)

        for category in sorted(
            error_examples
        ):

            print()
            print(
                f"[{category}]"
            )

            for message in (
                error_examples[
                    category
                ]
            ):

                print(
                    f"  {message}"
                )

    print()
    print("=" * 85)

    if not errors:

        print(
            "ENHANCED CLAIMS VALIDATION PASSED"
        )

    else:

        print(
            "ENHANCED CLAIMS VALIDATION FAILED"
        )

    print("=" * 85)
    print()


if __name__ == "__main__":
    main()