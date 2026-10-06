from pyspark import pipelines as dp
from pyspark.sql import functions as F


CATALOG = spark.conf.get(
    "payer.catalog"
)

BRONZE_SCHEMA = spark.conf.get(
    "payer.bronze_schema"
)

PRACTITIONER_BRONZE_TABLE = (
    f"{CATALOG}."
    f"{BRONZE_SCHEMA}."
    f"practitioner_raw"
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
    name="practitioner_changes"
)
@dp.expect_or_drop(
    "valid_practitioner_id",
    "practitioner_id IS NOT NULL "
    "AND TRIM(practitioner_id) <> ''",
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
def practitioner_changes():

    return (
        spark.readStream
        .table(
            PRACTITIONER_BRONZE_TABLE
        )
        .select(
            F.col("practitioner_id"),
            F.col("individual_npi"),
            F.col("first_name"),
            F.col("middle_initial"),
            F.col("last_name"),
            F.col("suffix"),
            F.col("credential"),
            F.col("primary_specialty"),
            F.col("license_number"),
            F.col("license_state"),

            yn_to_boolean(
                "board_certified_flag"
            ).alias(
                "board_certified_flag"
            ),

            F.col("practitioner_status"),

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
                "source_practitioner_key"
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
    name="practitioner",
    comment=(
        "Silver Practitioner dimension "
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
    target="practitioner",
    source="practitioner_changes",

    keys=[
        "practitioner_id"
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