import csv
import argparse
from collections import Counter, defaultdict
from datetime import date
from pathlib import Path

from config import (
    DATA_START_DATE,
    DATA_END_DATE,
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
    folder: str,
    pattern: str,
):

    rows = []

    directory = (
        data_root
        / folder
    )

    for file_path in sorted(
        directory.glob(pattern)
    ):

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


def add_years(
    value: date,
    years: int,
):

    try:

        return value.replace(
            year=value.year + years
        )

    except ValueError:

        # February 29
        return value.replace(
            month=2,
            day=28,
            year=value.year + years,
        )


def main():

    parser = argparse.ArgumentParser()

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

    data_root = (
        PROJECT_ROOT
        / "generated_data"
        / args.scale
    )

    # -----------------------------------------------------
    # Load source datasets
    # -----------------------------------------------------

    members = load_rows(
        data_root,
        "member",
        "member_*.csv",
    )

    products = load_rows(
        data_root,
        "product",
        "product_*.csv",
    )

    plans = load_rows(
        data_root,
        "benefit_plan",
        "benefit_plan_*.csv",
    )

    groups = load_rows(
        data_root,
        "group",
        "group_*.csv",
    )

    subgroups = load_rows(
        data_root,
        "subgroup",
        "subgroup_*.csv",
    )

    eligibility = load_rows(
        data_root,
        "eligibility",
        "eligibility_*.csv",
    )

    # -----------------------------------------------------
    # Build lookups
    # -----------------------------------------------------

    member_lookup = {
        row["member_id"]: row
        for row in members
    }

    product_lookup = {
        row["product_id"]: row
        for row in products
    }

    plan_lookup = {
        row["benefit_plan_id"]: row
        for row in plans
    }

    group_lookup = {
        row["group_id"]: row
        for row in groups
    }

    subgroup_lookup = {
        row["subgroup_id"]: row
        for row in subgroups
    }

    # -----------------------------------------------------
    # Error collection
    #
    # We keep errors by category so that if something
    # fails, we immediately know what kind of problem
    # exists rather than receiving one huge error list.
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
    # MEMBER MASTER VALIDATION
    # -----------------------------------------------------

    for member in members:

        member_id = (
            member["member_id"]
        )

        dob = parse_date(
            member["date_of_birth"]
        )

        death_date = parse_date(
            member["death_date"]
        )

        if (
            dob
            and dob > DATA_END_DATE
        ):

            add_error(
                "MEMBER_FUTURE_DOB",
                (
                    f"{member_id}: "
                    f"DOB {dob} is after "
                    f"DATA_END_DATE "
                    f"{DATA_END_DATE}"
                ),
            )

        if (
            dob
            and death_date
            and death_date < dob
        ):

            add_error(
                "MEMBER_INVALID_DEATH_DATE",
                (
                    f"{member_id}: "
                    f"death {death_date} "
                    f"is before DOB {dob}"
                ),
            )

        subscriber_id = (
            member["subscriber_id"]
        )

        subscriber = (
            member_lookup.get(
                subscriber_id
            )
        )

        if not subscriber:

            add_error(
                "MEMBER_MISSING_SUBSCRIBER",
                (
                    f"{member_id}: "
                    f"subscriber "
                    f"{subscriber_id} "
                    f"does not exist"
                ),
            )

        else:

            if (
                subscriber[
                    "relationship_to_subscriber"
                ]
                != "SELF"
            ):

                add_error(
                    "MEMBER_INVALID_SUBSCRIBER",
                    (
                        f"{member_id}: "
                        f"{subscriber_id} "
                        f"is not SELF"
                    ),
                )

            if (
                subscriber["family_id"]
                != member["family_id"]
            ):

                add_error(
                    "MEMBER_FAMILY_MISMATCH",
                    (
                        f"{member_id}: "
                        f"subscriber belongs "
                        f"to another family"
                    ),
                )

    # -----------------------------------------------------
    # ELIGIBILITY ROW VALIDATION
    # -----------------------------------------------------

    versions_by_member = defaultdict(
        list
    )

    event_counts = Counter()

    eligibility_ids = set()
    source_keys = set()

    termination_events = {
        "RETRO_TERM",
        "VOLUNTARY_TERM",
        "DEATH",
        "DEPENDENT_AGE_OUT",
        "REMOVE_DEPENDENT",
    }

    for row in eligibility:

        eligibility_id = (
            row["eligibility_id"]
        )

        member_id = (
            row["member_id"]
        )

        event_type = (
            row["event_type"]
        )

        event_counts[
            event_type
        ] += 1

        versions_by_member[
            member_id
        ].append(
            row
        )

        # -------------------------------------------------
        # Unique identifiers
        # -------------------------------------------------

        if (
            eligibility_id
            in eligibility_ids
        ):

            add_error(
                "DUPLICATE_ELIGIBILITY_ID",
                eligibility_id,
            )

        eligibility_ids.add(
            eligibility_id
        )

        source_key = (
            row[
                "source_eligibility_key"
            ]
        )

        if (
            source_key
            in source_keys
        ):

            add_error(
                "DUPLICATE_SOURCE_KEY",
                source_key,
            )

        source_keys.add(
            source_key
        )

        # -------------------------------------------------
        # Member integrity
        # -------------------------------------------------

        member = (
            member_lookup.get(
                member_id
            )
        )

        if not member:

            add_error(
                "MISSING_MEMBER",
                (
                    f"{eligibility_id}: "
                    f"{member_id}"
                ),
            )

            continue

        if (
            row["subscriber_id"]
            != member["subscriber_id"]
        ):

            add_error(
                "SUBSCRIBER_MISMATCH",
                eligibility_id,
            )

        if (
            row["family_id"]
            != member["family_id"]
        ):

            add_error(
                "FAMILY_MISMATCH",
                eligibility_id,
            )

        if (
            row[
                "relationship_to_subscriber"
            ]
            != member[
                "relationship_to_subscriber"
            ]
        ):

            add_error(
                "RELATIONSHIP_MISMATCH",
                eligibility_id,
            )

        dob = parse_date(
            member["date_of_birth"]
        )

        death_date = parse_date(
            member["death_date"]
        )

        # -------------------------------------------------
        # Parent hierarchy integrity
        # -------------------------------------------------

        subgroup = (
            subgroup_lookup.get(
                row["subgroup_id"]
            )
        )

        if not subgroup:

            add_error(
                "MISSING_SUBGROUP",
                eligibility_id,
            )

            continue

        group = (
            group_lookup.get(
                subgroup["group_id"]
            )
        )

        plan = (
            plan_lookup.get(
                subgroup[
                    "benefit_plan_id"
                ]
            )
        )

        if not group:

            add_error(
                "MISSING_GROUP",
                eligibility_id,
            )

            continue

        if not plan:

            add_error(
                "MISSING_BENEFIT_PLAN",
                eligibility_id,
            )

            continue

        product = (
            product_lookup.get(
                plan["product_id"]
            )
        )

        if not product:

            add_error(
                "MISSING_PRODUCT",
                eligibility_id,
            )

            continue

        if (
            row["group_id"]
            != group["group_id"]
        ):

            add_error(
                "GROUP_REFERENCE_MISMATCH",
                eligibility_id,
            )

        if (
            row["benefit_plan_id"]
            != plan[
                "benefit_plan_id"
            ]
        ):

            add_error(
                "PLAN_REFERENCE_MISMATCH",
                eligibility_id,
            )

        if (
            row["product_id"]
            != product["product_id"]
        ):

            add_error(
                "PRODUCT_REFERENCE_MISMATCH",
                eligibility_id,
            )

        if (
            row["line_of_business"]
            != product[
                "line_of_business"
            ]
        ):

            add_error(
                "LOB_MISMATCH",
                eligibility_id,
            )

        if (
            row["product_type"]
            != product[
                "product_type"
            ]
        ):

            add_error(
                "PRODUCT_TYPE_MISMATCH",
                eligibility_id,
            )

        if (
            row["network_id"]
            != plan["network_id"]
        ):

            add_error(
                "NETWORK_MISMATCH",
                eligibility_id,
            )

        # -------------------------------------------------
        # Benefit flags must match Benefit Plan
        # -------------------------------------------------

        for field_name in [
            "medical_coverage_flag",
            "pharmacy_coverage_flag",
            "dental_coverage_flag",
            "vision_coverage_flag",
        ]:

            if (
                row[field_name]
                != plan[field_name]
            ):

                add_error(
                    "BENEFIT_FLAG_MISMATCH",
                    (
                        f"{eligibility_id}: "
                        f"{field_name}"
                    ),
                )

        # -------------------------------------------------
        # Parse eligibility dates
        # -------------------------------------------------

        coverage_start = (
            parse_date(
                row[
                    "coverage_start_date"
                ]
            )
        )

        coverage_end = (
            parse_date(
                row[
                    "coverage_end_date"
                ]
            )
        )

        event_effective = (
            parse_date(
                row[
                    "event_effective_date"
                ]
            )
        )

        transaction_date = (
            parse_date(
                row[
                    "transaction_date"
                ]
            )
        )

        if (
            not coverage_start
            or not event_effective
            or not transaction_date
        ):

            add_error(
                "MISSING_REQUIRED_DATE",
                eligibility_id,
            )

            continue

        # -------------------------------------------------
        # Generic date integrity
        # -------------------------------------------------

        if (
            coverage_end
            and coverage_end
            < coverage_start
        ):

            add_error(
                "INVALID_COVERAGE_RANGE",
                (
                    f"{eligibility_id}: "
                    f"{coverage_start} > "
                    f"{coverage_end}"
                ),
            )

        if (
            dob
            and coverage_start < dob
        ):

            add_error(
                "COVERAGE_BEFORE_BIRTH",
                (
                    f"{eligibility_id}: "
                    f"coverage {coverage_start}, "
                    f"DOB {dob}"
                ),
            )

        if (
            death_date
            and coverage_start > death_date
        ):

            add_error(
                "COVERAGE_AFTER_DEATH",
                (
                    f"{eligibility_id}: "
                    f"coverage {coverage_start}, "
                    f"death {death_date}"
                ),
            )

        if (
            death_date
            and row[
                "eligibility_status"
            ] == "ACTIVE"
            and event_effective
            > death_date
        ):

            add_error(
                "ACTIVE_AFTER_DEATH",
                (
                    f"{eligibility_id}: "
                    f"event {event_effective}, "
                    f"death {death_date}"
                ),
            )

        if (
            row[
                "future_enrollment_flag"
            ]
            != "Y"
            and transaction_date
            > DATA_END_DATE
        ):

            add_error(
                "TRANSACTION_AFTER_DATA_END",
                eligibility_id,
            )

        # -------------------------------------------------
        # Product / Plan / Group / Subgroup date integrity
        # -------------------------------------------------

        parents = [
            (
                "PRODUCT",
                product,
            ),
            (
                "PLAN",
                plan,
            ),
            (
                "GROUP",
                group,
            ),
            (
                "SUBGROUP",
                subgroup,
            ),
        ]

        for (
            parent_name,
            parent,
        ) in parents:

            parent_start = (
                parse_date(
                    parent[
                        "effective_date"
                    ]
                )
            )

            parent_end = (
                parse_date(
                    parent[
                        "termination_date"
                    ]
                )
            )

            if (
                parent_start
                and coverage_start
                < parent_start
            ):

                add_error(
                    "PARENT_DATE_MISMATCH",
                    (
                        f"{eligibility_id}: "
                        f"coverage starts "
                        f"{coverage_start} before "
                        f"{parent_name} "
                        f"{parent_start}"
                    ),
                )

            if (
                parent_end
                and coverage_start
                > parent_end
            ):

                add_error(
                    "PARENT_DATE_MISMATCH",
                    (
                        f"{eligibility_id}: "
                        f"coverage starts "
                        f"{coverage_start} after "
                        f"{parent_name} ended "
                        f"{parent_end}"
                    ),
                )

            if (
                parent_end
                and row[
                    "eligibility_status"
                ]
                in [
                    "ACTIVE",
                    "FUTURE",
                ]
                and event_effective
                > parent_end
            ):

                add_error(
                    "ACTIVE_AFTER_PARENT_TERM",
                    (
                        f"{eligibility_id}: "
                        f"{parent_name} ended "
                        f"{parent_end}, "
                        f"event={event_effective}"
                    ),
                )

        # -------------------------------------------------
        # Generic termination integrity
        # -------------------------------------------------

        if (
            event_type
            in termination_events
        ):

            if (
                row[
                    "eligibility_status"
                ]
                != "TERMINATED"
            ):

                add_error(
                    "TERMINATION_STATUS_ERROR",
                    eligibility_id,
                )

            if not coverage_end:

                add_error(
                    "TERMINATION_MISSING_END_DATE",
                    eligibility_id,
                )

            if not row[
                "termination_reason"
            ]:

                add_error(
                    "TERMINATION_REASON_MISSING",
                    eligibility_id,
                )

        # -------------------------------------------------
        # RETRO TERM
        # -------------------------------------------------

        if (
            event_type
            == "RETRO_TERM"
        ):

            if (
                transaction_date
                <= event_effective
            ):

                add_error(
                    "RETRO_TERM_DATE_ERROR",
                    (
                        f"{eligibility_id}: "
                        f"effective="
                        f"{event_effective}, "
                        f"transaction="
                        f"{transaction_date}"
                    ),
                )

            if (
                row[
                    "retroactive_flag"
                ]
                != "Y"
            ):

                add_error(
                    "RETRO_TERM_FLAG_ERROR",
                    eligibility_id,
                )

            if (
                coverage_end
                != event_effective
            ):

                add_error(
                    "RETRO_TERM_END_DATE_ERROR",
                    eligibility_id,
                )

        # -------------------------------------------------
        # COVERAGE CORRECTION
        # -------------------------------------------------

        if (
            event_type
            == "COVERAGE_CORRECTION"
        ):

            if (
                row[
                    "retroactive_flag"
                ]
                != "Y"
            ):

                add_error(
                    "CORRECTION_RETRO_FLAG_ERROR",
                    eligibility_id,
                )

            if (
                transaction_date
                < event_effective
            ):

                add_error(
                    "CORRECTION_DATE_ERROR",
                    eligibility_id,
                )

        # -------------------------------------------------
        # FUTURE ENROLLMENT
        # -------------------------------------------------

        if (
            event_type
            == "FUTURE_ENROLLMENT"
        ):

            if (
                row[
                    "future_enrollment_flag"
                ]
                != "Y"
            ):

                add_error(
                    "FUTURE_FLAG_ERROR",
                    eligibility_id,
                )

            if (
                row[
                    "eligibility_status"
                ]
                != "FUTURE"
            ):

                add_error(
                    "FUTURE_STATUS_ERROR",
                    eligibility_id,
                )

            if (
                coverage_start
                <= DATA_END_DATE
            ):

                add_error(
                    "FUTURE_START_DATE_ERROR",
                    eligibility_id,
                )

            if (
                event_effective
                != coverage_start
            ):

                add_error(
                    "FUTURE_EFFECTIVE_DATE_ERROR",
                    eligibility_id,
                )

            if (
                transaction_date
                > DATA_END_DATE
            ):

                add_error(
                    "FUTURE_TRANSACTION_DATE_ERROR",
                    eligibility_id,
                )

        # -------------------------------------------------
        # REINSTATEMENT
        # -------------------------------------------------

        if (
            event_type
            == "REINSTATEMENT"
        ):

            if (
                row[
                    "reinstatement_flag"
                ]
                != "Y"
            ):

                add_error(
                    "REINSTATEMENT_FLAG_ERROR",
                    eligibility_id,
                )

            if (
                row[
                    "eligibility_status"
                ]
                != "ACTIVE"
            ):

                add_error(
                    "REINSTATEMENT_STATUS_ERROR",
                    eligibility_id,
                )

            if (
                coverage_start
                != event_effective
            ):

                add_error(
                    "REINSTATEMENT_START_ERROR",
                    eligibility_id,
                )

        # -------------------------------------------------
        # DEATH
        # -------------------------------------------------

        if (
            event_type
            == "DEATH"
        ):

            if not death_date:

                add_error(
                    "DEATH_EVENT_WITHOUT_DEATH_DATE",
                    eligibility_id,
                )

            else:

                if (
                    event_effective
                    != death_date
                ):

                    add_error(
                        "DEATH_EFFECTIVE_DATE_ERROR",
                        eligibility_id,
                    )

                if (
                    coverage_end
                    != death_date
                ):

                    add_error(
                        "DEATH_COVERAGE_END_ERROR",
                        eligibility_id,
                    )

                if (
                    coverage_start
                    > death_date
                ):

                    add_error(
                        "DEATH_BEFORE_COVERAGE_START",
                        eligibility_id,
                    )

        # -------------------------------------------------
        # NEWBORN
        # -------------------------------------------------

        if (
            event_type
            == "NEWBORN_ADDITION"
        ):

            if (
                member[
                    "relationship_to_subscriber"
                ]
                != "CHILD"
            ):

                add_error(
                    "NEWBORN_NOT_CHILD",
                    eligibility_id,
                )

            if (
                dob
                and event_effective
                != dob
            ):

                add_error(
                    "NEWBORN_EFFECTIVE_DATE_ERROR",
                    eligibility_id,
                )

            if (
                dob
                and coverage_start
                != dob
            ):

                add_error(
                    "NEWBORN_COVERAGE_START_ERROR",
                    eligibility_id,
                )

        # -------------------------------------------------
        # DEPENDENT AGE OUT
        # -------------------------------------------------

        if (
            event_type
            == "DEPENDENT_AGE_OUT"
        ):

            if (
                member[
                    "relationship_to_subscriber"
                ]
                != "CHILD"
            ):

                add_error(
                    "AGE_OUT_NOT_CHILD",
                    eligibility_id,
                )

            age_out_date = (
                add_years(
                    dob,
                    26,
                )
                if dob
                else None
            )

            if (
                age_out_date
                and event_effective
                != age_out_date
            ):

                add_error(
                    "AGE_OUT_DATE_ERROR",
                    eligibility_id,
                )

            if (
                age_out_date
                and coverage_end
                != age_out_date
            ):

                add_error(
                    "AGE_OUT_END_DATE_ERROR",
                    eligibility_id,
                )

        # -------------------------------------------------
        # REMOVE DEPENDENT
        # -------------------------------------------------

        if (
            event_type
            == "REMOVE_DEPENDENT"
            and member[
                "relationship_to_subscriber"
            ]
            == "SELF"
        ):

            add_error(
                "REMOVE_DEPENDENT_ON_SELF",
                eligibility_id,
            )

        # -------------------------------------------------
        # Flag exclusivity
        # -------------------------------------------------

        expected_retro_events = {
            "RETRO_TERM",
            "COVERAGE_CORRECTION",
        }

        if (
            row["retroactive_flag"]
            == "Y"
            and event_type
            not in expected_retro_events
        ):

            add_error(
                "UNEXPECTED_RETRO_FLAG",
                eligibility_id,
            )

        if (
            row[
                "future_enrollment_flag"
            ]
            == "Y"
            and event_type
            != "FUTURE_ENROLLMENT"
        ):

            add_error(
                "UNEXPECTED_FUTURE_FLAG",
                eligibility_id,
            )

        if (
            row[
                "reinstatement_flag"
            ]
            == "Y"
            and event_type
            != "REINSTATEMENT"
        ):

            add_error(
                "UNEXPECTED_REINSTATEMENT_FLAG",
                eligibility_id,
            )

        # Medicare should be individual coverage.
        if (
            row[
                "line_of_business"
            ]
            == "MEDICARE"
            and row[
                "coverage_tier"
            ]
            != "INDIVIDUAL"
        ):

            add_error(
                "MEDICARE_COVERAGE_TIER_ERROR",
                eligibility_id,
            )

    # -----------------------------------------------------
    # VERSION / MEMBER HISTORY VALIDATION
    # -----------------------------------------------------

    for member_id in member_lookup:

        rows = (
            versions_by_member.get(
                member_id,
                []
            )
        )

        if len(rows) != 3:

            add_error(
                "VERSION_COUNT_ERROR",
                (
                    f"{member_id}: "
                    f"{len(rows)} versions"
                ),
            )

            continue

        rows = sorted(
            rows,
            key=lambda row: int(
                row["record_version"]
            ),
        )

        versions = [
            int(
                row["record_version"]
            )
            for row in rows
        ]

        if versions != [
            1,
            2,
            3,
        ]:

            add_error(
                "VERSION_SEQUENCE_ERROR",
                (
                    f"{member_id}: "
                    f"{versions}"
                ),
            )

        current_rows = [
            row
            for row in rows
            if row[
                "current_record_flag"
            ]
            == "Y"
        ]

        if len(current_rows) != 1:

            add_error(
                "CURRENT_RECORD_COUNT_ERROR",
                member_id,
            )

        elif (
            current_rows[0][
                "record_version"
            ]
            != "3"
        ):

            add_error(
                "CURRENT_VERSION_ERROR",
                member_id,
            )

        # -------------------------------------------------
        # Transactions must never move backward in time.
        # -------------------------------------------------

        transaction_dates = [
            parse_date(
                row[
                    "transaction_date"
                ]
            )
            for row in rows
        ]

        if not (
            transaction_dates[0]
            <= transaction_dates[1]
            <= transaction_dates[2]
        ):

            add_error(
                "TRANSACTION_CHRONOLOGY_ERROR",
                (
                    f"{member_id}: "
                    f"{transaction_dates}"
                ),
            )

        # -------------------------------------------------
        # Event-specific change validation
        # -------------------------------------------------

        for index in [
            1,
            2,
        ]:

            previous = (
                rows[
                    index - 1
                ]
            )

            current = (
                rows[index]
            )

            event_type = (
                current[
                    "event_type"
                ]
            )

            if (
                event_type
                == "PLAN_CHANGE"
                and current[
                    "benefit_plan_id"
                ]
                == previous[
                    "benefit_plan_id"
                ]
            ):

                add_error(
                    "PLAN_CHANGE_WITHOUT_PLAN_CHANGE",
                    (
                        f"{member_id}: "
                        f"version "
                        f"{current['record_version']}"
                    ),
                )

            if (
                event_type
                == "GROUP_CHANGE"
                and current[
                    "group_id"
                ]
                == previous[
                    "group_id"
                ]
            ):

                add_error(
                    "GROUP_CHANGE_WITHOUT_GROUP_CHANGE",
                    (
                        f"{member_id}: "
                        f"version "
                        f"{current['record_version']}"
                    ),
                )

            if (
                event_type
                == "REINSTATEMENT"
                and previous[
                    "eligibility_status"
                ]
                != "TERMINATED"
            ):

                add_error(
                    "REINSTATEMENT_WITHOUT_TERM",
                    member_id,
                )

            if (
                event_type
                == "COVERAGE_CORRECTION"
            ):

                previous_start = (
                    parse_date(
                        previous[
                            "coverage_start_date"
                        ]
                    )
                )

                current_start = (
                    parse_date(
                        current[
                            "coverage_start_date"
                        ]
                    )
                )

                if (
                    current_start
                    > previous_start
                ):

                    add_error(
                        "INVALID_COVERAGE_CORRECTION",
                        member_id,
                    )

    # -----------------------------------------------------
    # GLOBAL ROW COUNT
    # -----------------------------------------------------

    expected_eligibility_rows = (
        len(members) * 3
    )

    if (
        len(eligibility)
        != expected_eligibility_rows
    ):

        add_error(
            "TOTAL_ROW_COUNT_ERROR",
            (
                f"Expected "
                f"{expected_eligibility_rows:,}; "
                f"found "
                f"{len(eligibility):,}"
            ),
        )

    # -----------------------------------------------------
    # REPORT
    # -----------------------------------------------------

    print()
    print("=" * 80)
    print(
        "ENHANCED ELIGIBILITY VALIDATION"
    )
    print("=" * 80)

    print(
        f"Members          : "
        f"{len(members):,}"
    )

    print(
        f"Eligibility rows : "
        f"{len(eligibility):,}"
    )

    print(
        f"Products         : "
        f"{len(products):,}"
    )

    print(
        f"Benefit Plans    : "
        f"{len(plans):,}"
    )

    print(
        f"Groups           : "
        f"{len(groups):,}"
    )

    print(
        f"Subgroups        : "
        f"{len(subgroups):,}"
    )

    print(
        f"Validation errors: "
        f"{len(errors):,}"
    )

    print()
    print(
        "EVENT DISTRIBUTION"
    )
    print("-" * 80)

    for (
        event,
        count,
    ) in event_counts.most_common():

        print(
            f"{event:35}"
            f"{count:>10,}"
        )

    if errors:

        print()
        print(
            "ERROR SUMMARY"
        )
        print("-" * 80)

        for (
            category,
            count,
        ) in error_counts.most_common():

            print(
                f"{category:45}"
                f"{count:>10,}"
            )

        print()
        print(
            "SAMPLE ERRORS BY CATEGORY"
        )
        print("-" * 80)

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
    print("=" * 80)

    if not errors:

        print(
            "ENHANCED ELIGIBILITY VALIDATION PASSED"
        )

    else:

        print(
            "ENHANCED ELIGIBILITY VALIDATION FAILED"
        )

    print("=" * 80)
    print()


if __name__ == "__main__":
    main()