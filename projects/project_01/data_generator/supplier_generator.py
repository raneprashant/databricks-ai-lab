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

from reference_data import (
    OWNERSHIP_TYPES,
    SUPPLIER_NAME_DESCRIPTORS,
    SUPPLIER_NAME_PREFIXES,
    SUPPLIER_NAME_SUFFIXES,
    SUPPLIER_TYPES,
)


SUPPLIER_COLUMNS = [
    "supplier_id",
    "supplier_name",
    "supplier_type",
    "tax_id",
    "organization_npi",
    "ownership_type",
    "network_status",
    "network_tier",
    "contract_status",
    "contract_effective_date",
    "contract_termination_date",
    "active_flag",
    "source_supplier_key",
    "create_ts",
    "update_ts",
]


def random_date_between(
    start_date: date,
    end_date: date,
    rng: random.Random,
) -> date:

    days = (end_date - start_date).days

    return start_date + timedelta(
        days=rng.randint(0, max(days, 0))
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


def generate_supplier_name(
    supplier_number: int,
    rng: random.Random,
) -> str:

    prefix = rng.choice(
        SUPPLIER_NAME_PREFIXES
    )

    descriptor = rng.choice(
        SUPPLIER_NAME_DESCRIPTORS
    )

    suffix = rng.choice(
        SUPPLIER_NAME_SUFFIXES
    )

    # The sequence makes names unique even when
    # synthetic name components repeat.
    return (
        f"{prefix} "
        f"{descriptor} "
        f"{suffix} "
        f"{supplier_number:04d}"
    )


def determine_contract(
    rng: random.Random,
):

    contract_status = rng.choices(
        population=[
            "ACTIVE",
            "TERMINATED",
            "PENDING",
        ],
        weights=[
            82,
            12,
            6,
        ],
        k=1,
    )[0]

    if contract_status == "ACTIVE":

        effective_date = random_date_between(
            date(2018, 1, 1),
            DATA_END_DATE,
            rng,
        )

        termination_date = ""

        active_flag = "Y"

    elif contract_status == "TERMINATED":

        effective_date = random_date_between(
            date(2015, 1, 1),
            date(2024, 12, 31),
            rng,
        )

        termination_date = random_date_between(
            effective_date,
            DATA_END_DATE,
            rng,
        ).isoformat()

        active_flag = "N"

    else:

        effective_date = random_date_between(
            DATA_END_DATE + timedelta(days=1),
            FUTURE_COVERAGE_END_DATE,
            rng,
        )

        termination_date = ""

        active_flag = "N"

    return (
        contract_status,
        effective_date,
        termination_date,
        active_flag,
    )


def generate_supplier_record(
    supplier_number: int,
    rng: random.Random,
):

    supplier_id = (
        f"SUP{supplier_number:08d}"
    )

    supplier_name = generate_supplier_name(
        supplier_number,
        rng,
    )

    supplier_type = rng.choices(
        population=SUPPLIER_TYPES,
        weights=[
            12,  # HOSPITAL_SYSTEM
            20,  # HOSPITAL_ORGANIZATION
            28,  # PHYSICIAN_GROUP
            8,   # BEHAVIORAL_HEALTH_ORG
            8,   # URGENT_CARE_ORG
            7,   # IMAGING_ORG
            7,   # LABORATORY_ORG
            10,  # SPECIALTY_CARE_ORG
        ],
        k=1,
    )[0]

    ownership_type = rng.choices(
        population=OWNERSHIP_TYPES,
        weights=[
            50,
            30,
            8,
            12,
        ],
        k=1,
    )[0]

    # Synthetic 9-digit Tax ID.
    tax_id = (
        f"{100000000 + supplier_number:09d}"
    )

    # Synthetic 10-digit organization NPI.
    # Structurally valid length, but intentionally
    # not intended to represent a real NPI.
    organization_npi = (
        f"19{supplier_number:08d}"
    )

    network_status = rng.choices(
        population=[
            "IN_NETWORK",
            "OUT_OF_NETWORK",
        ],
        weights=[
            88,
            12,
        ],
        k=1,
    )[0]

    if network_status == "IN_NETWORK":

        network_tier = rng.choices(
            population=[
                "TIER_1",
                "TIER_2",
                "TIER_3",
            ],
            weights=[
                55,
                35,
                10,
            ],
            k=1,
        )[0]

    else:

        network_tier = "NON_PAR"

    (
        contract_status,
        contract_effective_date,
        contract_termination_date,
        active_flag,
    ) = determine_contract(
        rng
    )

    create_date = random_date_between(
        date(2015, 1, 1),
        DATA_END_DATE,
        rng,
    )

    update_date = random_date_between(
        create_date,
        DATA_END_DATE,
        rng,
    )

    return {
        "supplier_id": supplier_id,
        "supplier_name": supplier_name,
        "supplier_type": supplier_type,
        "tax_id": tax_id,
        "organization_npi": organization_npi,
        "ownership_type": ownership_type,
        "network_status": network_status,
        "network_tier": network_tier,
        "contract_status": contract_status,
        "contract_effective_date": (
            contract_effective_date.isoformat()
        ),
        "contract_termination_date": (
            contract_termination_date
        ),
        "active_flag": active_flag,
        "source_supplier_key": (
            f"SRCSUP{supplier_number:08d}"
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


def generate_suppliers(
    supplier_count: int,
    output_root: Path,
) -> None:

    # Different seed offset keeps this domain deterministic
    # without producing the same random sequence as Member.
    rng = random.Random(
        RANDOM_SEED + 100
    )

    supplier_output_dir = (
        output_root / "supplier"
    )

    supplier_output_dir.mkdir(
        parents=True,
        exist_ok=True,
    )

    rows_per_file = (
        ROWS_PER_FILE["supplier"]
    )

    file_number = 1
    row_number = 1

    while row_number <= supplier_count:

        file_path = (
            supplier_output_dir
            / f"supplier_{file_number:03d}.csv"
        )

        print(
            f"Writing {file_path}"
        )

        with file_path.open(
            mode="w",
            newline="",
            encoding="utf-8",
        ) as file_handle:

            writer = csv.DictWriter(
                file_handle,
                fieldnames=SUPPLIER_COLUMNS,
            )

            writer.writeheader()

            rows_written = 0

            while (
                row_number <= supplier_count
                and rows_written < rows_per_file
            ):

                record = generate_supplier_record(
                    supplier_number=row_number,
                    rng=rng,
                )

                writer.writerow(
                    record
                )

                row_number += 1
                rows_written += 1

        file_number += 1

    print()
    print(
        f"Generated {supplier_count:,} supplier rows."
    )

    print(
        f"Supplier output directory: "
        f"{supplier_output_dir}"
    )