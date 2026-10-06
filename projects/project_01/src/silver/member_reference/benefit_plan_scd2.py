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

BENEFIT_PLAN_BRONZE_TABLE = (
    f"{CATALOG}."
    f"{BRONZE_SCHEMA}."
    f"benefit_plan_raw"
)


# ---------------------------------------------------------
# Helper:
# Convert source Y/N values into Silver BOOLEAN values.
# ---------------------------------------------------------

def yn_to_boolean(column_name):

    normalized_value = F.upper(
        F.trim(
            F.col(column_name)
        )
    )

    return (
        F.when(
            normalized_value == "Y",
            F.lit(True)
        )
        .when(
            normalized_value == "N",
            F.lit(False)
        )
        .otherwise(
            F.lit(None)
        )
        .cast("boolean")
    )


# ---------------------------------------------------------
# Step 1:
# Read Bronze Benefit Plan changes and apply Silver typing.
# ---------------------------------------------------------

@dp.temporary_view(
    name="benefit_plan_changes"
)
@dp.expect_or_drop(
    "valid_benefit_plan_id",
    "benefit_plan_id IS NOT NULL "
    "AND TRIM(benefit_plan_id) <> ''",
)
@dp.expect_or_drop(
    "valid_product_id",
    "product_id IS NOT NULL "
    "AND TRIM(product_id) <> ''",
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
    "valid_effective_dates",
    "termination_date IS NULL "
    "OR termination_date >= effective_date",
)
@dp.expect_or_drop(
    "valid_financial_amounts",
    """
    individual_deductible >= 0
    AND family_deductible >= 0
    AND individual_oop_max >= 0
    AND family_oop_max >= 0
    AND pcp_copay >= 0
    AND specialist_copay >= 0
    AND urgent_care_copay >= 0
    AND er_copay >= 0
    """,
)
@dp.expect_or_drop(
    "valid_coinsurance_pct",
    "coinsurance_pct >= 0 "
    "AND coinsurance_pct <= 100",
)
def benefit_plan_changes():

    return (
        spark.readStream
        .table(
            BENEFIT_PLAN_BRONZE_TABLE
        )
        .select(
            F.col("benefit_plan_id"),
            F.col("product_id"),
            F.col("plan_code"),
            F.col("plan_name"),
            F.col("metal_level"),
            F.col("network_id"),

            # ---------------------------------------------
            # Financial attributes:
            # STRING -> DECIMAL
            # ---------------------------------------------

            F.col(
                "individual_deductible"
            ).cast(
                "decimal(18,2)"
            ).alias(
                "individual_deductible"
            ),

            F.col(
                "family_deductible"
            ).cast(
                "decimal(18,2)"
            ).alias(
                "family_deductible"
            ),

            F.col(
                "individual_oop_max"
            ).cast(
                "decimal(18,2)"
            ).alias(
                "individual_oop_max"
            ),

            F.col(
                "family_oop_max"
            ).cast(
                "decimal(18,2)"
            ).alias(
                "family_oop_max"
            ),

            F.col(
                "pcp_copay"
            ).cast(
                "decimal(18,2)"
            ).alias(
                "pcp_copay"
            ),

            F.col(
                "specialist_copay"
            ).cast(
                "decimal(18,2)"
            ).alias(
                "specialist_copay"
            ),

            F.col(
                "urgent_care_copay"
            ).cast(
                "decimal(18,2)"
            ).alias(
                "urgent_care_copay"
            ),

            F.col(
                "er_copay"
            ).cast(
                "decimal(18,2)"
            ).alias(
                "er_copay"
            ),

            F.col(
                "coinsurance_pct"
            ).cast(
                "decimal(5,2)"
            ).alias(
                "coinsurance_pct"
            ),

            # ---------------------------------------------
            # Coverage flags:
            # Y/N STRING -> BOOLEAN
            # ---------------------------------------------

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

            yn_to_boolean(
                "referral_required_flag"
            ).alias(
                "referral_required_flag"
            ),

            F.col("plan_status"),

            # ---------------------------------------------
            # Dates:
            # STRING -> DATE
            # ---------------------------------------------

            F.to_date(
                "effective_date"
            ).alias(
                "effective_date"
            ),

            F.to_date(
                "termination_date"
            ).alias(
                "termination_date"
            ),

            F.col(
                "source_plan_key"
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

            # Used for DQ only.
            F.col(
                "_rescued_data"
            ),
        )
    )


# ---------------------------------------------------------
# Step 2:
# Create Silver Benefit Plan SCD Type 2 target.
# ---------------------------------------------------------

dp.create_streaming_table(
    name="benefit_plan",
    comment=(
        "Silver Benefit Plan dimension with "
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
# Apply changes using AUTO CDC SCD Type 2.
# ---------------------------------------------------------

dp.create_auto_cdc_flow(
    target="benefit_plan",
    source="benefit_plan_changes",

    keys=[
        "benefit_plan_id"
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