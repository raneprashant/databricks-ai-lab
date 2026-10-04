import argparse
import shutil
import subprocess
import sys
from pathlib import Path


PROJECT_ROOT = (
    Path(__file__)
    .resolve()
    .parents[1]
)


LANDING_DOMAINS = [
    "member",
    "supplier",
    "supplier_location",
    "practitioner",
    "practitioner_role",
    "address",
    "entity_address",
    "product",
    "benefit_plan",
    "group",
    "subgroup",
    "eligibility",
    "claim_header",
    "claim_line",
]


def run_command(
    command: list[str],
) -> None:

    print(
        " ".join(
            str(item)
            for item in command
        )
    )

    result = subprocess.run(
        command
    )

    if result.returncode != 0:

        raise SystemExit(
            result.returncode
        )


def main():

    parser = argparse.ArgumentParser(
        description=(
            "Upload generated payer source CSV "
            "files into a Databricks landing volume."
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

    parser.add_argument(
        "--profile",
        default="DATABRICKS_FREE",
    )

    parser.add_argument(
        "--catalog",
        default="payer_01_dev",
    )

    parser.add_argument(
        "--schema",
        default="bronze",
    )

    parser.add_argument(
        "--volume",
        default="landing",
    )

    args = parser.parse_args()

    # -----------------------------------------------------
    # Verify Databricks CLI exists
    # -----------------------------------------------------

    databricks_cli = shutil.which(
        "databricks"
    )

    if not databricks_cli:

        raise RuntimeError(
            "Databricks CLI was not found "
            "in PATH."
        )

    # -----------------------------------------------------
    # Local source root
    # -----------------------------------------------------

    local_root = (
        PROJECT_ROOT
        / "generated_data"
        / args.scale
    )

    if not local_root.exists():

        raise FileNotFoundError(
            f"Local generated-data folder "
            f"does not exist: {local_root}"
        )

    # -----------------------------------------------------
    # Databricks landing volume
    # -----------------------------------------------------

    remote_root = (
        f"dbfs:/Volumes/"
        f"{args.catalog}/"
        f"{args.schema}/"
        f"{args.volume}"
    )

    print()
    print("=" * 80)
    print(
        "DATABRICKS LANDING UPLOAD"
    )
    print("=" * 80)

    print(
        f"Scale        : {args.scale}"
    )

    print(
        f"Local source : {local_root}"
    )

    print(
        f"Remote target: {remote_root}"
    )

    print(
        f"Profile      : {args.profile}"
    )

    print("=" * 80)

    total_files = 0

    # -----------------------------------------------------
    # Process each source domain
    # -----------------------------------------------------

    for domain in LANDING_DOMAINS:

        local_domain = (
            local_root
            / domain
        )

        if not local_domain.exists():

            raise FileNotFoundError(
                f"Missing local domain "
                f"folder: {local_domain}"
            )

        csv_files = sorted(
            local_domain.glob(
                "*.csv"
            )
        )

        if not csv_files:

            raise RuntimeError(
                f"No CSV files found in "
                f"{local_domain}"
            )

        remote_domain = (
            f"{remote_root}/"
            f"{domain}"
        )

        print()
        print("-" * 80)
        print(
            f"DOMAIN: {domain}"
        )
        print(
            f"Files : {len(csv_files)}"
        )
        print("-" * 80)

        # -------------------------------------------------
        # Create destination directory
        #
        # Databricks fs mkdir is safe if the directory
        # already exists.
        # -------------------------------------------------

        run_command(
            [
                databricks_cli,
                "fs",
                "mkdir",
                remote_domain,
                "--profile",
                args.profile,
            ]
        )

        # -------------------------------------------------
        # Upload each CSV explicitly.
        #
        # Doing files individually avoids ambiguity about
        # whether a recursive directory copy adds another
        # nested directory level.
        # -------------------------------------------------

        for local_file in csv_files:

            remote_file = (
                f"{remote_domain}/"
                f"{local_file.name}"
            )

            run_command(
                [
                    databricks_cli,
                    "fs",
                    "cp",
                    str(local_file),
                    remote_file,
                    "--overwrite",
                    "--profile",
                    args.profile,
                ]
            )

            total_files += 1

    print()
    print("=" * 80)
    print(
        "LANDING UPLOAD COMPLETED"
    )
    print("=" * 80)

    print(
        f"Scale         : {args.scale}"
    )

    print(
        f"Domains       : "
        f"{len(LANDING_DOMAINS)}"
    )

    print(
        f"Files uploaded: "
        f"{total_files}"
    )

    print(
        f"Target        : "
        f"{remote_root}"
    )

    print("=" * 80)
    print()


if __name__ == "__main__":
    main()