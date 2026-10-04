import csv
import random
from datetime import date, datetime, timedelta
from pathlib import Path

from config import (
    DATA_END_DATE,
    DATA_START_DATE,
    RANDOM_SEED,
    ROWS_PER_FILE,
)
from reference_data import (
    FIRST_NAMES_FEMALE,
    FIRST_NAMES_MALE,
    LANGUAGES,
    LAST_NAMES,
    MARITAL_STATUSES,
)


MEMBER_COLUMNS = [
    "member_id",
    "family_id",
    "subscriber_id",
    "relationship_to_subscriber",
    "first_name",
    "middle_initial",
    "last_name",
    "date_of_birth",
    "gender",
    "marital_status",
    "preferred_language",
    "phone_number",
    "email_address",
    "member_status",
    "deceased_flag",
    "death_date",
    "source_member_key",
    "create_ts",
    "update_ts",
]


FAMILY_SIZE_VALUES = [1, 2, 3, 4, 5, 6]

FAMILY_SIZE_WEIGHTS = [
    0.25,
    0.25,
    0.20,
    0.15,
    0.10,
    0.05,
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


def birth_date_for_age(
    age: int,
    rng: random.Random,
) -> date:

    birth_year = (
        DATA_END_DATE.year - age
    )

    month = rng.randint(
        1,
        12,
    )

    # Keeping day <= 28 avoids invalid
    # calendar dates.
    day = rng.randint(
        1,
        28,
    )

    candidate_date = date(
        birth_year,
        month,
        day,
    )

    # Age-zero members must not have a DOB
    # after our synthetic observation date.
    #
    # Reflect any overflow back into the
    # valid observation period. This keeps
    # the child age approximately zero while
    # preserving deterministic RNG behavior.
    if candidate_date > DATA_END_DATE:

        overflow_days = (
            candidate_date
            - DATA_END_DATE
        ).days

        candidate_date = (
            DATA_END_DATE
            - timedelta(
                days=overflow_days
            )
        )

    return candidate_date


def choose_gender(
    rng: random.Random,
) -> str:

    return rng.choices(
        population=["M", "F", "X", "U"],
        weights=[49.0, 49.0, 1.0, 1.0],
        k=1,
    )[0]


def choose_name(
    gender: str,
    rng: random.Random,
):

    if gender == "M":
        first_name = rng.choice(FIRST_NAMES_MALE)

    elif gender == "F":
        first_name = rng.choice(FIRST_NAMES_FEMALE)

    else:
        first_name = rng.choice(
            FIRST_NAMES_MALE + FIRST_NAMES_FEMALE
        )

    last_name = rng.choice(LAST_NAMES)

    middle_initial = chr(
        rng.randint(
            ord("A"),
            ord("Z"),
        )
    )

    return first_name, middle_initial, last_name


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


def determine_death(
    age: int,
    dob: date,
    rng: random.Random,
):

    if age >= 70:
        death_probability = 0.015
    elif age >= 50:
        death_probability = 0.005
    elif age >= 18:
        death_probability = 0.001
    else:
        death_probability = 0.0003

    deceased = (
        rng.random()
        < death_probability
    )

    if not deceased:
        return "N", "", "ACTIVE"

    earliest_death = max(
        DATA_START_DATE,
        dob + timedelta(days=1),
    )

    death_date = random_date_between(
        earliest_death,
        DATA_END_DATE,
        rng,
    )

    return (
        "Y",
        death_date.isoformat(),
        "DECEASED",
    )


def generate_member_record(
    member_number: int,
    family_number: int,
    subscriber_id: str,
    relationship: str,
    subscriber_age: int,
    family_last_name: str,
    rng: random.Random,
):

    member_id = f"MBR{member_number:09d}"

    family_id = f"FAM{family_number:08d}"

    if relationship == "SELF":

        age = subscriber_age

    elif relationship == "SPOUSE":

        age = max(
            18,
            subscriber_age
            + rng.randint(-7, 7),
        )

    else:

        max_child_age = max(
            0,
            min(
                26,
                subscriber_age - 18,
            ),
        )

        age = rng.randint(
            0,
            max_child_age,
        )

    dob = birth_date_for_age(
        age,
        rng,
    )

    gender = choose_gender(
        rng
    )

    first_name, middle_initial, generated_last_name = (
        choose_name(
            gender,
            rng,
        )
    )

    # The subscriber establishes the household surname.
    # Most dependents share that surname, while a smaller
    # percentage intentionally have a different surname.
    if relationship == "SELF":
        last_name = family_last_name
    elif rng.random() < 0.82:
        last_name = family_last_name
    else:
        last_name = generated_last_name

    if relationship == "SELF":

        marital_status = rng.choices(
            population=MARITAL_STATUSES,
            weights=[35, 50, 10, 5],
            k=1,
        )[0]

    elif relationship == "SPOUSE":

        marital_status = "MARRIED"

    else:

        marital_status = "SINGLE"

    preferred_language = rng.choices(
        population=LANGUAGES,
        weights=[
            72,
            14,
            3,
            2,
            2,
            3,
            2,
            2,
        ],
        k=1,
    )[0]

    deceased_flag, death_date, member_status = (
        determine_death(
            age,
            dob,
            rng,
        )
    )

    phone_number = (
        f"{rng.randint(201, 989)}-"
        f"{rng.randint(200, 999)}-"
        f"{rng.randint(1000, 9999)}"
    )

    email_address = (
        f"{first_name.lower()}."
        f"{last_name.lower()}."
        f"{member_number}"
        "@syntheticpayer.test"
    )

    source_member_key = (
        f"SRCMBR{member_number:09d}"
    )

    create_date = random_date_between(
        date(2022, 1, 1),
        DATA_END_DATE,
        rng,
    )

    update_date = random_date_between(
        create_date,
        DATA_END_DATE,
        rng,
    )

    return {
        "member_id": member_id,
        "family_id": family_id,
        "subscriber_id": subscriber_id,
        "relationship_to_subscriber": relationship,
        "first_name": first_name,
        "middle_initial": middle_initial,
        "last_name": last_name,
        "date_of_birth": dob.isoformat(),
        "gender": gender,
        "marital_status": marital_status,
        "preferred_language": preferred_language,
        "phone_number": phone_number,
        "email_address": email_address,
        "member_status": member_status,
        "deceased_flag": deceased_flag,
        "death_date": death_date,
        "source_member_key": source_member_key,
        "create_ts": build_timestamp(
            create_date,
            rng,
        ),
        "update_ts": build_timestamp(
            update_date,
            rng,
        ),
    }


def generate_members(
    member_count: int,
    output_root: Path,
) -> None:

    rng = random.Random(
        RANDOM_SEED
    )

    member_output_dir = (
        output_root / "member"
    )

    member_output_dir.mkdir(
        parents=True,
        exist_ok=True,
    )

    rows_per_file = (
        ROWS_PER_FILE["member"]
    )

    member_number = 1
    family_number = 1
    file_number = 1

    rows_in_current_file = 0

    writer = None
    file_handle = None

    def open_next_file(
        current_file_number: int,
    ):

        file_path = (
            member_output_dir
            / f"member_{current_file_number:03d}.csv"
        )

        handle = file_path.open(
            mode="w",
            newline="",
            encoding="utf-8",
        )

        csv_writer = csv.DictWriter(
            handle,
            fieldnames=MEMBER_COLUMNS,
        )

        csv_writer.writeheader()

        print(
            f"Writing {file_path}"
        )

        return handle, csv_writer

    file_handle, writer = open_next_file(
        file_number
    )

    while member_number <= member_count:

        remaining = (
            member_count
            - member_number
            + 1
        )

        family_size = rng.choices(
            population=FAMILY_SIZE_VALUES,
            weights=FAMILY_SIZE_WEIGHTS,
            k=1,
        )[0]

        family_size = min(
            family_size,
            remaining,
        )

        subscriber_age = rng.randint(
            25,
            78,
        )

        subscriber_id = (
            f"MBR{member_number:09d}"
        )

        subscriber_gender = choose_gender(
            rng
        )

        (
            _,
            _,
            family_last_name,
        ) = choose_name(
            subscriber_gender,
            rng,
        )

        has_spouse = (
            family_size >= 2
            and rng.random() < 0.65
        )

        for family_position in range(
            family_size
        ):

            if family_position == 0:

                relationship = "SELF"

            elif (
                family_position == 1
                and has_spouse
            ):

                relationship = "SPOUSE"

            else:

                relationship = "CHILD"

            record = generate_member_record(
                member_number=member_number,
                family_number=family_number,
                subscriber_id=subscriber_id,
                relationship=relationship,
                subscriber_age=subscriber_age,
                family_last_name=family_last_name,
                rng=rng,
            )

            writer.writerow(
                record
            )

            member_number += 1
            rows_in_current_file += 1

            if (
                rows_in_current_file
                >= rows_per_file
                and member_number
                <= member_count
            ):

                file_handle.close()

                file_number += 1
                rows_in_current_file = 0

                (
                    file_handle,
                    writer,
                ) = open_next_file(
                    file_number
                )

        family_number += 1

    if file_handle:
        file_handle.close()

    print()
    print(
        f"Generated {member_count:,} member rows."
    )

    print(
        f"Generated {family_number - 1:,} families."
    )

    print(
        f"Member output directory: "
        f"{member_output_dir}"
    )