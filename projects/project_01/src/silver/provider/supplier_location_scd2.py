from pyspark import pipelines as dp
from pyspark.sql import functions as F


CATALOG = spark.conf.get(
    "payer.catalog"
)

BRONZE_SCHEMA = spark.conf.get(
    "payer.bronze_schema"
)

SUPPLIER_LOCATION_BRONZE_TABLE = (
    f"{CATALOG}."
    f"{BRONZE_SCHEMA}."
    f"supplier_location_raw"
)


def yn_to_boolean(column_name):

    value = F.upper(
        F.trim(
            F.col(column_name)
        )
    )

    return (
        F.when(value == "Y", F.lit(True))
        .when(value == "N", F.lit(False))
        .otherwise(F.lit(None))
        .cast("boolean")
    )


@dp.temporary_view(
    name="supplier_location_changes"
)
@dp.expect_or_drop(
    "valid_supplier_location_id",
    "supplier_location_id IS NOT NULL "
    "AND TRIM(supplier_location_id) <> ''",
)
@dp.expect_or_drop(
    "valid_supplier_id",
    "supplier_id IS NOT NULL "
    "AND TRIM(supplier_id) <> ''",
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
def supplier_location_changes():

    return (
        spark.readStream
        .table(
            SUPPLIER_LOCATION_BRONZE_TABLE
        )
        .select(
            F.col("supplier_location_id"),
            F.col("supplier_id"),
            F.col("location_name"),
            F.col("location_type"),
            F.col("facility_npi"),
            F.col("place_of_service_code"),
            F.col("network_status"),
            F.col("network_tier"),

            yn_to_boolean(
                "active_flag"
            ).alias(
                "active_flag"
            ),

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
                "source_location_key"
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


dp.create_streaming_table(
    name="supplier_location",
    comment=(
        "Silver Supplier Location dimension "
        "with SCD Type 2 history."
    ),
    table_properties={
        "quality": "silver",
        "layer": "conformed",
        "scd_type": "2",
        "source_system": "payer_01",
    },
)


dp.create_auto_cdc_flow(
    target="supplier_location",
    source="supplier_location_changes",

    keys=[
        "supplier_location_id"
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