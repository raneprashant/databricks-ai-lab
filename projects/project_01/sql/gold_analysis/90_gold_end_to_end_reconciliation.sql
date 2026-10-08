-- ============================================================
-- Project 01 - Healthcare Payer
-- Gold End-to-End Reconciliation
-- File: 90_gold_end_to_end_reconciliation.sql
--
-- Purpose:
--   Quick PASS / FAIL health check across the complete Gold
--   layer after any pipeline refresh or incremental batch.
-- ============================================================


-- ============================================================
-- 1. GRAIN / COUNT RECONCILIATION
-- ============================================================

WITH checks AS (

    SELECT

        'member_current_coverage_vs_silver_member'
            AS check_name,

        CAST((
            SELECT COUNT(*)
            FROM payer_01_dev.silver.member
            WHERE __END_AT IS NULL
        ) AS DECIMAL(38,2))
            AS expected_value,

        CAST((
            SELECT COUNT(*)
            FROM payer_01_dev.gold.member_current_coverage
        ) AS DECIMAL(38,2))
            AS actual_value


    UNION ALL


    SELECT

        'claims_enriched_vs_silver_claim_header',

        CAST((
            SELECT COUNT(*)
            FROM payer_01_dev.silver.claim_header
            WHERE __END_AT IS NULL
        ) AS DECIMAL(38,2)),

        CAST((
            SELECT COUNT(*)
            FROM payer_01_dev.gold.claims_enriched
        ) AS DECIMAL(38,2))


    UNION ALL


    SELECT

        'claim_line_enriched_vs_silver_claim_line',

        CAST((
            SELECT COUNT(*)
            FROM payer_01_dev.silver.claim_line
            WHERE __END_AT IS NULL
        ) AS DECIMAL(38,2)),

        CAST((
            SELECT COUNT(*)
            FROM payer_01_dev.gold.claim_line_enriched
        ) AS DECIMAL(38,2))


    UNION ALL


    SELECT

        'membership_summary_member_reconciliation',

        CAST((
            SELECT COUNT(*)
            FROM payer_01_dev.gold.member_current_coverage
            WHERE is_currently_covered = TRUE
        ) AS DECIMAL(38,2)),

        CAST((
            SELECT SUM(member_count)
            FROM payer_01_dev.gold.membership_summary
        ) AS DECIMAL(38,2))


    UNION ALL


    SELECT

        'claim_spend_summary_claim_reconciliation',

        CAST((
            SELECT COUNT(*)
            FROM payer_01_dev.gold.claims_enriched
        ) AS DECIMAL(38,2)),

        CAST((
            SELECT SUM(claim_count)
            FROM payer_01_dev.gold.claim_spend_summary
        ) AS DECIMAL(38,2))


    UNION ALL


    SELECT

        'provider_summary_line_reconciliation',

        CAST((
            SELECT COUNT(*)
            FROM payer_01_dev.gold.claim_line_enriched
        ) AS DECIMAL(38,2)),

        CAST((
            SELECT SUM(claim_line_count)
            FROM payer_01_dev.gold.provider_utilization_summary
        ) AS DECIMAL(38,2))

)

SELECT

    check_name,

    expected_value,

    actual_value,

    actual_value
        - expected_value
        AS difference,

    CASE

        WHEN actual_value = expected_value
        THEN 'PASS'

        ELSE 'FAIL'

    END AS validation_status

FROM
    checks

ORDER BY
    check_name
;


-- ============================================================
-- 2. CLAIM SPEND FINANCIAL RECONCILIATION
--
-- All differences expected = 0.00
-- ============================================================

WITH detail AS (

    SELECT

        SUM(total_billed_amount) AS billed,

        SUM(total_allowed_amount) AS allowed,

        SUM(total_paid_amount) AS paid,

        SUM(member_responsibility_amount) AS member

    FROM
        payer_01_dev.gold.claims_enriched

),

summary AS (

    SELECT

        SUM(total_billed_amount) AS billed,

        SUM(total_allowed_amount) AS allowed,

        SUM(total_paid_amount) AS paid,

        SUM(member_responsibility_amount) AS member

    FROM
        payer_01_dev.gold.claim_spend_summary

)

SELECT

    'claim_spend_summary' AS reconciliation_name,

    s.billed - d.billed
        AS billed_difference,

    s.allowed - d.allowed
        AS allowed_difference,

    s.paid - d.paid
        AS paid_difference,

    s.member - d.member
        AS member_responsibility_difference,

    CASE

        WHEN
               ABS(s.billed - d.billed) <= 0.01
           AND ABS(s.allowed - d.allowed) <= 0.01
           AND ABS(s.paid - d.paid) <= 0.01
           AND ABS(s.member - d.member) <= 0.01

        THEN 'PASS'

        ELSE 'FAIL'

    END AS validation_status

FROM
    detail d

CROSS JOIN
    summary s
;


-- ============================================================
-- 3. PROVIDER SUMMARY FINANCIAL RECONCILIATION
--
-- All differences expected = 0.00
-- ============================================================

WITH detail AS (

    SELECT

        SUM(line_billed_amount) AS billed,

        SUM(line_allowed_amount) AS allowed,

        SUM(line_paid_amount) AS paid,

        SUM(line_member_responsibility_amount) AS member

    FROM
        payer_01_dev.gold.claim_line_enriched

),

summary AS (

    SELECT

        SUM(total_billed_amount) AS billed,

        SUM(total_allowed_amount) AS allowed,

        SUM(total_paid_amount) AS paid,

        SUM(member_responsibility_amount) AS member

    FROM
        payer_01_dev.gold.provider_utilization_summary

)

SELECT

    'provider_utilization_summary'
        AS reconciliation_name,

    s.billed - d.billed
        AS billed_difference,

    s.allowed - d.allowed
        AS allowed_difference,

    s.paid - d.paid
        AS paid_difference,

    s.member - d.member
        AS member_responsibility_difference,

    CASE

        WHEN
               ABS(s.billed - d.billed) <= 0.01
           AND ABS(s.allowed - d.allowed) <= 0.01
           AND ABS(s.paid - d.paid) <= 0.01
           AND ABS(s.member - d.member) <= 0.01

        THEN 'PASS'

        ELSE 'FAIL'

    END AS validation_status

FROM
    detail d

CROSS JOIN
    summary s
;


-- ============================================================
-- END OF GOLD END-TO-END RECONCILIATION
-- ============================================================