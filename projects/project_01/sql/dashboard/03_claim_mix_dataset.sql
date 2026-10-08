-- ============================================================
-- Project 01 - Healthcare Payer
-- Dashboard Dataset
-- File: 03_claim_mix_dataset.sql
--
-- Source:
--   Gold claims_enriched
--
-- Purpose:
--   Claim-type, diagnosis, place-of-service and network analysis.
-- ============================================================

SELECT

    service_month,

    line_of_business,

    product_id,
    product_name,

    benefit_plan_id,
    plan_name,

    claim_type,

    claim_status,

    network_status,

    network_tier,

    place_of_service_code,

    primary_diagnosis_category,

    COUNT(*) AS claim_count,

    COUNT(
        DISTINCT member_id
    ) AS unique_member_count,

    COUNT(
        DISTINCT practitioner_id
    ) AS unique_practitioner_count,

    COUNT(
        DISTINCT supplier_id
    ) AS unique_supplier_count,

    SUM(total_billed_amount)
        AS total_billed_amount,

    SUM(total_allowed_amount)
        AS total_allowed_amount,

    SUM(total_paid_amount)
        AS total_paid_amount,

    SUM(member_responsibility_amount)
        AS member_responsibility_amount

FROM

    claims_enriched

GROUP BY

    service_month,

    line_of_business,

    product_id,
    product_name,

    benefit_plan_id,
    plan_name,

    claim_type,

    claim_status,

    network_status,

    network_tier,

    place_of_service_code,

    primary_diagnosis_category
;