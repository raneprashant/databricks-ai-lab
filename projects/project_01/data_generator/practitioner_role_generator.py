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
    PCP_ELIGIBLE_SPECIALTIES,
)


PRACTITIONER_ROLE_COLUMNS = [
    "practitioner_role_id",
    "practitioner_id",
    "supplier_id",
    "supplier_location_id",
    "role_type",
    "role_specialty",
    "pcp_flag",
    "primary_affiliation_flag",
    "panel_status",
    "accepting_new_patients_flag",
    "network_status",
    "network_tier",
    "role_status",
    "effective_date",
    "termination_date",
    "source_role_key",
    "create_ts",
    "update_ts",
]


def parse_date(
    date_value: str,
):
    if not date_value:
        return None

    return date.fromisoformat(
        date_value
    )


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


def load_csv_files(
    directory: Path,
    file_pattern: str,
):

    rows = []

    files = sorted(
        directory.glob(
            file_pattern
        )
    )

    if not files:

        raise FileNotFoundError(
            f"No files matching "
            f"'{file_pattern}' found in "
            f"{directory}."
        )

    for file_path in files:

        with file_path.open(
            mode="r",
            newline="",
            encoding="utf-8",
        ) as file_handle:

            reader = csv.DictReader(
                file_handle
            )

            rows.extend(
                reader
            )

    return rows


def parents_have_date_overlap(
    practitioner: dict,
    location: dict,
) -> bool:

    practitioner_start = parse_date(
        practitioner["effective_date"]
    )

    practitioner_end = parse_date(
        practitioner["termination_date"]
    ) or DATA_END_DATE

    location_start = parse_date(
        location["effective_date"]
    )

    location_end = parse_date(
        location["termination_date"]
    ) or DATA_END_DATE

    overlap_start = max(
        practitioner_start,
        location_start,
    )

    overlap_end = min(
        practitioner_end,
        location_end,
    )

    return (
        overlap_start
        <= overlap_end
    )


def choose_location(
    practitioner: dict,
    locations: list,
    used_location_ids: set,
    rng: random.Random,
):

    # -----------------------------------------------------
    # Fast path:
    #
    # Try random locations first. This is efficient when
    # generating hundreds of thousands of affiliations.
    # -----------------------------------------------------

    for _ in range(200):

        location = rng.choice(
            locations
        )

        location_id = (
            location[
                "supplier_location_id"
            ]
        )

        if (
            location_id
            in used_location_ids
        ):
            continue

        if not parents_have_date_overlap(
            practitioner,
            location,
        ):
            continue

        return location

    # -----------------------------------------------------
    # Fallback:
    #
    # If random selection did not find a match, scan the
    # available locations before concluding that no valid
    # temporal relationship exists.
    #
    # This prevents an unlucky random sample from causing
    # a false failure.
    # -----------------------------------------------------

    for location in locations:

        location_id = (
            location[
                "supplier_location_id"
            ]
        )

        if (
            location_id
            in used_location_ids
        ):
            continue

        if not parents_have_date_overlap(
            practitioner,
            location,
        ):
            continue

        return location

    raise RuntimeError(
        "No Supplier Location with a valid "
        "effective-date overlap exists for "
        f"{practitioner['practitioner_id']}."
    )

def choose_role_type(
    specialty: str,
    location_type: str,
    rng: random.Random,
) -> str:

    # -----------------------------------------------------
    # Primary care specialties
    # -----------------------------------------------------

    if specialty in PCP_ELIGIBLE_SPECIALTIES:

        if location_type in [
            "PHYSICIAN_OFFICE",
            "OUTPATIENT_CENTER",
            "SPECIALTY_CLINIC",
            "URGENT_CARE_CENTER",
        ]:

            return rng.choices(
                population=[
                    "PCP",
                    "SPECIALIST",
                    "ATTENDING_PHYSICIAN",
                    "CONSULTING_PHYSICIAN",
                ],
                weights=[
                    60,
                    15,
                    15,
                    10,
                ],
                k=1,
            )[0]

        return rng.choices(
            population=[
                "PCP",
                "HOSPITALIST",
                "ATTENDING_PHYSICIAN",
                "CONSULTING_PHYSICIAN",
            ],
            weights=[
                30,
                30,
                25,
                15,
            ],
            k=1,
        )[0]

    # -----------------------------------------------------
    # Surgery
    # -----------------------------------------------------

    if specialty == "GENERAL_SURGERY":

        return rng.choices(
            population=[
                "SURGEON",
                "ATTENDING_PHYSICIAN",
                "CONSULTING_PHYSICIAN",
            ],
            weights=[
                65,
                20,
                15,
            ],
            k=1,
        )[0]

    # -----------------------------------------------------
    # Emergency medicine
    # -----------------------------------------------------

    if specialty == "EMERGENCY_MEDICINE":

        return rng.choices(
            population=[
                "EMERGENCY_PHYSICIAN",
                "ATTENDING_PHYSICIAN",
                "HOSPITALIST",
            ],
            weights=[
                70,
                20,
                10,
            ],
            k=1,
        )[0]

    # -----------------------------------------------------
    # Other specialties
    # -----------------------------------------------------

    return rng.choices(
        population=[
            "SPECIALIST",
            "ATTENDING_PHYSICIAN",
            "CONSULTING_PHYSICIAN",
            "HOSPITALIST",
        ],
        weights=[
            60,
            20,
            15,
            5,
        ],
        k=1,
    )[0]


def determine_role_dates(
    practitioner: dict,
    location: dict,
    rng: random.Random,
):

    practitioner_start = parse_date(
        practitioner["effective_date"]
    )

    practitioner_end = parse_date(
        practitioner["termination_date"]
    ) or DATA_END_DATE

    location_start = parse_date(
        location["effective_date"]
    )

    location_end = parse_date(
        location["termination_date"]
    ) or DATA_END_DATE

    overlap_start = max(
        practitioner_start,
        location_start,
    )

    overlap_end = min(
        practitioner_end,
        location_end,
    )

    effective_date = random_date_between(
        overlap_start,
        overlap_end,
        rng,
    )

    # If either parent relationship ended,
    # this affiliation cannot remain active.
    parent_ended = (
        practitioner_end < DATA_END_DATE
        or location_end < DATA_END_DATE
    )

    if parent_ended:

        role_status = "TERMINATED"

        termination_date = random_date_between(
            effective_date,
            overlap_end,
            rng,
        )

    else:

        role_status = rng.choices(
            population=[
                "ACTIVE",
                "TERMINATED",
            ],
            weights=[
                94,
                6,
            ],
            k=1,
        )[0]

        if role_status == "ACTIVE":

            termination_date = None

        else:

            termination_date = random_date_between(
                effective_date,
                DATA_END_DATE,
                rng,
            )

    return (
        role_status,
        effective_date,
        termination_date,
    )


def determine_panel_information(
    role_type: str,
    rng: random.Random,
):

    if role_type != "PCP":

        return (
            "NOT_APPLICABLE",
            "N",
        )

    panel_status = rng.choices(
        population=[
            "OPEN",
            "LIMITED",
            "CLOSED",
        ],
        weights=[
            65,
            25,
            10,
        ],
        k=1,
    )[0]

    if panel_status == "OPEN":

        accepting_new_patients = "Y"

    elif panel_status == "LIMITED":

        accepting_new_patients = rng.choices(
            population=["Y", "N"],
            weights=[40, 60],
            k=1,
        )[0]

    else:

        accepting_new_patients = "N"

    return (
        panel_status,
        accepting_new_patients,
    )


def generate_role_record(
    role_number: int,
    practitioner: dict,
    location: dict,
    primary_affiliation_flag: str,
    rng: random.Random,
):

    practitioner_role_id = (
        f"PROLE{role_number:09d}"
    )

    specialty = (
        practitioner[
            "primary_specialty"
        ]
    )

    role_type = choose_role_type(
        specialty=specialty,
        location_type=(
            location["location_type"]
        ),
        rng=rng,
    )

    pcp_flag = (
        "Y"
        if role_type == "PCP"
        else "N"
    )

    (
        panel_status,
        accepting_new_patients_flag,
    ) = determine_panel_information(
        role_type,
        rng,
    )

    (
        role_status,
        effective_date,
        termination_date,
    ) = determine_role_dates(
        practitioner,
        location,
        rng,
    )

    create_date = random_date_between(
        effective_date,
        DATA_END_DATE,
        rng,
    )

    update_date = random_date_between(
        create_date,
        DATA_END_DATE,
        rng,
    )

    return {
        "practitioner_role_id": (
            practitioner_role_id
        ),
        "practitioner_id": (
            practitioner[
                "practitioner_id"
            ]
        ),
        "supplier_id": (
            location[
                "supplier_id"
            ]
        ),
        "supplier_location_id": (
            location[
                "supplier_location_id"
            ]
        ),
        "role_type": (
            role_type
        ),
        "role_specialty": (
            specialty
        ),
        "pcp_flag": (
            pcp_flag
        ),
        "primary_affiliation_flag": (
            primary_affiliation_flag
        ),
        "panel_status": (
            panel_status
        ),
        "accepting_new_patients_flag": (
            accepting_new_patients_flag
        ),
        "network_status": (
            location[
                "network_status"
            ]
        ),
        "network_tier": (
            location[
                "network_tier"
            ]
        ),
        "role_status": (
            role_status
        ),
        "effective_date": (
            effective_date.isoformat()
        ),
        "termination_date": (
            termination_date.isoformat()
            if termination_date
            else ""
        ),
        "source_role_key": (
            f"SRCPROLE"
            f"{role_number:09d}"
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


def build_affiliation_assignments(
    practitioners: list,
    locations: list,
    target_role_count: int,
    rng: random.Random,
):

    if target_role_count < len(
        practitioners
    ):

        raise ValueError(
            "Practitioner Role count must "
            "be at least as large as "
            "Practitioner count."
        )

    assignments = []

    used_locations = {
        practitioner[
            "practitioner_id"
        ]: set()
        for practitioner
        in practitioners
    }

    role_counts = {
        practitioner[
            "practitioner_id"
        ]: 0
        for practitioner
        in practitioners
    }

    # -----------------------------------------------------
    # First pass:
    # guarantee at least one affiliation for every
    # practitioner.
    # -----------------------------------------------------

    for practitioner in practitioners:

        practitioner_id = (
            practitioner[
                "practitioner_id"
            ]
        )

        location = choose_location(
            practitioner=practitioner,
            locations=locations,
            used_location_ids=(
                used_locations[
                    practitioner_id
                ]
            ),
            rng=rng,
        )

        used_locations[
            practitioner_id
        ].add(
            location[
                "supplier_location_id"
            ]
        )

        role_counts[
            practitioner_id
        ] += 1

        assignments.append(
            (
                practitioner,
                location,
                "Y",
            )
        )

    # -----------------------------------------------------
    # Additional affiliations.
    #
    # Cap a practitioner at six Supplier Locations.
    # -----------------------------------------------------

    while (
        len(assignments)
        < target_role_count
    ):

        practitioner = rng.choice(
            practitioners
        )

        practitioner_id = (
            practitioner[
                "practitioner_id"
            ]
        )

        if (
            role_counts[
                practitioner_id
            ]
            >= 6
        ):
            continue

        location = choose_location(
            practitioner=practitioner,
            locations=locations,
            used_location_ids=(
                used_locations[
                    practitioner_id
                ]
            ),
            rng=rng,
        )

        used_locations[
            practitioner_id
        ].add(
            location[
                "supplier_location_id"
            ]
        )

        role_counts[
            practitioner_id
        ] += 1

        assignments.append(
            (
                practitioner,
                location,
                "N",
            )
        )

    # Shuffle so output is not grouped entirely
    # by primary versus secondary affiliations.
    rng.shuffle(
        assignments
    )

    return assignments


def generate_practitioner_roles(
    role_count: int,
    output_root: Path,
) -> None:

    rng = random.Random(
        RANDOM_SEED + 400
    )

    practitioner_directory = (
        output_root
        / "practitioner"
    )

    supplier_location_directory = (
        output_root
        / "supplier_location"
    )

    practitioners = load_csv_files(
        practitioner_directory,
        "practitioner_*.csv",
    )

    locations = load_csv_files(
        supplier_location_directory,
        "supplier_location_*.csv",
    )

    assignments = (
        build_affiliation_assignments(
            practitioners=practitioners,
            locations=locations,
            target_role_count=role_count,
            rng=rng,
        )
    )

    role_output_dir = (
        output_root
        / "practitioner_role"
    )

    role_output_dir.mkdir(
        parents=True,
        exist_ok=True,
    )

    rows_per_file = (
        ROWS_PER_FILE[
            "practitioner_role"
        ]
    )

    role_number = 1
    assignment_index = 0
    file_number = 1

    while (
        assignment_index
        < len(assignments)
    ):

        file_path = (
            role_output_dir
            / (
                f"practitioner_role_"
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
                    PRACTITIONER_ROLE_COLUMNS
                ),
            )

            writer.writeheader()

            rows_written = 0

            while (
                assignment_index
                < len(assignments)
                and rows_written
                < rows_per_file
            ):

                (
                    practitioner,
                    location,
                    primary_flag,
                ) = assignments[
                    assignment_index
                ]

                record = generate_role_record(
                    role_number=role_number,
                    practitioner=practitioner,
                    location=location,
                    primary_affiliation_flag=(
                        primary_flag
                    ),
                    rng=rng,
                )

                writer.writerow(
                    record
                )

                assignment_index += 1
                role_number += 1
                rows_written += 1

        file_number += 1

    print()

    print(
        f"Generated {role_count:,} "
        f"practitioner role rows."
    )

    print(
        f"Parent Practitioners loaded: "
        f"{len(practitioners):,}"
    )

    print(
        f"Supplier Locations loaded: "
        f"{len(locations):,}"
    )

    print(
        f"Practitioner Role output directory: "
        f"{role_output_dir}"
    )