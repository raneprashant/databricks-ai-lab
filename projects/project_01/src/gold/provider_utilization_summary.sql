-- ============================================================
-- Project 01 - Healthcare Payer
-- Gold Layer
-- File: provider_utilization_summary.sql
--
-- Gold Table:
--   provider_utilization_summary
--
-- Grain:
--
--   service_month
--   + line_of_business
--   + product
--   + benefit_plan
--   + practitioner
--   + practitioner_role
--   + supplier
--   + supplier_location
--   + service_category
--
-- Purpose:
--   Provider utilization, service volume, and financial
--   reporting with coverage hierarchy dimensions included.
--
-- Why Product / Plan are included:
--   This allows provider utilization to be filtered and analyzed
--   consistently by Line of Business, Product, and Benefit Plan.
--
-- Source:
--   claim_line_enriched
--
-- Important:
--   Financial aggregation uses LINE-level amounts.
--   Claim Header totals are NOT aggregated here.
-- ============================================================


CREATE OR REFRESH MATERIALIZED VIEW provider_utilization_summary

COMMENT
'Gold monthly provider utilization summary by coverage, provider, location, and service category'

AS


SELECT


    -- ========================================================
    -- REPORTING PERIOD
    -- ========================================================

    service_month,


    -- ========================================================
    -- COVERAGE / PRODUCT HIERARCHY
    --
    -- Added so Provider analytics can be filtered consistently
    -- by the same business dimensions used throughout Gold.
    -- ========================================================

    line_of_business,


    product_id,

    product_code,

    product_name,


    benefit_plan_id,

    plan_code,

    plan_name,


    -- ========================================================
    -- PRACTITIONER
    -- ========================================================

    practitioner_id,

    individual_npi,

    practitioner_first_name,

    practitioner_last_name,

    practitioner_primary_specialty,


    -- ========================================================
    -- PRACTITIONER ROLE
    -- ========================================================

    practitioner_role_id,

    role_type,

    role_specialty,


    -- ========================================================
    -- SUPPLIER
    -- ========================================================

    supplier_id,

    supplier_name,


    -- ========================================================
    -- SUPPLIER LOCATION
    -- ========================================================

    supplier_location_id,

    supplier_location_name,


    -- ========================================================
    -- SERVICE
    -- ========================================================

    service_category,


    -- ========================================================
    -- UTILIZATION COUNTS
    -- ========================================================

    COUNT(*)
        AS claim_line_count,


    COUNT(
        DISTINCT claim_id
    ) AS claim_count,


    COUNT(
        DISTINCT member_id
    ) AS unique_member_count,


    SUM(units)
        AS total_units,


    -- ========================================================
    -- LINE-LEVEL FINANCIAL TOTALS
    -- ========================================================

    SUM(line_billed_amount)
        AS total_billed_amount,


    SUM(line_allowed_amount)
        AS total_allowed_amount,


    SUM(line_paid_amount)
        AS total_paid_amount,


    SUM(line_member_responsibility_amount)
        AS member_responsibility_amount,


    -- ========================================================
    -- AVERAGE LINE FINANCIALS
    -- ========================================================

    ROUND(
        AVG(line_billed_amount),
        2
    ) AS average_billed_per_line,


    ROUND(
        AVG(line_allowed_amount),
        2
    ) AS average_allowed_per_line,


    ROUND(
        AVG(line_paid_amount),
        2
    ) AS average_paid_per_line,


    -- ========================================================
    -- FINANCIAL RATIOS
    -- ========================================================

    ROUND(

        100.0
        * SUM(line_allowed_amount)

        / NULLIF(
            SUM(line_billed_amount),
            0
        ),

        2

    ) AS allowed_to_billed_pct,


    ROUND(

        100.0
        * SUM(line_paid_amount)

        / NULLIF(
            SUM(line_allowed_amount),
            0
        ),

        2

    ) AS paid_to_allowed_pct


FROM

    claim_line_enriched


GROUP BY

    service_month,


    line_of_business,


    product_id,

    product_code,

    product_name,


    benefit_plan_id,

    plan_code,

    plan_name,


    practitioner_id,

    individual_npi,

    practitioner_first_name,

    practitioner_last_name,

    practitioner_primary_specialty,


    practitioner_role_id,

    role_type,

    role_specialty,


    supplier_id,

    supplier_name,


    supplier_location_id,

    supplier_location_name,


    service_category

;