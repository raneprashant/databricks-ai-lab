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