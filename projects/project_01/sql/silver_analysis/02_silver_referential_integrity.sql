-- ============================================================
-- Project 01 - Healthcare Payer
-- Silver Referential Integrity Validation
-- File: 02_silver_referential_integrity.sql
--
-- Purpose:
--   Validate relationships across Silver tables after Batch 002.
--
-- Conventions:
--   1. SCD2 dimension/fact "current" rows use __END_AT IS NULL.
--   2. Eligibility is an event/history table and does not have
--      __START_AT / __END_AT.
--   3. Most orphan_count / issue_count results should be 0.
--   4. Known exception:
--        subgroup has 3 invalid source rows that were dropped by
--        Silver DQ in the existing Medium dataset. Therefore,
--        Eligibility or Claims that reference those subgroup_ids
--        may legitimately show non-zero orphan counts until the
--        Medium base dataset is regenerated with the fixed generator.
-- ============================================================


-- ============================================================
-- 1. CORE REFERENCE / DIMENSION RELATIONSHIPS
--
-- Expected: normally 0 for every orphan_count.
-- ============================================================

WITH
current_product AS (
    SELECT product_id
    FROM payer_01_dev.silver.product
    WHERE __END_AT IS NULL
),
current_benefit_plan AS (
    SELECT benefit_plan_id, product_id
    FROM payer_01_dev.silver.benefit_plan
    WHERE __END_AT IS NULL
),
current_group AS (
    SELECT group_id
    FROM payer_01_dev.silver.`group`
    WHERE __END_AT IS NULL
),
current_subgroup AS (
    SELECT subgroup_id, group_id, benefit_plan_id
    FROM payer_01_dev.silver.subgroup
    WHERE __END_AT IS NULL
)

SELECT
    'benefit_plan -> product' AS relationship_name,
    COUNT(*) AS orphan_count
FROM current_benefit_plan bp
LEFT JOIN current_product p
    ON bp.product_id = p.product_id
WHERE p.product_id IS NULL

UNION ALL

SELECT
    'subgroup -> group',
    COUNT(*)
FROM current_subgroup sg
LEFT JOIN current_group g
    ON sg.group_id = g.group_id
WHERE g.group_id IS NULL

UNION ALL

SELECT
    'subgroup -> benefit_plan',
    COUNT(*)
FROM current_subgroup sg
LEFT JOIN current_benefit_plan bp
    ON sg.benefit_plan_id = bp.benefit_plan_id
WHERE bp.benefit_plan_id IS NULL

ORDER BY relationship_name;


-- ============================================================
-- 2. ELIGIBILITY -> MEMBER / COVERAGE HIERARCHY
--
-- Eligibility contains history/events, so validate ALL rows.
--
-- Known note:
--   eligibility -> subgroup may be non-zero because 3 invalid
--   subgroup source rows were dropped in the current Medium load.
-- ============================================================

WITH
current_member AS (
    SELECT member_id
    FROM payer_01_dev.silver.member
    WHERE __END_AT IS NULL
),
current_product AS (
    SELECT product_id
    FROM payer_01_dev.silver.product
    WHERE __END_AT IS NULL
),
current_benefit_plan AS (
    SELECT benefit_plan_id
    FROM payer_01_dev.silver.benefit_plan
    WHERE __END_AT IS NULL
),
current_group AS (
    SELECT group_id
    FROM payer_01_dev.silver.`group`
    WHERE __END_AT IS NULL
),
current_subgroup AS (
    SELECT subgroup_id
    FROM payer_01_dev.silver.subgroup
    WHERE __END_AT IS NULL
)

SELECT
    'eligibility -> member' AS relationship_name,
    COUNT(*) AS orphan_count
FROM payer_01_dev.silver.eligibility e
LEFT JOIN current_member m
    ON e.member_id = m.member_id
WHERE m.member_id IS NULL

UNION ALL

SELECT
    'eligibility -> product',
    COUNT(*)
FROM payer_01_dev.silver.eligibility e
LEFT JOIN current_product p
    ON e.product_id = p.product_id
WHERE p.product_id IS NULL

UNION ALL

SELECT
    'eligibility -> benefit_plan',
    COUNT(*)
FROM payer_01_dev.silver.eligibility e
LEFT JOIN current_benefit_plan bp
    ON e.benefit_plan_id = bp.benefit_plan_id
WHERE bp.benefit_plan_id IS NULL

UNION ALL

SELECT
    'eligibility -> group',
    COUNT(*)
FROM payer_01_dev.silver.eligibility e
LEFT JOIN current_group g
    ON e.group_id = g.group_id
WHERE g.group_id IS NULL

UNION ALL

SELECT
    'eligibility -> subgroup',
    COUNT(*)
FROM payer_01_dev.silver.eligibility e
LEFT JOIN current_subgroup sg
    ON e.subgroup_id = sg.subgroup_id
WHERE sg.subgroup_id IS NULL

ORDER BY relationship_name;


-- ============================================================
-- 3. ELIGIBILITY HIERARCHY CONSISTENCY
--
-- These checks go beyond "key exists" and verify that the
-- relationships copied onto Eligibility agree with the current
-- Subgroup / Benefit Plan hierarchy.
--
-- Expected: normally 0.
-- ============================================================

WITH
current_subgroup AS (
    SELECT
        subgroup_id,
        group_id,
        benefit_plan_id
    FROM payer_01_dev.silver.subgroup
    WHERE __END_AT IS NULL
),
current_benefit_plan AS (
    SELECT
        benefit_plan_id,
        product_id
    FROM payer_01_dev.silver.benefit_plan
    WHERE __END_AT IS NULL
)

SELECT
    'eligibility subgroup.group_id mismatch' AS check_name,
    COUNT(*) AS issue_count
FROM payer_01_dev.silver.eligibility e
JOIN current_subgroup sg
    ON e.subgroup_id = sg.subgroup_id
WHERE e.group_id <> sg.group_id

UNION ALL

SELECT
    'eligibility subgroup.benefit_plan_id mismatch',
    COUNT(*)
FROM payer_01_dev.silver.eligibility e
JOIN current_subgroup sg
    ON e.subgroup_id = sg.subgroup_id
WHERE e.benefit_plan_id <> sg.benefit_plan_id

UNION ALL

SELECT
    'eligibility benefit_plan.product_id mismatch',
    COUNT(*)
FROM payer_01_dev.silver.eligibility e
JOIN current_benefit_plan bp
    ON e.benefit_plan_id = bp.benefit_plan_id
WHERE e.product_id <> bp.product_id

ORDER BY check_name;


-- ============================================================
-- 4. PROVIDER HIERARCHY REFERENTIAL INTEGRITY
--
-- Expected: all orphan_count values = 0.
-- ============================================================

WITH
current_practitioner AS (
    SELECT practitioner_id
    FROM payer_01_dev.silver.practitioner
    WHERE __END_AT IS NULL
),
current_supplier AS (
    SELECT supplier_id
    FROM payer_01_dev.silver.supplier
    WHERE __END_AT IS NULL
),
current_supplier_location AS (
    SELECT supplier_location_id, supplier_id
    FROM payer_01_dev.silver.supplier_location
    WHERE __END_AT IS NULL
),
current_practitioner_role AS (
    SELECT
        practitioner_role_id,
        practitioner_id,
        supplier_id,
        supplier_location_id
    FROM payer_01_dev.silver.practitioner_role
    WHERE __END_AT IS NULL
)

SELECT
    'supplier_location -> supplier' AS relationship_name,
    COUNT(*) AS orphan_count
FROM current_supplier_location sl
LEFT JOIN current_supplier s
    ON sl.supplier_id = s.supplier_id
WHERE s.supplier_id IS NULL

UNION ALL

SELECT
    'practitioner_role -> practitioner',
    COUNT(*)
FROM current_practitioner_role pr
LEFT JOIN current_practitioner p
    ON pr.practitioner_id = p.practitioner_id
WHERE p.practitioner_id IS NULL

UNION ALL

SELECT
    'practitioner_role -> supplier',
    COUNT(*)
FROM current_practitioner_role pr
LEFT JOIN current_supplier s
    ON pr.supplier_id = s.supplier_id
WHERE s.supplier_id IS NULL

UNION ALL

SELECT
    'practitioner_role -> supplier_location',
    COUNT(*)
FROM current_practitioner_role pr
LEFT JOIN current_supplier_location sl
    ON pr.supplier_location_id = sl.supplier_location_id
WHERE sl.supplier_location_id IS NULL

ORDER BY relationship_name;


-- ============================================================
-- 5. PROVIDER HIERARCHY CONSISTENCY
--
-- Practitioner Role carries supplier_id and supplier_location_id.
-- The selected Supplier Location must belong to the same Supplier.
--
-- Expected: issue_count = 0.
-- ============================================================

WITH
current_practitioner_role AS (
    SELECT
        practitioner_role_id,
        supplier_id,
        supplier_location_id
    FROM payer_01_dev.silver.practitioner_role
    WHERE __END_AT IS NULL
),
current_supplier_location AS (
    SELECT
        supplier_location_id,
        supplier_id
    FROM payer_01_dev.silver.supplier_location
    WHERE __END_AT IS NULL
)

SELECT
    COUNT(*) AS practitioner_role_supplier_location_mismatch
FROM current_practitioner_role pr
JOIN current_supplier_location sl
    ON pr.supplier_location_id = sl.supplier_location_id
WHERE pr.supplier_id <> sl.supplier_id;


-- ============================================================
-- 6. ENTITY ADDRESS -> ADDRESS MASTER
--
-- Expected: orphan_count = 0.
-- ============================================================

WITH
current_entity_address AS (
    SELECT *
    FROM payer_01_dev.silver.entity_address
    WHERE __END_AT IS NULL
),
current_address AS (
    SELECT address_id
    FROM payer_01_dev.silver.address
    WHERE __END_AT IS NULL
)

SELECT
    COUNT(*) AS entity_address_to_address_orphan_count
FROM current_entity_address ea
LEFT JOIN current_address a
    ON ea.address_id = a.address_id
WHERE a.address_id IS NULL;


-- ============================================================
-- 7. ENTITY ADDRESS -> ENTITY MASTER
--
-- Validate entity_id according to entity_type.
--
-- Expected: all orphan_count values = 0.
-- ============================================================

WITH
current_entity_address AS (
    SELECT *
    FROM payer_01_dev.silver.entity_address
    WHERE __END_AT IS NULL
),
current_member AS (
    SELECT member_id
    FROM payer_01_dev.silver.member
    WHERE __END_AT IS NULL
),
current_practitioner AS (
    SELECT practitioner_id
    FROM payer_01_dev.silver.practitioner
    WHERE __END_AT IS NULL
),
current_supplier AS (
    SELECT supplier_id
    FROM payer_01_dev.silver.supplier
    WHERE __END_AT IS NULL
),
current_supplier_location AS (
    SELECT supplier_location_id
    FROM payer_01_dev.silver.supplier_location
    WHERE __END_AT IS NULL
),
current_practitioner_role AS (
    SELECT practitioner_role_id
    FROM payer_01_dev.silver.practitioner_role
    WHERE __END_AT IS NULL
)

SELECT
    'entity_address MEMBER -> member' AS relationship_name,
    COUNT(*) AS orphan_count
FROM current_entity_address ea
LEFT JOIN current_member m
    ON ea.entity_id = m.member_id
WHERE ea.entity_type = 'MEMBER'
  AND m.member_id IS NULL

UNION ALL

SELECT
    'entity_address PRACTITIONER -> practitioner',
    COUNT(*)
FROM current_entity_address ea
LEFT JOIN current_practitioner p
    ON ea.entity_id = p.practitioner_id
WHERE ea.entity_type = 'PRACTITIONER'
  AND p.practitioner_id IS NULL

UNION ALL

SELECT
    'entity_address SUPPLIER -> supplier',
    COUNT(*)
FROM current_entity_address ea
LEFT JOIN current_supplier s
    ON ea.entity_id = s.supplier_id
WHERE ea.entity_type = 'SUPPLIER'
  AND s.supplier_id IS NULL

UNION ALL

SELECT
    'entity_address SUPPLIER_LOCATION -> supplier_location',
    COUNT(*)
FROM current_entity_address ea
LEFT JOIN current_supplier_location sl
    ON ea.entity_id = sl.supplier_location_id
WHERE ea.entity_type = 'SUPPLIER_LOCATION'
  AND sl.supplier_location_id IS NULL

UNION ALL

SELECT
    'entity_address PRACTITIONER_ROLE -> practitioner_role',
    COUNT(*)
FROM current_entity_address ea
LEFT JOIN current_practitioner_role pr
    ON ea.entity_id = pr.practitioner_role_id
WHERE ea.entity_type = 'PRACTITIONER_ROLE'
  AND pr.practitioner_role_id IS NULL

ORDER BY relationship_name;


-- ============================================================
-- 8. ENTITY ADDRESS - UNKNOWN ENTITY TYPES
--
-- Expected: unknown_entity_type_count = 0.
-- ============================================================

SELECT
    COUNT(*) AS unknown_entity_type_count
FROM payer_01_dev.silver.entity_address
WHERE __END_AT IS NULL
  AND entity_type NOT IN (
        'MEMBER',
        'PRACTITIONER',
        'SUPPLIER',
        'SUPPLIER_LOCATION',
        'PRACTITIONER_ROLE'
      );


-- ============================================================
-- 9. CURRENT CLAIM HEADER -> BUSINESS ENTITIES
--
-- Expected: normally 0.
--
-- Known note:
--   claim_header -> subgroup can be non-zero if Claims reference
--   one of the 3 invalid Subgroups dropped from Silver.
-- ============================================================

WITH
current_claim_header AS (
    SELECT *
    FROM payer_01_dev.silver.claim_header
    WHERE __END_AT IS NULL
),
current_member AS (
    SELECT member_id
    FROM payer_01_dev.silver.member
    WHERE __END_AT IS NULL
),
current_product AS (
    SELECT product_id
    FROM payer_01_dev.silver.product
    WHERE __END_AT IS NULL
),
current_benefit_plan AS (
    SELECT benefit_plan_id
    FROM payer_01_dev.silver.benefit_plan
    WHERE __END_AT IS NULL
),
current_group AS (
    SELECT group_id
    FROM payer_01_dev.silver.`group`
    WHERE __END_AT IS NULL
),
current_subgroup AS (
    SELECT subgroup_id
    FROM payer_01_dev.silver.subgroup
    WHERE __END_AT IS NULL
),
current_practitioner AS (
    SELECT practitioner_id
    FROM payer_01_dev.silver.practitioner
    WHERE __END_AT IS NULL
),
current_supplier AS (
    SELECT supplier_id
    FROM payer_01_dev.silver.supplier
    WHERE __END_AT IS NULL
),
current_supplier_location AS (
    SELECT supplier_location_id
    FROM payer_01_dev.silver.supplier_location
    WHERE __END_AT IS NULL
),
current_practitioner_role AS (
    SELECT practitioner_role_id
    FROM payer_01_dev.silver.practitioner_role
    WHERE __END_AT IS NULL
)

SELECT
    'claim_header -> member' AS relationship_name,
    COUNT(*) AS orphan_count
FROM current_claim_header ch
LEFT JOIN current_member m
    ON ch.member_id = m.member_id
WHERE m.member_id IS NULL

UNION ALL

SELECT
    'claim_header -> product',
    COUNT(*)
FROM current_claim_header ch
LEFT JOIN current_product p
    ON ch.product_id = p.product_id
WHERE p.product_id IS NULL

UNION ALL

SELECT
    'claim_header -> benefit_plan',
    COUNT(*)
FROM current_claim_header ch
LEFT JOIN current_benefit_plan bp
    ON ch.benefit_plan_id = bp.benefit_plan_id
WHERE bp.benefit_plan_id IS NULL

UNION ALL

SELECT
    'claim_header -> group',
    COUNT(*)
FROM current_claim_header ch
LEFT JOIN current_group g
    ON ch.group_id = g.group_id
WHERE g.group_id IS NULL

UNION ALL

SELECT
    'claim_header -> subgroup',
    COUNT(*)
FROM current_claim_header ch
LEFT JOIN current_subgroup sg
    ON ch.subgroup_id = sg.subgroup_id
WHERE sg.subgroup_id IS NULL

UNION ALL

SELECT
    'claim_header -> practitioner',
    COUNT(*)
FROM current_claim_header ch
LEFT JOIN current_practitioner p
    ON ch.practitioner_id = p.practitioner_id
WHERE p.practitioner_id IS NULL

UNION ALL

SELECT
    'claim_header -> supplier',
    COUNT(*)
FROM current_claim_header ch
LEFT JOIN current_supplier s
    ON ch.supplier_id = s.supplier_id
WHERE s.supplier_id IS NULL

UNION ALL

SELECT
    'claim_header -> supplier_location',
    COUNT(*)
FROM current_claim_header ch
LEFT JOIN current_supplier_location sl
    ON ch.supplier_location_id = sl.supplier_location_id
WHERE sl.supplier_location_id IS NULL

UNION ALL

SELECT
    'claim_header -> practitioner_role',
    COUNT(*)
FROM current_claim_header ch
LEFT JOIN current_practitioner_role pr
    ON ch.practitioner_role_id = pr.practitioner_role_id
WHERE pr.practitioner_role_id IS NULL

ORDER BY relationship_name;


-- ============================================================
-- 10. CURRENT CLAIM HEADER -> EXACT ELIGIBILITY EVENT
--
-- Claim Header stores eligibility_id + eligibility_record_version.
-- Both should match the exact Silver Eligibility event.
--
-- Expected: all issue_count values = 0.
-- ============================================================

WITH
current_claim_header AS (
    SELECT *
    FROM payer_01_dev.silver.claim_header
    WHERE __END_AT IS NULL
)

SELECT
    'claim_header -> eligibility_id missing' AS check_name,
    COUNT(*) AS issue_count
FROM current_claim_header ch
LEFT JOIN payer_01_dev.silver.eligibility e
    ON ch.eligibility_id = e.eligibility_id
WHERE e.eligibility_id IS NULL

UNION ALL

SELECT
    'claim_header eligibility_record_version mismatch',
    COUNT(*)
FROM current_claim_header ch
JOIN payer_01_dev.silver.eligibility e
    ON ch.eligibility_id = e.eligibility_id
WHERE ch.eligibility_record_version <> e.record_version

ORDER BY check_name;


-- ============================================================
-- 11. CLAIM HEADER VS ELIGIBILITY ATTRIBUTE CONSISTENCY
--
-- Claims carry a snapshot of coverage hierarchy.
-- It should agree with the exact Eligibility event used.
--
-- Expected: issue_count = 0 for all checks.
-- ============================================================

WITH
current_claim_header AS (
    SELECT *
    FROM payer_01_dev.silver.claim_header
    WHERE __END_AT IS NULL
)

SELECT
    'claim.member_id <> eligibility.member_id' AS check_name,
    COUNT(*) AS issue_count
FROM current_claim_header ch
JOIN payer_01_dev.silver.eligibility e
    ON ch.eligibility_id = e.eligibility_id
WHERE ch.member_id <> e.member_id

UNION ALL

SELECT
    'claim.group_id <> eligibility.group_id',
    COUNT(*)
FROM current_claim_header ch
JOIN payer_01_dev.silver.eligibility e
    ON ch.eligibility_id = e.eligibility_id
WHERE ch.group_id <> e.group_id

UNION ALL

SELECT
    'claim.subgroup_id <> eligibility.subgroup_id',
    COUNT(*)
FROM current_claim_header ch
JOIN payer_01_dev.silver.eligibility e
    ON ch.eligibility_id = e.eligibility_id
WHERE ch.subgroup_id <> e.subgroup_id

UNION ALL

SELECT
    'claim.product_id <> eligibility.product_id',
    COUNT(*)
FROM current_claim_header ch
JOIN payer_01_dev.silver.eligibility e
    ON ch.eligibility_id = e.eligibility_id
WHERE ch.product_id <> e.product_id

UNION ALL

SELECT
    'claim.benefit_plan_id <> eligibility.benefit_plan_id',
    COUNT(*)
FROM current_claim_header ch
JOIN payer_01_dev.silver.eligibility e
    ON ch.eligibility_id = e.eligibility_id
WHERE ch.benefit_plan_id <> e.benefit_plan_id

UNION ALL

SELECT
    'claim.line_of_business <> eligibility.line_of_business',
    COUNT(*)
FROM current_claim_header ch
JOIN payer_01_dev.silver.eligibility e
    ON ch.eligibility_id = e.eligibility_id
WHERE ch.line_of_business <> e.line_of_business

UNION ALL

SELECT
    'claim.product_type <> eligibility.product_type',
    COUNT(*)
FROM current_claim_header ch
JOIN payer_01_dev.silver.eligibility e
    ON ch.eligibility_id = e.eligibility_id
WHERE ch.product_type <> e.product_type

UNION ALL

SELECT
    'claim.network_id <> eligibility.network_id',
    COUNT(*)
FROM current_claim_header ch
JOIN payer_01_dev.silver.eligibility e
    ON ch.eligibility_id = e.eligibility_id
WHERE ch.network_id <> e.network_id

ORDER BY check_name;


-- ============================================================
-- 12. CLAIM HEADER VS PROVIDER ROLE CONSISTENCY
--
-- Claims store practitioner/provider context explicitly.
-- It should agree with the referenced Practitioner Role.
--
-- Expected: issue_count = 0 for all checks.
-- ============================================================

WITH
current_claim_header AS (
    SELECT *
    FROM payer_01_dev.silver.claim_header
    WHERE __END_AT IS NULL
),
current_practitioner_role AS (
    SELECT *
    FROM payer_01_dev.silver.practitioner_role
    WHERE __END_AT IS NULL
)

SELECT
    'claim.practitioner_id <> role.practitioner_id' AS check_name,
    COUNT(*) AS issue_count
FROM current_claim_header ch
JOIN current_practitioner_role pr
    ON ch.practitioner_role_id = pr.practitioner_role_id
WHERE ch.practitioner_id <> pr.practitioner_id

UNION ALL

SELECT
    'claim.supplier_id <> role.supplier_id',
    COUNT(*)
FROM current_claim_header ch
JOIN current_practitioner_role pr
    ON ch.practitioner_role_id = pr.practitioner_role_id
WHERE ch.supplier_id <> pr.supplier_id

UNION ALL

SELECT
    'claim.supplier_location_id <> role.supplier_location_id',
    COUNT(*)
FROM current_claim_header ch
JOIN current_practitioner_role pr
    ON ch.practitioner_role_id = pr.practitioner_role_id
WHERE ch.supplier_location_id <> pr.supplier_location_id

UNION ALL

SELECT
    'claim.network_status <> role.network_status',
    COUNT(*)
FROM current_claim_header ch
JOIN current_practitioner_role pr
    ON ch.practitioner_role_id = pr.practitioner_role_id
WHERE ch.network_status <> pr.network_status

UNION ALL

SELECT
    'claim.network_tier <> role.network_tier',
    COUNT(*)
FROM current_claim_header ch
JOIN current_practitioner_role pr
    ON ch.practitioner_role_id = pr.practitioner_role_id
WHERE ch.network_tier <> pr.network_tier

ORDER BY check_name;


-- ============================================================
-- 13. CLAIM LINE -> CURRENT CLAIM HEADER
--
-- Expected: orphan_count = 0.
-- ============================================================

WITH
current_claim_header AS (
    SELECT claim_id
    FROM payer_01_dev.silver.claim_header
    WHERE __END_AT IS NULL
),
current_claim_line AS (
    SELECT claim_line_id, claim_id
    FROM payer_01_dev.silver.claim_line
    WHERE __END_AT IS NULL
)

SELECT
    COUNT(*) AS claim_line_to_claim_header_orphan_count
FROM current_claim_line cl
LEFT JOIN current_claim_header ch
    ON cl.claim_id = ch.claim_id
WHERE ch.claim_id IS NULL;


-- ============================================================
-- 14. CLAIM SERVICE DATE WITHIN ELIGIBILITY COVERAGE
--
-- Service dates should fall within the exact Eligibility
-- coverage period referenced by the Claim.
--
-- Expected: issue_count = 0.
-- ============================================================

WITH
current_claim_header AS (
    SELECT *
    FROM payer_01_dev.silver.claim_header
    WHERE __END_AT IS NULL
)

SELECT
    COUNT(*) AS claim_outside_eligibility_coverage_count
FROM current_claim_header ch
JOIN payer_01_dev.silver.eligibility e
    ON ch.eligibility_id = e.eligibility_id
WHERE
       ch.service_from_date < e.coverage_start_date
    OR (
           e.coverage_end_date IS NOT NULL
       AND ch.service_to_date > e.coverage_end_date
       );


-- ============================================================
-- 15. CLAIM SERVICE DATE WITHIN PRACTITIONER ROLE PERIOD
--
-- Expected: issue_count = 0.
-- ============================================================

WITH
current_claim_header AS (
    SELECT *
    FROM payer_01_dev.silver.claim_header
    WHERE __END_AT IS NULL
),
current_practitioner_role AS (
    SELECT *
    FROM payer_01_dev.silver.practitioner_role
    WHERE __END_AT IS NULL
)

SELECT
    COUNT(*) AS claim_outside_practitioner_role_period_count
FROM current_claim_header ch
JOIN current_practitioner_role pr
    ON ch.practitioner_role_id = pr.practitioner_role_id
WHERE
       ch.service_from_date < pr.effective_date
    OR (
           pr.termination_date IS NOT NULL
       AND ch.service_to_date > pr.termination_date
       );


-- ============================================================
-- 16. DETAIL - ELIGIBILITY ROWS WITH MISSING SUBGROUP
--
-- Run this only if Section 2 shows eligibility -> subgroup > 0.
-- This is useful for confirming whether the orphan keys are the
-- known invalid Subgroups from the original Medium dataset.
-- ============================================================

WITH current_subgroup AS (
    SELECT subgroup_id
    FROM payer_01_dev.silver.subgroup
    WHERE __END_AT IS NULL
)
SELECT
    e.subgroup_id,
    COUNT(*) AS eligibility_row_count,
    COUNT(DISTINCT e.member_id) AS member_count
FROM payer_01_dev.silver.eligibility e
LEFT JOIN current_subgroup sg
    ON e.subgroup_id = sg.subgroup_id
WHERE sg.subgroup_id IS NULL
GROUP BY e.subgroup_id
ORDER BY eligibility_row_count DESC;


-- ============================================================
-- 17. DETAIL - CURRENT CLAIMS WITH MISSING SUBGROUP
--
-- Run this only if Section 9 shows claim_header -> subgroup > 0.
-- ============================================================

WITH
current_claim_header AS (
    SELECT *
    FROM payer_01_dev.silver.claim_header
    WHERE __END_AT IS NULL
),
current_subgroup AS (
    SELECT subgroup_id
    FROM payer_01_dev.silver.subgroup
    WHERE __END_AT IS NULL
)
SELECT
    ch.subgroup_id,
    COUNT(*) AS claim_count
FROM current_claim_header ch
LEFT JOIN current_subgroup sg
    ON ch.subgroup_id = sg.subgroup_id
WHERE sg.subgroup_id IS NULL
GROUP BY ch.subgroup_id
ORDER BY claim_count DESC;


-- ============================================================
-- END OF 02_silver_referential_integrity.sql
-- ============================================================
