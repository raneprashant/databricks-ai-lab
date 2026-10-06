from pyspark import pipelines as dp
from pyspark.sql import functions as F


CATALOG = spark.conf.get(
    "payer.catalog"
)

BRONZE_SCHEMA = spark.conf.get(
    "payer.bronze_schema"
)

ADDRESS_BRONZE_TABLE = (
    f"{CATALOG}."
    f"{BRONZE_SCHEMA}."
    f"address_raw"
)


@dp.temporary_view(
    name="address_changes"
)
@dp.expect_or_drop(
    "valid_address_id",
    "address_id IS NOT NULL "
    "AND TRIM(address_id) <> ''",
)
@dp.expect_or_drop(
    "valid_update_timestamp",
    "update_ts IS NOT NULL",
)
@dp.expect_or_drop(
    "no_rescued_data",
    "_rescued_data IS NULL",
)
def address_changes():

    return (
        spark.readStream
        .table(
            ADDRESS_BRONZE_TABLE
        )
        .select(
            F.col("address_id"),
            F.col("address_line_1"),
            F.col("address_line_2"),
            F.col("city"),
            F.col("state"),
            F.col("postal_code"),
            F.col("county"),
            F.col("country_code"),
            F.col("address_status"),
            F.col("geocode_quality"),

            F.col(
                "source_address_key"
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
    name="address",
    comment=(
        "Silver Address dimension with "
        "Slowly Changing Dimension Type 2 history."
    ),
    table_properties={
        "quality": "silver",
        "layer": "conformed",
        "scd_type": "2",
        "source_system": "payer_01",
    },
)


dp.create_auto_cdc_flow(
    target="address",
    source="address_changes",

    keys=[
        "address_id"
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