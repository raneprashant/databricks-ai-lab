"""
Project 01 - Healthcare Payer Data Platform
Module: upload_to_landing.py

Purpose
-------
Uploads generated Project 01 base or incremental CSV source files from
the local machine to the Databricks Bronze landing Volume.

What This Module Does
---------------------
- Verifies that the Databricks CLI is available in PATH.
- Supports smoke, medium, and full generated-data scales.
- Uploads either:
    - the base generated dataset, or
    - one specified incremental batch.
- Processes all 14 Project 01 source domains.
- Creates the remote domain directory when required.
- Copies each local CSV into the corresponding Databricks landing
  directory.
- Uses the configured Databricks CLI profile.
- Uses --overwrite when copying a file with the same remote filename.

Local Sources
-------------
Base load:

    generated_data/<scale>/<domain>/*.csv

Incremental load:

    generated_data/<scale>/incremental/<batch_id>/<domain>/*.csv

Default Databricks Target
-------------------------
    /Volumes/payer_01_dev/bronze/landing/<domain>/

The catalog, schema, Volume, and CLI profile can be overridden through
command-line arguments.

Execution
---------
Base upload example:

    python upload_to_landing.py --scale medium

Incremental upload example:

    python upload_to_landing.py \
        --scale medium \
        --batch-id 20261008_153701

Default CLI profile:

    DATABRICKS_FREE

Important Notes
---------------
This script uploads source files only. It does not execute Bronze,
Silver, Gold, validation, or dashboard pipelines/jobs.
"""


import argparse
import shutil
import subprocess
from pathlib import Path


PROJECT_ROOT = (
    Path(__file__)
    .resolve()
    .parents[1]
)


LANDING_DOMAINS = [
    "member",
    "product",
    "benefit_plan",
    "group",
    "subgroup",
    "eligibility",
    "practitioner",
    "supplier",
    "supplier_location",
    "practitioner_role",
    "address",
    "entity_address",
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
            "Upload base or incremental payer CSV files "
            "to Databricks landing volume."
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
        "--batch-id",
        required=False,
        help=(
            "Incremental batch folder, for example "
            "20261005_153749. "
            "If omitted, base files are uploaded."
        ),
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
    # Verify Databricks CLI
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
    # Determine local source
    #
    # No batch-id:
    #   generated_data/medium/member/*.csv
    #
    # With batch-id:
    #   generated_data/medium/incremental/
    #       20261005_153749/member/*.csv
    # -----------------------------------------------------

    scale_root = (
        PROJECT_ROOT
        / "generated_data"
        / args.scale
    )

    if args.batch_id:

        local_root = (
            scale_root
            / "incremental"
            / args.batch_id
        )

        load_type = "INCREMENTAL"

    else:

        local_root = (
            scale_root
        )

        load_type = "BASE"

    if not local_root.exists():

        raise FileNotFoundError(
            f"Local source folder "
            f"does not exist: "
            f"{local_root}"
        )

    # -----------------------------------------------------
    # Databricks landing root
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
        f"Load type    : {load_type}"
    )

    print(
        f"Scale        : {args.scale}"
    )

    if args.batch_id:

        print(
            f"Batch ID     : "
            f"{args.batch_id}"
        )

    print(
        f"Local source : "
        f"{local_root}"
    )

    print(
        f"Remote target: "
        f"{remote_root}"
    )

    print(
        f"Profile      : "
        f"{args.profile}"
    )

    print("=" * 80)

    total_files = 0

    # -----------------------------------------------------
    # Process all 14 domains
    # -----------------------------------------------------

    for domain in LANDING_DOMAINS:

        local_domain = (
            local_root
            / domain
        )

        if not local_domain.exists():

            raise FileNotFoundError(
                f"Missing domain folder: "
                f"{local_domain}"
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
            f"Files : "
            f"{len(csv_files)}"
        )

        print("-" * 80)

        # Ensure remote domain directory exists.
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

        # Upload every CSV in this domain.
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
        f"Load type     : "
        f"{load_type}"
    )

    print(
        f"Scale         : "
        f"{args.scale}"
    )

    if args.batch_id:

        print(
            f"Batch ID      : "
            f"{args.batch_id}"
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