-- ============================================================
-- Project 01 - Healthcare Payer
-- Gold Layer
-- File: membership_summary.sql
--
-- Gold Table:
--   membership_summary
--
-- Grain:
--
--   as_of_date
--   + line_of_business
--   + product
--   + benefit_plan
--   + group
--
-- Purpose:
--   Enrollment / membership KPI reporting.
--
-- Source:
--   member_current_coverage
--
-- Important:
--   Only currently covered Members are included.
-- ============================================================


CREATE OR REFRESH MATERIALIZED VIEW membership_summary

COMMENT
'Gold current membership summary by product, plan, and group'

AS


SELECT


    -- ========================================================
    -- REPORTING GRAIN
    -- ========================================================

    as_of_date,

    line_of_business,


    product_id,

    product_code,

    product_name,

    product_type,


    benefit_plan_id,

    plan_code,

    plan_name,


    group_id,

    group_number,

    group_name,


    -- ========================================================
    -- MEMBERSHIP MEASURES
    -- ========================================================

    COUNT(*)
        AS member_count,


    SUM(
        CASE
            WHEN relationship_to_subscriber = 'SELF'
            THEN 1
            ELSE 0
        END
    ) AS subscriber_count,


    SUM(
        CASE
            WHEN relationship_to_subscriber <> 'SELF'
            THEN 1
            ELSE 0
        END
    ) AS dependent_count,


    COUNT(
        DISTINCT family_id
    ) AS family_count,


    COUNT(
        DISTINCT subscriber_id
    ) AS unique_subscriber_count,


    -- ========================================================
    -- COVERAGE COUNTS
    -- ========================================================

    SUM(
        CASE
            WHEN medical_coverage_flag = TRUE
            THEN 1
            ELSE 0
        END
    ) AS medical_covered_member_count,


    SUM(
        CASE
            WHEN pharmacy_coverage_flag = TRUE
            THEN 1
            ELSE 0
        END
    ) AS pharmacy_covered_member_count,


    SUM(
        CASE
            WHEN dental_coverage_flag = TRUE
            THEN 1
            ELSE 0
        END
    ) AS dental_covered_member_count,


    SUM(
        CASE
            WHEN vision_coverage_flag = TRUE
            THEN 1
            ELSE 0
        END
    ) AS vision_covered_member_count


FROM

    member_current_coverage


WHERE

    is_currently_covered = TRUE


GROUP BY

    as_of_date,

    line_of_business,

    product_id,

    product_code,

    product_name,

    product_type,

    benefit_plan_id,

    plan_code,

    plan_name,

    group_id,

    group_number,

    group_name

;