"""
Project 01 - Healthcare Payer Data Platform
Module: supplier_location_generator.py

Purpose
-------
Generates physical Supplier Locations belonging to healthcare Supplier
organizations.

What This Module Does
---------------------
- Loads previously generated Supplier records.
- Guarantees at least one physical location for every Supplier.
- Uses weighted Supplier characteristics so larger organization types
  can naturally receive more locations.
- Generates location names and location types.
- Generates synthetic facility NPI values.
- Generates place-of-service codes.
- Generates network status and network tier.
- Generally inherits parent Supplier network characteristics while
  allowing limited location-level variation.
- Generates active status, effective/termination dates, source keys,
  and technical timestamps.

Inputs / Dependencies
---------------------
- supplier/*.csv
- config.py
- reference_data.py

Outputs
-------
generated_data/<scale>/supplier_location/supplier_location_###.csv

Execution
---------
Normally invoked through:

    python generate_data.py --scale medium --domain supplier_location

Business Role
-------------
Supplier Location represents the physical site where healthcare
services are delivered.
"""




import csv
import random
from datetime import date, datetime, timedelta
from pathlib import Path

from config import (
    DATA_END_DATE,
    RANDOM_SEED,
    ROWS_PER_FILE,
)

from reference_data import (
    PLACE_OF_SERVICE_CODES,
    SUPPLIER_LOCATION_NAME_SUFFIXES,
    SUPPLIER_LOCATION_TYPES,
)


SUPPLIER_LOCATION_COLUMNS = [
    "supplier_location_id",
    "supplier_id",
    "location_name",
    "location_type",
    "facility_npi",
    "place_of_service_code",
    "network_status",
    "network_tier",
    "active_flag",
    "effective_date",
    "termination_date",
    "source_location_key",
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


def load_suppliers(
    supplier_directory: Path,
):

    suppliers = []

    supplier_files = sorted(
        supplier_directory.glob(
            "supplier_*.csv"
        )
    )

    if not supplier_files:

        raise FileNotFoundError(
            f"No Supplier files found in "
            f"{supplier_directory}. "
            f"Generate Supplier first."
        )

    for file_path in supplier_files:

        with file_path.open(
            mode="r",
            newline="",
            encoding="utf-8",
        ) as file_handle:

            reader = csv.DictReader(
                file_handle
            )

            suppliers.extend(
                reader
            )

    return suppliers


def supplier_location_weight(
    supplier: dict,
) -> int:

    supplier_type = (
        supplier["supplier_type"]
    )

    if supplier_type == "HOSPITAL_SYSTEM":
        return 8

    if supplier_type == "HOSPITAL_ORGANIZATION":
        return 6

    if supplier_type == "PHYSICIAN_GROUP":
        return 5

    if supplier_type == "URGENT_CARE_ORG":
        return 4

    if supplier_type == "SPECIALTY_CARE_ORG":
        return 4

    if supplier_type == "BEHAVIORAL_HEALTH_ORG":
        return 3

    if supplier_type == "IMAGING_ORG":
        return 3

    if supplier_type == "LABORATORY_ORG":
        return 2

    return 1


def choose_location_type(
    supplier_type: str,
    rng: random.Random,
) -> str:

    if supplier_type in [
        "HOSPITAL_SYSTEM",
        "HOSPITAL_ORGANIZATION",
    ]:

        return rng.choices(
            population=[
                "ACUTE_CARE_HOSPITAL",
                "OUTPATIENT_CENTER",
                "AMBULATORY_SURGERY_CENTER",
                "SPECIALTY_CLINIC",
                "IMAGING_CENTER",
            ],
            weights=[
                35,
                25,
                15,
                15,
                10,
            ],
            k=1,
        )[0]

    if supplier_type == "PHYSICIAN_GROUP":

        return rng.choices(
            population=[
                "PHYSICIAN_OFFICE",
                "OUTPATIENT_CENTER",
                "SPECIALTY_CLINIC",
            ],
            weights=[
                60,
                20,
                20,
            ],
            k=1,
        )[0]

    if supplier_type == "URGENT_CARE_ORG":

        return "URGENT_CARE_CENTER"

    if supplier_type == "IMAGING_ORG":

        return "IMAGING_CENTER"

    if supplier_type == "LABORATORY_ORG":

        return "LABORATORY"

    if supplier_type == "BEHAVIORAL_HEALTH_ORG":

        return "BEHAVIORAL_HEALTH_CENTER"

    if supplier_type == "SPECIALTY_CARE_ORG":

        return rng.choice(
            [
                "SPECIALTY_CLINIC",
                "OUTPATIENT_CENTER",
                "PHYSICIAN_OFFICE",
            ]
        )

    return rng.choice(
        SUPPLIER_LOCATION_TYPES
    )


def choose_pos_code(
    location_type: str,
    rng: random.Random,
) -> str:

    mapping = {
        "ACUTE_CARE_HOSPITAL": ["21", "22", "23"],
        "OUTPATIENT_CENTER": ["19", "22"],
        "AMBULATORY_SURGERY_CENTER": ["24"],
        "PHYSICIAN_OFFICE": ["11"],
        "URGENT_CARE_CENTER": ["11", "49"],
        "IMAGING_CENTER": ["49"],
        "LABORATORY": ["81"],
        "BEHAVIORAL_HEALTH_CENTER": ["11", "49"],
        "REHABILITATION_CENTER": ["49"],
        "SPECIALTY_CLINIC": ["11", "49"],
    }

    return rng.choice(
        mapping.get(
            location_type,
            PLACE_OF_SERVICE_CODES,
        )
    )


def generate_location_record(
    location_number: int,
    supplier: dict,
    rng: random.Random,
):

    supplier_location_id = (
        f"SLOC{location_number:08d}"
    )

    location_suffix = rng.choice(
        SUPPLIER_LOCATION_NAME_SUFFIXES
    )

    location_name = (
        f"{supplier['supplier_name']} "
        f"- {location_suffix}"
    )

    location_type = choose_location_type(
        supplier["supplier_type"],
        rng,
    )

    place_of_service_code = (
        choose_pos_code(
            location_type,
            rng,
        )
    )

    # Locations generally inherit the parent Supplier's
    # network arrangement, but a small percentage differ.
    if rng.random() < 0.95:

        network_status = (
            supplier["network_status"]
        )

        network_tier = (
            supplier["network_tier"]
        )

    else:

        network_status = (
            "OUT_OF_NETWORK"
            if supplier["network_status"]
            == "IN_NETWORK"
            else "IN_NETWORK"
        )

        if network_status == "IN_NETWORK":

            network_tier = rng.choice(
                [
                    "TIER_1",
                    "TIER_2",
                    "TIER_3",
                ]
            )

        else:

            network_tier = "NON_PAR"

    effective_date = random_date_between(
        date(2016, 1, 1),
        DATA_END_DATE,
        rng,
    )

    # Most locations remain active.
    is_active = (
        rng.random() < 0.92
    )

    if is_active:

        active_flag = "Y"
        termination_date = ""

    else:

        active_flag = "N"

        termination_date = (
            random_date_between(
                effective_date,
                DATA_END_DATE,
                rng,
            ).isoformat()
        )

    create_date = random_date_between(
        date(2016, 1, 1),
        DATA_END_DATE,
        rng,
    )

    update_date = random_date_between(
        create_date,
        DATA_END_DATE,
        rng,
    )

    # Synthetic 10-digit facility NPI.
    facility_npi = (
        f"18{location_number:08d}"
    )

    return {
        "supplier_location_id": (
            supplier_location_id
        ),
        "supplier_id": (
            supplier["supplier_id"]
        ),
        "location_name": (
            location_name
        ),
        "location_type": (
            location_type
        ),
        "facility_npi": (
            facility_npi
        ),
        "place_of_service_code": (
            place_of_service_code
        ),
        "network_status": (
            network_status
        ),
        "network_tier": (
            network_tier
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
        "source_location_key": (
            f"SRCLOC{location_number:08d}"
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


def generate_supplier_locations(
    location_count: int,
    output_root: Path,
) -> None:

    rng = random.Random(
        RANDOM_SEED + 200
    )

    supplier_directory = (
        output_root / "supplier"
    )

    suppliers = load_suppliers(
        supplier_directory
    )

    location_output_dir = (
        output_root
        / "supplier_location"
    )

    location_output_dir.mkdir(
        parents=True,
        exist_ok=True,
    )

    rows_per_file = (
        ROWS_PER_FILE[
            "supplier_location"
        ]
    )

    # -----------------------------------------------------
    # Build weighted Supplier population.
    #
    # Hospital systems appear more often so they naturally
    # receive more locations.
    # -----------------------------------------------------

    supplier_weights = [
        supplier_location_weight(
            supplier
        )
        for supplier in suppliers
    ]

    # Every Supplier gets at least one physical location.
    supplier_assignment = list(
        suppliers
    )

    remaining_locations = (
        location_count
        - len(supplier_assignment)
    )

    if remaining_locations < 0:

        raise ValueError(
            "Supplier Location count must be "
            "at least as large as Supplier count."
        )

    if remaining_locations > 0:

        supplier_assignment.extend(
            rng.choices(
                population=suppliers,
                weights=supplier_weights,
                k=remaining_locations,
            )
        )

    # Shuffle so Supplier locations are not written
    # in a simple parent-by-parent pattern.
    rng.shuffle(
        supplier_assignment
    )

    file_number = 1
    location_number = 1
    assignment_index = 0

    while (
        assignment_index
        < len(supplier_assignment)
    ):

        file_path = (
            location_output_dir
            / (
                f"supplier_location_"
                f"{file_number:03d}.csv"
            )
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
                fieldnames=(
                    SUPPLIER_LOCATION_COLUMNS
                ),
            )

            writer.writeheader()

            rows_written = 0

            while (
                assignment_index
                < len(supplier_assignment)
                and rows_written
                < rows_per_file
            ):

                supplier = (
                    supplier_assignment[
                        assignment_index
                    ]
                )

                record = (
                    generate_location_record(
                        location_number=(
                            location_number
                        ),
                        supplier=supplier,
                        rng=rng,
                    )
                )

                writer.writerow(
                    record
                )

                assignment_index += 1
                location_number += 1
                rows_written += 1

        file_number += 1

    print()

    print(
        f"Generated {location_count:,} "
        f"supplier location rows."
    )

    print(
        f"Parent Suppliers loaded: "
        f"{len(suppliers):,}"
    )

    print(
        f"Supplier Location output directory: "
        f"{location_output_dir}"
    )