-- ============================================================
-- Project 01 - Healthcare Payer
-- Dashboard Dataset
-- File: 02_claim_spend_dataset.sql
--
-- Source:
--   Gold claim_spend_summary
--
-- Usage:
--   Executive Overview
--   Claims Dashboard
-- ============================================================

SELECT

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

    claim_count,

    unique_member_count,

    unique_supplier_count,

    total_billed_amount,

    total_allowed_amount,

    total_paid_amount,

    member_responsibility_amount,

    average_billed_per_claim,

    average_allowed_per_claim,

    average_paid_per_claim,

    allowed_to_billed_pct,

    paid_to_allowed_pct,

    member_responsibility_pct

FROM

    payer_01_dev.gold.claim_spend_summary
;