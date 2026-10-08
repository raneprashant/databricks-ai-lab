-- ============================================================
-- Project 01 - Healthcare Payer
-- Gold Validation
-- File: 04_membership_summary_validation.sql
-- ============================================================


-- ============================================================
-- 1. SUMMARY ROW COUNT
--
-- Current expected count = 1228
-- ============================================================

SELECT

    COUNT(*) AS summary_rows

FROM
    payer_01_dev.gold.membership_summary
;


-- ============================================================
-- 2. DUPLICATE SUMMARY GRAIN
--
-- Expected = 0
-- ============================================================

SELECT

    COUNT(*) AS duplicate_summary_grain_count

FROM (

    SELECT

        as_of_date,
        line_of_business,
        product_id,
        benefit_plan_id,
        group_id

    FROM
        payer_01_dev.gold.membership_summary

    GROUP BY

        as_of_date,
        line_of_business,
        product_id,
        benefit_plan_id,
        group_id

    HAVING
        COUNT(*) > 1

)
;


-- ============================================================
-- 3. SUMMARY MEMBER COUNT VS DETAIL
--
-- Expected difference = 0
-- ============================================================

WITH detail AS (

    SELECT

        COUNT(*) AS covered_members

    FROM
        payer_01_dev.gold.member_current_coverage

    WHERE
        is_currently_covered = TRUE

),

summary AS (

    SELECT

        SUM(member_count)
            AS covered_members

    FROM
        payer_01_dev.gold.membership_summary

)

SELECT

    d.covered_members
        AS detail_covered_members,

    s.covered_members
        AS summary_covered_members,

    s.covered_members
        - d.covered_members
        AS difference

FROM
    detail d

CROSS JOIN
    summary s
;


-- ============================================================
-- 4. SUBSCRIBER + DEPENDENT RECONCILIATION
--
-- Expected issue_count = 0
-- ============================================================

SELECT

    COUNT(*) AS issue_count

FROM
    payer_01_dev.gold.membership_summary

WHERE

    member_count
    <>
    subscriber_count + dependent_count
;


-- ============================================================
-- 5. COVERAGE COUNTS MUST NOT EXCEED MEMBERS
--
-- Expected every issue_count = 0
-- ============================================================

SELECT

    'medical_count_exceeds_members' AS check_name,
    COUNT(*) AS issue_count

FROM
    payer_01_dev.gold.membership_summary

WHERE
    medical_covered_member_count > member_count


UNION ALL


SELECT

    'pharmacy_count_exceeds_members',
    COUNT(*)

FROM
    payer_01_dev.gold.membership_summary

WHERE
    pharmacy_covered_member_count > member_count


UNION ALL


SELECT

    'dental_count_exceeds_members',
    COUNT(*)

FROM
    payer_01_dev.gold.membership_summary

WHERE
    dental_covered_member_count > member_count


UNION ALL


SELECT

    'vision_count_exceeds_members',
    COUNT(*)

FROM
    payer_01_dev.gold.membership_summary

WHERE
    vision_covered_member_count > member_count

ORDER BY
    check_name
;


-- ============================================================
-- 6. REQUIRED DIMENSION KEYS
--
-- Expected = 0
-- ============================================================

SELECT

    COUNT(*) AS missing_dimension_key_count

FROM
    payer_01_dev.gold.membership_summary

WHERE

       line_of_business IS NULL
    OR product_id IS NULL
    OR benefit_plan_id IS NULL
    OR group_id IS NULL
;


-- ============================================================
-- 7. MEMBERSHIP BY LINE OF BUSINESS
--
-- Informational
-- ============================================================

SELECT

    line_of_business,

    SUM(member_count)
        AS member_count,

    SUM(subscriber_count)
        AS subscriber_count,

    SUM(dependent_count)
        AS dependent_count,

    SUM(family_count)
        AS family_count

FROM
    payer_01_dev.gold.membership_summary

GROUP BY
    line_of_business

ORDER BY
    member_count DESC
;


-- ============================================================
-- END
-- ============================================================