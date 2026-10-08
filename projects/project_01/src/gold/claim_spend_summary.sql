-- ============================================================
-- Project 01 - Healthcare Payer
-- Gold Layer
-- File: claim_spend_summary.sql
--
-- Gold Table:
--   claim_spend_summary
--
-- Grain:
--
--   service_month
--   + line_of_business
--   + product
--   + benefit_plan
--   + claim_status
--   + network_status
--
-- Purpose:
--   Monthly Claim financial and utilization reporting.
--
-- Source:
--   claims_enriched
--
-- Important:
--   claims_enriched is one row per Claim, so Claim Header
--   financial totals can safely be aggregated here.
-- ============================================================


CREATE OR REFRESH MATERIALIZED VIEW claim_spend_summary

COMMENT
'Gold monthly Claim spend summary by product, plan, status, and network'

AS


SELECT


    -- ========================================================
    -- REPORTING GRAIN
    -- ========================================================

    service_month,

    line_of_business,


    product_id,

    product_code,

    product_name,

    product_type,


    benefit_plan_id,

    plan_code,

    plan_name,


    claim_status,

    network_status,


    -- ========================================================
    -- UTILIZATION COUNTS
    -- ========================================================

    COUNT(*)
        AS claim_count,


    COUNT(
        DISTINCT member_id
    ) AS unique_member_count,


    COUNT(
        DISTINCT supplier_id
    ) AS unique_supplier_count,


    -- ========================================================
    -- FINANCIAL TOTALS
    -- ========================================================

    SUM(total_billed_amount)
        AS total_billed_amount,


    SUM(total_allowed_amount)
        AS total_allowed_amount,


    SUM(total_paid_amount)
        AS total_paid_amount,


    SUM(member_responsibility_amount)
        AS member_responsibility_amount,


    -- ========================================================
    -- AVERAGE CLAIM METRICS
    -- ========================================================

    ROUND(
        AVG(total_billed_amount),
        2
    ) AS average_billed_per_claim,


    ROUND(
        AVG(total_allowed_amount),
        2
    ) AS average_allowed_per_claim,


    ROUND(
        AVG(total_paid_amount),
        2
    ) AS average_paid_per_claim,


    -- ========================================================
    -- FINANCIAL RATIOS
    -- ========================================================

    ROUND(

        100.0
        * SUM(total_allowed_amount)

        / NULLIF(
            SUM(total_billed_amount),
            0
        ),

        2

    ) AS allowed_to_billed_pct,


    ROUND(

        100.0
        * SUM(total_paid_amount)

        / NULLIF(
            SUM(total_allowed_amount),
            0
        ),

        2

    ) AS paid_to_allowed_pct,


    ROUND(

        100.0
        * SUM(member_responsibility_amount)

        / NULLIF(
            SUM(total_allowed_amount),
            0
        ),

        2

    ) AS member_responsibility_pct


FROM

    claims_enriched


GROUP BY

    service_month,

    line_of_business,

    product_id,

    product_code,

    product_name,

    product_type,

    benefit_plan_id,

    plan_code,

    plan_name,

    claim_status,

    network_status

;