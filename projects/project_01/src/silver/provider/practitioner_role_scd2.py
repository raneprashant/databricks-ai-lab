from pyspark import pipelines as dp
from pyspark.sql import functions as F


CATALOG = spark.conf.get(
    "payer.catalog"
)

BRONZE_SCHEMA = spark.conf.get(
    "payer.bronze_schema"
)

PRACTITIONER_ROLE_BRONZE_TABLE = (
    f"{CATALOG}."
    f"{BRONZE_SCHEMA}."
    f"practitioner_role_raw"
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
    name="practitioner_role_changes"
)
@dp.expect_or_drop(
    "valid_practitioner_role_id",
    "practitioner_role_id IS NOT NULL "
    "AND TRIM(practitioner_role_id) <> ''",
)
@dp.expect_or_drop(
    "valid_practitioner_id",
    "practitioner_id IS NOT NULL "
    "AND TRIM(practitioner_id) <> ''",
)
@dp.expect_or_drop(
    "valid_supplier_id",
    "supplier_id IS NOT NULL "
    "AND TRIM(supplier_id) <> ''",
)
@dp.expect_or_drop(
    "valid_supplier_location_id",
    "supplier_location_id IS NOT NULL "
    "AND TRIM(supplier_location_id) <> ''",
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
def practitioner_role_changes():

    return (
        spark.readStream
        .table(
            PRACTITIONER_ROLE_BRONZE_TABLE
        )
        .select(
            F.col("practitioner_role_id"),
            F.col("practitioner_id"),
            F.col("supplier_id"),
            F.col("supplier_location_id"),
            F.col("role_type"),
            F.col("role_specialty"),

            yn_to_boolean(
                "pcp_flag"
            ).alias(
                "pcp_flag"
            ),

            yn_to_boolean(
                "primary_affiliation_flag"
            ).alias(
                "primary_affiliation_flag"
            ),

            F.col("panel_status"),

            yn_to_boolean(
                "accepting_new_patients_flag"
            ).alias(
                "accepting_new_patients_flag"
            ),

            F.col("network_status"),
            F.col("network_tier"),
            F.col("role_status"),

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
                "source_role_key"
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
    name="practitioner_role",
    comment=(
        "Silver Practitioner Role dimension "
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
    target="practitioner_role",
    source="practitioner_role_changes",

    keys=[
        "practitioner_role_id"
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