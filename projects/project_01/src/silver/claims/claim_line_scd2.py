from pyspark import pipelines as dp
from pyspark.sql import functions as F


# ---------------------------------------------------------
# Pipeline configuration
# ---------------------------------------------------------

CATALOG = spark.conf.get(
    "payer.catalog"
)

BRONZE_SCHEMA = spark.conf.get(
    "payer.bronze_schema"
)

CLAIM_LINE_BRONZE_TABLE = (
    f"{CATALOG}."
    f"{BRONZE_SCHEMA}."
    f"claim_line_raw"
)


# ---------------------------------------------------------
# Step 1:
# Read Bronze Claim Line and apply Silver typing / DQ.
# ---------------------------------------------------------

@dp.temporary_view(
    name="claim_line_changes"
)
@dp.expect_or_drop(
    "valid_claim_line_id",
    "claim_line_id IS NOT NULL "
    "AND TRIM(claim_line_id) <> ''",
)
@dp.expect_or_drop(
    "valid_claim_id",
    "claim_id IS NOT NULL "
    "AND TRIM(claim_id) <> ''",
)
@dp.expect_or_drop(
    "valid_line_number",
    "line_number IS NOT NULL "
    "AND line_number > 0",
)
@dp.expect_or_drop(
    "valid_service_date",
    "service_date IS NOT NULL",
)
@dp.expect_or_drop(
    "valid_units",
    "units IS NOT NULL "
    "AND units > 0",
)
@dp.expect_or_drop(
    "valid_update_timestamp",
    "update_ts IS NOT NULL",
)
@dp.expect_or_drop(
    "valid_financial_order",
    "billed_amount >= allowed_amount "
    "AND allowed_amount >= paid_amount "
    "AND paid_amount >= 0 "
    "AND member_responsibility_amount >= 0",
)
@dp.expect_or_drop(
    "valid_financial_reconciliation",
    "allowed_amount = "
    "paid_amount + "
    "member_responsibility_amount",
)
@dp.expect_or_drop(
    "no_rescued_data",
    "_rescued_data IS NULL",
)
def claim_line_changes():

    return (
        spark.readStream
        .table(
            CLAIM_LINE_BRONZE_TABLE
        )
        .select(
            F.col("claim_line_id"),
            F.col("claim_id"),

            F.col(
                "line_number"
            ).cast(
                "int"
            ).alias(
                "line_number"
            ),

            F.to_date(
                "service_date"
            ).alias(
                "service_date"
            ),

            F.col("service_category"),
            F.col("procedure_code"),
            F.col("revenue_code"),

            F.col("diagnosis_code"),
            F.col("diagnosis_category"),

            F.col(
                "units"
            ).cast(
                "int"
            ).alias(
                "units"
            ),

            F.col("line_status"),

            F.col(
                "billed_amount"
            ).cast(
                "decimal(18,2)"
            ).alias(
                "billed_amount"
            ),

            F.col(
                "allowed_amount"
            ).cast(
                "decimal(18,2)"
            ).alias(
                "allowed_amount"
            ),

            F.col(
                "paid_amount"
            ).cast(
                "decimal(18,2)"
            ).alias(
                "paid_amount"
            ),

            F.col(
                "member_responsibility_amount"
            ).cast(
                "decimal(18,2)"
            ).alias(
                "member_responsibility_amount"
            ),

            F.col(
                "source_claim_line_key"
            ),

            F.to_timestamp(
                "create_ts"
            ).alias(
                "create_ts"
            ),

            F.to_timestamp(
                "update_ts"
            ).alias(
                "update_ts"
            ),

            F.col("_source_file"),

            F.col(
                "_source_file_modification_time"
            ),

            F.col("_ingest_timestamp"),

            F.col("_load_date"),

            F.col("_rescued_data"),
        )
    )


# ---------------------------------------------------------
# Step 2:
# Silver Claim Line SCD Type 2 target.
# ---------------------------------------------------------

dp.create_streaming_table(
    name="claim_line",
    comment=(
        "Silver Claim Line with SCD Type 2 "
        "history for line-level adjudication changes."
    ),
    table_properties={
        "quality": "silver",
        "history_type": "scd2",
        "source_system": "payer_01",
    },
)


# ---------------------------------------------------------
# Step 3:
# Same claim_line_id arriving again with changed
# business attributes creates another SCD2 version.
# ---------------------------------------------------------

dp.create_auto_cdc_flow(
    target="claim_line",
    source="claim_line_changes",
    keys=[
        "claim_line_id"
    ],
    sequence_by=F.col(
        "update_ts"
    ),
    stored_as_scd_type="2",

    except_column_list=[
        "_rescued_data"
    ],

    track_history_except_column_list=[
        "create_ts",
        "update_ts",
        "_source_file",
        "_source_file_modification_time",
        "_ingest_timestamp",
        "_load_date",
    ],
)