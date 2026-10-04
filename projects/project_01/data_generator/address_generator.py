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
    ADDRESS_REGIONS,
    STREET_NAMES,
    STREET_SUFFIXES,
)


ADDRESS_COLUMNS = [
    "address_id",
    "address_line_1",
    "address_line_2",
    "city",
    "state",
    "postal_code",
    "county",
    "country_code",
    "address_status",
    "geocode_quality",
    "source_address_key",
    "create_ts",
    "update_ts",
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


def build_address_components(
    address_number: int,
):

    # -----------------------------------------------------
    # Deterministic address generation.
    #
    # We intentionally produce a large reusable address
    # pool. Multiple entities can later point to the same
    # address through the Entity Address Bridge.
    # -----------------------------------------------------

    value = address_number - 1

    region_index = (
        value
        % len(ADDRESS_REGIONS)
    )

    value //= len(
        ADDRESS_REGIONS
    )

    street_index = (
        value
        % len(STREET_NAMES)
    )

    value //= len(
        STREET_NAMES
    )

    suffix_index = (
        value
        % len(STREET_SUFFIXES)
    )

    value //= len(
        STREET_SUFFIXES
    )

    street_number = (
        100
        + (value % 9800)
    )

    (
        city,
        state,
        county,
        zip_prefix,
    ) = ADDRESS_REGIONS[
        region_index
    ]

    street_name = (
        STREET_NAMES[
            street_index
        ]
    )

    street_suffix = (
        STREET_SUFFIXES[
            suffix_index
        ]
    )

    address_line_1 = (
        f"{street_number} "
        f"{street_name} "
        f"{street_suffix}"
    )

    postal_code = (
        f"{zip_prefix}"
        f"{address_number % 100:02d}"
    )

    return (
        address_line_1,
        city,
        state,
        postal_code,
        county,
    )


def generate_address_record(
    address_number: int,
    rng: random.Random,
):

    address_id = (
        f"ADR{address_number:09d}"
    )

    (
        address_line_1,
        city,
        state,
        postal_code,
        county,
    ) = build_address_components(
        address_number
    )

    # -----------------------------------------------------
    # Secondary address information.
    #
    # Some addresses represent apartment units,
    # office suites, floors, etc.
    # -----------------------------------------------------

    if rng.random() < 0.20:

        secondary_type = rng.choices(
            population=[
                "APT",
                "SUITE",
                "UNIT",
                "FLOOR",
            ],
            weights=[
                40,
                35,
                15,
                10,
            ],
            k=1,
        )[0]

        secondary_number = rng.randint(
            1,
            999,
        )

        address_line_2 = (
            f"{secondary_type} "
            f"{secondary_number}"
        )

    else:

        address_line_2 = ""

    # -----------------------------------------------------
    # Mostly good source data, with a small amount of
    # quality variation for later Bronze -> Silver work.
    # -----------------------------------------------------

    address_status = rng.choices(
        population=[
            "VALID",
            "UNVERIFIED",
            "UNDELIVERABLE",
        ],
        weights=[
            97,
            2,
            1,
        ],
        k=1,
    )[0]

    geocode_quality = rng.choices(
        population=[
            "ROOFTOP",
            "INTERPOLATED",
            "ZIP_CENTROID",
            "NOT_GEOCODED",
        ],
        weights=[
            72,
            18,
            7,
            3,
        ],
        k=1,
    )[0]

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
        "address_id": (
            address_id
        ),
        "address_line_1": (
            address_line_1
        ),
        "address_line_2": (
            address_line_2
        ),
        "city": (
            city
        ),
        "state": (
            state
        ),
        "postal_code": (
            postal_code
        ),
        "county": (
            county
        ),
        "country_code": (
            "US"
        ),
        "address_status": (
            address_status
        ),
        "geocode_quality": (
            geocode_quality
        ),
        "source_address_key": (
            f"SRCADR"
            f"{address_number:09d}"
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


def generate_addresses(
    address_count: int,
    output_root: Path,
) -> None:

    rng = random.Random(
        RANDOM_SEED + 500
    )

    address_output_dir = (
        output_root
        / "address"
    )

    address_output_dir.mkdir(
        parents=True,
        exist_ok=True,
    )

    rows_per_file = (
        ROWS_PER_FILE[
            "address"
        ]
    )

    address_number = 1
    file_number = 1

    while (
        address_number
        <= address_count
    ):

        file_path = (
            address_output_dir
            / (
                f"address_"
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
                    ADDRESS_COLUMNS
                ),
            )

            writer.writeheader()

            rows_written = 0

            while (
                address_number
                <= address_count
                and rows_written
                < rows_per_file
            ):

                record = (
                    generate_address_record(
                        address_number=(
                            address_number
                        ),
                        rng=rng,
                    )
                )

                writer.writerow(
                    record
                )

                address_number += 1
                rows_written += 1

        file_number += 1

    print()

    print(
        f"Generated {address_count:,} "
        f"address rows."
    )

    print(
        f"Address output directory: "
        f"{address_output_dir}"
    )