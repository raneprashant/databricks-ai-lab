-- ============================================================
-- Project 01 - Healthcare Payer
-- Dashboard Dataset
-- File: 04_provider_utilization_dataset.sql
--
-- Source:
--   Gold provider_utilization_summary
--
-- Purpose:
--   Provider Utilization dashboard dataset.
--
--   Gold already performs the aggregation and business logic.
--   Dashboard SQL remains intentionally thin.
-- ============================================================


SELECT

    -- Reporting period
    service_month,


    -- Coverage hierarchy
    line_of_business,

    product_id,
    product_code,
    product_name,

    benefit_plan_id,
    plan_code,
    plan_name,


    -- Practitioner
    practitioner_id,
    individual_npi,

    practitioner_first_name,
    practitioner_last_name,

    practitioner_primary_specialty,


    -- Practitioner role
    practitioner_role_id,

    role_type,
    role_specialty,


    -- Supplier
    supplier_id,
    supplier_name,


    -- Supplier location
    supplier_location_id,
    supplier_location_name,


    -- Service
    service_category,


    -- Utilization
    claim_line_count,
    claim_count,
    unique_member_count,
    total_units,


    -- Financials
    total_billed_amount,
    total_allowed_amount,
    total_paid_amount,
    member_responsibility_amount,


    -- Average financials
    average_billed_per_line,
    average_allowed_per_line,
    average_paid_per_line,


    -- Ratios
    allowed_to_billed_pct,
    paid_to_allowed_pct


FROM

    provider_utilization_summary
;