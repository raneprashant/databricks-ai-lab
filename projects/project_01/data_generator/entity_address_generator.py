import csv
import random
from datetime import date, datetime
from pathlib import Path

from config import (
    DATA_END_DATE,
    DATA_START_DATE,
    RANDOM_SEED,
    ROWS_PER_FILE,
)


ENTITY_ADDRESS_COLUMNS = [
    "entity_address_id",
    "entity_type",
    "entity_id",
    "address_id",
    "address_type",
    "primary_flag",
    "effective_date",
    "termination_date",
    "active_flag",
    "source_entity_address_key",
    "create_ts",
    "update_ts",
]


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
            f"No files matching '{file_pattern}' "
            f"found in {directory}."
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


def parse_date(
    value: str,
):

    if not value:
        return None

    # Handles timestamp values as well as plain dates.
    return date.fromisoformat(
        value[:10]
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


class AddressAllocator:
    """
    Provides unused physical addresses from Address Master.

    Addresses can later be reused deliberately by the
    bridge, but this allocator gives us a fresh address
    whenever a new physical address is required.
    """

    def __init__(
        self,
        addresses: list,
    ):

        self.addresses = addresses
        self.next_index = 0

    def next_address_id(
        self,
    ) -> str:

        if (
            self.next_index
            >= len(self.addresses)
        ):
            raise RuntimeError(
                "Address Master does not contain "
                "enough physical addresses."
            )

        address_id = (
            self.addresses[
                self.next_index
            ]["address_id"]
        )

        self.next_index += 1

        return address_id


def add_bridge_row(
    rows: list,
    entity_type: str,
    entity_id: str,
    address_id: str,
    address_type: str,
    primary_flag: str,
    effective_date: date,
    termination_date,
    rng: random.Random,
):

    row_number = len(rows) + 1

    if termination_date:

        active_flag = (
            "Y"
            if termination_date > DATA_END_DATE
            else "N"
        )

    else:

        active_flag = "Y"

    create_date = effective_date

    if create_date > DATA_END_DATE:
        create_date = DATA_END_DATE

    update_date = (
        termination_date
        if termination_date
        and termination_date <= DATA_END_DATE
        else DATA_END_DATE
    )

    if update_date < create_date:
        update_date = create_date

    rows.append(
        {
            "entity_address_id": (
                f"EADR{row_number:010d}"
            ),
            "entity_type": (
                entity_type
            ),
            "entity_id": (
                entity_id
            ),
            "address_id": (
                address_id
            ),
            "address_type": (
                address_type
            ),
            "primary_flag": (
                primary_flag
            ),
            "effective_date": (
                effective_date.isoformat()
            ),
            "termination_date": (
                termination_date.isoformat()
                if termination_date
                else ""
            ),
            "active_flag": (
                active_flag
            ),
            "source_entity_address_key": (
                f"SRCEADR{row_number:010d}"
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


def build_member_addresses(
    rows: list,
    members: list,
    allocator: AddressAllocator,
    rng: random.Random,
):

    family_address = {}

    for member in members:

        family_id = (
            member["family_id"]
        )

        # ---------------------------------------------
        # One household residential address per family.
        # ---------------------------------------------

        if family_id not in family_address:

            family_address[
                family_id
            ] = allocator.next_address_id()

        residential_address = (
            family_address[
                family_id
            ]
        )

        member_id = (
            member["member_id"]
        )

        effective_date = max(
            DATA_START_DATE,
            parse_date(
                member["create_ts"]
            ),
        )

        death_date = parse_date(
            member["death_date"]
        )

        add_bridge_row(
            rows=rows,
            entity_type="MEMBER",
            entity_id=member_id,
            address_id=residential_address,
            address_type="RESIDENTIAL",
            primary_flag="Y",
            effective_date=effective_date,
            termination_date=death_date,
            rng=rng,
        )

        # ---------------------------------------------
        # Mailing address.
        #
        # Most members receive one. Most reuse their
        # residential address; some use a different
        # mailing address.
        # ---------------------------------------------

        if rng.random() < 0.78:

            if rng.random() < 0.80:

                mailing_address = (
                    residential_address
                )

            else:

                mailing_address = (
                    allocator.next_address_id()
                )

            add_bridge_row(
                rows=rows,
                entity_type="MEMBER",
                entity_id=member_id,
                address_id=mailing_address,
                address_type="MAILING",
                primary_flag="N",
                effective_date=effective_date,
                termination_date=death_date,
                rng=rng,
            )

        # ---------------------------------------------
        # Correspondence address.
        # ---------------------------------------------

        if rng.random() < 0.28:

            if rng.random() < 0.70:

                correspondence_address = (
                    residential_address
                )

            else:

                correspondence_address = (
                    allocator.next_address_id()
                )

            add_bridge_row(
                rows=rows,
                entity_type="MEMBER",
                entity_id=member_id,
                address_id=(
                    correspondence_address
                ),
                address_type="CORRESPONDENCE",
                primary_flag="N",
                effective_date=effective_date,
                termination_date=death_date,
                rng=rng,
            )


def build_supplier_addresses(
    rows: list,
    suppliers: list,
    allocator: AddressAllocator,
    rng: random.Random,
):

    supplier_primary_addresses = {}

    for supplier in suppliers:

        supplier_id = (
            supplier["supplier_id"]
        )

        primary_address = (
            allocator.next_address_id()
        )

        supplier_primary_addresses[
            supplier_id
        ] = primary_address

        effective_date = max(
            DATA_START_DATE,
            parse_date(
                supplier[
                    "contract_effective_date"
                ]
            ),
        )

        termination_date = parse_date(
            supplier[
                "contract_termination_date"
            ]
        )

        add_bridge_row(
            rows,
            "SUPPLIER",
            supplier_id,
            primary_address,
            "PRIMARY_BUSINESS",
            "Y",
            effective_date,
            termination_date,
            rng,
        )

        # Mailing
        if rng.random() < 0.90:

            mailing_address = (
                primary_address
                if rng.random() < 0.75
                else allocator.next_address_id()
            )

            add_bridge_row(
                rows,
                "SUPPLIER",
                supplier_id,
                mailing_address,
                "MAILING",
                "N",
                effective_date,
                termination_date,
                rng,
            )

        # Billing
        if rng.random() < 0.80:

            billing_address = (
                primary_address
                if rng.random() < 0.45
                else allocator.next_address_id()
            )

            add_bridge_row(
                rows,
                "SUPPLIER",
                supplier_id,
                billing_address,
                "BILLING",
                "N",
                effective_date,
                termination_date,
                rng,
            )

        # Correspondence
        if rng.random() < 0.70:

            correspondence_address = (
                primary_address
                if rng.random() < 0.70
                else allocator.next_address_id()
            )

            add_bridge_row(
                rows,
                "SUPPLIER",
                supplier_id,
                correspondence_address,
                "CORRESPONDENCE",
                "N",
                effective_date,
                termination_date,
                rng,
            )

    return supplier_primary_addresses


def build_supplier_location_addresses(
    rows: list,
    locations: list,
    allocator: AddressAllocator,
    rng: random.Random,
):

    location_service_addresses = {}

    for location in locations:

        location_id = (
            location[
                "supplier_location_id"
            ]
        )

        service_address = (
            allocator.next_address_id()
        )

        location_service_addresses[
            location_id
        ] = service_address

        effective_date = max(
            DATA_START_DATE,
            parse_date(
                location["effective_date"]
            ),
        )

        termination_date = parse_date(
            location["termination_date"]
        )

        add_bridge_row(
            rows,
            "SUPPLIER_LOCATION",
            location_id,
            service_address,
            "SERVICE_LOCATION",
            "Y",
            effective_date,
            termination_date,
            rng,
        )

        if rng.random() < 0.35:

            mailing_address = (
                service_address
                if rng.random() < 0.75
                else allocator.next_address_id()
            )

            add_bridge_row(
                rows,
                "SUPPLIER_LOCATION",
                location_id,
                mailing_address,
                "MAILING",
                "N",
                effective_date,
                termination_date,
                rng,
            )

        if rng.random() < 0.25:

            billing_address = (
                service_address
                if rng.random() < 0.60
                else allocator.next_address_id()
            )

            add_bridge_row(
                rows,
                "SUPPLIER_LOCATION",
                location_id,
                billing_address,
                "BILLING",
                "N",
                effective_date,
                termination_date,
                rng,
            )

        if rng.random() < 0.25:

            correspondence_address = (
                service_address
                if rng.random() < 0.70
                else allocator.next_address_id()
            )

            add_bridge_row(
                rows,
                "SUPPLIER_LOCATION",
                location_id,
                correspondence_address,
                "CORRESPONDENCE",
                "N",
                effective_date,
                termination_date,
                rng,
            )

    return location_service_addresses


def build_role_addresses(
    rows: list,
    practitioner_roles: list,
    location_service_addresses: dict,
    allocator: AddressAllocator,
    rng: random.Random,
):

    for role in practitioner_roles:

        role_id = (
            role[
                "practitioner_role_id"
            ]
        )

        location_id = (
            role[
                "supplier_location_id"
            ]
        )

        # ---------------------------------------------
        # Critical relationship:
        #
        # Practitioner Role PRACTICE address is exactly
        # the Supplier Location SERVICE_LOCATION
        # physical address.
        # ---------------------------------------------

        practice_address = (
            location_service_addresses[
                location_id
            ]
        )

        effective_date = max(
            DATA_START_DATE,
            parse_date(
                role["effective_date"]
            ),
        )

        termination_date = parse_date(
            role["termination_date"]
        )

        add_bridge_row(
            rows,
            "PRACTITIONER_ROLE",
            role_id,
            practice_address,
            "PRACTICE",
            "Y",
            effective_date,
            termination_date,
            rng,
        )

        if rng.random() < 0.20:

            correspondence_address = (
                practice_address
                if rng.random() < 0.80
                else allocator.next_address_id()
            )

            add_bridge_row(
                rows,
                "PRACTITIONER_ROLE",
                role_id,
                correspondence_address,
                "CORRESPONDENCE",
                "N",
                effective_date,
                termination_date,
                rng,
            )


def build_practitioner_addresses(
    rows: list,
    practitioners: list,
    practitioner_roles: list,
    location_service_addresses: dict,
    allocator: AddressAllocator,
    rng: random.Random,
):

    # ---------------------------------------------
    # Index role rows by practitioner.
    # ---------------------------------------------

    roles_by_practitioner = {}

    for role in practitioner_roles:

        practitioner_id = (
            role["practitioner_id"]
        )

        roles_by_practitioner.setdefault(
            practitioner_id,
            [],
        ).append(
            role
        )

    for practitioner in practitioners:

        practitioner_id = (
            practitioner[
                "practitioner_id"
            ]
        )

        roles = roles_by_practitioner.get(
            practitioner_id,
            [],
        )

        if not roles:
            continue

        # Prefer the explicitly designated
        # primary affiliation.
        primary_role = next(
            (
                role
                for role in roles
                if role[
                    "primary_affiliation_flag"
                ] == "Y"
            ),
            roles[0],
        )

        location_id = (
            primary_role[
                "supplier_location_id"
            ]
        )

        primary_practice_address = (
            location_service_addresses[
                location_id
            ]
        )

        effective_date = max(
            DATA_START_DATE,
            parse_date(
                primary_role[
                    "effective_date"
                ]
            ),
        )

        termination_date = parse_date(
            practitioner[
                "termination_date"
            ]
        )

        add_bridge_row(
            rows,
            "PRACTITIONER",
            practitioner_id,
            primary_practice_address,
            "PRIMARY_PRACTICE",
            "Y",
            effective_date,
            termination_date,
            rng,
        )

        if rng.random() < 0.70:

            mailing_address = (
                primary_practice_address
                if rng.random() < 0.65
                else allocator.next_address_id()
            )

            add_bridge_row(
                rows,
                "PRACTITIONER",
                practitioner_id,
                mailing_address,
                "MAILING",
                "N",
                effective_date,
                termination_date,
                rng,
            )

        if rng.random() < 0.60:

            correspondence_address = (
                primary_practice_address
                if rng.random() < 0.70
                else allocator.next_address_id()
            )

            add_bridge_row(
                rows,
                "PRACTITIONER",
                practitioner_id,
                correspondence_address,
                "CORRESPONDENCE",
                "N",
                effective_date,
                termination_date,
                rng,
            )


def fill_to_target_count(
    rows: list,
    target_count: int,
    members: list,
    allocator: AddressAllocator,
    rng: random.Random,
):

    # -----------------------------------------------------
    # Optional historical correspondence addresses are
    # added only if required to reach our configured row
    # count.
    # -----------------------------------------------------

    member_index = 0

    while (
        len(rows)
        < target_count
    ):

        member = members[
            member_index
            % len(members)
        ]

        member_index += 1

        address_id = (
            allocator.next_address_id()
        )

        effective_date = (
            DATA_START_DATE
        )

        add_bridge_row(
            rows,
            "MEMBER",
            member["member_id"],
            address_id,
            "ALTERNATE_CORRESPONDENCE",
            "N",
            effective_date,
            None,
            rng,
        )


def write_entity_address_rows(
    rows: list,
    output_root: Path,
):

    output_dir = (
        output_root
        / "entity_address"
    )

    output_dir.mkdir(
        parents=True,
        exist_ok=True,
    )

    rows_per_file = (
        ROWS_PER_FILE[
            "entity_address"
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
                f"entity_address_"
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
                fieldnames=(
                    ENTITY_ADDRESS_COLUMNS
                ),
            )

            writer.writeheader()

            writer.writerows(
                batch
            )

        file_number += 1

    return output_dir


def generate_entity_addresses(
    entity_address_count: int,
    output_root: Path,
) -> None:

    rng = random.Random(
        RANDOM_SEED + 600
    )

    addresses = load_csv_files(
        output_root / "address",
        "address_*.csv",
    )

    members = load_csv_files(
        output_root / "member",
        "member_*.csv",
    )

    suppliers = load_csv_files(
        output_root / "supplier",
        "supplier_*.csv",
    )

    locations = load_csv_files(
        output_root / "supplier_location",
        "supplier_location_*.csv",
    )

    practitioners = load_csv_files(
        output_root / "practitioner",
        "practitioner_*.csv",
    )

    practitioner_roles = load_csv_files(
        output_root / "practitioner_role",
        "practitioner_role_*.csv",
    )

    allocator = AddressAllocator(
        addresses
    )

    rows = []

    # Supplier addresses
    build_supplier_addresses(
        rows,
        suppliers,
        allocator,
        rng,
    )

    # Supplier Location addresses must be created
    # before Practitioner Role and Practitioner addresses.
    location_service_addresses = (
        build_supplier_location_addresses(
            rows,
            locations,
            allocator,
            rng,
        )
    )

    # Practitioner Role addresses reuse the associated
    # Supplier Location service address.
    build_role_addresses(
        rows,
        practitioner_roles,
        location_service_addresses,
        allocator,
        rng,
    )

    # Practitioner PRIMARY_PRACTICE uses the practitioner's
    # primary role / Supplier Location.
    build_practitioner_addresses(
        rows,
        practitioners,
        practitioner_roles,
        location_service_addresses,
        allocator,
        rng,
    )

    # Member household addressing.
    build_member_addresses(
        rows,
        members,
        allocator,
        rng,
    )

    # Our configured target is approximate but we want
    # deterministic scale, so fill remaining capacity.
    if len(rows) < entity_address_count:

        fill_to_target_count(
            rows,
            entity_address_count,
            members,
            allocator,
            rng,
        )

    if len(rows) > entity_address_count:

        print()
        print(
            "WARNING: Required business address "
            "relationships exceeded configured "
            "entity_address count."
        )

        print(
            f"Configured target : "
            f"{entity_address_count:,}"
        )

        print(
            f"Required rows     : "
            f"{len(rows):,}"
        )

        print(
            "All required rows will be retained."
        )

    output_dir = write_entity_address_rows(
        rows,
        output_root,
    )

    print()
    print(
        f"Generated {len(rows):,} "
        f"entity address rows."
    )

    print(
        f"Address Master rows loaded: "
        f"{len(addresses):,}"
    )

    print(
        f"Member rows loaded: "
        f"{len(members):,}"
    )

    print(
        f"Practitioner rows loaded: "
        f"{len(practitioners):,}"
    )

    print(
        f"Supplier rows loaded: "
        f"{len(suppliers):,}"
    )

    print(
        f"Supplier Location rows loaded: "
        f"{len(locations):,}"
    )

    print(
        f"Practitioner Role rows loaded: "
        f"{len(practitioner_roles):,}"
    )

    print(
        f"Physical addresses consumed: "
        f"{allocator.next_index:,}"
    )

    print(
        f"Entity Address output directory: "
        f"{output_dir}"
    )
    