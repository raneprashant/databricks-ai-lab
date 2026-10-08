"""
Project 01 - Healthcare Payer Data Platform
Module: generate_incremental.py

Purpose
-------
Generates synthetic incremental source batches used to test end-to-end
incremental ingestion, CDC, SCD Type 2 history, Gold refresh, validation,
and dashboard processing.

What This Module Does
---------------------
- Reads the original base dataset.
- Reads all prior incremental batches that precede the new batch.
- Determines the latest known version of dimension-like business keys.
- Generates updates to existing dimension/reference entities.
- Generates new Eligibility events.
- Generates a mixture of new Claims and updates to existing Claims.
- Preserves Claim and Claim Line business IDs for updates so downstream
  SCD Type 2 processing can detect and retain meaningful history.
- Generates new business IDs where the event represents a true insert.
- Writes one incremental CSV for each of the 14 Project 01 domains.
- Creates batch_manifest.csv describing row counts, change types,
  and generated filenames.

Incremental Behavior
--------------------
Dimension-like domains update existing business keys.

Eligibility is generated as new event/history records.

Claims contain mixed insert/update behavior. Incoming updates that
change only excluded technical metadata may intentionally produce no
new downstream SCD Type 2 business-history version.

Inputs
------
Base data:

    generated_data/<scale>/<domain>/*.csv

Prior incremental data:

    generated_data/<scale>/incremental/<prior_batch_id>/<domain>/*.csv

Outputs
-------
    generated_data/<scale>/incremental/<batch_id>/

The batch folder contains all domain CSV files plus:

    batch_manifest.csv

Execution
---------
Example:

    python generate_incremental.py \
        --scale medium \
        --batch-id 20261008_153701

If --batch-id is omitted, a timestamp-based batch ID is generated.

Important Notes
---------------
This script generates files locally only. It does not upload files to
Databricks and does not execute the Bronze/Silver/Gold pipelines.
"""


import argparse
import csv
import random
import re
from copy import deepcopy
from datetime import datetime, timedelta
from decimal import Decimal, InvalidOperation
from pathlib import Path

from config import (
    DATA_END_DATE,
    RANDOM_SEED,
)

from claim_generator import (
    build_timestamp,
    choose_base_service_category,
    choose_claim_type,
    choose_line_service_category,
    choose_valid_role,
    determine_claim_status,
    diagnosis_category_for_role,
    generate_line_financials,
    money_string,
    parse_date,
    random_date_between,
)

from reference_data import (
    CLAIM_DIAGNOSIS_CODES,
    CLAIM_PROCEDURE_PROFILES,
)


# ============================================================
# Project paths
# ============================================================

PROJECT_ROOT = (
    Path(__file__)
    .resolve()
    .parents[1]
)


# ============================================================
# Incremental Batch 001 volumes
#
# Dimension-like tables:
#     update existing business keys.
#
# Fact/event-like tables:
#     create new business keys.
# ============================================================

INCREMENTAL_COUNTS = {
    "product": 2,
    "benefit_plan": 5,
    "group": 5,
    "subgroup": 8,
    "member": 15,
    "practitioner": 15,
    "supplier": 5,
    "supplier_location": 10,
    "practitioner_role": 15,
    "address": 15,
    "entity_address": 10,

    "eligibility": 200,

    "claim_header": 100,
    "claim_line": 300,
}


DOMAINS = [
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


# ============================================================
# File helpers
# ============================================================

def load_domain_rows(
    base_root: Path,
    domain: str,
    current_batch_id: str = None,
) -> list[dict]:

    rows = []

    # ---------------------------------------------------------
    # 1. Load original/base files.
    #
    # generated_data/medium/member/*.csv
    # ---------------------------------------------------------

    base_folder = (
        base_root
        / domain
    )

    base_files = sorted(
        base_folder.glob(
            "*.csv"
        )
    )

    if not base_files:

        raise FileNotFoundError(
            f"No source CSV files found "
            f"for domain '{domain}' "
            f"in {base_folder}"
        )

    for file_path in base_files:

        with file_path.open(
            mode="r",
            newline="",
            encoding="utf-8",
        ) as handle:

            rows.extend(
                csv.DictReader(
                    handle
                )
            )

    # ---------------------------------------------------------
    # 2. Load all PRIOR incremental batches.
    #
    # Example:
    #
    # incremental/
    #   20261005_153749/
    #   20261006_090000/
    #
    # When generating the second batch, include the first.
    # Do not include the batch currently being generated or
    # any later batch.
    # ---------------------------------------------------------

    incremental_root = (
        base_root
        / "incremental"
    )

    if incremental_root.exists():

        batch_folders = sorted(
            folder
            for folder
            in incremental_root.iterdir()
            if folder.is_dir()
        )

        for batch_folder in batch_folders:

            if (
                current_batch_id
                and batch_folder.name
                >= current_batch_id
            ):
                continue

            domain_folder = (
                batch_folder
                / domain
            )

            if not domain_folder.exists():
                continue

            incremental_files = sorted(
                domain_folder.glob(
                    "*.csv"
                )
            )

            for file_path in incremental_files:

                with file_path.open(
                    mode="r",
                    newline="",
                    encoding="utf-8",
                ) as handle:

                    rows.extend(
                        csv.DictReader(
                            handle
                        )
                    )

    return rows

def get_fieldnames(
    base_root: Path,
    domain: str,
) -> list[str]:

    file_path = next(
        iter(
            sorted(
                (
                    base_root
                    / domain
                ).glob(
                    "*.csv"
                )
            )
        ),
        None,
    )

    if not file_path:

        raise FileNotFoundError(
            f"No CSV found for "
            f"{domain}"
        )

    with file_path.open(
        mode="r",
        newline="",
        encoding="utf-8",
    ) as handle:

        reader = csv.reader(
            handle
        )

        return next(
            reader
        )


def write_incremental_rows(
    batch_root: Path,
    domain: str,
    rows: list[dict],
    fieldnames: list[str],
    batch_id: str,
) -> Path:

    domain_folder = (
        batch_root
        / domain
    )

    domain_folder.mkdir(
        parents=True,
        exist_ok=True,
    )

    output_file = (
        domain_folder
        / (
            f"{domain}_incremental_"
            f"{batch_id}.csv"
        )
    )

    with output_file.open(
        mode="w",
        newline="",
        encoding="utf-8",
    ) as handle:

        writer = csv.DictWriter(
            handle,
            fieldnames=fieldnames,
        )

        writer.writeheader()

        writer.writerows(
            rows
        )

    return output_file


# ============================================================
# General helpers
# ============================================================

def sample_rows(
    rows: list[dict],
    count: int,
    rng: random.Random,
) -> list[dict]:

    if len(rows) < count:

        raise RuntimeError(
            f"Requested {count} rows "
            f"but only {len(rows)} exist."
        )

    return [
        deepcopy(row)
        for row in rng.sample(
            rows,
            count,
        )
    ]


def latest_rows_by_key(
    rows: list[dict],
    key_column: str,
) -> list[dict]:

    latest = {}

    for row in rows:

        key_value = row.get(
            key_column,
            "",
        )

        if not key_value:
            continue

        previous = latest.get(
            key_value
        )

        if previous is None:

            latest[
                key_value
            ] = row

            continue

        current_update_ts = (
            row.get(
                "update_ts",
                "",
            )
        )

        previous_update_ts = (
            previous.get(
                "update_ts",
                "",
            )
        )

        if (
            current_update_ts
            >= previous_update_ts
        ):

            latest[
                key_value
            ] = row

    return list(
        latest.values()
    )

def toggle_flag(
    value: str,
) -> str:

    if value == "Y":
        return "N"

    return "Y"


def add_money(
    value: str,
    amount: str,
) -> str:

    try:

        result = (
            Decimal(value or "0")
            + Decimal(amount)
        )

        return f"{result:.2f}"

    except InvalidOperation:

        return value


def stamp_update(
    row: dict,
    batch_timestamp: str,
) -> None:

    if "update_ts" in row:

        row["update_ts"] = (
            batch_timestamp
        )


def next_id_factory(
    rows: list[dict],
    key_column: str,
):

    pattern = re.compile(
        r"^(.*?)(\d+)$"
    )

    prefix = None
    width = None
    maximum = 0

    for row in rows:

        value = row.get(
            key_column,
            "",
        )

        match = pattern.match(
            value
        )

        if not match:
            continue

        current_prefix = (
            match.group(1)
        )

        number_text = (
            match.group(2)
        )

        number_value = int(
            number_text
        )

        if prefix is None:

            prefix = (
                current_prefix
            )

            width = len(
                number_text
            )

        maximum = max(
            maximum,
            number_value,
        )

    if prefix is None:

        raise RuntimeError(
            f"Unable to determine ID "
            f"format for {key_column}."
        )

    counter = maximum

    def next_id():

        nonlocal counter

        counter += 1

        return (
            f"{prefix}"
            f"{counter:0{width}d}"
        )

    return next_id


# ============================================================
# Dimension-like incremental updates
# ============================================================

def build_dimension_updates(
    data: dict,
    rng: random.Random,
    batch_id: str,
    batch_timestamp: str,
):

    updates = {}

    short_batch = (
        batch_id[-6:]
    )

    # --------------------------------------------------------
    # PRODUCT
    # Same product_id, changed descriptive attribute.
    # --------------------------------------------------------

    rows = sample_rows(
        data["product"],
        INCREMENTAL_COUNTS[
            "product"
        ],
        rng,
    )

    for row in rows:

        row["product_name"] = (
            f"{row['product_name']} "
            f"REV-{short_batch}"
        )

        stamp_update(
            row,
            batch_timestamp,
        )

    updates["product"] = rows

    # --------------------------------------------------------
    # BENEFIT PLAN
    # Same plan ID, small copay change.
    # --------------------------------------------------------

    rows = sample_rows(
        data["benefit_plan"],
        INCREMENTAL_COUNTS[
            "benefit_plan"
        ],
        rng,
    )

    for row in rows:

        row["pcp_copay"] = (
            add_money(
                row[
                    "pcp_copay"
                ],
                "5.00",
            )
        )

        stamp_update(
            row,
            batch_timestamp,
        )

    updates[
        "benefit_plan"
    ] = rows

    # --------------------------------------------------------
    # GROUP
    # --------------------------------------------------------

    rows = sample_rows(
        data["group"],
        INCREMENTAL_COUNTS[
            "group"
        ],
        rng,
    )

    for row in rows:

        row["group_name"] = (
            f"{row['group_name']} "
            f"REV-{short_batch}"
        )

        stamp_update(
            row,
            batch_timestamp,
        )

    updates["group"] = rows

    # --------------------------------------------------------
    # SUBGROUP
    # --------------------------------------------------------

    rows = sample_rows(
        data["subgroup"],
        INCREMENTAL_COUNTS[
            "subgroup"
        ],
        rng,
    )

    for row in rows:

        row["subgroup_name"] = (
            f"{row['subgroup_name']} "
            f"REV-{short_batch}"
        )

        stamp_update(
            row,
            batch_timestamp,
        )

    updates["subgroup"] = rows

    # --------------------------------------------------------
    # MEMBER
    #
    # Simulate contact-information updates.
    # --------------------------------------------------------

    rows = sample_rows(
        data["member"],
        INCREMENTAL_COUNTS[
            "member"
        ],
        rng,
    )

    for index, row in enumerate(
        rows,
        start=1,
    ):

        row["phone_number"] = (
            f"716555"
            f"{index + 1000:04d}"
        )

        stamp_update(
            row,
            batch_timestamp,
        )

    updates["member"] = rows

    # --------------------------------------------------------
    # PRACTITIONER
    #
    # Toggle board-certification indicator.
    # --------------------------------------------------------

    rows = sample_rows(
        data["practitioner"],
        INCREMENTAL_COUNTS[
            "practitioner"
        ],
        rng,
    )

    for row in rows:

        row[
            "board_certified_flag"
        ] = toggle_flag(
            row[
                "board_certified_flag"
            ]
        )

        stamp_update(
            row,
            batch_timestamp,
        )

    updates[
        "practitioner"
    ] = rows

    # --------------------------------------------------------
    # SUPPLIER
    # --------------------------------------------------------

    rows = sample_rows(
        data["supplier"],
        INCREMENTAL_COUNTS[
            "supplier"
        ],
        rng,
    )

    for row in rows:

        row["supplier_name"] = (
            f"{row['supplier_name']} "
            f"REV-{short_batch}"
        )

        stamp_update(
            row,
            batch_timestamp,
        )

    updates["supplier"] = rows

    # --------------------------------------------------------
    # SUPPLIER LOCATION
    # --------------------------------------------------------

    rows = sample_rows(
        data[
            "supplier_location"
        ],
        INCREMENTAL_COUNTS[
            "supplier_location"
        ],
        rng,
    )

    for row in rows:

        row["location_name"] = (
            f"{row['location_name']} "
            f"REV-{short_batch}"
        )

        stamp_update(
            row,
            batch_timestamp,
        )

    updates[
        "supplier_location"
    ] = rows

    # --------------------------------------------------------
    # PRACTITIONER ROLE
    #
    # Safe operational attribute change.
    # --------------------------------------------------------

    rows = sample_rows(
        data[
            "practitioner_role"
        ],
        INCREMENTAL_COUNTS[
            "practitioner_role"
        ],
        rng,
    )

    for row in rows:

        row[
            "accepting_new_patients_flag"
        ] = toggle_flag(
            row[
                "accepting_new_patients_flag"
            ]
        )

        stamp_update(
            row,
            batch_timestamp,
        )

    updates[
        "practitioner_role"
    ] = rows

    # --------------------------------------------------------
    # ADDRESS
    #
    # Update Address Line 2.
    # --------------------------------------------------------

    rows = sample_rows(
        data["address"],
        INCREMENTAL_COUNTS[
            "address"
        ],
        rng,
    )

    for row in rows:

        row["address_line_2"] = (
            f"INC-{short_batch}"
        )

        stamp_update(
            row,
            batch_timestamp,
        )

    updates["address"] = rows

    # --------------------------------------------------------
    # ENTITY ADDRESS
    #
    # For first incremental batch avoid changing critical
    # RESIDENTIAL, PRACTICE or SERVICE_LOCATION links.
    #
    # Change a mailing/correspondence/billing relationship
    # to another valid Address ID.
    # --------------------------------------------------------

    candidates = [
        row
        for row in data[
            "entity_address"
        ]
        if row[
            "address_type"
        ]
        not in {
            "RESIDENTIAL",
            "PRACTICE",
            "SERVICE_LOCATION",
        }
    ]

    rows = sample_rows(
        candidates,
        INCREMENTAL_COUNTS[
            "entity_address"
        ],
        rng,
    )

    address_ids = [
        row["address_id"]
        for row in data[
            "address"
        ]
    ]

    for row in rows:

        original_address = (
            row[
                "address_id"
            ]
        )

        new_address = rng.choice(
            address_ids
        )

        while (
            new_address
            == original_address
        ):

            new_address = (
                rng.choice(
                    address_ids
                )
            )

        row["address_id"] = (
            new_address
        )

        stamp_update(
            row,
            batch_timestamp,
        )

    updates[
        "entity_address"
    ] = rows

    return updates


# ============================================================
# Eligibility incremental events
# ============================================================

def build_incremental_eligibility(
    eligibility_rows: list[dict],
    rng: random.Random,
    batch_id: str,
    batch_timestamp: str,
) -> list[dict]:

    # ---------------------------------------------------------
    # Generate IDs after considering base + all prior
    # incremental Eligibility rows.
    # ---------------------------------------------------------

    next_eligibility_id = (
        next_id_factory(
            eligibility_rows,
            "eligibility_id",
        )
    )

    # ---------------------------------------------------------
    # Determine the latest Eligibility version per Member.
    #
    # Do NOT depend only on current_record_flag because the
    # append-only source can contain more than one historical
    # record where current_record_flag = Y.
    # ---------------------------------------------------------

    latest_by_member = {}

    for row in eligibility_rows:

        member_id = row[
            "member_id"
        ]

        version = int(
            row.get(
                "record_version",
                "0",
            )
            or "0"
        )

        previous = (
            latest_by_member.get(
                member_id
            )
        )

        if previous is None:

            latest_by_member[
                member_id
            ] = row

            continue

        previous_version = int(
            previous.get(
                "record_version",
                "0",
            )
            or "0"
        )

        if (
            version
            > previous_version
        ):

            latest_by_member[
                member_id
            ] = row

        elif (
            version
            == previous_version
            and row.get(
                "update_ts",
                "",
            )
            > previous.get(
                "update_ts",
                "",
            )
        ):

            latest_by_member[
                member_id
            ] = row

    # ---------------------------------------------------------
    # Select active Eligibility records that are claimable
    # through DATA_END_DATE.
    # ---------------------------------------------------------

    candidates = []

    for row in latest_by_member.values():

        if (
            row[
                "eligibility_status"
            ]
            != "ACTIVE"
        ):
            continue

        if (
            row[
                "future_enrollment_flag"
            ]
            == "Y"
        ):
            continue

        coverage_start = (
            parse_date(
                row[
                    "coverage_start_date"
                ]
            )
        )

        coverage_end = (
            parse_date(
                row[
                    "coverage_end_date"
                ]
            )
        )

        if (
            coverage_start
            and coverage_start
            <= DATA_END_DATE
            and (
                coverage_end is None
                or coverage_end
                >= DATA_END_DATE
            )
        ):

            candidates.append(
                row
            )

    required_count = (
        INCREMENTAL_COUNTS[
            "eligibility"
        ]
    )

    if (
        len(candidates)
        < required_count
    ):

        raise RuntimeError(
            "Not enough active latest "
            "Eligibility rows to build "
            "the incremental batch."
        )

    selected = rng.sample(
        candidates,
        required_count,
    )

    new_rows = []

    event_types = [
        "DEMOGRAPHIC_CHANGE",
        "ADDRESS_CHANGE",
    ]

    for index, original in enumerate(
        selected,
        start=1,
    ):

        row = deepcopy(
            original
        )

        row[
            "eligibility_id"
        ] = next_eligibility_id()

        row[
            "record_version"
        ] = str(
            int(
                original[
                    "record_version"
                ]
            )
            + 1
        )

        # Source says this new event is current.
        # Silver later derives true current status
        # from the latest record_version.
        row[
            "current_record_flag"
        ] = "Y"

        row[
            "event_type"
        ] = rng.choice(
            event_types
        )

        row[
            "event_effective_date"
        ] = (
            DATA_END_DATE
            .isoformat()
        )

        row[
            "transaction_date"
        ] = (
            DATA_END_DATE
            .isoformat()
        )

        row[
            "termination_reason"
        ] = ""

        row[
            "retroactive_flag"
        ] = "N"

        row[
            "future_enrollment_flag"
        ] = "N"

        row[
            "reinstatement_flag"
        ] = "N"

        row[
            "source_eligibility_key"
        ] = (
            f"INCELIG_"
            f"{batch_id}_"
            f"{index:06d}"
        )

        row[
            "create_ts"
        ] = batch_timestamp

        row[
            "update_ts"
        ] = batch_timestamp

        new_rows.append(
            row
        )

    return new_rows

# ============================================================
# Incremental Claims
#
# 100 new headers
# exactly 3 lines each = 300 claim lines
# ============================================================

def build_incremental_claims(
    data: dict,
    rng: random.Random,
    batch_id: str,
    batch_timestamp: str,
):

    total_header_count = (
        INCREMENTAL_COUNTS[
            "claim_header"
        ]
    )

    total_line_count = (
        INCREMENTAL_COUNTS[
            "claim_line"
        ]
    )

    # ---------------------------------------------------------
    # Our incremental testing pattern:
    #
    # 70 brand-new claims
    # 30 updates to existing claims
    #
    # Every claim has exactly 3 lines.
    # ---------------------------------------------------------

    update_header_count = 30

    new_header_count = (
        total_header_count
        - update_header_count
    )

    if (
        total_line_count
        != total_header_count * 3
    ):

        raise RuntimeError(
            "Incremental Claims expect exactly "
            "3 Claim Lines per Claim Header."
        )

    # ---------------------------------------------------------
    # Resolve the latest version of every Claim Header and
    # Claim Line from base + prior incremental batches.
    # ---------------------------------------------------------

    latest_headers = (
        latest_rows_by_key(
            data[
                "claim_header"
            ],
            "claim_id",
        )
    )

    latest_lines = (
        latest_rows_by_key(
            data[
                "claim_line"
            ],
            "claim_line_id",
        )
    )

    lines_by_claim = {}

    for line in latest_lines:

        lines_by_claim.setdefault(
            line[
                "claim_id"
            ],
            [],
        ).append(
            line
        )

    # ---------------------------------------------------------
    # Only use claims having exactly three current lines.
    #
    # This keeps Batch 002 simple and makes Header/Line
    # reconciliation easy to validate.
    # ---------------------------------------------------------

    three_line_headers = []

    for header in latest_headers:

        claim_lines = (
            lines_by_claim.get(
                header[
                    "claim_id"
                ],
                [],
            )
        )

        if len(
            claim_lines
        ) == 3:

            three_line_headers.append(
                header
            )

    if (
        len(three_line_headers)
        < total_header_count
    ):

        raise RuntimeError(
            "Not enough 3-line Claims exist "
            "to build the incremental batch."
        )

    # ---------------------------------------------------------
    # Update candidates:
    #
    # Avoid fully denied claims because we want the update
    # to produce a meaningful adjudication change.
    # ---------------------------------------------------------

    update_candidates = []

    for header in three_line_headers:

        if (
            header[
                "claim_status"
            ]
            == "DENIED"
        ):
            continue

        claim_lines = (
            lines_by_claim[
                header[
                    "claim_id"
                ]
            ]
        )

        has_payable_line = any(
            Decimal(
                line.get(
                    "allowed_amount",
                    "0",
                )
                or "0"
            )
            > Decimal("0")
            for line in claim_lines
        )

        if has_payable_line:

            update_candidates.append(
                header
            )

    if (
        len(update_candidates)
        < update_header_count
    ):

        raise RuntimeError(
            "Not enough payable Claims "
            "exist for SCD2 updates."
        )

    # ---------------------------------------------------------
    # Select 30 Claims that will be UPDATED.
    # ---------------------------------------------------------

    update_headers = rng.sample(
        update_candidates,
        update_header_count,
    )

    update_claim_ids = {
        header[
            "claim_id"
        ]
        for header in update_headers
    }

    # ---------------------------------------------------------
    # Select 70 different Claims that will be used as
    # templates for BRAND-NEW claims.
    # ---------------------------------------------------------

    new_candidates = [
        header
        for header in three_line_headers
        if header[
            "claim_id"
        ]
        not in update_claim_ids
    ]

    if (
        len(new_candidates)
        < new_header_count
    ):

        raise RuntimeError(
            "Not enough Claim templates "
            "exist for new incremental Claims."
        )

    new_templates = rng.sample(
        new_candidates,
        new_header_count,
    )

    # ---------------------------------------------------------
    # New ID generators consider base + previous batches,
    # preventing ID collisions with Batch 001.
    # ---------------------------------------------------------

    next_claim_id = (
        next_id_factory(
            data[
                "claim_header"
            ],
            "claim_id",
        )
    )

    next_claim_line_id = (
        next_id_factory(
            data[
                "claim_line"
            ],
            "claim_line_id",
        )
    )

    header_rows = []
    line_rows = []

    # =========================================================
    # PART A
    # Generate 70 NEW Claims.
    #
    # We clone already-valid claim structures but assign new
    # Claim / Claim Line IDs and new source keys.
    # =========================================================

    for claim_index, template_header in enumerate(
        new_templates,
        start=1,
    ):

        old_claim_id = (
            template_header[
                "claim_id"
            ]
        )

        new_claim_id = (
            next_claim_id()
        )

        template_lines = sorted(
            lines_by_claim[
                old_claim_id
            ],
            key=lambda row: int(
                row[
                    "line_number"
                ]
            ),
        )

        new_header = deepcopy(
            template_header
        )

        new_header[
            "claim_id"
        ] = new_claim_id

        new_header[
            "source_claim_key"
        ] = (
            f"INCCLM_"
            f"{batch_id}_"
            f"NEW_"
            f"{claim_index:06d}"
        )

        new_header[
            "create_ts"
        ] = batch_timestamp

        new_header[
            "update_ts"
        ] = batch_timestamp

        new_header[
            "claim_line_count"
        ] = "3"

        header_rows.append(
            new_header
        )

        for line_number, template_line in enumerate(
            template_lines,
            start=1,
        ):

            new_line = deepcopy(
                template_line
            )

            new_line[
                "claim_line_id"
            ] = next_claim_line_id()

            new_line[
                "claim_id"
            ] = new_claim_id

            new_line[
                "line_number"
            ] = str(
                line_number
            )

            new_line[
                "source_claim_line_key"
            ] = (
                f"INCCLML_"
                f"{batch_id}_"
                f"NEW_"
                f"{claim_index:06d}_"
                f"{line_number}"
            )

            new_line[
                "create_ts"
            ] = batch_timestamp

            new_line[
                "update_ts"
            ] = batch_timestamp

            line_rows.append(
                new_line
            )

    # =========================================================
    # PART B
    # Generate 30 UPDATES to existing Claims.
    #
    # Keep the same:
    #
    # claim_id
    # claim_line_id
    #
    # but change adjudication amounts/status and update_ts.
    #
    # This is what lets Silver SCD Type 2 preserve old and
    # current Claim versions.
    # =========================================================

    for update_index, original_header in enumerate(
        update_headers,
        start=1,
    ):

        claim_id = (
            original_header[
                "claim_id"
            ]
        )

        original_lines = sorted(
            lines_by_claim[
                claim_id
            ],
            key=lambda row: int(
                row[
                    "line_number"
                ]
            ),
        )

        updated_lines = []

        total_billed = 0
        total_allowed = 0
        total_paid = 0
        total_member = 0

        line_statuses = []

        for original_line in original_lines:

            line = deepcopy(
                original_line
            )

            billed_cents = int(
                (
                    Decimal(
                        line[
                            "billed_amount"
                        ]
                    )
                    * 100
                )
            )

            allowed_cents = int(
                (
                    Decimal(
                        line[
                            "allowed_amount"
                        ]
                    )
                    * 100
                )
            )

            member_cents = int(
                (
                    Decimal(
                        line[
                            "member_responsibility_amount"
                        ]
                    )
                    * 100
                )
            )

            # -------------------------------------------------
            # Adjust payable lines by reducing the allowed
            # amount 5-15%.
            #
            # This represents a later claim adjudication.
            # -------------------------------------------------

            if allowed_cents > 0:

                reduction_pct = (
                    rng.randint(
                        5,
                        15,
                    )
                )

                reduction_cents = max(
                    1,
                    round(
                        allowed_cents
                        * reduction_pct
                        / 100
                    ),
                )

                adjusted_allowed = max(
                    0,
                    allowed_cents
                    - reduction_cents,
                )

                adjusted_member = min(
                    member_cents,
                    adjusted_allowed,
                )

                adjusted_paid = (
                    adjusted_allowed
                    - adjusted_member
                )

                line_status = (
                    "ADJUSTED"
                )

            else:

                adjusted_allowed = 0
                adjusted_paid = 0
                adjusted_member = 0

                line_status = (
                    "DENIED"
                )

            line[
                "billed_amount"
            ] = money_string(
                billed_cents
            )

            line[
                "allowed_amount"
            ] = money_string(
                adjusted_allowed
            )

            line[
                "paid_amount"
            ] = money_string(
                adjusted_paid
            )

            line[
                "member_responsibility_amount"
            ] = money_string(
                adjusted_member
            )

            line[
                "line_status"
            ] = line_status

            # Keep original create_ts.
            # Only update the source change timestamp.
            line[
                "update_ts"
            ] = batch_timestamp

            total_billed += (
                billed_cents
            )

            total_allowed += (
                adjusted_allowed
            )

            total_paid += (
                adjusted_paid
            )

            total_member += (
                adjusted_member
            )

            line_statuses.append(
                line_status
            )

            updated_lines.append(
                line
            )

        # -----------------------------------------------------
        # Recalculate Claim Header from adjusted lines.
        # -----------------------------------------------------

        updated_header = deepcopy(
            original_header
        )

        updated_header[
            "claim_status"
        ] = determine_claim_status(
            line_statuses
        )

        updated_header[
            "claim_line_count"
        ] = str(
            len(
                updated_lines
            )
        )

        updated_header[
            "total_billed_amount"
        ] = money_string(
            total_billed
        )

        updated_header[
            "total_allowed_amount"
        ] = money_string(
            total_allowed
        )

        updated_header[
            "total_paid_amount"
        ] = money_string(
            total_paid
        )

        updated_header[
            "member_responsibility_amount"
        ] = money_string(
            total_member
        )

        # Keep original claim_id and create_ts.
        updated_header[
            "update_ts"
        ] = batch_timestamp

        # The adjustment is considered adjudicated by
        # DATA_END_DATE for our synthetic observation period.
        updated_header[
            "adjudication_date"
        ] = (
            DATA_END_DATE
            .isoformat()
        )

        header_rows.append(
            updated_header
        )

        line_rows.extend(
            updated_lines
        )

    # ---------------------------------------------------------
    # Final safety checks.
    # ---------------------------------------------------------

    if (
        len(header_rows)
        != total_header_count
    ):

        raise RuntimeError(
            "Incremental Claim Header "
            "count is incorrect."
        )

    if (
        len(line_rows)
        != total_line_count
    ):

        raise RuntimeError(
            "Incremental Claim Line "
            "count is incorrect."
        )

    print()
    print(
        f"Claim inserts : "
        f"{new_header_count:,}"
    )

    print(
        f"Claim updates : "
        f"{update_header_count:,}"
    )

    print(
        f"New lines     : "
        f"{new_header_count * 3:,}"
    )

    print(
        f"Updated lines : "
        f"{update_header_count * 3:,}"
    )

    return (
        header_rows,
        line_rows,
    )
# ============================================================
# Batch manifest
# ============================================================

def write_manifest(
    batch_root: Path,
    manifest_rows: list[dict],
):

    output_file = (
        batch_root
        / "batch_manifest.csv"
    )

    with output_file.open(
        mode="w",
        newline="",
        encoding="utf-8",
    ) as handle:

        writer = csv.DictWriter(
            handle,
            fieldnames=[
                "domain",
                "row_count",
                "change_type",
                "file_name",
            ],
        )

        writer.writeheader()

        writer.writerows(
            manifest_rows
        )


# ============================================================
# Main
# ============================================================

def main():

    parser = argparse.ArgumentParser(
        description=(
            "Generate a small incremental "
            "healthcare payer source batch."
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
            "Optional batch ID in "
            "YYYYMMDD_HHMMSS format."
        ),
    )

    args = parser.parse_args()

    now = datetime.now()

    batch_id = (
        args.batch_id
        or now.strftime(
            "%Y%m%d_%H%M%S"
        )
    )

    try:

        batch_datetime = (
            datetime.strptime(
                batch_id,
                "%Y%m%d_%H%M%S",
            )
        )

    except ValueError as exc:

        raise ValueError(
            "--batch-id must use "
            "YYYYMMDD_HHMMSS format."
        ) from exc

    batch_timestamp = (
        batch_datetime
        .isoformat(
            timespec="seconds"
        )
    )

    rng = random.Random(
        RANDOM_SEED
        + sum(
            ord(character)
            for character
            in batch_id
        )
    )

    base_root = (
        PROJECT_ROOT
        / "generated_data"
        / args.scale
    )

    batch_root = (
        base_root
        / "incremental"
        / batch_id
    )

    batch_root.mkdir(
        parents=True,
        exist_ok=False,
    )

    print()
    print("=" * 80)
    print(
        "INCREMENTAL HEALTHCARE "
        "PAYER DATA GENERATION"
    )
    print("=" * 80)

    print(
        f"Scale    : {args.scale}"
    )

    print(
        f"Batch ID : {batch_id}"
    )

    print(
        f"Output   : {batch_root}"
    )

    print("=" * 80)

    # --------------------------------------------------------
    # Load all existing base data.
    # --------------------------------------------------------

    data = {}

    fieldnames = {}

    for domain in DOMAINS:

        data[domain] = (
        load_domain_rows(
        base_root,
        domain,
        current_batch_id=(
            batch_id
                ),
            )
        )

        fieldnames[domain] = (
            get_fieldnames(
                base_root,
                domain,
            )
        )

        # --------------------------------------------------------
    # For dimension-like domains, generate the next update
    # from the latest known version of each business key.
    # --------------------------------------------------------

    dimension_keys = {
        "member": "member_id",
        "product": "product_id",
        "benefit_plan": "benefit_plan_id",
        "group": "group_id",
        "subgroup": "subgroup_id",
        "practitioner": "practitioner_id",
        "supplier": "supplier_id",
        "supplier_location": (
            "supplier_location_id"
        ),
        "practitioner_role": (
            "practitioner_role_id"
        ),
        "address": "address_id",
        "entity_address": (
            "entity_address_id"
        ),
    }

    for (
        domain,
        key_column,
    ) in dimension_keys.items():

        data[domain] = (
            latest_rows_by_key(
                data[
                    domain
                ],
                key_column,
            )
        )

    # --------------------------------------------------------
    # Dimension updates
    # --------------------------------------------------------

    output = (
        build_dimension_updates(
            data=data,
            rng=rng,
            batch_id=batch_id,
            batch_timestamp=(
                batch_timestamp
            ),
        )
    )

    # --------------------------------------------------------
    # Eligibility events
    # --------------------------------------------------------

    incremental_eligibility = (
        build_incremental_eligibility(
            eligibility_rows=(
                data[
                    "eligibility"
                ]
            ),
            rng=rng,
            batch_id=batch_id,
            batch_timestamp=(
                batch_timestamp
            ),
        )
    )

    output[
        "eligibility"
    ] = incremental_eligibility

    # --------------------------------------------------------
    # Claims
    # --------------------------------------------------------

    (
        claim_headers,
        claim_lines,
    ) = build_incremental_claims(
        data=data,
        rng=rng,
        batch_id=batch_id,
        batch_timestamp=(
            batch_timestamp
        ),
    )

    output[
        "claim_header"
    ] = claim_headers

    output[
        "claim_line"
    ] = claim_lines

    # --------------------------------------------------------
    # Write all 14 source files
    # --------------------------------------------------------

    manifest_rows = []

    dimension_domains = {
        "member",
        "product",
        "benefit_plan",
        "group",
        "subgroup",
        "practitioner",
        "supplier",
        "supplier_location",
        "practitioner_role",
        "address",
        "entity_address",
    }

    for domain in DOMAINS:

        rows = output[
            domain
        ]

        output_file = (
            write_incremental_rows(
                batch_root=(
                    batch_root
                ),
                domain=domain,
                rows=rows,
                fieldnames=(
                    fieldnames[
                        domain
                    ]
                ),
                batch_id=batch_id,
            )
        )

        if domain in (
            dimension_domains
        ):

            change_type = (
                "UPDATE_EXISTING"
            )

        elif domain in {
            "claim_header",
            "claim_line",
        }:

            change_type = (
                "MIXED_INSERT_UPDATE"
            )

        else:

            change_type = (
                "INSERT_NEW"
            )

        manifest_rows.append(
            {
                "domain": domain,
                "row_count": (
                    len(rows)
                ),
                "change_type": (
                    change_type
                ),
                "file_name": (
                    output_file.name
                ),
            }
        )

        print(
            f"{domain:25}"
            f"{len(rows):>8,} rows"
        )

    write_manifest(
        batch_root,
        manifest_rows,
    )

    print()
    print("=" * 80)
    print(
        "INCREMENTAL BATCH COMPLETED"
    )
    print("=" * 80)

    print(
        f"Batch folder: "
        f"{batch_root}"
    )

    print(
        "Manifest    : "
        "batch_manifest.csv"
    )

    print("=" * 80)
    print()


if __name__ == "__main__":
    main()