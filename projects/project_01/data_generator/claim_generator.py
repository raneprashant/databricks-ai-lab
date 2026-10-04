import csv
import random
from collections import defaultdict
from datetime import date, datetime, timedelta
from pathlib import Path

from config import (
    DATA_END_DATE,
    DATA_START_DATE,
    RANDOM_SEED,
    ROWS_PER_FILE,
)

from reference_data import (
    CLAIM_DIAGNOSIS_CODES,
    CLAIM_PROCEDURE_PROFILES,
    SPECIALTY_DIAGNOSIS_CATEGORY,
)


CLAIM_HEADER_COLUMNS = [
    "claim_id",
    "member_id",
    "eligibility_id",
    "eligibility_record_version",
    "subscriber_id",
    "family_id",
    "group_id",
    "subgroup_id",
    "product_id",
    "benefit_plan_id",
    "line_of_business",
    "product_type",
    "network_id",
    "practitioner_role_id",
    "practitioner_id",
    "supplier_id",
    "supplier_location_id",
    "claim_type",
    "service_from_date",
    "service_to_date",
    "admission_date",
    "discharge_date",
    "received_date",
    "adjudication_date",
    "claim_status",
    "network_status",
    "network_tier",
    "place_of_service_code",
    "primary_diagnosis_code",
    "primary_diagnosis_category",
    "claim_line_count",
    "total_billed_amount",
    "total_allowed_amount",
    "total_paid_amount",
    "member_responsibility_amount",
    "source_claim_key",
    "create_ts",
    "update_ts",
]


CLAIM_LINE_COLUMNS = [
    "claim_line_id",
    "claim_id",
    "line_number",
    "service_date",
    "service_category",
    "procedure_code",
    "revenue_code",
    "diagnosis_code",
    "diagnosis_category",
    "units",
    "line_status",
    "billed_amount",
    "allowed_amount",
    "paid_amount",
    "member_responsibility_amount",
    "source_claim_line_key",
    "create_ts",
    "update_ts",
]


# ---------------------------------------------------------
# Generic file helpers
# ---------------------------------------------------------

def load_csv_files(
    directory: Path,
    pattern: str,
):

    rows = []

    files = sorted(
        directory.glob(pattern)
    )

    if not files:
        raise FileNotFoundError(
            f"No files matching '{pattern}' "
            f"found in {directory}."
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


def random_date_between(
    start_date: date,
    end_date: date,
    rng: random.Random,
):

    if end_date <= start_date:
        return start_date

    return start_date + timedelta(
        days=rng.randint(
            0,
            (
                end_date
                - start_date
            ).days,
        )
    )


def build_timestamp(
    value: date,
    rng: random.Random,
) -> str:

    dt = datetime(
        value.year,
        value.month,
        value.day,
        rng.randint(0, 23),
        rng.randint(0, 59),
        rng.randint(0, 59),
    )

    return dt.isoformat(
        timespec="seconds"
    )


def money_string(
    cents: int,
) -> str:

    return (
        f"{cents / 100:.2f}"
    )


# ---------------------------------------------------------
# Rolling writer
#
# This avoids holding millions of Claim Line rows in
# memory when we later run the Full scale.
# ---------------------------------------------------------

class RollingCsvWriter:

    def __init__(
        self,
        output_directory: Path,
        filename_prefix: str,
        columns: list,
        rows_per_file: int,
    ):

        self.output_directory = (
            output_directory
        )

        self.filename_prefix = (
            filename_prefix
        )

        self.columns = columns

        self.rows_per_file = (
            rows_per_file
        )

        self.file_number = 0
        self.rows_in_file = 0
        self.file_handle = None
        self.writer = None

        self.output_directory.mkdir(
            parents=True,
            exist_ok=True,
        )

    def _open_next_file(
        self,
    ):

        if self.file_handle:

            self.file_handle.close()

        self.file_number += 1

        file_path = (
            self.output_directory
            / (
                f"{self.filename_prefix}_"
                f"{self.file_number:03d}.csv"
            )
        )

        print(
            f"Writing {file_path}"
        )

        self.file_handle = (
            file_path.open(
                mode="w",
                newline="",
                encoding="utf-8",
            )
        )

        self.writer = csv.DictWriter(
            self.file_handle,
            fieldnames=self.columns,
        )

        self.writer.writeheader()

        self.rows_in_file = 0

    def write(
        self,
        row: dict,
    ):

        if (
            self.writer is None
            or self.rows_in_file
            >= self.rows_per_file
        ):

            self._open_next_file()

        self.writer.writerow(
            row
        )

        self.rows_in_file += 1

    def close(
        self,
    ):

        if self.file_handle:

            self.file_handle.close()

            self.file_handle = None
            self.writer = None


# ---------------------------------------------------------
# Eligibility
# ---------------------------------------------------------

def build_claimable_eligibility(
    eligibility_rows: list,
):

    by_member = defaultdict(
        list
    )

    for row in eligibility_rows:

        by_member[
            row["member_id"]
        ].append(
            row
        )

    claimable = {}

    for (
        member_id,
        rows,
    ) in by_member.items():

        rows = sorted(
            rows,
            key=lambda row: int(
                row["record_version"]
            ),
        )

        current_row = next(
            (
                row
                for row in rows
                if row[
                    "current_record_flag"
                ] == "Y"
            ),
            rows[-1],
        )

        # A FUTURE record does not describe coverage
        # available for claims as of DATA_END_DATE.
        # Use the most recent prior non-future version.
        if (
            current_row[
                "eligibility_status"
            ]
            == "FUTURE"
        ):

            prior_rows = [
                row
                for row in rows
                if (
                    row[
                        "eligibility_status"
                    ]
                    != "FUTURE"
                    and parse_date(
                        row[
                            "coverage_start_date"
                        ]
                    )
                    <= DATA_END_DATE
                )
            ]

            if not prior_rows:
                continue

            current_row = (
                prior_rows[-1]
            )

        coverage_start = max(
            parse_date(
                current_row[
                    "coverage_start_date"
                ]
            ),
            DATA_START_DATE,
        )

        coverage_end = (
            parse_date(
                current_row[
                    "coverage_end_date"
                ]
            )
            or DATA_END_DATE
        )

        coverage_end = min(
            coverage_end,
            DATA_END_DATE,
        )

        if (
            coverage_start
            > coverage_end
        ):
            continue

        claimable[
            member_id
        ] = {
            "eligibility": (
                current_row
            ),
            "coverage_start": (
                coverage_start
            ),
            "coverage_end": (
                coverage_end
            ),
        }

    if not claimable:

        raise RuntimeError(
            "No claimable Eligibility "
            "records were found."
        )

    return claimable


# ---------------------------------------------------------
# Practitioner Role validity
# ---------------------------------------------------------

def role_valid_on_date(
    role: dict,
    service_date: date,
) -> bool:

    effective_date = parse_date(
        role["effective_date"]
    )

    termination_date = (
        parse_date(
            role["termination_date"]
        )
        or DATA_END_DATE
    )

    return (
        effective_date
        <= service_date
        <= termination_date
    )


def choose_valid_role(
    roles: list,
    service_date: date,
    rng: random.Random,
):

    # Fast path for the large Full dataset.
    for _ in range(200):

        role = rng.choice(
            roles
        )

        if role_valid_on_date(
            role,
            service_date,
        ):

            return role

    # Exact fallback.
    for role in roles:

        if role_valid_on_date(
            role,
            service_date,
        ):

            return role

    raise RuntimeError(
        "No Practitioner Role is valid "
        f"on {service_date}."
    )


# ---------------------------------------------------------
# Claim classification
# ---------------------------------------------------------

def choose_claim_type(
    place_of_service_code: str,
    rng: random.Random,
):

    if place_of_service_code == "21":

        return rng.choices(
            population=[
                "INSTITUTIONAL_INPATIENT",
                "PROFESSIONAL",
            ],
            weights=[
                75,
                25,
            ],
            k=1,
        )[0]

    if place_of_service_code in [
        "19",
        "22",
        "23",
        "24",
        "49",
        "81",
    ]:

        return rng.choices(
            population=[
                "INSTITUTIONAL_OUTPATIENT",
                "PROFESSIONAL",
            ],
            weights=[
                55,
                45,
            ],
            k=1,
        )[0]

    return "PROFESSIONAL"


def diagnosis_category_for_role(
    role: dict,
):

    specialty = (
        role[
            "role_specialty"
        ]
    )

    return (
        SPECIALTY_DIAGNOSIS_CATEGORY
        .get(
            specialty,
            "GENERAL_MEDICAL",
        )
    )


def choose_base_service_category(
    role: dict,
    claim_type: str,
    location: dict,
    rng: random.Random,
):

    specialty = (
        role[
            "role_specialty"
        ]
    )

    location_type = (
        location[
            "location_type"
        ]
    )

    if (
        claim_type
        == "INSTITUTIONAL_INPATIENT"
    ):
        return "INPATIENT"

    if (
        specialty
        == "EMERGENCY_MEDICINE"
        or location_type
        == "URGENT_CARE_CENTER"
    ):
        return "EMERGENCY"

    if specialty == "GENERAL_SURGERY":
        return "SURGERY"

    if specialty == "RADIOLOGY":
        return "IMAGING"

    if specialty == "PATHOLOGY":
        return "LAB"

    if specialty == "PSYCHIATRY":
        return "BEHAVIORAL_HEALTH"

    if (
        specialty
        == "OBSTETRICS_GYNECOLOGY"
    ):
        return rng.choices(
            population=[
                "MATERNITY",
                "SPECIALTY_VISIT",
            ],
            weights=[
                45,
                55,
            ],
            k=1,
        )[0]

    if (
        role["pcp_flag"]
        == "Y"
    ):

        return rng.choices(
            population=[
                "OFFICE_VISIT",
                "PREVENTIVE",
            ],
            weights=[
                75,
                25,
            ],
            k=1,
        )[0]

    return "SPECIALTY_VISIT"


def choose_line_service_category(
    base_category: str,
    claim_type: str,
    line_number: int,
    rng: random.Random,
):

    if line_number == 1:
        return base_category

    if (
        claim_type
        == "INSTITUTIONAL_INPATIENT"
    ):

        return rng.choices(
            population=[
                "INPATIENT",
                "LAB",
                "IMAGING",
                "SURGERY",
            ],
            weights=[
                55,
                20,
                15,
                10,
            ],
            k=1,
        )[0]

    if (
        claim_type
        == "INSTITUTIONAL_OUTPATIENT"
    ):

        return rng.choices(
            population=[
                base_category,
                "LAB",
                "IMAGING",
            ],
            weights=[
                60,
                25,
                15,
            ],
            k=1,
        )[0]

    return rng.choices(
        population=[
            base_category,
            "LAB",
            "IMAGING",
        ],
        weights=[
            75,
            15,
            10,
        ],
        k=1,
    )[0]


# ---------------------------------------------------------
# Financial adjudication
# ---------------------------------------------------------

def plan_amount(
    plan: dict,
    column: str,
) -> int:

    value = plan.get(
        column,
        "0",
    )

    if not value:
        return 0

    return int(
        round(
            float(value) * 100
        )
    )


def generate_line_financials(
    service_category: str,
    role: dict,
    plan: dict,
    network_status: str,
    rng: random.Random,
):

    profile = (
        CLAIM_PROCEDURE_PROFILES[
            service_category
        ]
    )

    billed_cents = (
        rng.randint(
            profile["min_billed"],
            profile["max_billed"],
        )
        * 100
    )

    line_status = rng.choices(
        population=[
            "PAID",
            "ADJUSTED",
            "DENIED",
        ],
        weights=[
            89,
            6,
            5,
        ],
        k=1,
    )[0]

    if line_status == "DENIED":

        return (
            billed_cents,
            0,
            0,
            0,
            line_status,
        )

    if (
        network_status
        == "IN_NETWORK"
    ):

        allowed_pct = rng.randint(
            58,
            86,
        )

    else:

        allowed_pct = rng.randint(
            38,
            68,
        )

    if (
        line_status
        == "ADJUSTED"
    ):

        allowed_pct = max(
            25,
            allowed_pct
            - rng.randint(
                5,
                15,
            ),
        )

    allowed_cents = round(
        billed_cents
        * allowed_pct
        / 100
    )

    # -----------------------------------------------------
    # Member responsibility
    #
    # Use plan copays where appropriate; otherwise
    # use the plan's coinsurance percentage.
    # -----------------------------------------------------

    if service_category in [
        "OFFICE_VISIT",
        "PREVENTIVE",
        "SPECIALTY_VISIT",
    ]:

        if (
            role["pcp_flag"]
            == "Y"
        ):

            member_cents = plan_amount(
                plan,
                "pcp_copay",
            )

        else:

            member_cents = plan_amount(
                plan,
                "specialist_copay",
            )

    elif (
        service_category
        == "EMERGENCY"
    ):

        member_cents = plan_amount(
            plan,
            "er_copay",
        )

    else:

        coinsurance_pct = int(
            float(
                plan.get(
                    "coinsurance_pct",
                    20,
                )
                or 20
            )
        )

        if (
            network_status
            != "IN_NETWORK"
        ):

            coinsurance_pct = min(
                70,
                coinsurance_pct + 20,
            )

        member_cents = round(
            allowed_cents
            * coinsurance_pct
            / 100
        )

    member_cents = min(
        member_cents,
        allowed_cents,
    )

    paid_cents = (
        allowed_cents
        - member_cents
    )

    return (
        billed_cents,
        allowed_cents,
        paid_cents,
        member_cents,
        line_status,
    )


def determine_claim_status(
    line_statuses: list,
):

    if all(
        status == "DENIED"
        for status in line_statuses
    ):

        return "DENIED"

    if any(
        status
        in [
            "DENIED",
            "ADJUSTED",
        ]
        for status in line_statuses
    ):

        return "ADJUSTED"

    return "PAID"


# ---------------------------------------------------------
# Exact Header / Line count allocation
# ---------------------------------------------------------

def allocate_line_counts(
    claim_header_count: int,
    claim_line_count: int,
    rng: random.Random,
):

    if (
        claim_line_count
        < claim_header_count
    ):

        raise ValueError(
            "Claim Line count must be at "
            "least Claim Header count."
        )

    maximum_lines_per_claim = 8

    if (
        claim_line_count
        >
        claim_header_count
        * maximum_lines_per_claim
    ):

        raise ValueError(
            "Claim Line target requires "
            "more than 8 lines per claim."
        )

    counts = [
        1
        for _ in range(
            claim_header_count
        )
    ]

    remaining = (
        claim_line_count
        - claim_header_count
    )

    while remaining > 0:

        index = rng.randrange(
            claim_header_count
        )

        if (
            counts[index]
            >= maximum_lines_per_claim
        ):
            continue

        counts[index] += 1
        remaining -= 1

    return counts


# ---------------------------------------------------------
# Main generation
# ---------------------------------------------------------

def generate_claims(
    claim_header_count: int,
    claim_line_count: int,
    output_root: Path,
) -> None:

    rng = random.Random(
        RANDOM_SEED + 900
    )

    eligibility_rows = load_csv_files(
        output_root / "eligibility",
        "eligibility_*.csv",
    )

    practitioner_roles = load_csv_files(
        output_root / "practitioner_role",
        "practitioner_role_*.csv",
    )

    supplier_locations = load_csv_files(
        output_root / "supplier_location",
        "supplier_location_*.csv",
    )

    benefit_plans = load_csv_files(
        output_root / "benefit_plan",
        "benefit_plan_*.csv",
    )

    location_lookup = {
        row["supplier_location_id"]: row
        for row in supplier_locations
    }

    plan_lookup = {
        row["benefit_plan_id"]: row
        for row in benefit_plans
    }

    claimable_eligibility = (
        build_claimable_eligibility(
            eligibility_rows
        )
    )

    claimable_member_ids = list(
        claimable_eligibility.keys()
    )

    line_counts = allocate_line_counts(
        claim_header_count,
        claim_line_count,
        rng,
    )

    header_writer = RollingCsvWriter(
        output_root / "claim_header",
        "claim_header",
        CLAIM_HEADER_COLUMNS,
        ROWS_PER_FILE[
            "claim_header"
        ],
    )

    line_writer = RollingCsvWriter(
        output_root / "claim_line",
        "claim_line",
        CLAIM_LINE_COLUMNS,
        ROWS_PER_FILE[
            "claim_line"
        ],
    )

    claim_line_number_global = 1

    try:

        for claim_number in range(
            1,
            claim_header_count + 1,
        ):

            claim_id = (
                f"CLM{claim_number:010d}"
            )

            member_id = rng.choice(
                claimable_member_ids
            )

            eligibility_info = (
                claimable_eligibility[
                    member_id
                ]
            )

            eligibility = (
                eligibility_info[
                    "eligibility"
                ]
            )

            coverage_start = (
                eligibility_info[
                    "coverage_start"
                ]
            )

            coverage_end = (
                eligibility_info[
                    "coverage_end"
                ]
            )

            service_from_date = (
                random_date_between(
                    coverage_start,
                    coverage_end,
                    rng,
                )
            )

            role = choose_valid_role(
                practitioner_roles,
                service_from_date,
                rng,
            )

            location = (
                location_lookup[
                    role[
                        "supplier_location_id"
                    ]
                ]
            )

            plan = (
                plan_lookup[
                    eligibility[
                        "benefit_plan_id"
                    ]
                ]
            )

            place_of_service_code = (
                location[
                    "place_of_service_code"
                ]
            )

            claim_type = (
                choose_claim_type(
                    place_of_service_code,
                    rng,
                )
            )

            role_end = (
                parse_date(
                    role[
                        "termination_date"
                    ]
                )
                or DATA_END_DATE
            )

            maximum_service_end = min(
                coverage_end,
                role_end,
                DATA_END_DATE,
            )

            if (
                claim_type
                == "INSTITUTIONAL_INPATIENT"
            ):

                requested_stay = rng.randint(
                    1,
                    5,
                )

                service_to_date = min(
                    service_from_date
                    + timedelta(
                        days=(
                            requested_stay
                            - 1
                        )
                    ),
                    maximum_service_end,
                )

                admission_date = (
                    service_from_date
                )

                discharge_date = (
                    service_to_date
                )

            else:

                service_to_date = (
                    service_from_date
                )

                admission_date = None
                discharge_date = None

            received_date = min(
                service_to_date
                + timedelta(
                    days=rng.randint(
                        1,
                        30,
                    )
                ),
                DATA_END_DATE,
            )

            adjudication_date = min(
                received_date
                + timedelta(
                    days=rng.randint(
                        1,
                        30,
                    )
                ),
                DATA_END_DATE,
            )

            diagnosis_category = (
                diagnosis_category_for_role(
                    role
                )
            )

            diagnosis_codes = (
                CLAIM_DIAGNOSIS_CODES[
                    diagnosis_category
                ]
            )

            primary_diagnosis_code = (
                rng.choice(
                    diagnosis_codes
                )
            )

            base_service_category = (
                choose_base_service_category(
                    role,
                    claim_type,
                    location,
                    rng,
                )
            )

            number_of_lines = (
                line_counts[
                    claim_number - 1
                ]
            )

            total_billed = 0
            total_allowed = 0
            total_paid = 0
            total_member = 0

            line_statuses = []

            for line_number in range(
                1,
                number_of_lines + 1,
            ):

                service_category = (
                    choose_line_service_category(
                        base_service_category,
                        claim_type,
                        line_number,
                        rng,
                    )
                )

                procedure_profile = (
                    CLAIM_PROCEDURE_PROFILES[
                        service_category
                    ]
                )

                procedure_code = (
                    rng.choice(
                        procedure_profile[
                            "codes"
                        ]
                    )
                )

                revenue_code = (
                    procedure_profile[
                        "revenue_code"
                    ]
                )

                if (
                    claim_type
                    == "PROFESSIONAL"
                    and service_category
                    not in [
                        "LAB",
                        "IMAGING",
                    ]
                ):
                    revenue_code = ""

                if (
                    service_to_date
                    > service_from_date
                ):

                    line_service_date = (
                        random_date_between(
                            service_from_date,
                            service_to_date,
                            rng,
                        )
                    )

                else:

                    line_service_date = (
                        service_from_date
                    )

                diagnosis_code = (
                    rng.choice(
                        diagnosis_codes
                    )
                )

                units = (
                    rng.randint(
                        1,
                        3,
                    )
                )

                (
                    billed_cents,
                    allowed_cents,
                    paid_cents,
                    member_cents,
                    line_status,
                ) = generate_line_financials(
                    service_category=(
                        service_category
                    ),
                    role=role,
                    plan=plan,
                    network_status=(
                        role[
                            "network_status"
                        ]
                    ),
                    rng=rng,
                )

                total_billed += (
                    billed_cents
                )

                total_allowed += (
                    allowed_cents
                )

                total_paid += (
                    paid_cents
                )

                total_member += (
                    member_cents
                )

                line_statuses.append(
                    line_status
                )

                claim_line_id = (
                    f"CLML"
                    f"{claim_line_number_global:012d}"
                )

                line_row = {
                    "claim_line_id": (
                        claim_line_id
                    ),
                    "claim_id": (
                        claim_id
                    ),
                    "line_number": (
                        line_number
                    ),
                    "service_date": (
                        line_service_date
                        .isoformat()
                    ),
                    "service_category": (
                        service_category
                    ),
                    "procedure_code": (
                        procedure_code
                    ),
                    "revenue_code": (
                        revenue_code
                    ),
                    "diagnosis_code": (
                        diagnosis_code
                    ),
                    "diagnosis_category": (
                        diagnosis_category
                    ),
                    "units": (
                        units
                    ),
                    "line_status": (
                        line_status
                    ),
                    "billed_amount": (
                        money_string(
                            billed_cents
                        )
                    ),
                    "allowed_amount": (
                        money_string(
                            allowed_cents
                        )
                    ),
                    "paid_amount": (
                        money_string(
                            paid_cents
                        )
                    ),
                    "member_responsibility_amount": (
                        money_string(
                            member_cents
                        )
                    ),
                    "source_claim_line_key": (
                        f"SRCCLML"
                        f"{claim_line_number_global:012d}"
                    ),
                    "create_ts": (
                        build_timestamp(
                            received_date,
                            rng,
                        )
                    ),
                    "update_ts": (
                        build_timestamp(
                            adjudication_date,
                            rng,
                        )
                    ),
                }

                line_writer.write(
                    line_row
                )

                claim_line_number_global += 1

            claim_status = (
                determine_claim_status(
                    line_statuses
                )
            )

            header_row = {
                "claim_id": (
                    claim_id
                ),
                "member_id": (
                    member_id
                ),
                "eligibility_id": (
                    eligibility[
                        "eligibility_id"
                    ]
                ),
                "eligibility_record_version": (
                    eligibility[
                        "record_version"
                    ]
                ),
                "subscriber_id": (
                    eligibility[
                        "subscriber_id"
                    ]
                ),
                "family_id": (
                    eligibility[
                        "family_id"
                    ]
                ),
                "group_id": (
                    eligibility[
                        "group_id"
                    ]
                ),
                "subgroup_id": (
                    eligibility[
                        "subgroup_id"
                    ]
                ),
                "product_id": (
                    eligibility[
                        "product_id"
                    ]
                ),
                "benefit_plan_id": (
                    eligibility[
                        "benefit_plan_id"
                    ]
                ),
                "line_of_business": (
                    eligibility[
                        "line_of_business"
                    ]
                ),
                "product_type": (
                    eligibility[
                        "product_type"
                    ]
                ),
                "network_id": (
                    eligibility[
                        "network_id"
                    ]
                ),
                "practitioner_role_id": (
                    role[
                        "practitioner_role_id"
                    ]
                ),
                "practitioner_id": (
                    role[
                        "practitioner_id"
                    ]
                ),
                "supplier_id": (
                    role[
                        "supplier_id"
                    ]
                ),
                "supplier_location_id": (
                    role[
                        "supplier_location_id"
                    ]
                ),
                "claim_type": (
                    claim_type
                ),
                "service_from_date": (
                    service_from_date
                    .isoformat()
                ),
                "service_to_date": (
                    service_to_date
                    .isoformat()
                ),
                "admission_date": (
                    admission_date.isoformat()
                    if admission_date
                    else ""
                ),
                "discharge_date": (
                    discharge_date.isoformat()
                    if discharge_date
                    else ""
                ),
                "received_date": (
                    received_date
                    .isoformat()
                ),
                "adjudication_date": (
                    adjudication_date
                    .isoformat()
                ),
                "claim_status": (
                    claim_status
                ),
                "network_status": (
                    role[
                        "network_status"
                    ]
                ),
                "network_tier": (
                    role[
                        "network_tier"
                    ]
                ),
                "place_of_service_code": (
                    place_of_service_code
                ),
                "primary_diagnosis_code": (
                    primary_diagnosis_code
                ),
                "primary_diagnosis_category": (
                    diagnosis_category
                ),
                "claim_line_count": (
                    number_of_lines
                ),
                "total_billed_amount": (
                    money_string(
                        total_billed
                    )
                ),
                "total_allowed_amount": (
                    money_string(
                        total_allowed
                    )
                ),
                "total_paid_amount": (
                    money_string(
                        total_paid
                    )
                ),
                "member_responsibility_amount": (
                    money_string(
                        total_member
                    )
                ),
                "source_claim_key": (
                    f"SRCCLM"
                    f"{claim_number:010d}"
                ),
                "create_ts": (
                    build_timestamp(
                        received_date,
                        rng,
                    )
                ),
                "update_ts": (
                    build_timestamp(
                        adjudication_date,
                        rng,
                    )
                ),
            }

            header_writer.write(
                header_row
            )

    finally:

        header_writer.close()
        line_writer.close()

    print()
    print(
        f"Generated "
        f"{claim_header_count:,} "
        f"claim header rows."
    )

    print(
        f"Generated "
        f"{claim_line_count:,} "
        f"claim line rows."
    )

    print(
        f"Claimable Members: "
        f"{len(claimable_member_ids):,}"
    )

    print(
        f"Practitioner Roles loaded: "
        f"{len(practitioner_roles):,}"
    )

    print(
        f"Supplier Locations loaded: "
        f"{len(supplier_locations):,}"
    )