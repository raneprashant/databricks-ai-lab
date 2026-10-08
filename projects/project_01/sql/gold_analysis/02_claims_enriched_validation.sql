-- ============================================================
-- Project 01 - Healthcare Payer
-- Gold Validation
-- File: 02_claims_enriched_validation.sql
--
-- Gold Object:
--   payer_01_dev.gold.claims_enriched
--
-- Grain:
--   Exactly one row per CURRENT claim_id
--
-- Purpose:
--   Validate:
--     - Claim grain
--     - Gold vs Silver reconciliation
--     - Claim financials
--     - Exact Eligibility relationship
--     - Coverage dates
--     - Dimension enrichment
-- ============================================================



-- ============================================================
-- 1. ROW COUNT / CLAIM GRAIN
--
-- Expected after Batch 002:
--
--   total_rows      = 150170
--   distinct_claims = 150170
-- ============================================================

SELECT

    COUNT(*) AS total_rows,

    COUNT(
        DISTINCT claim_id
    ) AS distinct_claims

FROM

    payer_01_dev.gold.claims_enriched
;



-- ============================================================
-- 2. DUPLICATE CLAIM GRAIN
--
-- Expected:
--   duplicate_claim_count = 0
-- ============================================================

SELECT

    COUNT(*) AS duplicate_claim_count

FROM (

    SELECT

        claim_id

    FROM

        payer_01_dev.gold.claims_enriched

    GROUP BY

        claim_id

    HAVING

        COUNT(*) > 1

)
;



-- ============================================================
-- 3. GOLD CLAIM COUNT VS CURRENT SILVER CLAIM HEADER
--
-- Gold claims_enriched should contain exactly one row for every
-- current Silver Claim Header.
--
-- Expected:
--   difference = 0
-- ============================================================

WITH silver_count AS (

    SELECT

        COUNT(*) AS silver_current_claims

    FROM

        payer_01_dev.silver.claim_header

    WHERE

        __END_AT IS NULL

),

gold_count AS (

    SELECT

        COUNT(*) AS gold_claims

    FROM

        payer_01_dev.gold.claims_enriched

)

SELECT

    s.silver_current_claims,

    g.gold_claims,

    g.gold_claims
        - s.silver_current_claims
        AS difference

FROM

    silver_count s

CROSS JOIN

    gold_count g
;



-- ============================================================
-- 4. CURRENT SILVER CLAIMS MISSING FROM GOLD
--
-- Expected:
--   missing_from_gold = 0
-- ============================================================

SELECT

    COUNT(*) AS missing_from_gold

FROM

    payer_01_dev.silver.claim_header s

LEFT JOIN

    payer_01_dev.gold.claims_enriched g

    ON s.claim_id = g.claim_id

WHERE

    s.__END_AT IS NULL

    AND g.claim_id IS NULL
;



-- ============================================================
-- 5. GOLD CLAIMS MISSING FROM CURRENT SILVER
--
-- Expected:
--   missing_from_silver = 0
-- ============================================================

SELECT

    COUNT(*) AS missing_from_silver

FROM

    payer_01_dev.gold.claims_enriched g

LEFT JOIN

    payer_01_dev.silver.claim_header s

    ON g.claim_id = s.claim_id

    AND s.__END_AT IS NULL

WHERE

    s.claim_id IS NULL
;



-- ============================================================
-- 6. GOLD FINANCIAL TOTALS VS CURRENT SILVER
--
-- Enrichment must not duplicate or lose Claim Header amounts.
--
-- Expected:
--
--   claim_count_difference              = 0
--   billed_difference                   = 0.00
--   allowed_difference                  = 0.00
--   paid_difference                     = 0.00
--   member_responsibility_difference    = 0.00
-- ============================================================

WITH silver_totals AS (

    SELECT

        COUNT(*) AS claim_count,

        SUM(total_billed_amount)
            AS total_billed_amount,

        SUM(total_allowed_amount)
            AS total_allowed_amount,

        SUM(total_paid_amount)
            AS total_paid_amount,

        SUM(member_responsibility_amount)
            AS member_responsibility_amount

    FROM

        payer_01_dev.silver.claim_header

    WHERE

        __END_AT IS NULL

),

gold_totals AS (

    SELECT

        COUNT(*) AS claim_count,

        SUM(total_billed_amount)
            AS total_billed_amount,

        SUM(total_allowed_amount)
            AS total_allowed_amount,

        SUM(total_paid_amount)
            AS total_paid_amount,

        SUM(member_responsibility_amount)
            AS member_responsibility_amount

    FROM

        payer_01_dev.gold.claims_enriched

)

SELECT

    s.claim_count
        AS silver_claim_count,

    g.claim_count
        AS gold_claim_count,

    g.claim_count
        - s.claim_count
        AS claim_count_difference,


    s.total_billed_amount
        AS silver_billed,

    g.total_billed_amount
        AS gold_billed,

    g.total_billed_amount
        - s.total_billed_amount
        AS billed_difference,


    s.total_allowed_amount
        AS silver_allowed,

    g.total_allowed_amount
        AS gold_allowed,

    g.total_allowed_amount
        - s.total_allowed_amount
        AS allowed_difference,


    s.total_paid_amount
        AS silver_paid,

    g.total_paid_amount
        AS gold_paid,

    g.total_paid_amount
        - s.total_paid_amount
        AS paid_difference,


    s.member_responsibility_amount
        AS silver_member_responsibility,

    g.member_responsibility_amount
        AS gold_member_responsibility,

    g.member_responsibility_amount
        - s.member_responsibility_amount
        AS member_responsibility_difference

FROM

    silver_totals s

CROSS JOIN

    gold_totals g
;



-- ============================================================
-- 7. CLAIM FINANCIAL BUSINESS RULES
--
-- Expected:
--   every issue_count = 0
-- ============================================================

SELECT

    'billed_less_than_allowed'
        AS check_name,

    COUNT(*) AS issue_count

FROM

    payer_01_dev.gold.claims_enriched

WHERE

    total_billed_amount
        < total_allowed_amount


UNION ALL


SELECT

    'allowed_less_than_paid',

    COUNT(*)

FROM

    payer_01_dev.gold.claims_enriched

WHERE

    total_allowed_amount
        < total_paid_amount


UNION ALL


SELECT

    'negative_paid_amount',

    COUNT(*)

FROM

    payer_01_dev.gold.claims_enriched

WHERE

    total_paid_amount < 0


UNION ALL


SELECT

    'negative_member_responsibility',

    COUNT(*)

FROM

    payer_01_dev.gold.claims_enriched

WHERE

    member_responsibility_amount < 0


UNION ALL


SELECT

    'allowed_paid_member_reconciliation',

    COUNT(*)

FROM

    payer_01_dev.gold.claims_enriched

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
-- 8. EXACT ELIGIBILITY EVENT EXISTS
--
-- Claim Header stores eligibility_id.
--
-- Gold must enrich from that exact Eligibility event,
-- not from the Member's current Eligibility.
--
-- Expected:
--   missing_eligibility_count = 0
-- ============================================================

SELECT

    COUNT(*) AS missing_eligibility_count

FROM

    payer_01_dev.gold.claims_enriched g

LEFT JOIN

    payer_01_dev.silver.eligibility e

    ON g.eligibility_id = e.eligibility_id

WHERE

    e.eligibility_id IS NULL
;



-- ============================================================
-- 9. CLAIM VS EXACT ELIGIBILITY CONSISTENCY
--
-- Expected:
--   eligibility_mismatch_count = 0
-- ============================================================

SELECT

    COUNT(*) AS eligibility_mismatch_count

FROM

    payer_01_dev.gold.claims_enriched g

JOIN

    payer_01_dev.silver.eligibility e

    ON g.eligibility_id = e.eligibility_id

WHERE

       g.member_id <> e.member_id

    OR g.eligibility_record_version
       <> e.record_version

    OR g.group_id <> e.group_id

    OR g.subgroup_id <> e.subgroup_id

    OR g.product_id <> e.product_id

    OR g.benefit_plan_id <> e.benefit_plan_id
;



-- ============================================================
-- 10. CLAIM SERVICE DATE WITHIN ELIGIBILITY COVERAGE
--
-- Expected:
--   claim_outside_coverage_count = 0
-- ============================================================

SELECT

    COUNT(*) AS claim_outside_coverage_count

FROM

    payer_01_dev.gold.claims_enriched

WHERE

       service_from_date < coverage_start_date

    OR (

           coverage_end_date IS NOT NULL

       AND service_to_date > coverage_end_date

    )
;



-- ============================================================
-- 11. SERVICE MONTH VALIDATION
--
-- service_month should always equal the first day of the
-- service_from_date month.
--
-- Expected:
--   invalid_service_month_count = 0
-- ============================================================

SELECT

    COUNT(*) AS invalid_service_month_count

FROM

    payer_01_dev.gold.claims_enriched

WHERE

    service_month
    <>
    CAST(

        DATE_TRUNC(
            'MONTH',
            service_from_date
        )

        AS DATE

    )
;



-- ============================================================
-- 12. MISSING MEMBER ENRICHMENT
--
-- Expected:
--   missing_member_enrichment_count = 0
-- ============================================================

SELECT

    COUNT(*) AS missing_member_enrichment_count

FROM

    payer_01_dev.gold.claims_enriched

WHERE

    member_last_name IS NULL
;



-- ============================================================
-- 13. MISSING COVERAGE REFERENCE ENRICHMENT
--
-- Normally:
--   product_missing = 0
--   plan_missing    = 0
--   group_missing   = 0
--
-- subgroup_missing should also normally be 0, but if non-zero,
-- compare it to the known original synthetic Subgroup defect.
-- ============================================================

SELECT

    SUM(
        CASE
            WHEN product_name IS NULL
            THEN 1
            ELSE 0
        END
    ) AS product_missing,

    SUM(
        CASE
            WHEN plan_name IS NULL
            THEN 1
            ELSE 0
        END
    ) AS plan_missing,

    SUM(
        CASE
            WHEN group_name IS NULL
            THEN 1
            ELSE 0
        END
    ) AS group_missing,

    SUM(
        CASE
            WHEN subgroup_name IS NULL
            THEN 1
            ELSE 0
        END
    ) AS subgroup_missing

FROM

    payer_01_dev.gold.claims_enriched
;



-- ============================================================
-- 14. MISSING PROVIDER ENRICHMENT
--
-- Expected:
--   normally 0 for each column.
-- ============================================================

SELECT

    SUM(
        CASE
            WHEN practitioner_last_name IS NULL
            THEN 1
            ELSE 0
        END
    ) AS practitioner_missing,

    SUM(
        CASE
            WHEN role_type IS NULL
            THEN 1
            ELSE 0
        END
    ) AS practitioner_role_missing,

    SUM(
        CASE
            WHEN supplier_name IS NULL
            THEN 1
            ELSE 0
        END
    ) AS supplier_missing,

    SUM(
        CASE
            WHEN supplier_location_name IS NULL
            THEN 1
            ELSE 0
        END
    ) AS supplier_location_missing

FROM

    payer_01_dev.gold.claims_enriched
;



-- ============================================================
-- 15. CLAIM STATUS / TYPE DISTRIBUTION
--
-- Informational
-- ============================================================

SELECT

    claim_status,

    claim_type,

    COUNT(*) AS claim_count,

    SUM(total_billed_amount)
        AS total_billed_amount,

    SUM(total_allowed_amount)
        AS total_allowed_amount,

    SUM(total_paid_amount)
        AS total_paid_amount,

    SUM(member_responsibility_amount)
        AS member_responsibility_amount

FROM

    payer_01_dev.gold.claims_enriched

GROUP BY

    claim_status,

    claim_type

ORDER BY

    claim_status,

    claim_type
;



-- ============================================================
-- 16. LINE OF BUSINESS / PRODUCT DISTRIBUTION
--
-- Informational
-- ============================================================

SELECT

    line_of_business,

    product_type,

    COUNT(*) AS claim_count,

    COUNT(
        DISTINCT member_id
    ) AS unique_members,

    SUM(total_allowed_amount)
        AS total_allowed_amount,

    SUM(total_paid_amount)
        AS total_paid_amount

FROM

    payer_01_dev.gold.claims_enriched

GROUP BY

    line_of_business,

    product_type

ORDER BY

    line_of_business,

    product_type
;



-- ============================================================
-- END OF 02_claims_enriched_validation.sql
-- ============================================================