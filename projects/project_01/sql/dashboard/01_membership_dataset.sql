-- ============================================================
-- Project 01 - Healthcare Payer
-- Dashboard Dataset
-- File: 01_membership_dataset.sql
--
-- Source:
--   Gold membership_summary
--
-- Usage:
--   Executive Overview
--   Membership Dashboard
-- ============================================================

SELECT

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

    member_count,

    subscriber_count,

    dependent_count,

    family_count,

    unique_subscriber_count,

    medical_covered_member_count,

    pharmacy_covered_member_count,

    dental_covered_member_count,

    vision_covered_member_count

FROM

    payer_01_dev.gold.membership_summary
;