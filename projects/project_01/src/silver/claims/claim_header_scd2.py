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

CLAIM_HEADER_BRONZE_TABLE = (
    f"{CATALOG}."
    f"{BRONZE_SCHEMA}."
    f"claim_header_raw"
)


# ---------------------------------------------------------
# Step 1:
# Read Bronze Claim Header and apply Silver typing / DQ.
# ---------------------------------------------------------

@dp.temporary_view(
    name="claim_header_changes"
)
@dp.expect_or_drop(
    "valid_claim_id",
    "claim_id IS NOT NULL "
    "AND TRIM(claim_id) <> ''",
)
@dp.expect_or_drop(
    "valid_member_id",
    "member_id IS NOT NULL "
    "AND TRIM(member_id) <> ''",
)
@dp.expect_or_drop(
    "valid_update_timestamp",
    "update_ts IS NOT NULL",
)
@dp.expect_or_drop(
    "valid_service_dates",
    "service_from_date IS NOT NULL "
    "AND service_to_date IS NOT NULL "
    "AND service_to_date >= service_from_date",
)
@dp.expect_or_drop(
    "valid_claim_line_count",
    "claim_line_count IS NOT NULL "
    "AND claim_line_count > 0",
)
@dp.expect_or_drop(
    "valid_financial_order",
    "total_billed_amount >= total_allowed_amount "
    "AND total_allowed_amount >= total_paid_amount "
    "AND total_paid_amount >= 0 "
    "AND member_responsibility_amount >= 0",
)
@dp.expect_or_drop(
    "valid_financial_reconciliation",
    "total_allowed_amount = "
    "total_paid_amount + "
    "member_responsibility_amount",
)
@dp.expect_or_drop(
    "no_rescued_data",
    "_rescued_data IS NULL",
)
def claim_header_changes():

    return (
        spark.readStream
        .table(
            CLAIM_HEADER_BRONZE_TABLE
        )
        .select(
            F.col("claim_id"),
            F.col("member_id"),
            F.col("eligibility_id"),

            F.col(
                "eligibility_record_version"
            ).cast(
                "int"
            ).alias(
                "eligibility_record_version"
            ),

            F.col("subscriber_id"),
            F.col("family_id"),
            F.col("group_id"),
            F.col("subgroup_id"),
            F.col("product_id"),
            F.col("benefit_plan_id"),

            F.col("line_of_business"),
            F.col("product_type"),
            F.col("network_id"),

            F.col("practitioner_role_id"),
            F.col("practitioner_id"),
            F.col("supplier_id"),
            F.col("supplier_location_id"),

            F.col("claim_type"),

            F.to_date(
                "service_from_date"
            ).alias(
                "service_from_date"
            ),

            F.to_date(
                "service_to_date"
            ).alias(
                "service_to_date"
            ),

            F.to_date(
                "admission_date"
            ).alias(
                "admission_date"
            ),

            F.to_date(
                "discharge_date"
            ).alias(
                "discharge_date"
            ),

            F.to_date(
                "received_date"
            ).alias(
                "received_date"
            ),

            F.to_date(
                "adjudication_date"
            ).alias(
                "adjudication_date"
            ),

            F.col("claim_status"),
            F.col("network_status"),
            F.col("network_tier"),
            F.col("place_of_service_code"),

            F.col("primary_diagnosis_code"),
            F.col("primary_diagnosis_category"),

            F.col(
                "claim_line_count"
            ).cast(
                "int"
            ).alias(
                "claim_line_count"
            ),

            F.col(
                "total_billed_amount"
            ).cast(
                "decimal(18,2)"
            ).alias(
                "total_billed_amount"
            ),

            F.col(
                "total_allowed_amount"
            ).cast(
                "decimal(18,2)"
            ).alias(
                "total_allowed_amount"
            ),

            F.col(
                "total_paid_amount"
            ).cast(
                "decimal(18,2)"
            ).alias(
                "total_paid_amount"
            ),

            F.col(
                "member_responsibility_amount"
            ).cast(
                "decimal(18,2)"
            ).alias(
                "member_responsibility_amount"
            ),

            F.col("source_claim_key"),

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
# Silver Claim Header SCD Type 2 target.
# ---------------------------------------------------------

dp.create_streaming_table(
    name="claim_header",
    comment=(
        "Silver Claim Header with SCD Type 2 "
        "history for claim adjudication changes."
    ),
    table_properties={
        "quality": "silver",
        "history_type": "scd2",
        "source_system": "payer_01",
    },
)


# ---------------------------------------------------------
# Step 3:
# Apply AUTO CDC.
#
# Same claim_id arriving again with changed business
# attributes creates a new SCD2 version.
# ---------------------------------------------------------

dp.create_auto_cdc_flow(
    target="claim_header",
    source="claim_header_changes",
    keys=[
        "claim_id"
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