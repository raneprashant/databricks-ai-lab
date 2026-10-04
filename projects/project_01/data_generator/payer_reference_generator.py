import csv
import random
from datetime import date, datetime, timedelta
from pathlib import Path

from config import (
    DATA_END_DATE,
    FUTURE_COVERAGE_END_DATE,
    RANDOM_SEED,
    ROWS_PER_FILE,
)


PRODUCT_COLUMNS = [
    "product_id",
    "product_code",
    "product_name",
    "line_of_business",
    "product_type",
    "market_segment",
    "funding_type",
    "network_model",
    "active_flag",
    "effective_date",
    "termination_date",
    "source_product_key",
    "create_ts",
    "update_ts",
]


BENEFIT_PLAN_COLUMNS = [
    "benefit_plan_id",
    "product_id",
    "plan_code",
    "plan_name",
    "metal_level",
    "network_id",
    "individual_deductible",
    "family_deductible",
    "individual_oop_max",
    "family_oop_max",
    "pcp_copay",
    "specialist_copay",
    "urgent_care_copay",
    "er_copay",
    "coinsurance_pct",
    "medical_coverage_flag",
    "pharmacy_coverage_flag",
    "dental_coverage_flag",
    "vision_coverage_flag",
    "referral_required_flag",
    "plan_status",
    "effective_date",
    "termination_date",
    "source_plan_key",
    "create_ts",
    "update_ts",
]


GROUP_COLUMNS = [
    "group_id",
    "group_number",
    "group_name",
    "group_type",
    "line_of_business",
    "market_segment",
    "funding_arrangement",
    "group_status",
    "effective_date",
    "termination_date",
    "source_group_key",
    "create_ts",
    "update_ts",
]


SUBGROUP_COLUMNS = [
    "subgroup_id",
    "group_id",
    "subgroup_code",
    "subgroup_name",
    "employee_class",
    "benefit_plan_id",
    "subgroup_status",
    "effective_date",
    "termination_date",
    "source_subgroup_key",
    "create_ts",
    "update_ts",
]


PRODUCT_TEMPLATES = [
    {
        "lob": "COMMERCIAL",
        "type": "PPO",
        "segment": "LARGE_GROUP",
        "funding": "FULLY_INSURED",
        "network": "BROAD_PPO",
        "name": "Commercial PPO",
    },
    {
        "lob": "COMMERCIAL",
        "type": "HMO",
        "segment": "LARGE_GROUP",
        "funding": "FULLY_INSURED",
        "network": "NARROW_HMO",
        "name": "Commercial HMO",
    },
    {
        "lob": "COMMERCIAL",
        "type": "EPO",
        "segment": "SMALL_GROUP",
        "funding": "FULLY_INSURED",
        "network": "REGIONAL_EPO",
        "name": "Commercial EPO",
    },
    {
        "lob": "COMMERCIAL",
        "type": "POS",
        "segment": "LARGE_GROUP",
        "funding": "ASO",
        "network": "BROAD_POS",
        "name": "Commercial POS",
    },
    {
        "lob": "MEDICARE",
        "type": "MA_HMO",
        "segment": "SENIOR",
        "funding": "GOVERNMENT",
        "network": "MEDICARE_HMO",
        "name": "Medicare Advantage HMO",
    },
    {
        "lob": "MEDICARE",
        "type": "MA_PPO",
        "segment": "SENIOR",
        "funding": "GOVERNMENT",
        "network": "MEDICARE_PPO",
        "name": "Medicare Advantage PPO",
    },
    {
        "lob": "MEDICAID",
        "type": "MANAGED_CARE",
        "segment": "GOVERNMENT",
        "funding": "GOVERNMENT",
        "network": "MEDICAID_NETWORK",
        "name": "Medicaid Managed Care",
    },
    {
        "lob": "EXCHANGE",
        "type": "EPO",
        "segment": "INDIVIDUAL",
        "funding": "FULLY_INSURED",
        "network": "EXCHANGE_EPO",
        "name": "Individual Exchange EPO",
    },
]


GROUP_NAME_PREFIXES = [
    "Acme",
    "Northstar",
    "Empire",
    "Liberty",
    "Summit",
    "Lakeside",
    "Heritage",
    "Grandview",
    "Evergreen",
    "Pioneer",
    "Blue Ridge",
    "Riverbend",
]


GROUP_NAME_SUFFIXES = [
    "Manufacturing",
    "Technology",
    "Services",
    "Retail",
    "Education",
    "Logistics",
    "Healthcare",
    "Hospitality",
    "Financial",
    "Industries",
]


EMPLOYEE_CLASSES = [
    "SALARIED",
    "HOURLY",
    "UNION",
    "NON_UNION",
    "MANAGEMENT",
    "RETIREE",
]


def random_date_between(
    start_date: date,
    end_date: date,
    rng: random.Random,
) -> date:

    days = (
        end_date - start_date
    ).days

    return start_date + timedelta(
        days=rng.randint(
            0,
            max(days, 0),
        )
    )


def build_timestamp(
    event_date: date,
    rng: random.Random,
) -> str:

    event_datetime = datetime(
        event_date.year,
        event_date.month,
        event_date.day,
        rng.randint(0, 23),
        rng.randint(0, 59),
        rng.randint(0, 59),
    )

    return event_datetime.isoformat(
        timespec="seconds"
    )


def write_rows(
    rows: list,
    output_directory: Path,
    filename_prefix: str,
    columns: list,
    rows_per_file: int,
):

    output_directory.mkdir(
        parents=True,
        exist_ok=True,
    )

    file_number = 1

    for start_index in range(
        0,
        len(rows),
        rows_per_file,
    ):

        file_path = (
            output_directory
            / (
                f"{filename_prefix}_"
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
        ) as file_handle:

            writer = csv.DictWriter(
                file_handle,
                fieldnames=columns,
            )

            writer.writeheader()

            writer.writerows(
                batch
            )

        file_number += 1


def generate_products(
    product_count: int,
    rng: random.Random,
):

    products = []

    for number in range(
        1,
        product_count + 1,
    ):

        template = PRODUCT_TEMPLATES[
            (number - 1)
            % len(PRODUCT_TEMPLATES)
        ]

        variation = (
            ((number - 1)
             // len(PRODUCT_TEMPLATES))
            + 1
        )

        product_id = (
            f"PROD{number:05d}"
        )

        effective_date = random_date_between(
            date(2022, 1, 1),
            date(2024, 1, 1),
            rng,
        )

        active_flag = "Y"
        termination_date = ""

        create_date = effective_date

        update_date = random_date_between(
            create_date,
            DATA_END_DATE,
            rng,
        )

        products.append(
            {
                "product_id": product_id,
                "product_code": (
                    f"P{number:04d}"
                ),
                "product_name": (
                    f"{template['name']} "
                    f"{variation}"
                ),
                "line_of_business": (
                    template["lob"]
                ),
                "product_type": (
                    template["type"]
                ),
                "market_segment": (
                    template["segment"]
                ),
                "funding_type": (
                    template["funding"]
                ),
                "network_model": (
                    template["network"]
                ),
                "active_flag": (
                    active_flag
                ),
                "effective_date": (
                    effective_date.isoformat()
                ),
                "termination_date": (
                    termination_date
                ),
                "source_product_key": (
                    f"SRCPROD{number:05d}"
                ),
                "create_ts": build_timestamp(
                    create_date,
                    rng,
                ),
                "update_ts": build_timestamp(
                    update_date,
                    rng,
                ),
            }
        )

    return products


def benefit_values(
    product_type: str,
    rng: random.Random,
):

    if product_type in [
        "MA_HMO",
        "MA_PPO",
        "MANAGED_CARE",
    ]:

        deductible = rng.choice(
            [0, 250, 500]
        )

        oop_max = rng.choice(
            [3000, 4500, 6000]
        )

        pcp_copay = rng.choice(
            [0, 10, 20]
        )

        specialist_copay = rng.choice(
            [20, 30, 40]
        )

        coinsurance = rng.choice(
            [0, 10, 20]
        )

    else:

        deductible = rng.choice(
            [
                500,
                1000,
                1500,
                2500,
                3000,
                5000,
            ]
        )

        oop_max = rng.choice(
            [
                4000,
                5500,
                7000,
                8500,
            ]
        )

        pcp_copay = rng.choice(
            [15, 20, 25, 30, 40]
        )

        specialist_copay = rng.choice(
            [30, 40, 50, 60, 75]
        )

        coinsurance = rng.choice(
            [10, 20, 30]
        )

    return {
        "individual_deductible": deductible,
        "family_deductible": (
            deductible * 2
        ),
        "individual_oop_max": oop_max,
        "family_oop_max": (
            oop_max * 2
        ),
        "pcp_copay": pcp_copay,
        "specialist_copay": (
            specialist_copay
        ),
        "urgent_care_copay": rng.choice(
            [25, 40, 50, 75]
        ),
        "er_copay": rng.choice(
            [100, 150, 250, 350]
        ),
        "coinsurance_pct": coinsurance,
    }


def generate_benefit_plans(
    plan_count: int,
    products: list,
    rng: random.Random,
):

    plans = []

    for number in range(
        1,
        plan_count + 1,
    ):

        product = products[
            (number - 1)
            % len(products)
        ]

        benefits = benefit_values(
            product["product_type"],
            rng,
        )

        benefit_plan_id = (
            f"PLAN{number:06d}"
        )

        # A small percentage represent future offerings.
        if rng.random() < 0.10:

            effective_date = (
                random_date_between(
                    DATA_END_DATE
                    + timedelta(days=1),
                    FUTURE_COVERAGE_END_DATE,
                    rng,
                )
            )

            plan_status = "FUTURE"

        else:

            effective_date = (
                random_date_between(
                    date(2023, 1, 1),
                    date(2024, 1, 1),
                    rng,
                )
            )

            plan_status = "ACTIVE"

        termination_date = ""

        if (
            product[
                "line_of_business"
            ]
            in [
                "COMMERCIAL",
                "EXCHANGE",
            ]
        ):

            metal_level = rng.choice(
                [
                    "BRONZE",
                    "SILVER",
                    "GOLD",
                    "PLATINUM",
                ]
            )

        else:

            metal_level = ""

        referral_required_flag = (
            "Y"
            if product["product_type"]
            in [
                "HMO",
                "MA_HMO",
            ]
            else "N"
        )

        create_date = min(
            effective_date,
            DATA_END_DATE,
        )

        update_date = max(
            create_date,
            DATA_END_DATE,
        )

        plans.append(
            {
                "benefit_plan_id": (
                    benefit_plan_id
                ),
                "product_id": (
                    product[
                        "product_id"
                    ]
                ),
                "plan_code": (
                    f"BP{number:05d}"
                ),
                "plan_name": (
                    f"{product['product_name']} "
                    f"Plan {number:03d}"
                ),
                "metal_level": (
                    metal_level
                ),
                "network_id": (
                    f"NET_"
                    f"{product['network_model']}"
                ),
                **benefits,
                "medical_coverage_flag": (
                    "Y"
                ),
                "pharmacy_coverage_flag": (
                    "Y"
                ),
                "dental_coverage_flag": (
                    rng.choices(
                        ["Y", "N"],
                        weights=[45, 55],
                        k=1,
                    )[0]
                ),
                "vision_coverage_flag": (
                    rng.choices(
                        ["Y", "N"],
                        weights=[40, 60],
                        k=1,
                    )[0]
                ),
                "referral_required_flag": (
                    referral_required_flag
                ),
                "plan_status": (
                    plan_status
                ),
                "effective_date": (
                    effective_date.isoformat()
                ),
                "termination_date": (
                    termination_date
                ),
                "source_plan_key": (
                    f"SRCPLAN"
                    f"{number:06d}"
                ),
                "create_ts": build_timestamp(
                    create_date,
                    rng,
                ),
                "update_ts": build_timestamp(
                    update_date,
                    rng,
                ),
            }
        )

    return plans


def choose_group_type(
    line_of_business: str,
):

    mapping = {
        "COMMERCIAL": (
            "EMPLOYER_GROUP"
        ),
        "MEDICARE": (
            "MEDICARE_BOOK"
        ),
        "MEDICAID": (
            "MEDICAID_PROGRAM"
        ),
        "EXCHANGE": (
            "INDIVIDUAL_MARKET"
        ),
    }

    return mapping[
        line_of_business
    ]


def generate_groups(
    group_count: int,
    products: list,
    rng: random.Random,
):

    groups = []

    for number in range(
        1,
        group_count + 1,
    ):

        product = rng.choice(
            products
        )

        lob = (
            product[
                "line_of_business"
            ]
        )

        group_type = choose_group_type(
            lob
        )

        if group_type == "EMPLOYER_GROUP":

            group_name = (
                f"{rng.choice(GROUP_NAME_PREFIXES)} "
                f"{rng.choice(GROUP_NAME_SUFFIXES)} "
                f"{number:04d}"
            )

        elif group_type == "MEDICARE_BOOK":

            group_name = (
                f"Medicare Regional Book "
                f"{number:04d}"
            )

        elif group_type == "MEDICAID_PROGRAM":

            group_name = (
                f"Medicaid Managed Program "
                f"{number:04d}"
            )

        else:

            group_name = (
                f"Individual Market Book "
                f"{number:04d}"
            )

        effective_date = random_date_between(
            date(2022, 1, 1),
            date(2024, 1, 1),
            rng,
        )

        if rng.random() < 0.96:

            group_status = "ACTIVE"
            termination_date = ""

        else:

            group_status = "TERMINATED"

            termination_date = (
                random_date_between(
                    date(2024, 1, 1),
                    DATA_END_DATE,
                    rng,
                ).isoformat()
            )

        create_date = effective_date

        update_date = random_date_between(
            create_date,
            DATA_END_DATE,
            rng,
        )

        groups.append(
            {
                "group_id": (
                    f"GRP{number:07d}"
                ),
                "group_number": (
                    f"G{number:07d}"
                ),
                "group_name": (
                    group_name
                ),
                "group_type": (
                    group_type
                ),
                "line_of_business": (
                    lob
                ),
                "market_segment": (
                    product[
                        "market_segment"
                    ]
                ),
                "funding_arrangement": (
                    product[
                        "funding_type"
                    ]
                ),
                "group_status": (
                    group_status
                ),
                "effective_date": (
                    effective_date.isoformat()
                ),
                "termination_date": (
                    termination_date
                ),
                "source_group_key": (
                    f"SRCGRP"
                    f"{number:07d}"
                ),
                "create_ts": build_timestamp(
                    create_date,
                    rng,
                ),
                "update_ts": build_timestamp(
                    update_date,
                    rng,
                ),
            }
        )

    return groups


def generate_subgroups(
    subgroup_count: int,
    groups: list,
    products: list,
    plans: list,
    rng: random.Random,
):

    product_by_id = {
        row["product_id"]: row
        for row in products
    }

    plans_by_lob = {}

    for plan in plans:

        product = product_by_id[
            plan["product_id"]
        ]

        lob = product[
            "line_of_business"
        ]

        plans_by_lob.setdefault(
            lob,
            [],
        ).append(
            plan
        )

    subgroups = []

    for number in range(
        1,
        subgroup_count + 1,
    ):

        group = groups[
            (number - 1)
            % len(groups)
        ]

        matching_plans = (
            plans_by_lob[
                group[
                    "line_of_business"
                ]
            ]
        )

        benefit_plan = rng.choice(
            matching_plans
        )

        group_start = date.fromisoformat(
            group[
                "effective_date"
            ]
        )

        plan_start = date.fromisoformat(
            benefit_plan[
                "effective_date"
            ]
        )

        effective_date = max(
            group_start,
            plan_start,
        )

        group_end = (
            date.fromisoformat(
                group[
                    "termination_date"
                ]
            )
            if group[
                "termination_date"
            ]
            else None
        )

        if group_end:

            subgroup_status = (
                "TERMINATED"
            )

            termination_date = (
                group_end
            )

        elif (
            effective_date
            > DATA_END_DATE
        ):

            subgroup_status = (
                "FUTURE"
            )

            termination_date = None

        else:

            subgroup_status = (
                "ACTIVE"
            )

            termination_date = None

        if (
            group[
                "group_type"
            ]
            == "EMPLOYER_GROUP"
        ):

            employee_class = (
                rng.choice(
                    EMPLOYEE_CLASSES
                )
            )

        elif (
            group[
                "group_type"
            ]
            == "MEDICARE_BOOK"
        ):

            employee_class = (
                "MEDICARE_ELIGIBLE"
            )

        elif (
            group[
                "group_type"
            ]
            == "MEDICAID_PROGRAM"
        ):

            employee_class = (
                "MEDICAID_ELIGIBLE"
            )

        else:

            employee_class = (
                "INDIVIDUAL"
            )

        create_date = min(
            effective_date,
            DATA_END_DATE,
        )

        update_date = max(
            create_date,
            DATA_END_DATE,
        )

        subgroups.append(
            {
                "subgroup_id": (
                    f"SGRP{number:08d}"
                ),
                "group_id": (
                    group[
                        "group_id"
                    ]
                ),
                "subgroup_code": (
                    f"SG{number:08d}"
                ),
                "subgroup_name": (
                    f"{employee_class} "
                    f"{number:04d}"
                ),
                "employee_class": (
                    employee_class
                ),
                "benefit_plan_id": (
                    benefit_plan[
                        "benefit_plan_id"
                    ]
                ),
                "subgroup_status": (
                    subgroup_status
                ),
                "effective_date": (
                    effective_date.isoformat()
                ),
                "termination_date": (
                    termination_date.isoformat()
                    if termination_date
                    else ""
                ),
                "source_subgroup_key": (
                    f"SRCSGRP"
                    f"{number:08d}"
                ),
                "create_ts": build_timestamp(
                    create_date,
                    rng,
                ),
                "update_ts": build_timestamp(
                    update_date,
                    rng,
                ),
            }
        )

    return subgroups


def generate_payer_reference_data(
    product_count: int,
    benefit_plan_count: int,
    group_count: int,
    subgroup_count: int,
    output_root: Path,
) -> None:

    rng = random.Random(
        RANDOM_SEED + 700
    )

    products = generate_products(
        product_count,
        rng,
    )

    plans = generate_benefit_plans(
        benefit_plan_count,
        products,
        rng,
    )

    groups = generate_groups(
        group_count,
        products,
        rng,
    )

    subgroups = generate_subgroups(
        subgroup_count,
        groups,
        products,
        plans,
        rng,
    )

    write_rows(
        products,
        output_root / "product",
        "product",
        PRODUCT_COLUMNS,
        ROWS_PER_FILE["product"],
    )

    write_rows(
        plans,
        output_root / "benefit_plan",
        "benefit_plan",
        BENEFIT_PLAN_COLUMNS,
        ROWS_PER_FILE["benefit_plan"],
    )

    write_rows(
        groups,
        output_root / "group",
        "group",
        GROUP_COLUMNS,
        ROWS_PER_FILE["group"],
    )

    write_rows(
        subgroups,
        output_root / "subgroup",
        "subgroup",
        SUBGROUP_COLUMNS,
        ROWS_PER_FILE["subgroup"],
    )

    print()
    print(
        f"Generated {len(products):,} products."
    )

    print(
        f"Generated {len(plans):,} benefit plans."
    )

    print(
        f"Generated {len(groups):,} groups."
    )

    print(
        f"Generated {len(subgroups):,} subgroups."
    )