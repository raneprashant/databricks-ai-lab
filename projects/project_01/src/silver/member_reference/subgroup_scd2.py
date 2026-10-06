from pyspark import pipelines as dp
from pyspark.sql import functions as F


CATALOG = spark.conf.get(
    "payer.catalog"
)

BRONZE_SCHEMA = spark.conf.get(
    "payer.bronze_schema"
)

SUBGROUP_BRONZE_TABLE = (
    f"{CATALOG}."
    f"{BRONZE_SCHEMA}."
    f"subgroup_raw"
)


@dp.temporary_view(
    name="subgroup_changes"
)
@dp.expect_or_drop(
    "valid_subgroup_id",
    "subgroup_id IS NOT NULL "
    "AND TRIM(subgroup_id) <> ''",
)
@dp.expect_or_drop(
    "valid_group_id",
    "group_id IS NOT NULL "
    "AND TRIM(group_id) <> ''",
)
@dp.expect_or_drop(
    "valid_benefit_plan_id",
    "benefit_plan_id IS NOT NULL "
    "AND TRIM(benefit_plan_id) <> ''",
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
def subgroup_changes():

    return (
        spark.readStream
        .table(
            SUBGROUP_BRONZE_TABLE
        )
        .select(
            F.col("subgroup_id"),
            F.col("group_id"),
            F.col("subgroup_code"),
            F.col("subgroup_name"),
            F.col("employee_class"),
            F.col("benefit_plan_id"),
            F.col("subgroup_status"),

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
                "source_subgroup_key"
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
    name="subgroup",
    comment=(
        "Silver Subgroup dimension with "
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
    target="subgroup",
    source="subgroup_changes",

    keys=[
        "subgroup_id"
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