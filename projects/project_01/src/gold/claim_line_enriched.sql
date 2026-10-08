-- ============================================================
-- Project 01 - Healthcare Payer
-- Gold Layer
-- File: claim_line_enriched.sql
--
-- Gold Table:
--   claim_line_enriched
--
-- Grain:
--   Exactly one row per CURRENT Claim Line / claim_line_id.
--
-- Purpose:
--   Provide procedure/service-level Claim analytics while
--   reusing the conformed Claim context already created in:
--
--       claims_enriched
--
-- Important:
--
--   Silver Claim Line is SCD Type 2.
--
--   Only:
--
--       __END_AT IS NULL
--
--   is used for normal Gold reporting.
--
--   Line-level financials are clearly prefixed with "line_".
--   Header-level Claim totals are clearly prefixed with
--   "claim_total_" to avoid accidental double counting.
-- ============================================================


CREATE OR REFRESH MATERIALIZED VIEW claim_line_enriched

COMMENT
'Gold current Claim Line analytical mart; one row per current claim_line_id'

AS


WITH


-- ============================================================
-- 1. CURRENT SILVER CLAIM LINE
-- ============================================================

current_claim_line AS (

    SELECT

        claim_line_id,

        claim_id,

        line_number,

        service_date,

        CAST(
            DATE_TRUNC(
                'MONTH',
                service_date
            )
            AS DATE
        ) AS service_month,

        service_category,

        procedure_code,

        revenue_code,

        diagnosis_code,

        diagnosis_category,

        units,

        line_status,

        billed_amount,

        allowed_amount,

        paid_amount,

        member_responsibility_amount

    FROM

        ${payer.catalog}.${payer.silver_schema}.claim_line

    WHERE

        __END_AT IS NULL

)


-- ============================================================
-- 2. FINAL CLAIM LINE ENRICHED
--
-- claims_enriched already contains:
--
--   Member
--   Eligibility
--   Product / Plan / Group / Subgroup
--   Practitioner
--   Practitioner Role
--   Supplier
--   Supplier Location
--   Claim Header context
--
-- Therefore, we reuse it rather than repeating all those joins.
-- ============================================================

SELECT


    -- ========================================================
    -- CLAIM LINE IDENTIFIERS
    -- ========================================================

    cl.claim_line_id,

    cl.claim_id,

    cl.line_number,


    -- ========================================================
    -- LINE SERVICE DETAIL
    -- ========================================================

    cl.service_date,

    cl.service_month,

    cl.service_category,

    cl.procedure_code,

    cl.revenue_code,

    cl.diagnosis_code,

    cl.diagnosis_category,

    cl.units,

    cl.line_status,


    -- ========================================================
    -- LINE FINANCIALS
    -- ========================================================

    cl.billed_amount
        AS line_billed_amount,

    cl.allowed_amount
        AS line_allowed_amount,

    cl.paid_amount
        AS line_paid_amount,

    cl.member_responsibility_amount
        AS line_member_responsibility_amount,


    -- ========================================================
    -- MEMBER
    -- ========================================================

    ce.member_id,

    ce.subscriber_id,

    ce.family_id,

    ce.relationship_to_subscriber,

    ce.member_first_name,

    ce.member_middle_initial,

    ce.member_last_name,

    ce.member_date_of_birth,

    ce.member_gender,

    ce.member_status,

    ce.deceased_flag,


    -- ========================================================
    -- EXACT ELIGIBILITY CONTEXT USED BY CLAIM
    -- ========================================================

    ce.eligibility_id,

    ce.eligibility_record_version,

    ce.eligibility_status,

    ce.eligibility_event_type,

    ce.eligibility_event_effective_date,

    ce.coverage_start_date,

    ce.coverage_end_date,

    ce.coverage_tier,

    ce.medical_coverage_flag,

    ce.pharmacy_coverage_flag,

    ce.dental_coverage_flag,

    ce.vision_coverage_flag,


    -- ========================================================
    -- COVERAGE HIERARCHY
    -- ========================================================

    ce.group_id,

    ce.group_number,

    ce.group_name,

    ce.group_type,

    ce.group_market_segment,

    ce.funding_arrangement,


    ce.subgroup_id,

    ce.subgroup_code,

    ce.subgroup_name,

    ce.employee_class,


    ce.product_id,

    ce.product_code,

    ce.product_name,

    ce.line_of_business,

    ce.product_type,

    ce.product_market_segment,

    ce.funding_type,

    ce.network_model,


    ce.benefit_plan_id,

    ce.plan_code,

    ce.plan_name,

    ce.metal_level,

    ce.network_id,


    -- ========================================================
    -- CLAIM HEADER CONTEXT
    -- ========================================================

    ce.claim_type,

    ce.claim_status,

    ce.network_status,

    ce.network_tier,

    ce.place_of_service_code,

    ce.service_from_date
        AS claim_service_from_date,

    ce.service_to_date
        AS claim_service_to_date,

    ce.received_date,

    ce.adjudication_date,

    ce.primary_diagnosis_code
        AS claim_primary_diagnosis_code,

    ce.primary_diagnosis_category
        AS claim_primary_diagnosis_category,


    -- ========================================================
    -- PROVIDER
    -- ========================================================

    ce.practitioner_role_id,

    ce.practitioner_id,

    ce.individual_npi,

    ce.practitioner_first_name,

    ce.practitioner_middle_initial,

    ce.practitioner_last_name,

    ce.practitioner_credential,

    ce.practitioner_primary_specialty,

    ce.role_type,

    ce.role_specialty,

    ce.pcp_flag,

    ce.role_status,


    -- ========================================================
    -- SUPPLIER / LOCATION
    -- ========================================================

    ce.supplier_id,

    ce.supplier_name,

    ce.supplier_type,

    ce.organization_npi,

    ce.supplier_location_id,

    ce.supplier_location_name,

    ce.supplier_location_type,

    ce.facility_npi,


    -- ========================================================
    -- CLAIM HEADER TOTALS
    --
    -- These values repeat for every Claim Line belonging to
    -- the Claim.
    --
    -- DO NOT sum these columns at Claim Line grain unless the
    -- data is first reduced to one row per claim_id.
    -- ========================================================

    ce.claim_line_count,

    ce.total_billed_amount
        AS claim_total_billed_amount,

    ce.total_allowed_amount
        AS claim_total_allowed_amount,

    ce.total_paid_amount
        AS claim_total_paid_amount,

    ce.member_responsibility_amount
        AS claim_total_member_responsibility_amount


FROM

    current_claim_line cl


LEFT JOIN

    claims_enriched ce

    ON cl.claim_id = ce.claim_id

;