import csv
from collections import Counter, defaultdict
from pathlib import Path


PROJECT_ROOT = Path(__file__).resolve().parents[1]

DATA_ROOT = (
    PROJECT_ROOT
    / "generated_data"
    / "smoke"
)


def load_rows(
    folder_name: str,
    file_pattern: str,
):
    rows = []

    folder = (
        DATA_ROOT
        / folder_name
    )

    for file_path in sorted(
        folder.glob(file_pattern)
    ):
        with file_path.open(
            mode="r",
            newline="",
            encoding="utf-8",
        ) as file_handle:

            rows.extend(
                csv.DictReader(file_handle)
            )

    return rows


def main():

    entity_addresses = load_rows(
        "entity_address",
        "entity_address_*.csv",
    )

    members = load_rows(
        "member",
        "member_*.csv",
    )

    practitioners = load_rows(
        "practitioner",
        "practitioner_*.csv",
    )

    suppliers = load_rows(
        "supplier",
        "supplier_*.csv",
    )

    supplier_locations = load_rows(
        "supplier_location",
        "supplier_location_*.csv",
    )

    practitioner_roles = load_rows(
        "practitioner_role",
        "practitioner_role_*.csv",
    )

    print()
    print("=" * 75)
    print("ENTITY ADDRESS VALIDATION")
    print("=" * 75)

    # ---------------------------------------------------------
    # 1. Distribution by entity type / address type
    # ---------------------------------------------------------

    combinations = Counter(
        (
            row["entity_type"],
            row["address_type"],
        )
        for row in entity_addresses
    )

    print()
    print("ADDRESS RELATIONSHIPS BY TYPE")
    print("-" * 75)

    for (
        entity_type,
        address_type,
    ), count in sorted(
        combinations.items()
    ):
        print(
            f"{entity_type:25}"
            f"{address_type:25}"
            f"{count:>10,}"
        )

    # ---------------------------------------------------------
    # 2. Required address types
    # ---------------------------------------------------------

    required_relationships = {
        "MEMBER": "RESIDENTIAL",
        "PRACTITIONER": "PRIMARY_PRACTICE",
        "SUPPLIER": "PRIMARY_BUSINESS",
        "SUPPLIER_LOCATION": "SERVICE_LOCATION",
        "PRACTITIONER_ROLE": "PRACTICE",
    }

    bridge_lookup = defaultdict(
        lambda: defaultdict(list)
    )

    for row in entity_addresses:

        bridge_lookup[
            row["entity_type"]
        ][
            row["entity_id"]
        ].append(
            row
        )

    source_entities = {
        "MEMBER": [
            row["member_id"]
            for row in members
        ],
        "PRACTITIONER": [
            row["practitioner_id"]
            for row in practitioners
        ],
        "SUPPLIER": [
            row["supplier_id"]
            for row in suppliers
        ],
        "SUPPLIER_LOCATION": [
            row["supplier_location_id"]
            for row in supplier_locations
        ],
        "PRACTITIONER_ROLE": [
            row["practitioner_role_id"]
            for row in practitioner_roles
        ],
    }

    print()
    print("REQUIRED ADDRESS CHECK")
    print("-" * 75)

    required_errors = 0

    for (
        entity_type,
        required_address_type,
    ) in required_relationships.items():

        missing_count = 0

        for entity_id in source_entities[
            entity_type
        ]:

            address_types = {
                row["address_type"]
                for row in bridge_lookup[
                    entity_type
                ][
                    entity_id
                ]
            }

            if (
                required_address_type
                not in address_types
            ):
                missing_count += 1

        required_errors += (
            missing_count
        )

        print(
            f"{entity_type:25}"
            f"{required_address_type:25}"
            f"missing = {missing_count:,}"
        )

    # ---------------------------------------------------------
    # 3. Supplier Location SERVICE_LOCATION lookup
    # ---------------------------------------------------------

    location_service_address = {}

    for row in entity_addresses:

        if (
            row["entity_type"]
            == "SUPPLIER_LOCATION"
            and row["address_type"]
            == "SERVICE_LOCATION"
        ):

            location_service_address[
                row["entity_id"]
            ] = row["address_id"]

    # ---------------------------------------------------------
    # 4. Practitioner Role PRACTICE address must equal
    #    Supplier Location SERVICE_LOCATION
    # ---------------------------------------------------------

    role_practice_address = {}

    for row in entity_addresses:

        if (
            row["entity_type"]
            == "PRACTITIONER_ROLE"
            and row["address_type"]
            == "PRACTICE"
        ):

            role_practice_address[
                row["entity_id"]
            ] = row["address_id"]

    role_location_mismatches = []

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

        expected_address = (
            location_service_address.get(
                location_id
            )
        )

        actual_address = (
            role_practice_address.get(
                role_id
            )
        )

        if (
            expected_address
            != actual_address
        ):
            role_location_mismatches.append(
                (
                    role_id,
                    location_id,
                    expected_address,
                    actual_address,
                )
            )

    print()
    print(
        "PRACTITIONER ROLE → SUPPLIER LOCATION ADDRESS CHECK"
    )
    print("-" * 75)

    print(
        f"Roles checked : "
        f"{len(practitioner_roles):,}"
    )

    print(
        f"Mismatches    : "
        f"{len(role_location_mismatches):,}"
    )

    # ---------------------------------------------------------
    # 5. Practitioner PRIMARY_PRACTICE should match
    #    primary affiliation location
    # ---------------------------------------------------------

    practitioner_primary_address = {}

    for row in entity_addresses:

        if (
            row["entity_type"]
            == "PRACTITIONER"
            and row["address_type"]
            == "PRIMARY_PRACTICE"
        ):
            practitioner_primary_address[
                row["entity_id"]
            ] = row["address_id"]

    primary_roles = {
        row["practitioner_id"]: row
        for row in practitioner_roles
        if row[
            "primary_affiliation_flag"
        ] == "Y"
    }

    practitioner_mismatches = []

    for practitioner_id, role in (
        primary_roles.items()
    ):

        location_id = (
            role[
                "supplier_location_id"
            ]
        )

        expected_address = (
            location_service_address.get(
                location_id
            )
        )

        actual_address = (
            practitioner_primary_address.get(
                practitioner_id
            )
        )

        if (
            expected_address
            != actual_address
        ):
            practitioner_mismatches.append(
                practitioner_id
            )

    print()
    print(
        "PRACTITIONER PRIMARY PRACTICE CHECK"
    )
    print("-" * 75)

    print(
        f"Practitioners checked : "
        f"{len(primary_roles):,}"
    )

    print(
        f"Mismatches            : "
        f"{len(practitioner_mismatches):,}"
    )

    # ---------------------------------------------------------
    # 6. Household sharing check
    # ---------------------------------------------------------

    member_residential_address = {}

    for row in entity_addresses:

        if (
            row["entity_type"]
            == "MEMBER"
            and row["address_type"]
            == "RESIDENTIAL"
        ):

            member_residential_address[
                row["entity_id"]
            ] = row["address_id"]

    families = defaultdict(
        list
    )

    for member in members:

        families[
            member["family_id"]
        ].append(
            member["member_id"]
        )

    shared_family_count = 0
    family_mismatch_count = 0

    for member_ids in (
        families.values()
    ):

        if len(member_ids) <= 1:
            continue

        addresses = {
            member_residential_address.get(
                member_id
            )
            for member_id in member_ids
        }

        addresses.discard(
            None
        )

        if len(addresses) == 1:
            shared_family_count += 1
        else:
            family_mismatch_count += 1

    print()
    print(
        "HOUSEHOLD RESIDENTIAL ADDRESS CHECK"
    )
    print("-" * 75)

    print(
        f"Multi-member families sharing "
        f"one address : "
        f"{shared_family_count:,}"
    )

    print(
        f"Family mismatches                  : "
        f"{family_mismatch_count:,}"
    )

    # ---------------------------------------------------------
    # 7. Show how many entities have multiple address types
    # ---------------------------------------------------------

    print()
    print(
        "ENTITIES WITH MULTIPLE ADDRESS TYPES"
    )
    print("-" * 75)

    for entity_type in [
        "MEMBER",
        "PRACTITIONER",
        "SUPPLIER",
        "SUPPLIER_LOCATION",
        "PRACTITIONER_ROLE",
    ]:

        multiple_count = 0

        for rows in (
            bridge_lookup[
                entity_type
            ].values()
        ):

            address_types = {
                row["address_type"]
                for row in rows
            }

            if len(address_types) > 1:
                multiple_count += 1

        print(
            f"{entity_type:25}"
            f"{multiple_count:>10,}"
        )

    # ---------------------------------------------------------
    # Final result
    # ---------------------------------------------------------

    total_errors = (
        required_errors
        + len(
            role_location_mismatches
        )
        + len(
            practitioner_mismatches
        )
        + family_mismatch_count
    )

    print()
    print("=" * 75)

    if total_errors == 0:

        print(
            "ADDRESS VALIDATION PASSED"
        )

    else:

        print(
            "ADDRESS VALIDATION FAILED"
        )

        print(
            f"Total validation errors: "
            f"{total_errors:,}"
        )

    print("=" * 75)
    print()


if __name__ == "__main__":
    main()