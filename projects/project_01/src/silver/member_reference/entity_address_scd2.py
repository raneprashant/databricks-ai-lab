from pyspark import pipelines as dp
from pyspark.sql import functions as F


CATALOG = spark.conf.get(
    "payer.catalog"
)

BRONZE_SCHEMA = spark.conf.get(
    "payer.bronze_schema"
)

ENTITY_ADDRESS_BRONZE_TABLE = (
    f"{CATALOG}."
    f"{BRONZE_SCHEMA}."
    f"entity_address_raw"
)


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


@dp.temporary_view(
    name="entity_address_changes"
)
@dp.expect_or_drop(
    "valid_entity_address_id",
    "entity_address_id IS NOT NULL "
    "AND TRIM(entity_address_id) <> ''",
)
@dp.expect_or_drop(
    "valid_entity_id",
    "entity_id IS NOT NULL "
    "AND TRIM(entity_id) <> ''",
)
@dp.expect_or_drop(
    "valid_address_id",
    "address_id IS NOT NULL "
    "AND TRIM(address_id) <> ''",
)
@dp.expect_or_drop(
    "valid_entity_type",
    """
    entity_type IN (
        'MEMBER',
        'PRACTITIONER',
        'SUPPLIER',
        'SUPPLIER_LOCATION',
        'PRACTITIONER_ROLE'
    )
    """,
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
def entity_address_changes():

    return (
        spark.readStream
        .table(
            ENTITY_ADDRESS_BRONZE_TABLE
        )
        .select(
            F.col("entity_address_id"),
            F.col("entity_type"),
            F.col("entity_id"),
            F.col("address_id"),
            F.col("address_type"),

            yn_to_boolean(
                "primary_flag"
            ).alias(
                "primary_flag"
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

            yn_to_boolean(
                "active_flag"
            ).alias(
                "active_flag"
            ),

            F.col(
                "source_entity_address_key"
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
    name="entity_address",
    comment=(
        "Silver Entity Address bridge with "
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
    target="entity_address",
    source="entity_address_changes",

    keys=[
        "entity_address_id"
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