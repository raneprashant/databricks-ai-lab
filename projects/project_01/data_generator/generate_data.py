import argparse

from config import GENERATED_DATA_ROOT, get_scale
from member_generator import generate_members
from supplier_generator import generate_suppliers
from supplier_location_generator import generate_supplier_locations
from practitioner_generator import generate_practitioners
from practitioner_role_generator import generate_practitioner_roles
from address_generator import generate_addresses
from entity_address_generator import generate_entity_addresses
from payer_reference_generator import generate_payer_reference_data
from eligibility_generator import generate_eligibility
from claim_generator import generate_claims


def print_generation_plan(scale_name: str) -> None:
    """
    Display the planned number of rows for the selected dataset scale.
    This does not generate any data.
    """

    config = get_scale(scale_name)

    output_dir = GENERATED_DATA_ROOT / scale_name
    output_dir.mkdir(parents=True, exist_ok=True)

    print()
    print("=" * 65)
    print("Healthcare Payer Synthetic Data Generator")
    print("=" * 65)

    print(f"Scale       : {scale_name}")
    print(f"Output path : {output_dir}")
    print()

    print("Planned row counts")
    print("-" * 65)

    print(f"{'Product':30} {config.products:>12,}")
    print(f"{'Benefit Plan':30} {config.benefit_plans:>12,}")
    print(f"{'Group':30} {config.groups:>12,}")
    print(f"{'Subgroup':30} {config.subgroups:>12,}")
    print(f"{'Member':30} {config.members:>12,}")
    print(f"{'Eligibility':30} {config.eligibility:>12,}")
    print(f"{'Practitioner':30} {config.practitioners:>12,}")
    print(f"{'Supplier':30} {config.suppliers:>12,}")
    print(f"{'Supplier Location':30} {config.supplier_locations:>12,}")
    print(f"{'Practitioner Role':30} {config.practitioner_roles:>12,}")
    print(f"{'Address Master':30} {config.addresses:>12,}")
    print(f"{'Entity Address Bridge':30} {config.entity_addresses:>12,}")
    print(f"{'Claim Header':30} {config.claim_headers:>12,}")
    print(f"{'Claim Line':30} {config.claim_lines:>12,}")

    print("-" * 65)
    print(f"{'TOTAL':30} {config.total_rows:>12,}")
    print("=" * 65)

    print()
    print("Generator configuration validated successfully.")
    print()


def main() -> None:
    """
    Main command-line entry point.
    """

    # ---------------------------------------------------------
    # ARGUMENT PARSER
    # ---------------------------------------------------------

    parser = argparse.ArgumentParser(
        description="Generate synthetic healthcare payer data."
    )

    parser.add_argument(
        "--scale",
        choices=["smoke", "medium", "full"],
        default="smoke",
        help="Dataset size to generate.",
    )

    parser.add_argument(
        "--domain",
        choices=[
            "summary",
            "member",
            "supplier",
            "supplier_location",
            "practitioner",
            "practitioner_role",
            "address",
            "entity_address",
            "payer_reference",
            "eligibility",
            "claims",
        ],
        default="summary",
        help="Generator domain to execute.",
    )

    args = parser.parse_args()

    # ---------------------------------------------------------
    # DOMAIN ROUTING
    # ---------------------------------------------------------

    if args.domain == "summary":

        print_generation_plan(
            args.scale
        )

    elif args.domain == "member":

        scale_config = get_scale(
            args.scale
        )

        output_dir = (
            GENERATED_DATA_ROOT
            / args.scale
        )

        generate_members(
            member_count=scale_config.members,
            output_root=output_dir,
        )

    elif args.domain == "supplier":

        scale_config = get_scale(
            args.scale
        )

        output_dir = (
            GENERATED_DATA_ROOT
            / args.scale
        )

        generate_suppliers(
            supplier_count=scale_config.suppliers,
            output_root=output_dir,
        )

    elif args.domain == "supplier_location":

        scale_config = get_scale(
            args.scale
        )

        output_dir = (
            GENERATED_DATA_ROOT
            / args.scale
        )

        generate_supplier_locations(
            location_count=(
                scale_config.supplier_locations
            ),
            output_root=output_dir,
        )

    elif args.domain == "practitioner":

        scale_config = get_scale(
            args.scale
        )

        output_dir = (
            GENERATED_DATA_ROOT
            / args.scale
        )

        generate_practitioners(
            practitioner_count=(
                scale_config.practitioners
            ),
            output_root=output_dir,
        )

    elif args.domain == "practitioner_role":

        scale_config = get_scale(
            args.scale
        )

        output_dir = (
            GENERATED_DATA_ROOT
            / args.scale
        )

        generate_practitioner_roles(
            role_count=(
                scale_config.practitioner_roles
            ),
            output_root=output_dir,
        )

    elif args.domain == "address":

        scale_config = get_scale(
            args.scale
        )

        output_dir = (
            GENERATED_DATA_ROOT
            / args.scale
        )

        generate_addresses(
            address_count=(
                scale_config.addresses
            ),
            output_root=output_dir,
        )

    elif args.domain == "entity_address":

        scale_config = get_scale(
            args.scale
        )

        output_dir = (
            GENERATED_DATA_ROOT
            / args.scale
        )

        generate_entity_addresses(
            entity_address_count=(
                scale_config.entity_addresses
            ),
            output_root=output_dir,
        )

    elif args.domain == "payer_reference":

        scale_config = get_scale(
            args.scale
        )

        output_dir = (
            GENERATED_DATA_ROOT
            / args.scale
        )

        generate_payer_reference_data(
            product_count=(
                scale_config.products
            ),
            benefit_plan_count=(
                scale_config.benefit_plans
            ),
            group_count=(
                scale_config.groups
            ),
            subgroup_count=(
                scale_config.subgroups
            ),
            output_root=output_dir,
        )

    elif args.domain == "eligibility":

        scale_config = get_scale(
            args.scale
        )

        output_dir = (
            GENERATED_DATA_ROOT
            / args.scale
        )

        generate_eligibility(
            eligibility_count=(
                scale_config.eligibility
            ),
            output_root=output_dir,
        )

    elif args.domain == "claims":

        scale_config = get_scale(
            args.scale
        )

        output_dir = (
            GENERATED_DATA_ROOT
            / args.scale
        )

        generate_claims(
            claim_header_count=(
                scale_config.claim_headers
            ),
            claim_line_count=(
                scale_config.claim_lines
            ),
            output_root=output_dir,
        )

if __name__ == "__main__":
    main()