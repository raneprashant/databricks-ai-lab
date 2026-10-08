"""
Project 01 - Healthcare Payer Data Platform
Module: generate_all.py

Purpose
-------
Runs the complete base synthetic-data generation process in the
required dependency order.

What This Module Does
---------------------
Executes generate_data.py as a separate subprocess for each domain
group in this sequence:

    1. member
    2. supplier
    3. supplier_location
    4. practitioner
    5. practitioner_role
    6. address
    7. entity_address
    8. payer_reference
    9. eligibility
   10. claims

Why The Order Matters
---------------------
Several generators depend on data produced by earlier generators.
For example:

- Supplier Location requires Supplier.
- Practitioner Role requires Practitioner and Supplier Location.
- Entity Address requires the Address and provider/member domains.
- Eligibility requires Member and payer-reference data.
- Claims require Eligibility and provider/reference data.

Behavior
--------
- Executes each domain through generate_data.py.
- Reports execution time for each domain.
- Stops immediately if any domain-generation subprocess fails.
- Reports total generation runtime after successful completion.

Execution
---------
Example:

    python generate_all.py --scale medium

Supported scales:

    smoke
    medium
    full
"""



import argparse
import subprocess
import sys
import time
from pathlib import Path


SCRIPT_DIR = (
    Path(__file__)
    .resolve()
    .parent
)

GENERATE_SCRIPT = (
    SCRIPT_DIR
    / "generate_data.py"
)


GENERATION_SEQUENCE = [
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
]


def run_domain(
    scale: str,
    domain: str,
) -> None:

    command = [
        sys.executable,
        str(GENERATE_SCRIPT),
        "--scale",
        scale,
        "--domain",
        domain,
    ]

    print()
    print("=" * 80)
    print(
        f"GENERATING DOMAIN: "
        f"{domain.upper()}"
    )
    print(
        f"SCALE            : "
        f"{scale}"
    )
    print("=" * 80)

    start_time = time.time()

    result = subprocess.run(
        command
    )

    elapsed_seconds = (
        time.time()
        - start_time
    )

    if result.returncode != 0:

        print()
        print("=" * 80)
        print(
            f"GENERATION FAILED: "
            f"{domain}"
        )
        print(
            f"Exit code: "
            f"{result.returncode}"
        )
        print("=" * 80)

        raise SystemExit(
            result.returncode
        )

    print()
    print(
        f"Completed {domain} "
        f"in {elapsed_seconds:.1f} seconds."
    )


def main():

    parser = argparse.ArgumentParser(
        description=(
            "Generate all synthetic healthcare "
            "payer datasets in dependency order."
        )
    )

    parser.add_argument(
        "--scale",
        choices=[
            "smoke",
            "medium",
            "full",
        ],
        required=True,
    )

    args = parser.parse_args()

    print()
    print("=" * 80)
    print(
        "HEALTHCARE PAYER DATA GENERATION"
    )
    print("=" * 80)

    print(
        f"Scale   : {args.scale}"
    )

    print(
        f"Domains : "
        f"{len(GENERATION_SEQUENCE)}"
    )

    print()

    for index, domain in enumerate(
        GENERATION_SEQUENCE,
        start=1,
    ):

        print(
            f"[{index}/"
            f"{len(GENERATION_SEQUENCE)}] "
            f"{domain}"
        )

    overall_start = time.time()

    for domain in (
        GENERATION_SEQUENCE
    ):

        run_domain(
            scale=args.scale,
            domain=domain,
        )

    total_seconds = (
        time.time()
        - overall_start
    )

    print()
    print("=" * 80)
    print(
        "ALL DATA GENERATION COMPLETED"
    )
    print("=" * 80)

    print(
        f"Scale        : "
        f"{args.scale}"
    )

    print(
        f"Domains      : "
        f"{len(GENERATION_SEQUENCE)}"
    )

    print(
        f"Total runtime: "
        f"{total_seconds:.1f} seconds"
    )

    print("=" * 80)
    print()


if __name__ == "__main__":
    main()