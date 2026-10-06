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

ELIGIBILITY_BRONZE_TABLE = (
    f"{CATALOG}."
    f"{BRONZE_SCHEMA}."
    f"eligibility_raw"
)


# ---------------------------------------------------------
# Helper:
# Convert source Y/N values into Silver BOOLEAN values.
# ---------------------------------------------------------

def yn_to_boolean(column_name):

    value = F.upper(
        F.trim(
            F.col(column_name)
        )
    )

    return (
        F.when(
            value == "Y",
            F.lit(True)
        )
        .when(
            value == "N",
            F.lit(False)
        )
        .otherwise(
            F.lit(None)
        )
        .cast("boolean")
    )


# ---------------------------------------------------------
# Step 1:
# Read Bronze eligibility history and apply Silver typing.
#
# Eligibility is already an event/history structure.
# We are NOT applying SCD Type 2 here.
# ---------------------------------------------------------

@dp.temporary_view(
    name="eligibility_changes"
)
@dp.expect_or_drop(
    "valid_eligibility_id",
    "eligibility_id IS NOT NULL "
    "AND TRIM(eligibility_id) <> ''",
)
@dp.expect_or_drop(
    "valid_member_id",
    "member_id IS NOT NULL "
    "AND TRIM(member_id) <> ''",
)
@dp.expect_or_drop(
    "valid_record_version",
    "record_version IS NOT NULL "
    "AND record_version > 0",
)
@dp.expect_or_drop(
    "valid_update_timestamp",
    "update_ts IS NOT NULL",
)
@dp.expect_or_drop(
    "no_rescued_data",
    "_rescued_data IS NULL",
)
@dp.expect_or_drop(
    "valid_coverage_dates",
    "coverage_end_date IS NULL "
    "OR coverage_end_date >= coverage_start_date",
)
def eligibility_changes():

    return (
        spark.readStream
        .table(
            ELIGIBILITY_BRONZE_TABLE
        )
        .select(
            F.col("eligibility_id"),
            F.col("member_id"),
            F.col("subscriber_id"),
            F.col("family_id"),
            F.col(
                "relationship_to_subscriber"
            ),

            F.col("group_id"),
            F.col("subgroup_id"),
            F.col("product_id"),
            F.col("benefit_plan_id"),

            F.col("line_of_business"),
            F.col("product_type"),
            F.col("network_id"),
            F.col("coverage_tier"),

            # ---------------------------------------------
            # Coverage dates:
            # STRING -> DATE
            # ---------------------------------------------

            F.to_date(
                "coverage_start_date"
            ).alias(
                "coverage_start_date"
            ),

            F.to_date(
                "coverage_end_date"
            ).alias(
                "coverage_end_date"
            ),

            F.col(
                "eligibility_status"
            ),

            F.col(
                "event_type"
            ),

            F.to_date(
                "event_effective_date"
            ).alias(
                "event_effective_date"
            ),

            F.to_date(
                "transaction_date"
            ).alias(
                "transaction_date"
            ),

            F.col(
                "termination_reason"
            ),

            # ---------------------------------------------
            # Source flags:
            # Y/N STRING -> BOOLEAN
            # ---------------------------------------------

            yn_to_boolean(
                "retroactive_flag"
            ).alias(
                "retroactive_flag"
            ),

            yn_to_boolean(
                "future_enrollment_flag"
            ).alias(
                "future_enrollment_flag"
            ),

            yn_to_boolean(
                "reinstatement_flag"
            ).alias(
                "reinstatement_flag"
            ),

            yn_to_boolean(
                "medical_coverage_flag"
            ).alias(
                "medical_coverage_flag"
            ),

            yn_to_boolean(
                "pharmacy_coverage_flag"
            ).alias(
                "pharmacy_coverage_flag"
            ),

            yn_to_boolean(
                "dental_coverage_flag"
            ).alias(
                "dental_coverage_flag"
            ),

            yn_to_boolean(
                "vision_coverage_flag"
            ).alias(
                "vision_coverage_flag"
            ),

            # ---------------------------------------------
            # Version:
            # STRING -> INT
            # ---------------------------------------------

            F.col(
                "record_version"
            ).cast(
                "int"
            ).alias(
                "record_version"
            ),

            # Rename this so it is obvious that this
            # represents what the SOURCE record claimed.
            yn_to_boolean(
                "current_record_flag"
            ).alias(
                "source_current_record_flag"
            ),

            F.col(
                "source_system"
            ),

            F.col(
                "source_eligibility_key"
            ),

            # ---------------------------------------------
            # Audit timestamps:
            # STRING -> TIMESTAMP
            # ---------------------------------------------

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

            # Bronze lineage metadata
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

            # Needed for DQ expectation.
            F.col(
                "_rescued_data"
            ),
        )
    )


# ---------------------------------------------------------
# Step 2:
# Publish valid Eligibility events to Silver.
#
# Every valid source eligibility event is retained.
# This is NOT SCD Type 2.
# ---------------------------------------------------------

@dp.table(
    name="eligibility",
    comment=(
        "Silver Eligibility event and history table. "
        "Retains typed eligibility lifecycle records."
    ),
    table_properties={
        "quality": "silver",
        "layer": "conformed",
        "history_type": "event",
        "source_system": "payer_01",
    },
)
def eligibility():

    return (
        spark.readStream
        .table(
            "eligibility_changes"
        )
        .drop(
            "_rescued_data"
        )
    )