from pyspark import pipelines as dp
from pyspark.sql import functions as F


# ---------------------------------------------------------
# Pipeline configuration
# ---------------------------------------------------------

CATALOG = spark.conf.get(
    "payer.catalog",
    "payer_01_dev",
)

BRONZE_SCHEMA = spark.conf.get(
    "payer.bronze_schema",
    "bronze",
)

MEMBER_BRONZE_TABLE = (
    f"{CATALOG}."
    f"{BRONZE_SCHEMA}."
    f"member_raw"
)


# ---------------------------------------------------------
# Step 1:
# Read Bronze incrementally and convert raw STRING columns
# into proper Silver data types.
#
# This is a temporary pipeline view, not a published table.
# ---------------------------------------------------------

@dp.temporary_view(
    name="member_changes"
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
    "no_rescued_data",
    "_rescued_data IS NULL",
)
def member_changes():

    return (
        spark.readStream
        .table(
            MEMBER_BRONZE_TABLE
        )
        .select(
            F.col("member_id"),
            F.col("family_id"),
            F.col("subscriber_id"),
            F.col(
                "relationship_to_subscriber"
            ),

            F.col("first_name"),
            F.col("middle_initial"),
            F.col("last_name"),

            F.to_date(
                "date_of_birth"
            ).alias(
                "date_of_birth"
            ),

            F.col("gender"),
            F.col("marital_status"),
            F.col("preferred_language"),
            F.col("phone_number"),
            F.col("email_address"),
            F.col("member_status"),
            F.col("deceased_flag"),

            F.to_date(
                "death_date"
            ).alias(
                "death_date"
            ),

            F.col(
                "source_member_key"
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

            # Keep selected Bronze lineage
            # information in Silver.
            F.col(
                "_source_file"
            ),

            F.col(
                "_source_file_modification_time"
            ),

            F.col(
                "_ingest_timestamp"
            ),

            F.col(
            "_load_date"
        ),

        F.col(
            "_rescued_data"
        ),
        )
    )


# ---------------------------------------------------------
# Step 2:
# Create the Silver SCD Type 2 target.
#
# Because the Silver pipeline's default schema will be
# "silver", this becomes:
#
# payer_01_dev.silver.member
# ---------------------------------------------------------

dp.create_streaming_table(
    name="member",
    comment=(
        "Silver Member dimension with "
        "Slowly Changing Dimension Type 2 history."
    ),
    table_properties={
        "quality": "silver",
        "layer": "conformed",
        "scd_type": "2",
        "source_system": "payer_01",
    },
)


# ---------------------------------------------------------
# Step 3:
# Apply Bronze changes to Silver using AUTO CDC.
#
# member_id
#     = dimension business key
#
# update_ts
#     = sequencing field
#
# stored_as_scd_type="2"
#     = preserve historical versions
# ---------------------------------------------------------

dp.create_auto_cdc_flow(
    target="member",
    source="member_changes",

    keys=[
        "member_id"
    ],

    sequence_by=F.col(
        "update_ts"
    ),

    except_column_list=[
        "_rescued_data"
    ],

    stored_as_scd_type="2",

    track_history_except_column_list=[
        "create_ts",
        "update_ts",
        "_source_file",
        "_source_file_modification_time",
        "_ingest_timestamp",
        "_load_date",
    ],
)