-- ============================================================
-- Project 01 - Healthcare Payer
-- Gold Validation
-- File: 06_provider_utilization_summary_validation.sql
-- ============================================================


-- ============================================================
-- 1. SUMMARY ROW COUNT
--
-- Current expected = 214282
-- ============================================================

SELECT

    COUNT(*) AS summary_rows

FROM
    payer_01_dev.gold.provider_utilization_summary
;


-- ============================================================
-- 2. DUPLICATE SUMMARY GRAIN
--
-- Expected = 0
-- ============================================================

SELECT

    COUNT(*) AS duplicate_summary_grain_count

FROM (

    SELECT

        service_month,
        practitioner_id,
        supplier_id,
        supplier_location_id,
        service_category

    FROM
        payer_01_dev.gold.provider_utilization_summary

    GROUP BY

        service_month,
        practitioner_id,
        supplier_id,
        supplier_location_id,
        service_category

    HAVING
        COUNT(*) > 1

)
;


-- ============================================================
-- 3. CLAIM LINE COUNT RECONCILIATION
--
-- Expected:
--   detail_lines  = 450510
--   difference    = 0
-- ============================================================

WITH detail AS (

    SELECT
        COUNT(*) AS line_count

    FROM
        payer_01_dev.gold.claim_line_enriched

),

summary AS (

    SELECT
        SUM(claim_line_count) AS line_count

    FROM
        payer_01_dev.gold.provider_utilization_summary

)

SELECT

    d.line_count
        AS detail_line_count,

    s.line_count
        AS summary_line_count,

    s.line_count
        - d.line_count
        AS difference

FROM
    detail d

CROSS JOIN
    summary s
;


-- ============================================================
-- 4. UNIT RECONCILIATION
--
-- Expected difference = 0
-- ============================================================

WITH detail AS (

    SELECT
        SUM(units) AS total_units

    FROM
        payer_01_dev.gold.claim_line_enriched

),

summary AS (

    SELECT
        SUM(total_units) AS total_units

    FROM
        payer_01_dev.gold.provider_utilization_summary

)

SELECT

    d.total_units
        AS detail_units,

    s.total_units
        AS summary_units,

    s.total_units
        - d.total_units
        AS difference

FROM
    detail d

CROSS JOIN
    summary s
;


-- ============================================================
-- 5. FINANCIAL TOTAL RECONCILIATION
--
-- Expected all differences = 0.00
-- ============================================================

WITH detail AS (

    SELECT

        SUM(line_billed_amount)
            AS billed,

        SUM(line_allowed_amount)
            AS allowed,

        SUM(line_paid_amount)
            AS paid,

        SUM(line_member_responsibility_amount)
            AS member

    FROM
        payer_01_dev.gold.claim_line_enriched

),

summary AS (

    SELECT

        SUM(total_billed_amount)
            AS billed,

        SUM(total_allowed_amount)
            AS allowed,

        SUM(total_paid_amount)
            AS paid,

        SUM(member_responsibility_amount)
            AS member

    FROM
        payer_01_dev.gold.provider_utilization_summary

)

SELECT

    s.billed - d.billed
        AS billed_difference,

    s.allowed - d.allowed
        AS allowed_difference,

    s.paid - d.paid
        AS paid_difference,

    s.member - d.member
        AS member_responsibility_difference

FROM
    detail d

CROSS JOIN
    summary s
;


-- ============================================================
-- 6. SUMMARY FINANCIAL RULES
--
-- Expected every issue_count = 0
-- ============================================================

SELECT

    'billed_less_than_allowed' AS check_name,
    COUNT(*) AS issue_count

FROM
    payer_01_dev.gold.provider_utilization_summary

WHERE
    total_billed_amount < total_allowed_amount


UNION ALL


SELECT

    'allowed_less_than_paid',
    COUNT(*)

FROM
    payer_01_dev.gold.provider_utilization_summary

WHERE
    total_allowed_amount < total_paid_amount


UNION ALL


SELECT

    'allowed_paid_member_reconciliation',
    COUNT(*)

FROM
    payer_01_dev.gold.provider_utilization_summary

WHERE

    ABS(
        total_allowed_amount
        - total_paid_amount
        - member_responsibility_amount
    ) > 0.01

ORDER BY
    check_name
;


-- ============================================================
-- 7. REQUIRED PROVIDER KEYS
--
-- Expected = 0
-- ============================================================

SELECT

    COUNT(*) AS missing_provider_key_count

FROM
    payer_01_dev.gold.provider_utilization_summary

WHERE

       practitioner_id IS NULL
    OR supplier_id IS NULL
    OR supplier_location_id IS NULL
    OR service_category IS NULL
;


-- ============================================================
-- 8. TOP PROVIDER UTILIZATION
--
-- Informational
-- ============================================================

SELECT

    practitioner_id,

    practitioner_first_name,

    practitioner_last_name,

    practitioner_primary_specialty,

    supplier_name,

    SUM(claim_line_count)
        AS claim_line_count,

    SUM(claim_count)
        AS grouped_claim_count,

    SUM(total_units)
        AS total_units,

    SUM(total_paid_amount)
        AS total_paid_amount

FROM
    payer_01_dev.gold.provider_utilization_summary

GROUP BY

    practitioner_id,
    practitioner_first_name,
    practitioner_last_name,
    practitioner_primary_specialty,
    supplier_name

ORDER BY
    total_paid_amount DESC

LIMIT 20
;


-- ============================================================
-- END
-- ============================================================