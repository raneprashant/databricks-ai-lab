from pyspark import pipelines as dp
from pyspark.sql import functions as F


CATALOG = spark.conf.get(
    "payer.catalog"
)

BRONZE_SCHEMA = spark.conf.get(
    "payer.bronze_schema"
)

SUPPLIER_BRONZE_TABLE = (
    f"{CATALOG}."
    f"{BRONZE_SCHEMA}."
    f"supplier_raw"
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
    name="supplier_changes"
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
    "valid_contract_dates",
    "contract_termination_date IS NULL "
    "OR contract_termination_date "
    ">= contract_effective_date",
)
def supplier_changes():

    return (
        spark.readStream
        .table(
            SUPPLIER_BRONZE_TABLE
        )
        .select(
            F.col("supplier_id"),
            F.col("supplier_name"),
            F.col("supplier_type"),
            F.col("tax_id"),
            F.col("organization_npi"),
            F.col("ownership_type"),
            F.col("network_status"),
            F.col("network_tier"),
            F.col("contract_status"),

            F.to_date(
                "contract_effective_date"
            ).alias(
                "contract_effective_date"
            ),

            F.to_date(
                "contract_termination_date"
            ).alias(
                "contract_termination_date"
            ),

            yn_to_boolean(
                "active_flag"
            ).alias(
                "active_flag"
            ),

            F.col(
                "source_supplier_key"
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
    name="supplier",
    comment=(
        "Silver Supplier dimension "
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
    target="supplier",
    source="supplier_changes",

    keys=[
        "supplier_id"
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