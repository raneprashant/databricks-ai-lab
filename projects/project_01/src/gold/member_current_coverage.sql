-- ============================================================
-- Project 01 - Healthcare Payer
-- Gold Layer
-- File: member_current_coverage.sql
--
-- Gold Table:
--   member_current_coverage
--
-- Grain:
--   Exactly one row per current Member.
--
-- Business As-Of Date:
--   2026-09-30
--
-- Purpose:
--   Create a Member 360 / current coverage snapshot by combining:
--
--     Member
--       +
--     selected Eligibility version
--       +
--     Product
--       +
--     Benefit Plan
--       +
--     Group
--       +
--     Subgroup
--
-- Important Eligibility rule:
--
--   We do NOT simply use source_current_record_flag.
--
--   We also do NOT first filter only Eligibility rows whose
--   coverage_end_date includes the as-of date.
--
--   Instead:
--
--     1. Find Eligibility versions that were applicable/known
--        by the as-of date.
--
--     2. Select the highest record_version for each Member.
--
--     3. Use update_ts as a tie-breaker.
--
--     4. After selecting the latest applicable version,
--        determine whether the Member is actually covered
--        on the as-of date.
--
-- This avoids incorrectly falling back to an older ACTIVE
-- Eligibility version after a newer termination or retro-term.
-- ============================================================


CREATE OR REFRESH MATERIALIZED VIEW member_current_coverage

COMMENT
'Gold Member 360 current coverage snapshot; one row per current Member'

AS


WITH


-- ============================================================
-- 1. REPORTING PARAMETER
--
-- We use the same business observation end date as the
-- synthetic generator:
--
--     DATA_END_DATE = 2026-09-30
--
-- We intentionally do NOT use current_date().
-- ============================================================

params AS (

    SELECT
        CAST(
            '2026-09-30'
            AS DATE
        ) AS as_of_date

),


-- ============================================================
-- 2. CURRENT MEMBER
--
-- Silver Member is SCD Type 2.
--
-- __END_AT IS NULL identifies the current business version.
--
-- This CTE establishes the Gold grain:
--
--     one current row per Member
-- ============================================================

current_member AS (

    SELECT

        member_id,
        family_id,
        subscriber_id,
        relationship_to_subscriber,

        first_name,
        middle_initial,
        last_name,

        date_of_birth,
        gender,
        marital_status,

        preferred_language,
        phone_number,
        email_address,

        member_status,

        deceased_flag,
        death_date

    FROM
        ${payer.catalog}.${payer.silver_schema}.member

    WHERE
        __END_AT IS NULL

),


-- ============================================================
-- 3. ELIGIBILITY VERSIONS APPLICABLE BY THE AS-OF DATE
--
-- IMPORTANT:
--
-- We intentionally do NOT filter:
--
--     coverage_end_date >= as_of_date
--
-- at this stage.
--
-- Example:
--
--     Version 2
--       ACTIVE
--       coverage_end_date = NULL
--
--     Version 3
--       RETRO_TERM
--       coverage_end_date = 2026-08-31
--
-- If we filtered Version 3 out before ranking,
-- Version 2 could incorrectly appear to be current coverage.
--
-- Therefore:
--
--     first determine latest applicable version,
--     then determine whether it represents active coverage.
-- ============================================================

applicable_eligibility_versions AS (

    SELECT

        e.*,

        p.as_of_date,

        ROW_NUMBER() OVER (

            PARTITION BY
                e.member_id

            ORDER BY

                e.record_version DESC,

                e.update_ts DESC,

                e.eligibility_id DESC

        ) AS eligibility_rank

    FROM

        ${payer.catalog}.${payer.silver_schema}.eligibility e

    CROSS JOIN

        params p

    WHERE

        -- Coverage must have started by the reporting date.
        e.coverage_start_date <= p.as_of_date

        -- The business event itself must be effective by
        -- the reporting date.
        AND (

            e.event_effective_date IS NULL

            OR e.event_effective_date <= p.as_of_date

        )

        -- The transaction must already have been received/
        -- known by the reporting date.
        AND (

            e.transaction_date IS NULL

            OR e.transaction_date <= p.as_of_date

        )

        -- A future Eligibility version should not replace
        -- coverage that applies to the reporting date.
        AND e.eligibility_status <> 'FUTURE'

),


-- ============================================================
-- 4. SELECT ONE ELIGIBILITY VERSION PER MEMBER
--
-- eligibility_rank = 1 gives us the most recent applicable
-- Eligibility version for each Member.
-- ============================================================

selected_eligibility AS (

    SELECT
        *

    FROM
        applicable_eligibility_versions

    WHERE
        eligibility_rank = 1

),


-- ============================================================
-- 5. CURRENT PRODUCT
-- ============================================================

current_product AS (

    SELECT

        product_id,
        product_code,
        product_name,

        line_of_business,
        product_type,

        market_segment,
        funding_type,
        network_model

    FROM
        ${payer.catalog}.${payer.silver_schema}.product

    WHERE
        __END_AT IS NULL

),


-- ============================================================
-- 6. CURRENT BENEFIT PLAN
-- ============================================================

current_benefit_plan AS (

    SELECT

        benefit_plan_id,
        product_id,

        plan_code,
        plan_name,

        metal_level,
        network_id,

        individual_deductible,
        family_deductible,

        individual_oop_max,
        family_oop_max,

        pcp_copay,
        specialist_copay,
        urgent_care_copay,
        er_copay,

        coinsurance_pct

    FROM
        ${payer.catalog}.${payer.silver_schema}.benefit_plan

    WHERE
        __END_AT IS NULL

),


-- ============================================================
-- 7. CURRENT GROUP
-- ============================================================

current_group AS (

    SELECT

        group_id,
        group_number,
        group_name,

        group_type,
        market_segment,
        funding_arrangement

    FROM
        ${payer.catalog}.${payer.silver_schema}.`group`

    WHERE
        __END_AT IS NULL

),


-- ============================================================
-- 8. CURRENT SUBGROUP
-- ============================================================

current_subgroup AS (

    SELECT

        subgroup_id,
        group_id,

        subgroup_code,
        subgroup_name,

        employee_class,
        benefit_plan_id

    FROM
        ${payer.catalog}.${payer.silver_schema}.subgroup

    WHERE
        __END_AT IS NULL

)


-- ============================================================
-- 9. FINAL GOLD MEMBER CURRENT COVERAGE
--
-- Start from Current Member and LEFT JOIN Eligibility.
--
-- This ensures:
--
--     Gold grain = one row per Member
--
-- A Member without active coverage is still retained.
-- ============================================================

SELECT


    -- ========================================================
    -- MEMBER ATTRIBUTES
    -- ========================================================

    m.member_id,

    m.family_id,

    m.subscriber_id,

    m.relationship_to_subscriber,

    m.first_name,

    m.middle_initial,

    m.last_name,

    m.date_of_birth,

    m.gender,

    m.marital_status,

    m.preferred_language,

    m.phone_number,

    m.email_address,

    m.member_status,

    m.deceased_flag,

    m.death_date,


    -- ========================================================
    -- CURRENT COVERAGE INDICATOR
    --
    -- The selected Eligibility version exists, is ACTIVE,
    -- and its coverage span includes the reporting date.
    -- ========================================================

    CASE

        WHEN

            e.eligibility_id IS NOT NULL

            AND e.eligibility_status = 'ACTIVE'

            AND e.coverage_start_date <= e.as_of_date

            AND (

                e.coverage_end_date IS NULL

                OR e.coverage_end_date >= e.as_of_date

            )

        THEN TRUE

        ELSE FALSE

    END AS is_currently_covered,


    -- ========================================================
    -- SELECTED ELIGIBILITY
    -- ========================================================

    e.eligibility_id,

    e.record_version
        AS eligibility_record_version,

    e.eligibility_status,

    e.event_type
        AS eligibility_event_type,

    e.event_effective_date,

    e.transaction_date,

    e.coverage_start_date,

    e.coverage_end_date,

    e.coverage_tier,


    -- ========================================================
    -- COVERAGE HIERARCHY KEYS
    -- ========================================================

    e.group_id,

    e.subgroup_id,

    e.product_id,

    e.benefit_plan_id,


    -- ========================================================
    -- PRODUCT
    -- ========================================================

    p.product_code,

    p.product_name,

    e.line_of_business,

    e.product_type,

    p.market_segment
        AS product_market_segment,

    p.funding_type,

    p.network_model,


    -- ========================================================
    -- BENEFIT PLAN
    -- ========================================================

    bp.plan_code,

    bp.plan_name,

    bp.metal_level,

    e.network_id,

    bp.individual_deductible,

    bp.family_deductible,

    bp.individual_oop_max,

    bp.family_oop_max,

    bp.pcp_copay,

    bp.specialist_copay,

    bp.urgent_care_copay,

    bp.er_copay,

    bp.coinsurance_pct,


    -- ========================================================
    -- GROUP
    -- ========================================================

    g.group_number,

    g.group_name,

    g.group_type,

    g.market_segment
        AS group_market_segment,

    g.funding_arrangement,


    -- ========================================================
    -- SUBGROUP
    -- ========================================================

    sg.subgroup_code,

    sg.subgroup_name,

    sg.employee_class,


    -- ========================================================
    -- COVERAGE FLAGS
    -- ========================================================

    e.medical_coverage_flag,

    e.pharmacy_coverage_flag,

    e.dental_coverage_flag,

    e.vision_coverage_flag,


    -- ========================================================
    -- REPORTING CONTEXT
    -- ========================================================

    CAST('2026-09-30' AS DATE) AS as_of_date


FROM

    current_member m


LEFT JOIN

    selected_eligibility e

    ON m.member_id = e.member_id


LEFT JOIN

    current_product p

    ON e.product_id = p.product_id


LEFT JOIN

    current_benefit_plan bp

    ON e.benefit_plan_id = bp.benefit_plan_id


LEFT JOIN

    current_group g

    ON e.group_id = g.group_id


LEFT JOIN

    current_subgroup sg

    ON e.subgroup_id = sg.subgroup_id

;