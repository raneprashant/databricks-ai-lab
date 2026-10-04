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
    FIRST_NAMES_FEMALE,
    FIRST_NAMES_MALE,
    LAST_NAMES,
    PRACTITIONER_CREDENTIALS,
    PRACTITIONER_SPECIALTIES,
    PRACTITIONER_SUFFIXES,
    US_LICENSE_STATES,
)


PRACTITIONER_COLUMNS = [
    "practitioner_id",
    "individual_npi",
    "first_name",
    "middle_initial",
    "last_name",
    "suffix",
    "credential",
    "primary_specialty",
    "license_number",
    "license_state",
    "board_certified_flag",
    "practitioner_status",
    "effective_date",
    "termination_date",
    "source_practitioner_key",
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


def choose_practitioner_name(
    rng: random.Random,
):

    gender = rng.choice(
        ["M", "F"]
    )

    if gender == "M":

        first_name = rng.choice(
            FIRST_NAMES_MALE
        )

    else:

        first_name = rng.choice(
            FIRST_NAMES_FEMALE
        )

    middle_initial = chr(
        rng.randint(
            ord("A"),
            ord("Z"),
        )
    )

    last_name = rng.choice(
        LAST_NAMES
    )

    return (
        first_name,
        middle_initial,
        last_name,
    )


def determine_practitioner_status(
    rng: random.Random,
):

    status = rng.choices(
        population=[
            "ACTIVE",
            "INACTIVE",
            "RETIRED",
            "SUSPENDED",
        ],
        weights=[
            91,
            4,
            4,
            1,
        ],
        k=1,
    )[0]

    # -----------------------------------------------------
    # All Practitioners in this project are relevant to
    # our healthcare observation period.
    #
    # ACTIVE practitioners remain active through the
    # current data end date.
    #
    # INACTIVE / RETIRED / SUSPENDED practitioners were
    # active for at least part of the 2024-2026 period.
    # -----------------------------------------------------

    if status == "ACTIVE":

        effective_date = random_date_between(
            date(2010, 1, 1),
            DATA_END_DATE,
            rng,
        )

        termination_date = ""

    else:

        effective_date = random_date_between(
            date(2010, 1, 1),
            date(2023, 12, 31),
            rng,
        )

        # Historical practitioners remain relevant for
        # at least part of our project observation window.
        termination_date = random_date_between(
            date(2024, 1, 1),
            DATA_END_DATE,
            rng,
        ).isoformat()

    return (
        status,
        effective_date,
        termination_date,
    )

def generate_practitioner_record(
    practitioner_number: int,
    rng: random.Random,
):

    practitioner_id = (
        f"PRV{practitioner_number:09d}"
    )

    (
        first_name,
        middle_initial,
        last_name,
    ) = choose_practitioner_name(
        rng
    )

    credential = rng.choices(
        population=PRACTITIONER_CREDENTIALS,
        weights=[85, 15],
        k=1,
    )[0]

    suffix = rng.choice(
        PRACTITIONER_SUFFIXES
    )

    primary_specialty = rng.choices(
        population=PRACTITIONER_SPECIALTIES,
        weights=[
            15,  # FAMILY_MEDICINE
            12,  # INTERNAL_MEDICINE
            8,   # PEDIATRICS
            6,   # CARDIOLOGY
            5,   # ORTHOPEDICS
            4,   # DERMATOLOGY
            4,   # NEUROLOGY
            5,   # PSYCHIATRY
            5,   # GENERAL_SURGERY
            5,   # OB/GYN
            5,   # EMERGENCY_MEDICINE
            4,   # ANESTHESIOLOGY
            4,   # RADIOLOGY
            2,   # PATHOLOGY
            3,   # ONCOLOGY
            3,   # GASTROENTEROLOGY
            2,   # ENDOCRINOLOGY
            2,   # NEPHROLOGY
            2,   # PULMONOLOGY
            1,   # RHEUMATOLOGY
            2,   # UROLOGY
            2,   # OPHTHALMOLOGY
            1,   # OTOLARYNGOLOGY
        ],
        k=1,
    )[0]

    license_state = rng.choice(
        US_LICENSE_STATES
    )

    license_number = (
        f"{license_state}"
        f"{practitioner_number:09d}"
    )

    board_certified_flag = rng.choices(
        population=["Y", "N"],
        weights=[88, 12],
        k=1,
    )[0]

    (
        practitioner_status,
        effective_date,
        termination_date,
    ) = determine_practitioner_status(
        rng
    )

    # Synthetic 10-digit individual NPI.
    individual_npi = (
        f"17{practitioner_number:08d}"
    )

    create_date = random_date_between(
        date(2010, 1, 1),
        DATA_END_DATE,
        rng,
    )

    update_date = random_date_between(
        create_date,
        DATA_END_DATE,
        rng,
    )

    return {
        "practitioner_id": (
            practitioner_id
        ),
        "individual_npi": (
            individual_npi
        ),
        "first_name": (
            first_name
        ),
        "middle_initial": (
            middle_initial
        ),
        "last_name": (
            last_name
        ),
        "suffix": (
            suffix
        ),
        "credential": (
            credential
        ),
        "primary_specialty": (
            primary_specialty
        ),
        "license_number": (
            license_number
        ),
        "license_state": (
            license_state
        ),
        "board_certified_flag": (
            board_certified_flag
        ),
        "practitioner_status": (
            practitioner_status
        ),
        "effective_date": (
            effective_date.isoformat()
        ),
        "termination_date": (
            termination_date
        ),
        "source_practitioner_key": (
            f"SRCPRV{practitioner_number:09d}"
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


def generate_practitioners(
    practitioner_count: int,
    output_root: Path,
) -> None:

    rng = random.Random(
        RANDOM_SEED + 300
    )

    practitioner_output_dir = (
        output_root
        / "practitioner"
    )

    practitioner_output_dir.mkdir(
        parents=True,
        exist_ok=True,
    )

    rows_per_file = (
        ROWS_PER_FILE[
            "practitioner"
        ]
    )

    file_number = 1
    practitioner_number = 1

    while (
        practitioner_number
        <= practitioner_count
    ):

        file_path = (
            practitioner_output_dir
            / (
                f"practitioner_"
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
                    PRACTITIONER_COLUMNS
                ),
            )

            writer.writeheader()

            rows_written = 0

            while (
                practitioner_number
                <= practitioner_count
                and rows_written
                < rows_per_file
            ):

                record = (
                    generate_practitioner_record(
                        practitioner_number=(
                            practitioner_number
                        ),
                        rng=rng,
                    )
                )

                writer.writerow(
                    record
                )

                practitioner_number += 1
                rows_written += 1

        file_number += 1

    print()

    print(
        f"Generated {practitioner_count:,} "
        f"practitioner rows."
    )

    print(
        f"Practitioner output directory: "
        f"{practitioner_output_dir}"
    )