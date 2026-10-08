-- ============================================================
-- Project 01 - Healthcare Payer
-- Gold Layer
-- File: claims_enriched.sql
--
-- Gold Table:
--   claims_enriched
--
-- Grain:
--   Exactly one row per CURRENT Claim Header / claim_id.
--
-- Purpose:
--   Create the primary claim-level analytical fact by enriching
--   the current Claim Header with:
--
--     Member
--     Exact Eligibility event
--     Product
--     Benefit Plan
--     Group
--     Subgroup
--     Practitioner
--     Practitioner Role
--     Supplier
--     Supplier Location
--
-- Important:
--
--   Claim Header is SCD Type 2 in Silver.
--
--   Only:
--
--       __END_AT IS NULL
--
--   is used for standard Gold reporting.
--
--   Historical Claim versions remain in Silver and are not mixed
--   into this Gold mart, preventing double-counting.
--
--   Claim Line is intentionally NOT joined here because that
--   would change the grain from one Claim to multiple Claim Lines.
-- ============================================================


CREATE OR REFRESH MATERIALIZED VIEW claims_enriched

COMMENT
'Gold current Claim Header analytical mart; one row per current claim_id'

AS


WITH


-- ============================================================
-- 1. CURRENT CLAIM HEADER
-- ============================================================

current_claim_header AS (

    SELECT
        *
    FROM
        ${payer.catalog}.${payer.silver_schema}.claim_header
    WHERE
        __END_AT IS NULL

),


-- ============================================================
-- 2. CURRENT MEMBER
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

        member_status,
        deceased_flag

    FROM
        ${payer.catalog}.${payer.silver_schema}.member

    WHERE
        __END_AT IS NULL

),


-- ============================================================
-- 3. CURRENT PRODUCT
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
-- 4. CURRENT BENEFIT PLAN
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
-- 5. CURRENT GROUP
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
-- 6. CURRENT SUBGROUP
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

),


-- ============================================================
-- 7. CURRENT PRACTITIONER
-- ============================================================

current_practitioner AS (

    SELECT

        practitioner_id,
        individual_npi,

        first_name,
        middle_initial,
        last_name,
        suffix,

        credential,
        primary_specialty,

        license_number,
        license_state,

        board_certified_flag,
        practitioner_status

    FROM
        ${payer.catalog}.${payer.silver_schema}.practitioner

    WHERE
        __END_AT IS NULL

),


-- ============================================================
-- 8. CURRENT PRACTITIONER ROLE
-- ============================================================

current_practitioner_role AS (

    SELECT

        practitioner_role_id,
        practitioner_id,
        supplier_id,
        supplier_location_id,

        role_type,
        role_specialty,

        pcp_flag,
        primary_affiliation_flag,
        panel_status,
        accepting_new_patients_flag,

        role_status

    FROM
        ${payer.catalog}.${payer.silver_schema}.practitioner_role

    WHERE
        __END_AT IS NULL

),


-- ============================================================
-- 9. CURRENT SUPPLIER
-- ============================================================

current_supplier AS (

    SELECT

        supplier_id,
        supplier_name,
        supplier_type,

        tax_id,
        organization_npi,

        ownership_type,
        contract_status

    FROM
        ${payer.catalog}.${payer.silver_schema}.supplier

    WHERE
        __END_AT IS NULL

),


-- ============================================================
-- 10. CURRENT SUPPLIER LOCATION
-- ============================================================

current_supplier_location AS (

    SELECT

        supplier_location_id,
        supplier_id,

        location_name,
        location_type,

        facility_npi,
        place_of_service_code

    FROM
        ${payer.catalog}.${payer.silver_schema}.supplier_location

    WHERE
        __END_AT IS NULL

)


-- ============================================================
-- 11. FINAL GOLD CLAIM
-- ============================================================

SELECT


    -- ========================================================
    -- CLAIM IDENTIFIERS
    -- ========================================================

    ch.claim_id,

    ch.member_id,

    ch.eligibility_id,

    ch.eligibility_record_version,

    ch.subscriber_id,

    ch.family_id,


    -- ========================================================
    -- CLAIM SERVICE / PROCESSING DATES
    -- ========================================================

    ch.service_from_date,

    ch.service_to_date,

    CAST(
        DATE_TRUNC(
            'MONTH',
            ch.service_from_date
        )
        AS DATE
    ) AS service_month,

    ch.admission_date,

    ch.discharge_date,

    ch.received_date,

    ch.adjudication_date,


    -- ========================================================
    -- CLAIM CLASSIFICATION
    -- ========================================================

    ch.claim_type,

    ch.claim_status,

    ch.network_status,

    ch.network_tier,

    ch.place_of_service_code,

    ch.primary_diagnosis_code,

    ch.primary_diagnosis_category,


    -- ========================================================
    -- MEMBER
    -- ========================================================

    m.relationship_to_subscriber,

    m.first_name
        AS member_first_name,

    m.middle_initial
        AS member_middle_initial,

    m.last_name
        AS member_last_name,

    m.date_of_birth
        AS member_date_of_birth,

    m.gender
        AS member_gender,

    m.member_status,

    m.deceased_flag,


    -- ========================================================
    -- EXACT ELIGIBILITY EVENT REFERENCED BY THE CLAIM
    --
    -- This is NOT the Member's current Eligibility.
    --
    -- Claims must retain the coverage context used when the
    -- Claim was generated/adjudicated.
    -- ========================================================

    e.eligibility_status,

    e.event_type
        AS eligibility_event_type,

    e.event_effective_date
        AS eligibility_event_effective_date,

    e.coverage_start_date,

    e.coverage_end_date,

    e.coverage_tier,

    e.medical_coverage_flag,

    e.pharmacy_coverage_flag,

    e.dental_coverage_flag,

    e.vision_coverage_flag,


    -- ========================================================
    -- COVERAGE HIERARCHY KEYS
    -- ========================================================

    ch.group_id,

    ch.subgroup_id,

    ch.product_id,

    ch.benefit_plan_id,


    -- ========================================================
    -- PRODUCT
    -- ========================================================

    p.product_code,

    p.product_name,

    ch.line_of_business,

    ch.product_type,

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

    ch.network_id,

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
    -- PROVIDER KEYS
    -- ========================================================

    ch.practitioner_role_id,

    ch.practitioner_id,

    ch.supplier_id,

    ch.supplier_location_id,


    -- ========================================================
    -- PRACTITIONER
    -- ========================================================

    pr.individual_npi,

    pr.first_name
        AS practitioner_first_name,

    pr.middle_initial
        AS practitioner_middle_initial,

    pr.last_name
        AS practitioner_last_name,

    pr.suffix
        AS practitioner_suffix,

    pr.credential
        AS practitioner_credential,

    pr.primary_specialty
        AS practitioner_primary_specialty,

    pr.license_number
        AS practitioner_license_number,

    pr.license_state
        AS practitioner_license_state,

    pr.board_certified_flag,

    pr.practitioner_status,


    -- ========================================================
    -- PRACTITIONER ROLE
    -- ========================================================

    role.role_type,

    role.role_specialty,

    role.pcp_flag,

    role.primary_affiliation_flag,

    role.panel_status,

    role.accepting_new_patients_flag,

    role.role_status,


    -- ========================================================
    -- SUPPLIER
    -- ========================================================

    s.supplier_name,

    s.supplier_type,

    s.tax_id
        AS supplier_tax_id,

    s.organization_npi,

    s.ownership_type,

    s.contract_status,


    -- ========================================================
    -- SUPPLIER LOCATION
    -- ========================================================

    sl.location_name
        AS supplier_location_name,

    sl.location_type
        AS supplier_location_type,

    sl.facility_npi,

    sl.place_of_service_code
        AS location_place_of_service_code,


    -- ========================================================
    -- CLAIM FINANCIALS
    -- ========================================================

    ch.claim_line_count,

    ch.total_billed_amount,

    ch.total_allowed_amount,

    ch.total_paid_amount,

    ch.member_responsibility_amount


FROM

    current_claim_header ch


-- Exact historical/event Eligibility row referenced by Claim.
LEFT JOIN

    ${payer.catalog}.${payer.silver_schema}.eligibility e

    ON ch.eligibility_id = e.eligibility_id


LEFT JOIN

    current_member m

    ON ch.member_id = m.member_id


LEFT JOIN

    current_product p

    ON ch.product_id = p.product_id


LEFT JOIN

    current_benefit_plan bp

    ON ch.benefit_plan_id = bp.benefit_plan_id


LEFT JOIN

    current_group g

    ON ch.group_id = g.group_id


LEFT JOIN

    current_subgroup sg

    ON ch.subgroup_id = sg.subgroup_id


LEFT JOIN

    current_practitioner pr

    ON ch.practitioner_id = pr.practitioner_id


LEFT JOIN

    current_practitioner_role role

    ON ch.practitioner_role_id =
       role.practitioner_role_id


LEFT JOIN

    current_supplier s

    ON ch.supplier_id = s.supplier_id


LEFT JOIN

    current_supplier_location sl

    ON ch.supplier_location_id =
       sl.supplier_location_id

;