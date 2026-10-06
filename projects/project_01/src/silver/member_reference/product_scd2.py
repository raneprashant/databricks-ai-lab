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

PRODUCT_BRONZE_TABLE = (
    f"{CATALOG}."
    f"{BRONZE_SCHEMA}."
    f"product_raw"
)


# ---------------------------------------------------------
# Step 1:
# Read Bronze Product changes and apply Silver typing.
# ---------------------------------------------------------

@dp.temporary_view(
    name="product_changes"
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
def product_changes():

    return (
        spark.readStream
        .table(
            PRODUCT_BRONZE_TABLE
        )
        .select(
            F.col("product_id"),
            F.col("product_code"),
            F.col("product_name"),
            F.col("line_of_business"),
            F.col("product_type"),
            F.col("market_segment"),
            F.col("funding_type"),
            F.col("network_model"),

            # Bronze stores Y/N as STRING.
            # Silver converts it to BOOLEAN.
            F.when(
                F.upper(
                    F.trim(
                        F.col("active_flag")
                    )
                ) == "Y",
                F.lit(True)
            )
            .when(
                F.upper(
                    F.trim(
                        F.col("active_flag")
                    )
                ) == "N",
                F.lit(False)
            )
            .otherwise(
                F.lit(None)
            )
            .cast("boolean")
            .alias("active_flag"),

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
                "source_product_key"
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

            # Needed for DQ validation,
            # but excluded from final Silver table.
            F.col(
                "_rescued_data"
            ),
        )
    )


# ---------------------------------------------------------
# Step 2:
# Create Silver Product SCD Type 2 target.
# ---------------------------------------------------------

dp.create_streaming_table(
    name="product",
    comment=(
        "Silver Product dimension with "
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
# Apply Bronze Product changes using AUTO CDC SCD Type 2.
# ---------------------------------------------------------

dp.create_auto_cdc_flow(
    target="product",
    source="product_changes",

    keys=[
        "product_id"
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