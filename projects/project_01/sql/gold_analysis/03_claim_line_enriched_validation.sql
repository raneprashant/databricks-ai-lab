-- ============================================================
-- Project 01 - Healthcare Payer
-- Gold Validation
-- File: 03_claim_line_enriched_validation.sql
--
-- Gold Object:
--   payer_01_dev.gold.claim_line_enriched
--
-- Grain:
--   One row per CURRENT claim_line_id
-- ============================================================


-- ============================================================
-- 1. ROW COUNT / GRAIN
--
-- Expected:
--   total_rows     = 450510
--   distinct_lines = 450510
-- ============================================================

SELECT

    COUNT(*) AS total_rows,

    COUNT(DISTINCT claim_line_id)
        AS distinct_lines

FROM
    payer_01_dev.gold.claim_line_enriched
;


-- ============================================================
-- 2. DUPLICATE CLAIM LINE GRAIN
--
-- Expected = 0
-- ============================================================

SELECT

    COUNT(*) AS duplicate_claim_line_count

FROM (

    SELECT
        claim_line_id

    FROM
        payer_01_dev.gold.claim_line_enriched

    GROUP BY
        claim_line_id

    HAVING
        COUNT(*) > 1

)
;


-- ============================================================
-- 3. GOLD VS CURRENT SILVER CLAIM LINE COUNT
--
-- Expected difference = 0
-- ============================================================

WITH silver_count AS (

    SELECT
        COUNT(*) AS silver_current_lines

    FROM
        payer_01_dev.silver.claim_line

    WHERE
        __END_AT IS NULL

),

gold_count AS (

    SELECT
        COUNT(*) AS gold_lines

    FROM
        payer_01_dev.gold.claim_line_enriched

)

SELECT

    s.silver_current_lines,

    g.gold_lines,

    g.gold_lines
        - s.silver_current_lines
        AS difference

FROM
    silver_count s

CROSS JOIN
    gold_count g
;


-- ============================================================
-- 4. SILVER LINES MISSING FROM GOLD
--
-- Expected = 0
-- ============================================================

SELECT

    COUNT(*) AS silver_line_missing_from_gold

FROM
    payer_01_dev.silver.claim_line s

LEFT JOIN
    payer_01_dev.gold.claim_line_enriched g

    ON s.claim_line_id = g.claim_line_id

WHERE
    s.__END_AT IS NULL
    AND g.claim_line_id IS NULL
;


-- ============================================================
-- 5. GOLD LINES MISSING FROM SILVER
--
-- Expected = 0
-- ============================================================

SELECT

    COUNT(*) AS gold_line_missing_from_silver

FROM
    payer_01_dev.gold.claim_line_enriched g

LEFT JOIN
    payer_01_dev.silver.claim_line s

    ON g.claim_line_id = s.claim_line_id
    AND s.__END_AT IS NULL

WHERE
    s.claim_line_id IS NULL
;


-- ============================================================
-- 6. LINE FINANCIAL TOTALS VS SILVER
--
-- Expected all differences = 0.00
-- ============================================================

WITH silver_totals AS (

    SELECT

        SUM(billed_amount)
            AS billed_amount,

        SUM(allowed_amount)
            AS allowed_amount,

        SUM(paid_amount)
            AS paid_amount,

        SUM(member_responsibility_amount)
            AS member_responsibility_amount

    FROM
        payer_01_dev.silver.claim_line

    WHERE
        __END_AT IS NULL

),

gold_totals AS (

    SELECT

        SUM(line_billed_amount)
            AS billed_amount,

        SUM(line_allowed_amount)
            AS allowed_amount,

        SUM(line_paid_amount)
            AS paid_amount,

        SUM(line_member_responsibility_amount)
            AS member_responsibility_amount

    FROM
        payer_01_dev.gold.claim_line_enriched

)

SELECT

    g.billed_amount
        - s.billed_amount
        AS billed_difference,

    g.allowed_amount
        - s.allowed_amount
        AS allowed_difference,

    g.paid_amount
        - s.paid_amount
        AS paid_difference,

    g.member_responsibility_amount
        - s.member_responsibility_amount
        AS member_responsibility_difference

FROM
    silver_totals s

CROSS JOIN
    gold_totals g
;


-- ============================================================
-- 7. LINE FINANCIAL BUSINESS RULES
--
-- Expected every issue_count = 0
-- ============================================================

SELECT

    'billed_less_than_allowed' AS check_name,
    COUNT(*) AS issue_count

FROM
    payer_01_dev.gold.claim_line_enriched

WHERE
    line_billed_amount < line_allowed_amount


UNION ALL


SELECT

    'allowed_less_than_paid',
    COUNT(*)

FROM
    payer_01_dev.gold.claim_line_enriched

WHERE
    line_allowed_amount < line_paid_amount


UNION ALL


SELECT

    'negative_paid',
    COUNT(*)

FROM
    payer_01_dev.gold.claim_line_enriched

WHERE
    line_paid_amount < 0


UNION ALL


SELECT

    'negative_member_responsibility',
    COUNT(*)

FROM
    payer_01_dev.gold.claim_line_enriched

WHERE
    line_member_responsibility_amount < 0


UNION ALL


SELECT

    'allowed_paid_member_reconciliation',
    COUNT(*)

FROM
    payer_01_dev.gold.claim_line_enriched

WHERE

    ABS(
        line_allowed_amount
        - line_paid_amount
        - line_member_responsibility_amount
    ) > 0.01

ORDER BY
    check_name
;


-- ============================================================
-- 8. CLAIM LINE -> GOLD CLAIM HEADER
--
-- Expected = 0
-- ============================================================

SELECT

    COUNT(*) AS missing_gold_claim_header_count

FROM
    payer_01_dev.gold.claim_line_enriched cl

LEFT JOIN
    payer_01_dev.gold.claims_enriched ch

    ON cl.claim_id = ch.claim_id

WHERE
    ch.claim_id IS NULL
;


-- ============================================================
-- 9. CLAIM LINE SERVICE DATE WITHIN CLAIM DATES
--
-- Expected = 0
-- ============================================================

SELECT

    COUNT(*) AS invalid_line_service_date_count

FROM
    payer_01_dev.gold.claim_line_enriched

WHERE

       service_date < claim_service_from_date

    OR service_date > claim_service_to_date
;


-- ============================================================
-- 10. GOLD CLAIM HEADER VS GOLD CLAIM LINE RECONCILIATION
--
-- Expected:
--   mismatched_claim_count = 0
-- ============================================================

WITH line_rollup AS (

    SELECT

        claim_id,

        COUNT(*) AS actual_line_count,

        SUM(line_billed_amount)
            AS total_billed_amount,

        SUM(line_allowed_amount)
            AS total_allowed_amount,

        SUM(line_paid_amount)
            AS total_paid_amount,

        SUM(line_member_responsibility_amount)
            AS member_responsibility_amount

    FROM
        payer_01_dev.gold.claim_line_enriched

    GROUP BY
        claim_id

)

SELECT

    COUNT(*) AS mismatched_claim_count

FROM
    payer_01_dev.gold.claims_enriched ch

LEFT JOIN
    line_rollup lr

    ON ch.claim_id = lr.claim_id

WHERE

       ch.claim_line_count
       <> COALESCE(lr.actual_line_count, 0)

    OR ABS(
           ch.total_billed_amount
           - COALESCE(lr.total_billed_amount, 0)
       ) > 0.01

    OR ABS(
           ch.total_allowed_amount
           - COALESCE(lr.total_allowed_amount, 0)
       ) > 0.01

    OR ABS(
           ch.total_paid_amount
           - COALESCE(lr.total_paid_amount, 0)
       ) > 0.01

    OR ABS(
           ch.member_responsibility_amount
           - COALESCE(
                 lr.member_responsibility_amount,
                 0
             )
       ) > 0.01
;


-- ============================================================
-- 11. SERVICE CATEGORY DISTRIBUTION
--
-- Informational
-- ============================================================

SELECT

    service_category,

    COUNT(*) AS claim_line_count,

    COUNT(DISTINCT claim_id)
        AS claim_count,

    COUNT(DISTINCT member_id)
        AS member_count,

    SUM(units)
        AS total_units,

    SUM(line_paid_amount)
        AS total_paid_amount

FROM
    payer_01_dev.gold.claim_line_enriched

GROUP BY
    service_category

ORDER BY
    claim_line_count DESC
;


-- ============================================================
-- END
-- ============================================================