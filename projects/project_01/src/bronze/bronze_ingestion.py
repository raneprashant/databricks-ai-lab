from pyspark import pipelines as dp
from pyspark.sql import functions as F


# ---------------------------------------------------------
# Pipeline configuration
# ---------------------------------------------------------

LANDING_ROOT = spark.conf.get(
    "payer.landing_root",
    "/Volumes/payer_01_dev/bronze/landing",
)


# ---------------------------------------------------------
# Bronze source metadata
#
# Metadata-driven Bronze ingestion configuration
# for all payer source domains.
# ---------------------------------------------------------

BRONZE_SOURCES = [
    {
        "source_name": "member",
        "target_table": "member_raw",
        "flow_name": "member_raw_ingest_flow",
        "comment": (
            "Raw Member records incrementally ingested "
            "from the payer landing volume using Auto Loader."
        ),
    },
    {
        "source_name": "product",
        "target_table": "product_raw",
        "flow_name": "product_raw_ingest_flow",
        "comment": (
            "Raw Product records incrementally ingested "
            "from the payer landing volume using Auto Loader."
        ),
    },
    {
        "source_name": "benefit_plan",
        "target_table": "benefit_plan_raw",
        "flow_name": "benefit_plan_raw_ingest_flow",
        "comment": (
            "Raw Benefit Plan records incrementally ingested "
            "from the payer landing volume using Auto Loader."
        ),
    },
    {
        "source_name": "group",
        "target_table": "group_raw",
        "flow_name": "group_raw_ingest_flow",
        "comment": (
            "Raw Group records incrementally ingested "
            "from the payer landing volume using Auto Loader."
        ),
    },
    {
        "source_name": "subgroup",
        "target_table": "subgroup_raw",
        "flow_name": "subgroup_raw_ingest_flow",
        "comment": (
            "Raw Subgroup records incrementally ingested "
            "from the payer landing volume using Auto Loader."
        ),
    },
    {
        "source_name": "eligibility",
        "target_table": "eligibility_raw",
        "flow_name": "eligibility_raw_ingest_flow",
        "comment": (
            "Raw Eligibility records incrementally ingested "
            "from the payer landing volume using Auto Loader."
        ),
    },
    {
        "source_name": "practitioner",
        "target_table": "practitioner_raw",
        "flow_name": "practitioner_raw_ingest_flow",
        "comment": (
            "Raw Practitioner records incrementally ingested "
            "from the payer landing volume using Auto Loader."
        ),
    },
    {
        "source_name": "supplier",
        "target_table": "supplier_raw",
        "flow_name": "supplier_raw_ingest_flow",
        "comment": (
            "Raw Supplier records incrementally ingested "
            "from the payer landing volume using Auto Loader."
        ),
    },
    {
        "source_name": "supplier_location",
        "target_table": "supplier_location_raw",
        "flow_name": "supplier_location_raw_ingest_flow",
        "comment": (
            "Raw Supplier Location records incrementally ingested "
            "from the payer landing volume using Auto Loader."
        ),
    },
    {
        "source_name": "practitioner_role",
        "target_table": "practitioner_role_raw",
        "flow_name": "practitioner_role_raw_ingest_flow",
        "comment": (
            "Raw Practitioner Role records incrementally ingested "
            "from the payer landing volume using Auto Loader."
        ),
    },
    {
        "source_name": "address",
        "target_table": "address_raw",
        "flow_name": "address_raw_ingest_flow",
        "comment": (
            "Raw Address records incrementally ingested "
            "from the payer landing volume using Auto Loader."
        ),
    },
    {
        "source_name": "entity_address",
        "target_table": "entity_address_raw",
        "flow_name": "entity_address_raw_ingest_flow",
        "comment": (
            "Raw Entity Address records incrementally ingested "
            "from the payer landing volume using Auto Loader."
        ),
    },
    {
        "source_name": "claim_header",
        "target_table": "claim_header_raw",
        "flow_name": "claim_header_raw_ingest_flow",
        "comment": (
            "Raw Claim Header records incrementally ingested "
            "from the payer landing volume using Auto Loader."
        ),
    },
    {
        "source_name": "claim_line",
        "target_table": "claim_line_raw",
        "flow_name": "claim_line_raw_ingest_flow",
        "comment": (
            "Raw Claim Line records incrementally ingested "
            "from the payer landing volume using Auto Loader."
        ),
    },
]
# ---------------------------------------------------------
# Create one Bronze streaming table + Auto Loader flow
# for each configured source.
# ---------------------------------------------------------

for source in BRONZE_SOURCES:

    source_name = source[
        "source_name"
    ]

    target_table = source[
        "target_table"
    ]

    flow_name = source[
        "flow_name"
    ]

    comment = source[
        "comment"
    ]

    source_path = (
        f"{LANDING_ROOT}/"
        f"{source_name}"
    )

    # -----------------------------------------------------
    # Bronze target table
    # -----------------------------------------------------

    dp.create_streaming_table(
        name=target_table,
        comment=comment,
        table_properties={
            "quality": "bronze",
            "layer": "raw",
            "source_system": "payer_01",
        },
    )

    # -----------------------------------------------------
    # Incremental Auto Loader flow
    #
    # Default arguments are important here.
    # They bind the current loop values to this flow.
    # -----------------------------------------------------

    @dp.append_flow(
        target=target_table,
        name=flow_name,
    )
    def ingest_source(
        source_path=source_path,
    ):

        return (
            spark.readStream
            .format(
                "cloudFiles"
            )

            .option(
                "cloudFiles.format",
                "csv",
            )

            .option(
                "header",
                "true",
            )

            .option(
                "cloudFiles.inferColumnTypes",
                "false",
            )

            .option(
                "cloudFiles.schemaEvolutionMode",
                "addNewColumns",
            )

            .option(
                "rescuedDataColumn",
                "_rescued_data",
            )

            .option(
                "pathGlobFilter",
                "*.csv",
            )

            .load(
                source_path
            )

            .select(
                "*",

                F.col(
                    "_metadata.file_path"
                ).alias(
                    "_source_file"
                ),

                F.col(
                    "_metadata.file_modification_time"
                ).alias(
                    "_source_file_modification_time"
                ),

                F.current_timestamp().alias(
                    "_ingest_timestamp"
                ),

                F.current_date().alias(
                    "_load_date"
                ),
            )
        )