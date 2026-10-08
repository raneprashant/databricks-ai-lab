"""
Project 01 - Healthcare Payer Data Platform
Module: eligibility_generator.py

Purpose
-------
Generates realistic longitudinal Member Eligibility history for the
healthcare payer source model.

What This Module Does
---------------------
- Loads Member and payer-reference source datasets.
- Creates exactly three Eligibility versions per Member for the
  configured base dataset.
- Links coverage to valid Product, Benefit Plan, Group, and Subgroup
  combinations.
- Enforces effective-date compatibility across the payer hierarchy.
- Models subscriber/dependent and family coverage behavior.
- Generates realistic Eligibility lifecycle events such as:
    - NEW_ENROLLMENT
    - PLAN_CHANGE
    - GROUP_CHANGE
    - DEMOGRAPHIC_CHANGE
    - ADDRESS_CHANGE
    - RETROACTIVE_TERMINATION
    - REINSTATEMENT
    - FUTURE_ENROLLMENT
    - COVERAGE_CORRECTION
    - NEWBORN_ADDITION
    - DEPENDENT_AGE_OUT
    - DEPENDENT_REMOVED
    - DEATH
- Handles member birth, death, age, and relationship constraints.
- Generates coverage dates, transaction dates, event-effective dates,
  source-current indicators, and coverage flags.

Inputs / Dependencies
---------------------
- member/*.csv
- product/*.csv
- benefit_plan/*.csv
- group/*.csv
- subgroup/*.csv
- config.py

Outputs
-------
generated_data/<scale>/eligibility/eligibility_###.csv

Execution
---------
Normally invoked through:

    python generate_data.py --scale medium --domain eligibility

Important Notes
---------------
For the base dataset, the configured Eligibility row count must equal
three records per Member.

Eligibility is intentionally modeled as event/history data rather than
as a simple one-row-per-member current-state table.
"""


import csv
import random
from collections import defaultdict
from datetime import date, datetime, timedelta
from pathlib import Path

from config import (
    DATA_END_DATE,
    DATA_START_DATE,
    FUTURE_COVERAGE_END_DATE,
    RANDOM_SEED,
    ROWS_PER_FILE,
)


ELIGIBILITY_COLUMNS = [
    "eligibility_id",
    "member_id",
    "subscriber_id",
    "family_id",
    "relationship_to_subscriber",
    "group_id",
    "subgroup_id",
    "product_id",
    "benefit_plan_id",
    "line_of_business",
    "product_type",
    "network_id",
    "coverage_tier",
    "coverage_start_date",
    "coverage_end_date",
    "eligibility_status",
    "event_type",
    "event_effective_date",
    "transaction_date",
    "termination_reason",
    "retroactive_flag",
    "future_enrollment_flag",
    "reinstatement_flag",
    "medical_coverage_flag",
    "pharmacy_coverage_flag",
    "dental_coverage_flag",
    "vision_coverage_flag",
    "record_version",
    "current_record_flag",
    "source_system",
    "source_eligibility_key",
    "create_ts",
    "update_ts",
]


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


def calculate_age(
    birth_date: date,
    as_of_date: date,
) -> int:

    age = (
        as_of_date.year
        - birth_date.year
    )

    if (
        as_of_date.month,
        as_of_date.day,
    ) < (
        birth_date.month,
        birth_date.day,
    ):
        age -= 1

    return age


def add_years(
    value: date,
    years: int,
) -> date:

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


def random_date_between(
    start_date: date,
    end_date: date,
    rng: random.Random,
):

    if end_date <= start_date:
        return start_date

    days = (
        end_date - start_date
    ).days

    return start_date + timedelta(
        days=rng.randint(
            0,
            days,
        )
    )


def build_followup_dates(
    baseline_start: date,
    rng: random.Random,
):

    # Never operate beyond the observation window.
    baseline_start = min(
        baseline_start,
        DATA_END_DATE,
    )

    remaining_days = (
        DATA_END_DATE
        - baseline_start
    ).days

    # Member entered on the last available day.
    # Later versions may be processed on that
    # same date, but never before Version 1.
    if remaining_days <= 0:

        return (
            DATA_END_DATE,
            DATA_END_DATE,
        )

    # Only one later day is available.
    if remaining_days == 1:

        return (
            DATA_END_DATE,
            DATA_END_DATE,
        )

    # Version 2 must occur strictly after
    # Version 1 whenever the timeline allows it.
    event2_min = (
        baseline_start
        + timedelta(days=1)
    )

    event2_max = (
        DATA_END_DATE
        - timedelta(days=1)
    )

    event2_date = random_date_between(
        event2_min,
        event2_max,
        rng,
    )

    # Version 3 occurs after Version 2.
    event3_min = min(
        event2_date
        + timedelta(days=1),
        DATA_END_DATE,
    )

    event3_date = random_date_between(
        event3_min,
        DATA_END_DATE,
        rng,
    )

    return (
        event2_date,
        event3_date,
    )



def determine_coverage_tier(
    family_members: list,
    line_of_business: str,
):

    # Medicare eligibility is ordinarily individual.
    if line_of_business == "MEDICARE":
        return "INDIVIDUAL"

    family_size = len(
        family_members
    )

    if family_size == 1:
        return "EMPLOYEE_ONLY"

    has_spouse = any(
        member[
            "relationship_to_subscriber"
        ] == "SPOUSE"
        for member in family_members
    )

    has_child = any(
        member[
            "relationship_to_subscriber"
        ] == "CHILD"
        for member in family_members
    )

    if (
        has_spouse
        and has_child
    ):
        return "FAMILY"

    if has_spouse:
        return "EMPLOYEE_SPOUSE"

    if has_child:
        return "EMPLOYEE_CHILDREN"

    return "FAMILY"


def desired_lob_for_member(
    member: dict,
    rng: random.Random,
):

    dob = parse_date(
        member["date_of_birth"]
    )

    age = calculate_age(
        dob,
        DATA_END_DATE,
    )

    relationship = (
        member[
            "relationship_to_subscriber"
        ]
    )

    # Medicare is much more likely for age 65+.
    if age >= 65:

        return rng.choices(
            population=[
                "MEDICARE",
                "COMMERCIAL",
                "MEDICAID",
                "EXCHANGE",
            ],
            weights=[
                72,
                10,
                10,
                8,
            ],
            k=1,
        )[0]

    # Dependents generally participate through
    # commercial / Medicaid / exchange coverage.
    if relationship != "SELF":

        return rng.choices(
            population=[
                "COMMERCIAL",
                "MEDICAID",
                "EXCHANGE",
            ],
            weights=[
                72,
                18,
                10,
            ],
            k=1,
        )[0]

    return rng.choices(
        population=[
            "COMMERCIAL",
            "MEDICAID",
            "EXCHANGE",
        ],
        weights=[
            70,
            17,
            13,
        ],
        k=1,
    )[0]

def coverage_valid_on_date(
    coverage: dict,
    target_date: date,
) -> bool:

    """
    A coverage hierarchy is usable only when Product,
    Benefit Plan, Group and Subgroup are all effective
    on the requested date.
    """

    for parent_name in [
        "product",
        "plan",
        "group",
        "subgroup",
    ]:

        parent = coverage[
            parent_name
        ]

        effective_date = parse_date(
            parent["effective_date"]
        )

        termination_date = parse_date(
            parent["termination_date"]
        )

        if (
            effective_date
            and target_date
            < effective_date
        ):
            return False

        if (
            termination_date
            and target_date
            > termination_date
        ):
            return False

    return True


def build_reference_indexes(
    products: list,
    plans: list,
    groups: list,
    subgroups: list,
):

    product_by_id = {
        row["product_id"]: row
        for row in products
    }

    plan_by_id = {
        row["benefit_plan_id"]: row
        for row in plans
    }

    group_by_id = {
        row["group_id"]: row
        for row in groups
    }

    subgroup_details = []

    all_by_lob = defaultdict(
        list
    )

    current_by_lob = defaultdict(
        list
    )

    for subgroup in subgroups:

        group = group_by_id[
            subgroup["group_id"]
        ]

        plan = plan_by_id[
            subgroup[
                "benefit_plan_id"
            ]
        ]

        product = product_by_id[
            plan["product_id"]
        ]

        coverage = {
            "subgroup": subgroup,
            "group": group,
            "plan": plan,
            "product": product,
        }

        subgroup_details.append(
            coverage
        )

        lob = product[
            "line_of_business"
        ]

        # All combinations are retained because some
        # may be useful for future enrollment.
        all_by_lob[
            lob
        ].append(
            coverage
        )

        # Current coverage must still be valid on the
        # end of our observation period.
        #
        # Choosing baseline/current coverage from this
        # collection prevents an ACTIVE eligibility row
        # from continuing after its Group/Subgroup ended.
        if coverage_valid_on_date(
            coverage,
            DATA_END_DATE,
        ):

            current_by_lob[
                lob
            ].append(
                coverage
            )

    return (
        product_by_id,
        plan_by_id,
        group_by_id,
        subgroup_details,
        current_by_lob,
        all_by_lob,
    )


def choose_initial_coverage(
    member: dict,
    subscriber_coverage: dict,
    current_by_lob: dict,
    rng: random.Random,
):

    relationship = (
        member[
            "relationship_to_subscriber"
        ]
    )

    # Dependents normally inherit the subscriber's
    # coverage unless the subscriber has Medicare.
    if (
        relationship != "SELF"
        and subscriber_coverage
        and subscriber_coverage[
            "product"
        ][
            "line_of_business"
        ]
        != "MEDICARE"
    ):

        return subscriber_coverage

    desired_lob = (
        desired_lob_for_member(
            member,
            rng,
        )
    )

    candidates = list(
        current_by_lob.get(
            desired_lob,
            [],
        )
    )

    # Defensive fallback if a particular LOB happens
    # to have no valid current offering in a small
    # synthetic sample.
    if not candidates:

        for rows in (
            current_by_lob.values()
        ):
            candidates.extend(
                rows
            )

    if not candidates:

        raise RuntimeError(
            "No Product / Plan / Group / "
            "Subgroup combination is valid "
            "through DATA_END_DATE."
        )

    return rng.choice(
        candidates
    )


def choose_plan_change_coverage(
    current_coverage: dict,
    current_by_lob: dict,
    rng: random.Random,
):

    lob = (
        current_coverage[
            "product"
        ][
            "line_of_business"
        ]
    )

    current_plan_id = (
        current_coverage[
            "plan"
        ][
            "benefit_plan_id"
        ]
    )

    current_group_id = (
        current_coverage[
            "group"
        ][
            "group_id"
        ]
    )

    # Prefer changing plans within the same Group.
    candidates = [
        item
        for item in current_by_lob[
            lob
        ]
        if (
            item[
                "plan"
            ][
                "benefit_plan_id"
            ]
            != current_plan_id
            and item[
                "group"
            ][
                "group_id"
            ]
            == current_group_id
        )
    ]

    # If this synthetic Group doesn't offer another
    # plan, allow another compatible Group — but the
    # Benefit Plan still MUST actually change.
    if not candidates:

        candidates = [
            item
            for item in current_by_lob[
                lob
            ]
            if (
                item[
                    "plan"
                ][
                    "benefit_plan_id"
                ]
                != current_plan_id
            )
        ]

    if not candidates:

        raise RuntimeError(
            "PLAN_CHANGE requested but no "
            "different Benefit Plan is available."
        )

    return rng.choice(
        candidates
    )


def choose_group_change_coverage(
    current_coverage: dict,
    current_by_lob: dict,
    rng: random.Random,
):

    lob = (
        current_coverage[
            "product"
        ][
            "line_of_business"
        ]
    )

    current_group_id = (
        current_coverage[
            "group"
        ][
            "group_id"
        ]
    )

    candidates = [
        item
        for item in current_by_lob[
            lob
        ]
        if (
            item[
                "group"
            ][
                "group_id"
            ]
            != current_group_id
        )
    ]

    if not candidates:

        raise RuntimeError(
            "GROUP_CHANGE requested but no "
            "different Group is available."
        )

    return rng.choice(
        candidates
    )


def choose_future_coverage(
    current_coverage: dict,
    all_by_lob: dict,
    future_start: date,
    rng: random.Random,
):

    lob = (
        current_coverage[
            "product"
        ][
            "line_of_business"
        ]
    )

    candidates = [
        coverage
        for coverage
        in all_by_lob[
            lob
        ]
        if coverage_valid_on_date(
            coverage,
            future_start,
        )
    ]

    if not candidates:

        raise RuntimeError(
            "No Product / Plan / Group / "
            "Subgroup combination is valid "
            f"for future date {future_start}."
        )

    return rng.choice(
        candidates
    )

def scenario_for_member(
    member: dict,
    rng: random.Random,
):

    dob = parse_date(
        member["date_of_birth"]
    )

    death_date = parse_date(
        member["death_date"]
    )

    relationship = (
        member[
            "relationship_to_subscriber"
        ]
    )

    # Real member-life events override random scenarios.
    if (
        death_date
        and DATA_START_DATE
        <= death_date
        <= DATA_END_DATE
    ):
        return "DEATH"

    if (
        relationship == "CHILD"
        and DATA_START_DATE
        <= dob
        <= DATA_END_DATE
    ):
        return "NEWBORN"

    if relationship == "CHILD":

        age_out_date = add_years(
            dob,
            26,
        )

        if (
            DATA_START_DATE
            <= age_out_date
            <= DATA_END_DATE
        ):
            return "AGE_OUT"

    choices = [
        "STANDARD",
        "PLAN_CHANGE",
        "GROUP_CHANGE",
        "RETRO_TERM",
        "REINSTATEMENT",
        "FUTURE_ENROLLMENT",
        "COVERAGE_CORRECTION",
    ]

    weights = [
        27,
        20,
        8,
        10,
        10,
        10,
        15,
    ]

    if relationship != "SELF":

        choices.append(
            "REMOVE_DEPENDENT"
        )

        weights.append(
            8
        )

    return rng.choices(
        population=choices,
        weights=weights,
        k=1,
    )[0]


def baseline_event_type(
    member: dict,
):

    dob = parse_date(
        member["date_of_birth"]
    )

    relationship = (
        member[
            "relationship_to_subscriber"
        ]
    )

    if (
        relationship == "CHILD"
        and DATA_START_DATE
        <= dob
        <= DATA_END_DATE
    ):
        return "NEWBORN_ADDITION"

    if relationship != "SELF":
        return "ADD_DEPENDENT"

    return "NEW_ENROLLMENT"


def make_row(
    eligibility_number: int,
    member: dict,
    coverage: dict,
    family_members: list,
    version: int,
    current_record_flag: str,
    event_type: str,
    event_effective_date: date,
    transaction_date: date,
    coverage_start_date: date,
    coverage_end_date,
    eligibility_status: str,
    termination_reason: str,
    retroactive_flag: str,
    future_enrollment_flag: str,
    reinstatement_flag: str,
    rng: random.Random,
):

    product = coverage[
        "product"
    ]

    plan = coverage[
        "plan"
    ]

    group = coverage[
        "group"
    ]

    subgroup = coverage[
        "subgroup"
    ]

    coverage_tier = (
        determine_coverage_tier(
            family_members,
            product[
                "line_of_business"
            ],
        )
    )

    create_date = min(
        transaction_date,
        DATA_END_DATE,
    )

    return {
        "eligibility_id": (
            f"ELIG"
            f"{eligibility_number:010d}"
        ),
        "member_id": (
            member["member_id"]
        ),
        "subscriber_id": (
            member["subscriber_id"]
        ),
        "family_id": (
            member["family_id"]
        ),
        "relationship_to_subscriber": (
            member[
                "relationship_to_subscriber"
            ]
        ),
        "group_id": (
            group["group_id"]
        ),
        "subgroup_id": (
            subgroup["subgroup_id"]
        ),
        "product_id": (
            product["product_id"]
        ),
        "benefit_plan_id": (
            plan["benefit_plan_id"]
        ),
        "line_of_business": (
            product[
                "line_of_business"
            ]
        ),
        "product_type": (
            product[
                "product_type"
            ]
        ),
        "network_id": (
            plan["network_id"]
        ),
        "coverage_tier": (
            coverage_tier
        ),
        "coverage_start_date": (
            coverage_start_date.isoformat()
        ),
        "coverage_end_date": (
            coverage_end_date.isoformat()
            if coverage_end_date
            else ""
        ),
        "eligibility_status": (
            eligibility_status
        ),
        "event_type": (
            event_type
        ),
        "event_effective_date": (
            event_effective_date.isoformat()
        ),
        "transaction_date": (
            transaction_date.isoformat()
        ),
        "termination_reason": (
            termination_reason
        ),
        "retroactive_flag": (
            retroactive_flag
        ),
        "future_enrollment_flag": (
            future_enrollment_flag
        ),
        "reinstatement_flag": (
            reinstatement_flag
        ),
        "medical_coverage_flag": (
            plan[
                "medical_coverage_flag"
            ]
        ),
        "pharmacy_coverage_flag": (
            plan[
                "pharmacy_coverage_flag"
            ]
        ),
        "dental_coverage_flag": (
            plan[
                "dental_coverage_flag"
            ]
        ),
        "vision_coverage_flag": (
            plan[
                "vision_coverage_flag"
            ]
        ),
        "record_version": (
            version
        ),
        "current_record_flag": (
            current_record_flag
        ),
        "source_system": (
            "SYNTHETIC_ENROLLMENT"
        ),
        "source_eligibility_key": (
            f"SRCELIG"
            f"{eligibility_number:010d}"
        ),
        "create_ts": build_timestamp(
            create_date,
            rng,
        ),
        "update_ts": build_timestamp(
            create_date,
            rng,
        ),
    }


def generate_member_history(
    member: dict,
    family_members: list,
    initial_coverage: dict,
    current_by_lob: dict,
    all_by_lob: dict,
    starting_eligibility_number: int,
    rng: random.Random,
):

    rows = []

    dob = parse_date(
        member["date_of_birth"]
    )

    death_date = parse_date(
        member["death_date"]
    )

    relationship = (
        member[
            "relationship_to_subscriber"
        ]
    )

    scenario = scenario_for_member(
        member,
        rng,
    )

    # -----------------------------------------------------
    # Determine a valid initial coverage date.
    #
    # Coverage cannot start:
    #   - before birth
    #   - after death for a death scenario
    #   - after dependent age-out for an age-out scenario
    # -----------------------------------------------------

    if scenario == "NEWBORN":

        baseline_start = dob

    elif scenario == "DEATH":

        baseline_floor = max(
            DATA_START_DATE,
            dob,
        )

        baseline_ceiling = min(
            date(2024, 6, 30),
            death_date,
        )

        if (
            baseline_ceiling
            < baseline_floor
        ):

            baseline_start = (
                baseline_floor
            )

        else:

            baseline_start = (
                random_date_between(
                    baseline_floor,
                    baseline_ceiling,
                    rng,
                )
            )

    elif scenario == "AGE_OUT":

        age_out_date = add_years(
            dob,
            26,
        )

        baseline_floor = max(
            DATA_START_DATE,
            dob,
        )

        baseline_ceiling = min(
            date(2024, 6, 30),
            age_out_date,
        )

        if (
            baseline_ceiling
            < baseline_floor
        ):

            baseline_start = (
                baseline_floor
            )

        else:

            baseline_start = (
                random_date_between(
                    baseline_floor,
                    baseline_ceiling,
                    rng,
                )
            )

    elif (
        relationship == "CHILD"
        and dob > DATA_START_DATE
    ):

        baseline_start = min(
            dob,
            DATA_END_DATE,
        )

    else:

        baseline_start = (
            random_date_between(
                DATA_START_DATE,
                date(2024, 6, 30),
                rng,
            )
        )

    # -----------------------------------------------------
    # VERSION 1
    # -----------------------------------------------------

    event1 = baseline_event_type(
        member
    )

    transaction1 = baseline_start

    current_coverage = (
        initial_coverage
    )

    rows.append(
        make_row(
            starting_eligibility_number,
            member,
            current_coverage,
            family_members,
            1,
            "N",
            event1,
            baseline_start,
            transaction1,
            baseline_start,
            None,
            "ACTIVE",
            "",
            "N",
            "N",
            "N",
            rng,
        )
    )

    # -----------------------------------------------------
    # VERSION 2 / VERSION 3 timeline
    # -----------------------------------------------------

    (
        event2_date,
        event3_date,
    ) = build_followup_dates(
        baseline_start,
        rng,
    )

    # -----------------------------------------------------
    # Scenario-specific Version 2 / Version 3
    # -----------------------------------------------------

    if scenario == "PLAN_CHANGE":

        new_coverage = (
            choose_plan_change_coverage(
                current_coverage,
                current_by_lob,
                rng,
            )
        )

        rows.append(
            make_row(
                starting_eligibility_number + 1,
                member,
                new_coverage,
                family_members,
                2,
                "N",
                "PLAN_CHANGE",
                event2_date,
                event2_date,
                event2_date,
                None,
                "ACTIVE",
                "",
                "N",
                "N",
                "N",
                rng,
            )
        )

        current_coverage = (
            new_coverage
        )

        rows.append(
            make_row(
                starting_eligibility_number + 2,
                member,
                current_coverage,
                family_members,
                3,
                "Y",
                "DEMOGRAPHIC_CHANGE",
                event3_date,
                event3_date,
                event2_date,
                None,
                "ACTIVE",
                "",
                "N",
                "N",
                "N",
                rng,
            )
        )

    elif scenario == "GROUP_CHANGE":

        new_coverage = (
            choose_group_change_coverage(
                current_coverage,
                current_by_lob,
                rng,
            )
        )

        rows.append(
            make_row(
                starting_eligibility_number + 1,
                member,
                new_coverage,
                family_members,
                2,
                "N",
                "GROUP_CHANGE",
                event2_date,
                event2_date,
                event2_date,
                None,
                "ACTIVE",
                "",
                "N",
                "N",
                "N",
                rng,
            )
        )

        rows.append(
            make_row(
                starting_eligibility_number + 2,
                member,
                new_coverage,
                family_members,
                3,
                "Y",
                "ADDRESS_CHANGE",
                event3_date,
                event3_date,
                event2_date,
                None,
                "ACTIVE",
                "",
                "N",
                "N",
                "N",
                rng,
            )
        )

    elif scenario == "RETRO_TERM":

        rows.append(
            make_row(
                starting_eligibility_number + 1,
                member,
                current_coverage,
                family_members,
                2,
                "N",
                "DEMOGRAPHIC_CHANGE",
                event2_date,
                event2_date,
                baseline_start,
                None,
                "ACTIVE",
                "",
                "N",
                "N",
                "N",
                rng,
            )
        )

        # A retro termination must have an
        # effective date strictly before the
        # transaction date.

        latest_retro_end = (
            event3_date
            - timedelta(days=1)
        )

        if (
            latest_retro_end
            < baseline_start
        ):

            raise RuntimeError(
                "RETRO_TERM scenario does not "
                "have enough historical time "
                f"for member {member['member_id']}."
            )

        retro_end = random_date_between(
            baseline_start,
            latest_retro_end,
            rng,
        )

        rows.append(
            make_row(
                starting_eligibility_number + 2,
                member,
                current_coverage,
                family_members,
                3,
                "Y",
                "RETRO_TERM",
                retro_end,
                event3_date,
                baseline_start,
                retro_end,
                "TERMINATED",
                "RETROACTIVE_TERMINATION",
                "Y",
                "N",
                "N",
                rng,
            )
        )

    elif scenario == "REINSTATEMENT":

        rows.append(
            make_row(
                starting_eligibility_number + 1,
                member,
                current_coverage,
                family_members,
                2,
                "N",
                "VOLUNTARY_TERM",
                event2_date,
                event2_date,
                baseline_start,
                event2_date,
                "TERMINATED",
                "VOLUNTARY",
                "N",
                "N",
                "N",
                rng,
            )
        )

        reinstate_date = min(
            event2_date
            + timedelta(
                days=rng.randint(
                    5,
                    45,
                )
            ),
            DATA_END_DATE,
        )

        rows.append(
            make_row(
                starting_eligibility_number + 2,
                member,
                current_coverage,
                family_members,
                3,
                "Y",
                "REINSTATEMENT",
                reinstate_date,
                reinstate_date,
                reinstate_date,
                None,
                "ACTIVE",
                "",
                "N",
                "N",
                "Y",
                rng,
            )
        )

    elif scenario == "FUTURE_ENROLLMENT":

        rows.append(
            make_row(
                starting_eligibility_number + 1,
                member,
                current_coverage,
                family_members,
                2,
                "N",
                "ADDRESS_CHANGE",
                event2_date,
                event2_date,
                baseline_start,
                None,
                "ACTIVE",
                "",
                "N",
                "N",
                "N",
                rng,
            )
        )


        future_start = (
            random_date_between(
                DATA_END_DATE
                + timedelta(days=1),
                FUTURE_COVERAGE_END_DATE,
                rng,
            )
        )

        future_coverage = (
            choose_future_coverage(
                current_coverage,
                all_by_lob,
                future_start,
                rng,
            )
        )

        rows.append(
            make_row(
                starting_eligibility_number + 2,
                member,
                future_coverage,
                family_members,
                3,
                "Y",
                "FUTURE_ENROLLMENT",
                future_start,
                DATA_END_DATE,
                future_start,
                None,
                "FUTURE",
                "",
                "N",
                "Y",
                "N",
                rng,
            )
        )

    elif scenario == "COVERAGE_CORRECTION":

        rows.append(
            make_row(
                starting_eligibility_number + 1,
                member,
                current_coverage,
                family_members,
                2,
                "N",
                "DEMOGRAPHIC_CHANGE",
                event2_date,
                event2_date,
                baseline_start,
                None,
                "ACTIVE",
                "",
                "N",
                "N",
                "N",
                rng,
            )
        )

        corrected_start = max(
            DATA_START_DATE,
            baseline_start
            - timedelta(
                days=rng.randint(
                    1,
                    30,
                )
            ),
        )

        rows.append(
            make_row(
                starting_eligibility_number + 2,
                member,
                current_coverage,
                family_members,
                3,
                "Y",
                "COVERAGE_CORRECTION",
                corrected_start,
                event3_date,
                corrected_start,
                None,
                "ACTIVE",
                "",
                "Y",
                "N",
                "N",
                rng,
            )
        )

    elif scenario == "DEATH":

        death_effective = (
            death_date
        )

        event2_date = min(
            event2_date,
            max(
                baseline_start,
                death_effective
                - timedelta(days=15),
            ),
        )

        rows.append(
            make_row(
                starting_eligibility_number + 1,
                member,
                current_coverage,
                family_members,
                2,
                "N",
                "DEMOGRAPHIC_CHANGE",
                event2_date,
                event2_date,
                baseline_start,
                None,
                "ACTIVE",
                "",
                "N",
                "N",
                "N",
                rng,
            )
        )

        rows.append(
            make_row(
                starting_eligibility_number + 2,
                member,
                current_coverage,
                family_members,
                3,
                "Y",
                "DEATH",
                death_effective,
                death_effective,
                baseline_start,
                death_effective,
                "TERMINATED",
                "DEATH",
                "N",
                "N",
                "N",
                rng,
            )
        )

    elif scenario == "AGE_OUT":

        age_out_date = add_years(
            dob,
            26,
        )

        pre_age_out = max(
            baseline_start,
            age_out_date
            - timedelta(days=30),
        )

        rows.append(
            make_row(
                starting_eligibility_number + 1,
                member,
                current_coverage,
                family_members,
                2,
                "N",
                "DEMOGRAPHIC_CHANGE",
                pre_age_out,
                pre_age_out,
                baseline_start,
                None,
                "ACTIVE",
                "",
                "N",
                "N",
                "N",
                rng,
            )
        )

        rows.append(
            make_row(
                starting_eligibility_number + 2,
                member,
                current_coverage,
                family_members,
                3,
                "Y",
                "DEPENDENT_AGE_OUT",
                age_out_date,
                age_out_date,
                baseline_start,
                age_out_date,
                "TERMINATED",
                "DEPENDENT_AGE_OUT",
                "N",
                "N",
                "N",
                rng,
            )
        )

    elif scenario == "NEWBORN":

        rows.append(
            make_row(
                starting_eligibility_number + 1,
                member,
                current_coverage,
                family_members,
                2,
                "N",
                "DEMOGRAPHIC_CHANGE",
                min(
                    dob
                    + timedelta(days=30),
                    DATA_END_DATE,
                ),
                min(
                    dob
                    + timedelta(days=30),
                    DATA_END_DATE,
                ),
                dob,
                None,
                "ACTIVE",
                "",
                "N",
                "N",
                "N",
                rng,
            )
        )

        rows.append(
            make_row(
                starting_eligibility_number + 2,
                member,
                current_coverage,
                family_members,
                3,
                "Y",
                "ADDRESS_CHANGE",
                min(
                    dob
                    + timedelta(days=90),
                    DATA_END_DATE,
                ),
                min(
                    dob
                    + timedelta(days=90),
                    DATA_END_DATE,
                ),
                dob,
                None,
                "ACTIVE",
                "",
                "N",
                "N",
                "N",
                rng,
            )
        )

    elif scenario == "REMOVE_DEPENDENT":

        rows.append(
            make_row(
                starting_eligibility_number + 1,
                member,
                current_coverage,
                family_members,
                2,
                "N",
                "DEMOGRAPHIC_CHANGE",
                event2_date,
                event2_date,
                baseline_start,
                None,
                "ACTIVE",
                "",
                "N",
                "N",
                "N",
                rng,
            )
        )

        rows.append(
            make_row(
                starting_eligibility_number + 2,
                member,
                current_coverage,
                family_members,
                3,
                "Y",
                "REMOVE_DEPENDENT",
                event3_date,
                event3_date,
                baseline_start,
                event3_date,
                "TERMINATED",
                "DEPENDENT_REMOVED",
                "N",
                "N",
                "N",
                rng,
            )
        )

    else:

        # STANDARD
        rows.append(
            make_row(
                starting_eligibility_number + 1,
                member,
                current_coverage,
                family_members,
                2,
                "N",
                "DEMOGRAPHIC_CHANGE",
                event2_date,
                event2_date,
                baseline_start,
                None,
                "ACTIVE",
                "",
                "N",
                "N",
                "N",
                rng,
            )
        )

        rows.append(
            make_row(
                starting_eligibility_number + 2,
                member,
                current_coverage,
                family_members,
                3,
                "Y",
                "ADDRESS_CHANGE",
                event3_date,
                event3_date,
                baseline_start,
                None,
                "ACTIVE",
                "",
                "N",
                "N",
                "N",
                rng,
            )
        )

    return rows


def write_eligibility_rows(
    rows: list,
    output_root: Path,
):

    output_dir = (
        output_root
        / "eligibility"
    )

    output_dir.mkdir(
        parents=True,
        exist_ok=True,
    )

    rows_per_file = (
        ROWS_PER_FILE[
            "eligibility"
        ]
    )

    file_number = 1

    for start_index in range(
        0,
        len(rows),
        rows_per_file,
    ):

        file_path = (
            output_dir
            / (
                f"eligibility_"
                f"{file_number:03d}.csv"
            )
        )

        print(
            f"Writing {file_path}"
        )

        batch = rows[
            start_index:
            start_index
            + rows_per_file
        ]

        with file_path.open(
            mode="w",
            newline="",
            encoding="utf-8",
        ) as handle:

            writer = csv.DictWriter(
                handle,
                fieldnames=(
                    ELIGIBILITY_COLUMNS
                ),
            )

            writer.writeheader()

            writer.writerows(
                batch
            )

        file_number += 1

    return output_dir


def generate_eligibility(
    eligibility_count: int,
    output_root: Path,
) -> None:

    rng = random.Random(
        RANDOM_SEED + 800
    )

    members = load_csv_files(
        output_root / "member",
        "member_*.csv",
    )

    products = load_csv_files(
        output_root / "product",
        "product_*.csv",
    )

    plans = load_csv_files(
        output_root / "benefit_plan",
        "benefit_plan_*.csv",
    )

    groups = load_csv_files(
        output_root / "group",
        "group_*.csv",
    )

    subgroups = load_csv_files(
        output_root / "subgroup",
        "subgroup_*.csv",
    )

    expected_count = (
        len(members) * 3
    )

    if (
        eligibility_count
        != expected_count
    ):

        raise ValueError(
            "Eligibility configuration must "
            "currently equal exactly three "
            "records per Member. "
            f"Expected {expected_count:,}, "
            f"configured {eligibility_count:,}."
        )

    (
        _,
        _,
        _,
        _,
        current_by_lob,
        all_by_lob,
    ) = build_reference_indexes(
        products,
        plans,
        groups,
        subgroups,
    )

    families = defaultdict(
        list
    )

    for member in members:

        families[
            member["family_id"]
        ].append(
            member
        )

    # Sort so SELF normally appears before
    # spouse / child records within each family.
    members_sorted = sorted(
        members,
        key=lambda row: (
            row["family_id"],
            0
            if row[
                "relationship_to_subscriber"
            ] == "SELF"
            else 1,
            row["member_id"],
        ),
    )

    subscriber_coverage_by_family = {}

    all_rows = []

    eligibility_number = 1

    for member in members_sorted:

        family_id = (
            member["family_id"]
        )

        subscriber_coverage = (
            subscriber_coverage_by_family.get(
                family_id
            )
        )

        initial_coverage = (
            choose_initial_coverage(
                member,
                subscriber_coverage,
                current_by_lob,
                rng,
            )
        )

        if (
            member[
                "relationship_to_subscriber"
            ]
            == "SELF"
        ):

            subscriber_coverage_by_family[
                family_id
            ] = initial_coverage

        member_rows = (
            generate_member_history(
                member=member,
                family_members=(
                    families[
                        family_id
                    ]
                ),
                initial_coverage=(
                    initial_coverage
                ),
                current_by_lob=(
                    current_by_lob
                ),
                all_by_lob=(
                    all_by_lob
                ),
                starting_eligibility_number=(
                    eligibility_number
                ),
                rng=rng,
            )
        )

        all_rows.extend(
            member_rows
        )

        eligibility_number += 3

    output_dir = (
        write_eligibility_rows(
            all_rows,
            output_root,
        )
    )

    print()
    print(
        f"Generated {len(all_rows):,} "
        f"eligibility history rows."
    )

    print(
        f"Members processed: "
        f"{len(members):,}"
    )

    print(
        "Eligibility versions per member: 3"
    )

    print(
        f"Eligibility output directory: "
        f"{output_dir}"
    )