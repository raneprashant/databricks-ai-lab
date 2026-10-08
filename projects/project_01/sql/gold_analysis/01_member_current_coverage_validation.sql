-- ============================================================
-- 1. GOLD MEMBER CURRENT COVERAGE - GRAIN / COUNTS
-- ============================================================

SELECT
    COUNT(*) AS total_rows,
    COUNT(DISTINCT member_id) AS distinct_members,

    SUM(
        CASE
            WHEN is_currently_covered = TRUE THEN 1
            ELSE 0
        END
    ) AS currently_covered_members,

    SUM(
        CASE
            WHEN is_currently_covered = FALSE THEN 1
            ELSE 0
        END
    ) AS not_currently_covered_members,

    MIN(as_of_date) AS min_as_of_date,
    MAX(as_of_date) AS max_as_of_date

FROM payer_01_dev.gold.member_current_coverage;

-- ============================================================
-- 2. DUPLICATE MEMBER GRAIN
-- Expected = 0
-- ============================================================

SELECT
    COUNT(*) AS duplicate_member_count
FROM (
    SELECT
        member_id
    FROM payer_01_dev.gold.member_current_coverage
    GROUP BY member_id
    HAVING COUNT(*) > 1
);


-- ============================================================
-- 3. INVALID "CURRENTLY COVERED" ROWS
-- Expected = 0
-- ============================================================

SELECT
    COUNT(*) AS invalid_current_coverage_count
FROM payer_01_dev.gold.member_current_coverage
WHERE
    is_currently_covered = TRUE
    AND (
           eligibility_id IS NULL
        OR eligibility_status <> 'ACTIVE'
        OR coverage_start_date > as_of_date
        OR (
               coverage_end_date IS NOT NULL
           AND coverage_end_date < as_of_date
        )
    );


    -- ============================================================
-- 4. ELIGIBILITY / COVERAGE DISTRIBUTION
-- ============================================================

SELECT
    eligibility_status,
    eligibility_event_type,
    is_currently_covered,
    COUNT(*) AS member_count
FROM payer_01_dev.gold.member_current_coverage
GROUP BY
    eligibility_status,
    eligibility_event_type,
    is_currently_covered
ORDER BY
    eligibility_status,
    eligibility_event_type,
    is_currently_covered;



-- ============================================================
-- 5. COVERED MEMBERS MISSING REFERENCE DESCRIPTIONS
--
-- Ideally 0. If subgroup_missing is non-zero, we will inspect
-- whether it relates to the known original synthetic Subgroup
-- issue rather than immediately treating it as a Gold defect.
-- ============================================================

SELECT

    SUM(
        CASE
            WHEN is_currently_covered = TRUE
             AND product_name IS NULL
            THEN 1 ELSE 0
        END
    ) AS product_missing,

    SUM(
        CASE
            WHEN is_currently_covered = TRUE
             AND plan_name IS NULL
            THEN 1 ELSE 0
        END
    ) AS plan_missing,

    SUM(
        CASE
            WHEN is_currently_covered = TRUE
             AND group_name IS NULL
            THEN 1 ELSE 0
        END
    ) AS group_missing,

    SUM(
        CASE
            WHEN is_currently_covered = TRUE
             AND subgroup_name IS NULL
            THEN 1 ELSE 0
        END
    ) AS subgroup_missing

FROM payer_01_dev.gold.member_current_coverage;

-- ============================================================
-- 6. GOLD VS CURRENT SILVER MEMBER COUNT
--
-- Expected difference = 0
-- ============================================================

WITH silver_count AS (

    SELECT
        COUNT(*) AS silver_current_members

    FROM
        payer_01_dev.silver.member

    WHERE
        __END_AT IS NULL

),

gold_count AS (

    SELECT
        COUNT(*) AS gold_members

    FROM
        payer_01_dev.gold.member_current_coverage

)

SELECT

    s.silver_current_members,

    g.gold_members,

    g.gold_members
        - s.silver_current_members
        AS difference

FROM

    silver_count s

CROSS JOIN

    gold_count g
;