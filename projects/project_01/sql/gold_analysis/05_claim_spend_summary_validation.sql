-- ============================================================
-- Project 01 - Healthcare Payer
-- Gold Validation
-- File: 05_claim_spend_summary_validation.sql
-- ============================================================


-- ============================================================
-- 1. SUMMARY ROW COUNT
--
-- Current expected = 7806
-- ============================================================

SELECT

    COUNT(*) AS summary_rows

FROM
    payer_01_dev.gold.claim_spend_summary
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
        line_of_business,
        product_id,
        benefit_plan_id,
        claim_status,
        network_status

    FROM
        payer_01_dev.gold.claim_spend_summary

    GROUP BY

        service_month,
        line_of_business,
        product_id,
        benefit_plan_id,
        claim_status,
        network_status

    HAVING
        COUNT(*) > 1

)
;


-- ============================================================
-- 3. CLAIM COUNT RECONCILIATION
--
-- Expected difference = 0
-- ============================================================

WITH detail AS (

    SELECT
        COUNT(*) AS claim_count

    FROM
        payer_01_dev.gold.claims_enriched

),

summary AS (

    SELECT
        SUM(claim_count) AS claim_count

    FROM
        payer_01_dev.gold.claim_spend_summary

)

SELECT

    d.claim_count
        AS detail_claim_count,

    s.claim_count
        AS summary_claim_count,

    s.claim_count
        - d.claim_count
        AS difference

FROM
    detail d

CROSS JOIN
    summary s
;


-- ============================================================
-- 4. FINANCIAL TOTAL RECONCILIATION
--
-- Expected all differences = 0.00
-- ============================================================

WITH detail AS (

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
        payer_01_dev.gold.claims_enriched

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
        payer_01_dev.gold.claim_spend_summary

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
-- 5. SUMMARY FINANCIAL RULES
--
-- Expected every issue_count = 0
-- ============================================================

SELECT

    'billed_less_than_allowed' AS check_name,
    COUNT(*) AS issue_count

FROM
    payer_01_dev.gold.claim_spend_summary

WHERE
    total_billed_amount < total_allowed_amount


UNION ALL


SELECT

    'allowed_less_than_paid',
    COUNT(*)

FROM
    payer_01_dev.gold.claim_spend_summary

WHERE
    total_allowed_amount < total_paid_amount


UNION ALL


SELECT

    'allowed_paid_member_reconciliation',
    COUNT(*)

FROM
    payer_01_dev.gold.claim_spend_summary

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
-- 6. PERCENTAGE SANITY
--
-- Expected = 0
-- ============================================================

SELECT

    COUNT(*) AS invalid_ratio_count

FROM
    payer_01_dev.gold.claim_spend_summary

WHERE

       allowed_to_billed_pct < 0
    OR allowed_to_billed_pct > 100

    OR paid_to_allowed_pct < 0
    OR paid_to_allowed_pct > 100

    OR member_responsibility_pct < 0
    OR member_responsibility_pct > 100
;


-- ============================================================
-- 7. MONTHLY CLAIM TREND
--
-- Informational
-- ============================================================

SELECT

    service_month,

    SUM(claim_count)
        AS claim_count,

    SUM(unique_member_count)
        AS grouped_member_occurrences,

    SUM(total_billed_amount)
        AS billed_amount,

    SUM(total_allowed_amount)
        AS allowed_amount,

    SUM(total_paid_amount)
        AS paid_amount,

    SUM(member_responsibility_amount)
        AS member_responsibility_amount

FROM
    payer_01_dev.gold.claim_spend_summary

GROUP BY
    service_month

ORDER BY
    service_month
;


-- ============================================================
-- END
-- ============================================================