-- ============================================================
-- DQ 01 - Row counts and rescued data
-- ============================================================

SELECT 'member_raw' AS table_name,
       COUNT(*) AS total_rows,
       COUNT_IF(_rescued_data IS NOT NULL) AS rescued_rows
FROM payer_01_dev.bronze.member_raw

UNION ALL
SELECT 'product_raw', COUNT(*), COUNT_IF(_rescued_data IS NOT NULL)
FROM payer_01_dev.bronze.product_raw

UNION ALL
SELECT 'benefit_plan_raw', COUNT(*), COUNT_IF(_rescued_data IS NOT NULL)
FROM payer_01_dev.bronze.benefit_plan_raw

UNION ALL
SELECT 'group_raw', COUNT(*), COUNT_IF(_rescued_data IS NOT NULL)
FROM payer_01_dev.bronze.group_raw

UNION ALL
SELECT 'subgroup_raw', COUNT(*), COUNT_IF(_rescued_data IS NOT NULL)
FROM payer_01_dev.bronze.subgroup_raw

UNION ALL
SELECT 'eligibility_raw', COUNT(*), COUNT_IF(_rescued_data IS NOT NULL)
FROM payer_01_dev.bronze.eligibility_raw

UNION ALL
SELECT 'practitioner_raw', COUNT(*), COUNT_IF(_rescued_data IS NOT NULL)
FROM payer_01_dev.bronze.practitioner_raw

UNION ALL
SELECT 'supplier_raw', COUNT(*), COUNT_IF(_rescued_data IS NOT NULL)
FROM payer_01_dev.bronze.supplier_raw

UNION ALL
SELECT 'supplier_location_raw', COUNT(*), COUNT_IF(_rescued_data IS NOT NULL)
FROM payer_01_dev.bronze.supplier_location_raw

UNION ALL
SELECT 'practitioner_role_raw', COUNT(*), COUNT_IF(_rescued_data IS NOT NULL)
FROM payer_01_dev.bronze.practitioner_role_raw

UNION ALL
SELECT 'address_raw', COUNT(*), COUNT_IF(_rescued_data IS NOT NULL)
FROM payer_01_dev.bronze.address_raw

UNION ALL
SELECT 'entity_address_raw', COUNT(*), COUNT_IF(_rescued_data IS NOT NULL)
FROM payer_01_dev.bronze.entity_address_raw

UNION ALL
SELECT 'claim_header_raw', COUNT(*), COUNT_IF(_rescued_data IS NOT NULL)
FROM payer_01_dev.bronze.claim_header_raw

UNION ALL
SELECT 'claim_line_raw', COUNT(*), COUNT_IF(_rescued_data IS NOT NULL)
FROM payer_01_dev.bronze.claim_line_raw

ORDER BY table_name;


-- ============================================================
-- DQ 02 - Bronze ingestion metadata completeness
-- ============================================================

SELECT
    'member_raw' AS table_name,
    COUNT(*) AS total_rows,
    COUNT_IF(_source_file IS NULL) AS missing_source_file,
    COUNT_IF(_source_file_modification_time IS NULL) AS missing_file_modification_time,
    COUNT_IF(_ingest_timestamp IS NULL) AS missing_ingest_timestamp,
    COUNT_IF(_load_date IS NULL) AS missing_load_date
FROM payer_01_dev.bronze.member_raw

UNION ALL
SELECT 'product_raw', COUNT(*),
       COUNT_IF(_source_file IS NULL),
       COUNT_IF(_source_file_modification_time IS NULL),
       COUNT_IF(_ingest_timestamp IS NULL),
       COUNT_IF(_load_date IS NULL)
FROM payer_01_dev.bronze.product_raw

UNION ALL
SELECT 'benefit_plan_raw', COUNT(*),
       COUNT_IF(_source_file IS NULL),
       COUNT_IF(_source_file_modification_time IS NULL),
       COUNT_IF(_ingest_timestamp IS NULL),
       COUNT_IF(_load_date IS NULL)
FROM payer_01_dev.bronze.benefit_plan_raw

UNION ALL
SELECT 'group_raw', COUNT(*),
       COUNT_IF(_source_file IS NULL),
       COUNT_IF(_source_file_modification_time IS NULL),
       COUNT_IF(_ingest_timestamp IS NULL),
       COUNT_IF(_load_date IS NULL)
FROM payer_01_dev.bronze.group_raw

UNION ALL
SELECT 'subgroup_raw', COUNT(*),
       COUNT_IF(_source_file IS NULL),
       COUNT_IF(_source_file_modification_time IS NULL),
       COUNT_IF(_ingest_timestamp IS NULL),
       COUNT_IF(_load_date IS NULL)
FROM payer_01_dev.bronze.subgroup_raw

UNION ALL
SELECT 'eligibility_raw', COUNT(*),
       COUNT_IF(_source_file IS NULL),
       COUNT_IF(_source_file_modification_time IS NULL),
       COUNT_IF(_ingest_timestamp IS NULL),
       COUNT_IF(_load_date IS NULL)
FROM payer_01_dev.bronze.eligibility_raw

UNION ALL
SELECT 'practitioner_raw', COUNT(*),
       COUNT_IF(_source_file IS NULL),
       COUNT_IF(_source_file_modification_time IS NULL),
       COUNT_IF(_ingest_timestamp IS NULL),
       COUNT_IF(_load_date IS NULL)
FROM payer_01_dev.bronze.practitioner_raw

UNION ALL
SELECT 'supplier_raw', COUNT(*),
       COUNT_IF(_source_file IS NULL),
       COUNT_IF(_source_file_modification_time IS NULL),
       COUNT_IF(_ingest_timestamp IS NULL),
       COUNT_IF(_load_date IS NULL)
FROM payer_01_dev.bronze.supplier_raw

UNION ALL
SELECT 'supplier_location_raw', COUNT(*),
       COUNT_IF(_source_file IS NULL),
       COUNT_IF(_source_file_modification_time IS NULL),
       COUNT_IF(_ingest_timestamp IS NULL),
       COUNT_IF(_load_date IS NULL)
FROM payer_01_dev.bronze.supplier_location_raw

UNION ALL
SELECT 'practitioner_role_raw', COUNT(*),
       COUNT_IF(_source_file IS NULL),
       COUNT_IF(_source_file_modification_time IS NULL),
       COUNT_IF(_ingest_timestamp IS NULL),
       COUNT_IF(_load_date IS NULL)
FROM payer_01_dev.bronze.practitioner_role_raw

UNION ALL
SELECT 'address_raw', COUNT(*),
       COUNT_IF(_source_file IS NULL),
       COUNT_IF(_source_file_modification_time IS NULL),
       COUNT_IF(_ingest_timestamp IS NULL),
       COUNT_IF(_load_date IS NULL)
FROM payer_01_dev.bronze.address_raw

UNION ALL
SELECT 'entity_address_raw', COUNT(*),
       COUNT_IF(_source_file IS NULL),
       COUNT_IF(_source_file_modification_time IS NULL),
       COUNT_IF(_ingest_timestamp IS NULL),
       COUNT_IF(_load_date IS NULL)
FROM payer_01_dev.bronze.entity_address_raw

UNION ALL
SELECT 'claim_header_raw', COUNT(*),
       COUNT_IF(_source_file IS NULL),
       COUNT_IF(_source_file_modification_time IS NULL),
       COUNT_IF(_ingest_timestamp IS NULL),
       COUNT_IF(_load_date IS NULL)
FROM payer_01_dev.bronze.claim_header_raw

UNION ALL
SELECT 'claim_line_raw', COUNT(*),
       COUNT_IF(_source_file IS NULL),
       COUNT_IF(_source_file_modification_time IS NULL),
       COUNT_IF(_ingest_timestamp IS NULL),
       COUNT_IF(_load_date IS NULL)
FROM payer_01_dev.bronze.claim_line_raw

ORDER BY table_name;


-- ============================================================
-- DQ 03 - Missing primary/business keys
-- ============================================================

SELECT
    'member_raw' AS table_name,
    'member_id' AS key_column,
    COUNT(*) AS total_rows,
    COUNT_IF(member_id IS NULL OR TRIM(member_id) = '') AS missing_key_rows
FROM payer_01_dev.bronze.member_raw

UNION ALL
SELECT 'product_raw', 'product_id', COUNT(*),
       COUNT_IF(product_id IS NULL OR TRIM(product_id) = '')
FROM payer_01_dev.bronze.product_raw

UNION ALL
SELECT 'benefit_plan_raw', 'benefit_plan_id', COUNT(*),
       COUNT_IF(benefit_plan_id IS NULL OR TRIM(benefit_plan_id) = '')
FROM payer_01_dev.bronze.benefit_plan_raw

UNION ALL
SELECT 'group_raw', 'group_id', COUNT(*),
       COUNT_IF(group_id IS NULL OR TRIM(group_id) = '')
FROM payer_01_dev.bronze.group_raw

UNION ALL
SELECT 'subgroup_raw', 'subgroup_id', COUNT(*),
       COUNT_IF(subgroup_id IS NULL OR TRIM(subgroup_id) = '')
FROM payer_01_dev.bronze.subgroup_raw

UNION ALL
SELECT 'eligibility_raw', 'eligibility_id', COUNT(*),
       COUNT_IF(eligibility_id IS NULL OR TRIM(eligibility_id) = '')
FROM payer_01_dev.bronze.eligibility_raw

UNION ALL
SELECT 'practitioner_raw', 'practitioner_id', COUNT(*),
       COUNT_IF(practitioner_id IS NULL OR TRIM(practitioner_id) = '')
FROM payer_01_dev.bronze.practitioner_raw

UNION ALL
SELECT 'supplier_raw', 'supplier_id', COUNT(*),
       COUNT_IF(supplier_id IS NULL OR TRIM(supplier_id) = '')
FROM payer_01_dev.bronze.supplier_raw

UNION ALL
SELECT 'supplier_location_raw', 'supplier_location_id', COUNT(*),
       COUNT_IF(
           supplier_location_id IS NULL
           OR TRIM(supplier_location_id) = ''
       )
FROM payer_01_dev.bronze.supplier_location_raw

UNION ALL
SELECT 'practitioner_role_raw', 'practitioner_role_id', COUNT(*),
       COUNT_IF(
           practitioner_role_id IS NULL
           OR TRIM(practitioner_role_id) = ''
       )
FROM payer_01_dev.bronze.practitioner_role_raw

UNION ALL
SELECT 'address_raw', 'address_id', COUNT(*),
       COUNT_IF(address_id IS NULL OR TRIM(address_id) = '')
FROM payer_01_dev.bronze.address_raw

UNION ALL
SELECT 'entity_address_raw', 'entity_address_id', COUNT(*),
       COUNT_IF(
           entity_address_id IS NULL
           OR TRIM(entity_address_id) = ''
       )
FROM payer_01_dev.bronze.entity_address_raw

UNION ALL
SELECT 'claim_header_raw', 'claim_id', COUNT(*),
       COUNT_IF(claim_id IS NULL OR TRIM(claim_id) = '')
FROM payer_01_dev.bronze.claim_header_raw

UNION ALL
SELECT 'claim_line_raw', 'claim_line_id', COUNT(*),
       COUNT_IF(claim_line_id IS NULL OR TRIM(claim_line_id) = '')
FROM payer_01_dev.bronze.claim_line_raw

ORDER BY table_name;


-- ============================================================
-- DQ 04 - Duplicate primary/business keys
-- ============================================================

SELECT
    'member_raw' AS table_name,
    COUNT(*) AS total_rows,
    COUNT(DISTINCT member_id) AS distinct_keys,
    COUNT(*) - COUNT(DISTINCT member_id) AS duplicate_rows
FROM payer_01_dev.bronze.member_raw

UNION ALL
SELECT 'product_raw',
       COUNT(*),
       COUNT(DISTINCT product_id),
       COUNT(*) - COUNT(DISTINCT product_id)
FROM payer_01_dev.bronze.product_raw

UNION ALL
SELECT 'benefit_plan_raw',
       COUNT(*),
       COUNT(DISTINCT benefit_plan_id),
       COUNT(*) - COUNT(DISTINCT benefit_plan_id)
FROM payer_01_dev.bronze.benefit_plan_raw

UNION ALL
SELECT 'group_raw',
       COUNT(*),
       COUNT(DISTINCT group_id),
       COUNT(*) - COUNT(DISTINCT group_id)
FROM payer_01_dev.bronze.group_raw

UNION ALL
SELECT 'subgroup_raw',
       COUNT(*),
       COUNT(DISTINCT subgroup_id),
       COUNT(*) - COUNT(DISTINCT subgroup_id)
FROM payer_01_dev.bronze.subgroup_raw

UNION ALL
SELECT 'eligibility_raw',
       COUNT(*),
       COUNT(DISTINCT eligibility_id),
       COUNT(*) - COUNT(DISTINCT eligibility_id)
FROM payer_01_dev.bronze.eligibility_raw

UNION ALL
SELECT 'practitioner_raw',
       COUNT(*),
       COUNT(DISTINCT practitioner_id),
       COUNT(*) - COUNT(DISTINCT practitioner_id)
FROM payer_01_dev.bronze.practitioner_raw

UNION ALL
SELECT 'supplier_raw',
       COUNT(*),
       COUNT(DISTINCT supplier_id),
       COUNT(*) - COUNT(DISTINCT supplier_id)
FROM payer_01_dev.bronze.supplier_raw

UNION ALL
SELECT 'supplier_location_raw',
       COUNT(*),
       COUNT(DISTINCT supplier_location_id),
       COUNT(*) - COUNT(DISTINCT supplier_location_id)
FROM payer_01_dev.bronze.supplier_location_raw

UNION ALL
SELECT 'practitioner_role_raw',
       COUNT(*),
       COUNT(DISTINCT practitioner_role_id),
       COUNT(*) - COUNT(DISTINCT practitioner_role_id)
FROM payer_01_dev.bronze.practitioner_role_raw

UNION ALL
SELECT 'address_raw',
       COUNT(*),
       COUNT(DISTINCT address_id),
       COUNT(*) - COUNT(DISTINCT address_id)
FROM payer_01_dev.bronze.address_raw

UNION ALL
SELECT 'entity_address_raw',
       COUNT(*),
       COUNT(DISTINCT entity_address_id),
       COUNT(*) - COUNT(DISTINCT entity_address_id)
FROM payer_01_dev.bronze.entity_address_raw

UNION ALL
SELECT 'claim_header_raw',
       COUNT(*),
       COUNT(DISTINCT claim_id),
       COUNT(*) - COUNT(DISTINCT claim_id)
FROM payer_01_dev.bronze.claim_header_raw

UNION ALL
SELECT 'claim_line_raw',
       COUNT(*),
       COUNT(DISTINCT claim_line_id),
       COUNT(*) - COUNT(DISTINCT claim_line_id)
FROM payer_01_dev.bronze.claim_line_raw

ORDER BY table_name;


-- ============================================================
-- DQ 05 - Source file lineage
-- ============================================================

SELECT
    'member_raw' AS table_name,
    COUNT(DISTINCT _source_file) AS source_file_count
FROM payer_01_dev.bronze.member_raw

UNION ALL
SELECT 'product_raw', COUNT(DISTINCT _source_file)
FROM payer_01_dev.bronze.product_raw

UNION ALL
SELECT 'benefit_plan_raw', COUNT(DISTINCT _source_file)
FROM payer_01_dev.bronze.benefit_plan_raw

UNION ALL
SELECT 'group_raw', COUNT(DISTINCT _source_file)
FROM payer_01_dev.bronze.group_raw

UNION ALL
SELECT 'subgroup_raw', COUNT(DISTINCT _source_file)
FROM payer_01_dev.bronze.subgroup_raw

UNION ALL
SELECT 'eligibility_raw', COUNT(DISTINCT _source_file)
FROM payer_01_dev.bronze.eligibility_raw

UNION ALL
SELECT 'practitioner_raw', COUNT(DISTINCT _source_file)
FROM payer_01_dev.bronze.practitioner_raw

UNION ALL
SELECT 'supplier_raw', COUNT(DISTINCT _source_file)
FROM payer_01_dev.bronze.supplier_raw

UNION ALL
SELECT 'supplier_location_raw', COUNT(DISTINCT _source_file)
FROM payer_01_dev.bronze.supplier_location_raw

UNION ALL
SELECT 'practitioner_role_raw', COUNT(DISTINCT _source_file)
FROM payer_01_dev.bronze.practitioner_role_raw

UNION ALL
SELECT 'address_raw', COUNT(DISTINCT _source_file)
FROM payer_01_dev.bronze.address_raw

UNION ALL
SELECT 'entity_address_raw', COUNT(DISTINCT _source_file)
FROM payer_01_dev.bronze.entity_address_raw

UNION ALL
SELECT 'claim_header_raw', COUNT(DISTINCT _source_file)
FROM payer_01_dev.bronze.claim_header_raw

UNION ALL
SELECT 'claim_line_raw', COUNT(DISTINCT _source_file)
FROM payer_01_dev.bronze.claim_line_raw

ORDER BY table_name;


-- ============================================================
-- DQ 06 - Row counts by source file
-- ============================================================

SELECT
    'member_raw' AS table_name,
    _source_file,
    COUNT(*) AS row_count
FROM payer_01_dev.bronze.member_raw
GROUP BY _source_file

UNION ALL

SELECT
    'product_raw',
    _source_file,
    COUNT(*)
FROM payer_01_dev.bronze.product_raw
GROUP BY _source_file

UNION ALL

SELECT
    'benefit_plan_raw',
    _source_file,
    COUNT(*)
FROM payer_01_dev.bronze.benefit_plan_raw
GROUP BY _source_file

UNION ALL

SELECT
    'group_raw',
    _source_file,
    COUNT(*)
FROM payer_01_dev.bronze.group_raw
GROUP BY _source_file

UNION ALL

SELECT
    'subgroup_raw',
    _source_file,
    COUNT(*)
FROM payer_01_dev.bronze.subgroup_raw
GROUP BY _source_file

UNION ALL

SELECT
    'eligibility_raw',
    _source_file,
    COUNT(*)
FROM payer_01_dev.bronze.eligibility_raw
GROUP BY _source_file

UNION ALL

SELECT
    'practitioner_raw',
    _source_file,
    COUNT(*)
FROM payer_01_dev.bronze.practitioner_raw
GROUP BY _source_file

UNION ALL

SELECT
    'supplier_raw',
    _source_file,
    COUNT(*)
FROM payer_01_dev.bronze.supplier_raw
GROUP BY _source_file

UNION ALL

SELECT
    'supplier_location_raw',
    _source_file,
    COUNT(*)
FROM payer_01_dev.bronze.supplier_location_raw
GROUP BY _source_file

UNION ALL

SELECT
    'practitioner_role_raw',
    _source_file,
    COUNT(*)
FROM payer_01_dev.bronze.practitioner_role_raw
GROUP BY _source_file

UNION ALL

SELECT
    'address_raw',
    _source_file,
    COUNT(*)
FROM payer_01_dev.bronze.address_raw
GROUP BY _source_file

UNION ALL

SELECT
    'entity_address_raw',
    _source_file,
    COUNT(*)
FROM payer_01_dev.bronze.entity_address_raw
GROUP BY _source_file

UNION ALL

SELECT
    'claim_header_raw',
    _source_file,
    COUNT(*)
FROM payer_01_dev.bronze.claim_header_raw
GROUP BY _source_file

UNION ALL

SELECT
    'claim_line_raw',
    _source_file,
    COUNT(*)
FROM payer_01_dev.bronze.claim_line_raw
GROUP BY _source_file

ORDER BY table_name, _source_file;

-- ============================================================
-- DQ 07 - Bronze ingestion timing
-- ============================================================

SELECT
    'member_raw' AS table_name,
    MIN(_ingest_timestamp) AS first_ingest_timestamp,
    MAX(_ingest_timestamp) AS last_ingest_timestamp,
    MIN(_load_date) AS first_load_date,
    MAX(_load_date) AS last_load_date
FROM payer_01_dev.bronze.member_raw

UNION ALL
SELECT 'product_raw',
       MIN(_ingest_timestamp),
       MAX(_ingest_timestamp),
       MIN(_load_date),
       MAX(_load_date)
FROM payer_01_dev.bronze.product_raw

UNION ALL
SELECT 'benefit_plan_raw',
       MIN(_ingest_timestamp),
       MAX(_ingest_timestamp),
       MIN(_load_date),
       MAX(_load_date)
FROM payer_01_dev.bronze.benefit_plan_raw

UNION ALL
SELECT 'group_raw',
       MIN(_ingest_timestamp),
       MAX(_ingest_timestamp),
       MIN(_load_date),
       MAX(_load_date)
FROM payer_01_dev.bronze.group_raw

UNION ALL
SELECT 'subgroup_raw',
       MIN(_ingest_timestamp),
       MAX(_ingest_timestamp),
       MIN(_load_date),
       MAX(_load_date)
FROM payer_01_dev.bronze.subgroup_raw

UNION ALL
SELECT 'eligibility_raw',
       MIN(_ingest_timestamp),
       MAX(_ingest_timestamp),
       MIN(_load_date),
       MAX(_load_date)
FROM payer_01_dev.bronze.eligibility_raw

UNION ALL
SELECT 'practitioner_raw',
       MIN(_ingest_timestamp),
       MAX(_ingest_timestamp),
       MIN(_load_date),
       MAX(_load_date)
FROM payer_01_dev.bronze.practitioner_raw

UNION ALL
SELECT 'supplier_raw',
       MIN(_ingest_timestamp),
       MAX(_ingest_timestamp),
       MIN(_load_date),
       MAX(_load_date)
FROM payer_01_dev.bronze.supplier_raw

UNION ALL
SELECT 'supplier_location_raw',
       MIN(_ingest_timestamp),
       MAX(_ingest_timestamp),
       MIN(_load_date),
       MAX(_load_date)
FROM payer_01_dev.bronze.supplier_location_raw

UNION ALL
SELECT 'practitioner_role_raw',
       MIN(_ingest_timestamp),
       MAX(_ingest_timestamp),
       MIN(_load_date),
       MAX(_load_date)
FROM payer_01_dev.bronze.practitioner_role_raw

UNION ALL
SELECT 'address_raw',
       MIN(_ingest_timestamp),
       MAX(_ingest_timestamp),
       MIN(_load_date),
       MAX(_load_date)
FROM payer_01_dev.bronze.address_raw

UNION ALL
SELECT 'entity_address_raw',
       MIN(_ingest_timestamp),
       MAX(_ingest_timestamp),
       MIN(_load_date),
       MAX(_load_date)
FROM payer_01_dev.bronze.entity_address_raw

UNION ALL
SELECT 'claim_header_raw',
       MIN(_ingest_timestamp),
       MAX(_ingest_timestamp),
       MIN(_load_date),
       MAX(_load_date)
FROM payer_01_dev.bronze.claim_header_raw

UNION ALL
SELECT 'claim_line_raw',
       MIN(_ingest_timestamp),
       MAX(_ingest_timestamp),
       MIN(_load_date),
       MAX(_load_date)
FROM payer_01_dev.bronze.claim_line_raw

ORDER BY table_name;


-- ============================================================
-- DQ 08 - Show tables containing rescued rows only
-- ============================================================

WITH dq AS (

    SELECT 'member_raw' AS table_name,
           COUNT_IF(_rescued_data IS NOT NULL) AS rescued_rows
    FROM payer_01_dev.bronze.member_raw

    UNION ALL
    SELECT 'product_raw',
           COUNT_IF(_rescued_data IS NOT NULL)
    FROM payer_01_dev.bronze.product_raw

    UNION ALL
    SELECT 'benefit_plan_raw',
           COUNT_IF(_rescued_data IS NOT NULL)
    FROM payer_01_dev.bronze.benefit_plan_raw

    UNION ALL
    SELECT 'group_raw',
           COUNT_IF(_rescued_data IS NOT NULL)
    FROM payer_01_dev.bronze.group_raw

    UNION ALL
    SELECT 'subgroup_raw',
           COUNT_IF(_rescued_data IS NOT NULL)
    FROM payer_01_dev.bronze.subgroup_raw

    UNION ALL
    SELECT 'eligibility_raw',
           COUNT_IF(_rescued_data IS NOT NULL)
    FROM payer_01_dev.bronze.eligibility_raw

    UNION ALL
    SELECT 'practitioner_raw',
           COUNT_IF(_rescued_data IS NOT NULL)
    FROM payer_01_dev.bronze.practitioner_raw

    UNION ALL
    SELECT 'supplier_raw',
           COUNT_IF(_rescued_data IS NOT NULL)
    FROM payer_01_dev.bronze.supplier_raw

    UNION ALL
    SELECT 'supplier_location_raw',
           COUNT_IF(_rescued_data IS NOT NULL)
    FROM payer_01_dev.bronze.supplier_location_raw

    UNION ALL
    SELECT 'practitioner_role_raw',
           COUNT_IF(_rescued_data IS NOT NULL)
    FROM payer_01_dev.bronze.practitioner_role_raw

    UNION ALL
    SELECT 'address_raw',
           COUNT_IF(_rescued_data IS NOT NULL)
    FROM payer_01_dev.bronze.address_raw

    UNION ALL
    SELECT 'entity_address_raw',
           COUNT_IF(_rescued_data IS NOT NULL)
    FROM payer_01_dev.bronze.entity_address_raw

    UNION ALL
    SELECT 'claim_header_raw',
           COUNT_IF(_rescued_data IS NOT NULL)
    FROM payer_01_dev.bronze.claim_header_raw

    UNION ALL
    SELECT 'claim_line_raw',
           COUNT_IF(_rescued_data IS NOT NULL)
    FROM payer_01_dev.bronze.claim_line_raw
)

SELECT *
FROM dq
WHERE rescued_rows > 0
ORDER BY rescued_rows DESC;


