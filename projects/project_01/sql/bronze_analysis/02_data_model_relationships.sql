-- =====================================================================
-- PROJECT 01
-- BRONZE DATA MODEL / RELATIONSHIP EXERCISES
--
-- Catalog : payer_01_dev
-- Schema  : bronze
--
-- Purpose:
--   Understand the healthcare payer data model before building Silver.
--
-- Important:
--   Bronze source attributes are intentionally STRING.
--   Run each numbered query separately in Databricks SQL Editor.
-- =====================================================================



-- =====================================================================
-- 01. MEMBER / FAMILY STRUCTURE
--
-- Understand:
--   family_id
--   subscriber_id
--   SELF / SPOUSE / CHILD
--
-- One subscriber can have multiple family members.
-- =====================================================================

SELECT
    family_id,
    subscriber_id,
    COUNT(*) AS family_member_count,
    COUNT_IF(relationship_to_subscriber = 'SELF')   AS subscribers,
    COUNT_IF(relationship_to_subscriber = 'SPOUSE') AS spouses,
    COUNT_IF(relationship_to_subscriber = 'CHILD')  AS children
FROM payer_01_dev.bronze.member_raw
GROUP BY
    family_id,
    subscriber_id
ORDER BY family_member_count DESC
LIMIT 100;



-- =====================================================================
-- 02. SHOW COMPLETE FAMILIES
--
-- Pick some families and inspect every person belonging to them.
-- =====================================================================

WITH selected_families AS
(
    SELECT family_id
    FROM payer_01_dev.bronze.member_raw
    GROUP BY family_id
    HAVING COUNT(*) >= 4
    ORDER BY COUNT(*) DESC
    LIMIT 10
)

SELECT
    m.family_id,
    m.subscriber_id,
    m.member_id,
    m.relationship_to_subscriber,
    m.first_name,
    m.last_name,
    m.date_of_birth,
    m.gender,
    m.member_status
FROM payer_01_dev.bronze.member_raw m
INNER JOIN selected_families f
    ON m.family_id = f.family_id
ORDER BY
    m.family_id,
    CASE m.relationship_to_subscriber
        WHEN 'SELF' THEN 1
        WHEN 'SPOUSE' THEN 2
        ELSE 3
    END,
    m.member_id;



-- =====================================================================
-- 03. VALIDATE MEMBER -> SUBSCRIBER RELATIONSHIP
--
-- Every member's subscriber_id should resolve to a Member record.
-- This is the first simple relationship validation.
-- =====================================================================

SELECT
    COUNT(*) AS member_rows,
    COUNT_IF(s.member_id IS NULL) AS missing_subscriber_rows
FROM payer_01_dev.bronze.member_raw m
LEFT JOIN payer_01_dev.bronze.member_raw s
    ON m.subscriber_id = s.member_id;



-- =====================================================================
-- 04. PRODUCT -> BENEFIT PLAN
--
-- Product is the higher-level insurance offering.
-- Benefit Plan describes a particular benefit configuration under it.
-- =====================================================================

SELECT
    p.product_id,
    p.line_of_business,
    p.product_type,
    COUNT(bp.benefit_plan_id) AS benefit_plan_count
FROM payer_01_dev.bronze.product_raw p
LEFT JOIN payer_01_dev.bronze.benefit_plan_raw bp
    ON p.product_id = bp.product_id
GROUP BY
    p.product_id,
    p.line_of_business,
    p.product_type
ORDER BY
    benefit_plan_count DESC,
    p.product_id;



-- =====================================================================
-- 05. GROUP -> SUBGROUP -> BENEFIT PLAN -> PRODUCT
--
-- This is one of the most important payer hierarchy relationships.
--
-- Product
--    ↓
-- Benefit Plan
--    ↑
-- Subgroup
--    ↑
-- Group
-- =====================================================================

SELECT
    g.group_id,
    sg.subgroup_id,
    bp.benefit_plan_id,
    p.product_id,
    p.line_of_business,
    p.product_type
FROM payer_01_dev.bronze.group_raw g
INNER JOIN payer_01_dev.bronze.subgroup_raw sg
    ON g.group_id = sg.group_id
INNER JOIN payer_01_dev.bronze.benefit_plan_raw bp
    ON sg.benefit_plan_id = bp.benefit_plan_id
INNER JOIN payer_01_dev.bronze.product_raw p
    ON bp.product_id = p.product_id
ORDER BY
    g.group_id,
    sg.subgroup_id
LIMIT 200;



-- =====================================================================
-- 06. CHECK FOR BROKEN PAYER HIERARCHY REFERENCES
--
-- Ideally every value below should be 0.
-- =====================================================================

SELECT
    COUNT(*) AS subgroup_rows,

    COUNT_IF(
        g.group_id IS NULL
    ) AS subgroup_missing_group,

    COUNT_IF(
        bp.benefit_plan_id IS NULL
    ) AS subgroup_missing_benefit_plan,

    COUNT_IF(
        p.product_id IS NULL
    ) AS benefit_plan_missing_product

FROM payer_01_dev.bronze.subgroup_raw sg

LEFT JOIN payer_01_dev.bronze.group_raw g
    ON sg.group_id = g.group_id

LEFT JOIN payer_01_dev.bronze.benefit_plan_raw bp
    ON sg.benefit_plan_id = bp.benefit_plan_id

LEFT JOIN payer_01_dev.bronze.product_raw p
    ON bp.product_id = p.product_id;



-- =====================================================================
-- 07. MEMBER -> ELIGIBILITY HISTORY
--
-- Eligibility contains multiple versions/events for a Member.
--
-- Our generated model currently has 3 eligibility records per Member.
-- =====================================================================

SELECT
    e.member_id,
    m.first_name,
    m.last_name,

    COUNT(*) AS eligibility_versions,

    MIN(CAST(e.coverage_start_date AS DATE))
        AS earliest_coverage_start,

    MAX(CAST(e.event_effective_date AS DATE))
        AS latest_event_date

FROM payer_01_dev.bronze.eligibility_raw e

INNER JOIN payer_01_dev.bronze.member_raw m
    ON e.member_id = m.member_id

GROUP BY
    e.member_id,
    m.first_name,
    m.last_name

ORDER BY eligibility_versions DESC
LIMIT 100;



-- =====================================================================
-- 08. SEE ELIGIBILITY HISTORY FOR INDIVIDUAL MEMBERS
--
-- This makes event/version behavior easy to understand.
-- =====================================================================

WITH sample_members AS
(
    SELECT member_id
    FROM payer_01_dev.bronze.eligibility_raw
    GROUP BY member_id
    ORDER BY member_id
    LIMIT 20
)

SELECT
    e.member_id,
    e.eligibility_id,
    e.record_version,
    e.current_record_flag,
    e.event_type,
    e.eligibility_status,

    e.product_id,
    e.benefit_plan_id,
    e.group_id,
    e.subgroup_id,

    e.coverage_start_date,
    e.coverage_end_date,
    e.event_effective_date,
    e.transaction_date,

    e.retroactive_flag,
    e.future_enrollment_flag,
    e.reinstatement_flag

FROM payer_01_dev.bronze.eligibility_raw e

INNER JOIN sample_members s
    ON e.member_id = s.member_id

ORDER BY
    e.member_id,
    CAST(e.record_version AS INT);



-- =====================================================================
-- 09. ELIGIBILITY EVENT DISTRIBUTION
--
-- Understand what kinds of eligibility lifecycle events exist.
-- =====================================================================

SELECT
    event_type,
    eligibility_status,
    COUNT(*) AS row_count
FROM payer_01_dev.bronze.eligibility_raw
GROUP BY
    event_type,
    eligibility_status
ORDER BY row_count DESC;



-- =====================================================================
-- 10. ELIGIBILITY -> FULL PAYER HIERARCHY
--
-- Shows how an eligibility row resolves through the reference model.
-- =====================================================================

SELECT
    e.eligibility_id,
    e.member_id,

    e.group_id,
    e.subgroup_id,
    e.benefit_plan_id,
    e.product_id,

    p.line_of_business,
    p.product_type,
    p.network_id,

    e.coverage_start_date,
    e.coverage_end_date,
    e.eligibility_status,
    e.event_type

FROM payer_01_dev.bronze.eligibility_raw e

INNER JOIN payer_01_dev.bronze.subgroup_raw sg
    ON e.subgroup_id = sg.subgroup_id

INNER JOIN payer_01_dev.bronze.group_raw g
    ON e.group_id = g.group_id

INNER JOIN payer_01_dev.bronze.benefit_plan_raw bp
    ON e.benefit_plan_id = bp.benefit_plan_id

INNER JOIN payer_01_dev.bronze.product_raw p
    ON e.product_id = p.product_id

LIMIT 200;



-- =====================================================================
-- 11. PROVIDER MODEL:
--     PRACTITIONER -> PRACTITIONER ROLE -> SUPPLIER -> LOCATION
--
-- Practitioner:
--     Individual clinician.
--
-- Supplier:
--     Organization / hospital / medical group.
--
-- Practitioner Role:
--     Affiliation connecting the clinician with organization/location.
-- =====================================================================

SELECT
    pr.practitioner_role_id,

    p.practitioner_id,
    p.first_name,
    p.last_name,

    pr.role_type,
    pr.role_specialty,
    pr.pcp_flag,

    s.supplier_id,
    s.supplier_name,

    sl.supplier_location_id,
    sl.location_type,
    sl.place_of_service_code,

    pr.network_status,
    pr.network_tier,

    pr.effective_date,
    pr.termination_date

FROM payer_01_dev.bronze.practitioner_role_raw pr

INNER JOIN payer_01_dev.bronze.practitioner_raw p
    ON pr.practitioner_id = p.practitioner_id

INNER JOIN payer_01_dev.bronze.supplier_raw s
    ON pr.supplier_id = s.supplier_id

INNER JOIN payer_01_dev.bronze.supplier_location_raw sl
    ON pr.supplier_location_id = sl.supplier_location_id

LIMIT 200;



-- =====================================================================
-- 12. HOW MANY PRACTITIONER ROLES DOES EACH PRACTITIONER HAVE?
--
-- One practitioner can work at multiple locations and/or suppliers.
-- =====================================================================

SELECT
    p.practitioner_id,
    p.first_name,
    p.last_name,

    COUNT(*) AS role_count,

    COUNT(DISTINCT pr.supplier_id)
        AS supplier_count,

    COUNT(DISTINCT pr.supplier_location_id)
        AS location_count

FROM payer_01_dev.bronze.practitioner_raw p

INNER JOIN payer_01_dev.bronze.practitioner_role_raw pr
    ON p.practitioner_id = pr.practitioner_id

GROUP BY
    p.practitioner_id,
    p.first_name,
    p.last_name

ORDER BY role_count DESC
LIMIT 100;



-- =====================================================================
-- 13. SUPPLIER -> SUPPLIER LOCATION
--
-- One Supplier organization may operate multiple physical locations.
-- =====================================================================

SELECT
    s.supplier_id,
    s.supplier_name,
    s.supplier_type,

    COUNT(sl.supplier_location_id)
        AS location_count

FROM payer_01_dev.bronze.supplier_raw s

LEFT JOIN payer_01_dev.bronze.supplier_location_raw sl
    ON s.supplier_id = sl.supplier_id

GROUP BY
    s.supplier_id,
    s.supplier_name,
    s.supplier_type

ORDER BY location_count DESC
LIMIT 100;



-- =====================================================================
-- 14. ENTITY ADDRESS BRIDGE
--
-- Address itself is stored once in address_raw.
--
-- entity_address_raw tells us:
--    WHO uses the address
--    WHAT TYPE of address it is
--
-- Examples:
--    MEMBER / RESIDENTIAL
--    SUPPLIER / BILLING
--    SUPPLIER_LOCATION / SERVICE_LOCATION
--    PRACTITIONER / PRIMARY_PRACTICE
-- =====================================================================

SELECT
    ea.entity_type,
    ea.address_type,
    COUNT(*) AS relationship_count,
    COUNT(DISTINCT ea.entity_id) AS entity_count,
    COUNT(DISTINCT ea.address_id) AS address_count
FROM payer_01_dev.bronze.entity_address_raw ea
GROUP BY
    ea.entity_type,
    ea.address_type
ORDER BY
    ea.entity_type,
    relationship_count DESC;



-- =====================================================================
-- 15. MEMBER -> RESIDENTIAL ADDRESS
--
-- Demonstrates bridge-table usage.
-- =====================================================================

SELECT
    m.member_id,
    m.family_id,
    m.first_name,
    m.last_name,

    ea.address_type,

    a.address_id,
    a.address_line_1,
    a.city,
    a.state,
    a.postal_code

FROM payer_01_dev.bronze.member_raw m

INNER JOIN payer_01_dev.bronze.entity_address_raw ea
    ON ea.entity_id = m.member_id
   AND ea.entity_type = 'MEMBER'
   AND ea.address_type = 'RESIDENTIAL'

INNER JOIN payer_01_dev.bronze.address_raw a
    ON ea.address_id = a.address_id

LIMIT 200;



-- =====================================================================
-- 16. CLAIM HEADER -> CLAIM LINE
--
-- Claim Header contains claim-level information.
-- Claim Line contains service/procedure-level information.
--
-- Header financial totals should equal the sum of its Lines.
-- =====================================================================

SELECT
    ch.claim_id,

    ch.member_id,
    ch.claim_type,
    ch.claim_status,

    ch.claim_line_count,

    COUNT(cl.claim_line_id)
        AS actual_line_count,

    CAST(ch.total_billed_amount AS DECIMAL(18,2))
        AS header_billed,

    SUM(
        CAST(cl.billed_amount AS DECIMAL(18,2))
    ) AS line_billed,

    CAST(ch.total_allowed_amount AS DECIMAL(18,2))
        AS header_allowed,

    SUM(
        CAST(cl.allowed_amount AS DECIMAL(18,2))
    ) AS line_allowed,

    CAST(ch.total_paid_amount AS DECIMAL(18,2))
        AS header_paid,

    SUM(
        CAST(cl.paid_amount AS DECIMAL(18,2))
    ) AS line_paid

FROM payer_01_dev.bronze.claim_header_raw ch

INNER JOIN payer_01_dev.bronze.claim_line_raw cl
    ON ch.claim_id = cl.claim_id

GROUP BY
    ch.claim_id,
    ch.member_id,
    ch.claim_type,
    ch.claim_status,
    ch.claim_line_count,
    ch.total_billed_amount,
    ch.total_allowed_amount,
    ch.total_paid_amount

ORDER BY ch.claim_id

LIMIT 200;



-- =====================================================================
-- 17. CLAIM HEADER -> ELIGIBILITY -> MEMBER
--
-- This is one of the core payer Fact relationships.
--
-- Member
--      ↓
-- Eligibility
--      ↓
-- Claim Header
-- =====================================================================

SELECT
    ch.claim_id,

    m.member_id,
    m.first_name,
    m.last_name,

    e.eligibility_id,
    e.record_version,
    e.eligibility_status,

    e.product_id,
    e.benefit_plan_id,
    e.group_id,
    e.subgroup_id,

    ch.service_from_date,
    ch.service_to_date,

    ch.claim_type,
    ch.claim_status,

    ch.total_billed_amount,
    ch.total_allowed_amount,
    ch.total_paid_amount

FROM payer_01_dev.bronze.claim_header_raw ch

INNER JOIN payer_01_dev.bronze.eligibility_raw e
    ON ch.eligibility_id = e.eligibility_id

INNER JOIN payer_01_dev.bronze.member_raw m
    ON ch.member_id = m.member_id

LIMIT 200;



-- =====================================================================
-- 18. CLAIM -> PROVIDER RELATIONSHIP
--
-- Claim Header stores practitioner_role_id.
--
-- That one Role lets us resolve:
--
-- Practitioner
-- Supplier
-- Supplier Location
-- =====================================================================

SELECT
    ch.claim_id,
    ch.service_from_date,

    pr.practitioner_role_id,

    p.practitioner_id,
    p.first_name AS practitioner_first_name,
    p.last_name  AS practitioner_last_name,

    pr.role_specialty,

    s.supplier_id,
    s.supplier_name,

    sl.supplier_location_id,
    sl.location_type,
    sl.place_of_service_code,

    ch.network_status,
    ch.network_tier,

    ch.total_paid_amount

FROM payer_01_dev.bronze.claim_header_raw ch

INNER JOIN payer_01_dev.bronze.practitioner_role_raw pr
    ON ch.practitioner_role_id = pr.practitioner_role_id

INNER JOIN payer_01_dev.bronze.practitioner_raw p
    ON pr.practitioner_id = p.practitioner_id

INNER JOIN payer_01_dev.bronze.supplier_raw s
    ON pr.supplier_id = s.supplier_id

INNER JOIN payer_01_dev.bronze.supplier_location_raw sl
    ON pr.supplier_location_id = sl.supplier_location_id

LIMIT 200;



-- =====================================================================
-- 19. END-TO-END HEALTHCARE JOIN
--
-- This query connects nearly the whole business model:
--
-- Member
--   ↓
-- Eligibility
--   ↓
-- Product / Plan / Group / Subgroup
--   ↓
-- Claim Header
--   ↓
-- Claim Line
--   ↓
-- Practitioner Role
--   ↓
-- Practitioner / Supplier / Supplier Location
-- =====================================================================

SELECT
    -- Member
    m.member_id,
    m.family_id,
    m.relationship_to_subscriber,

    -- Eligibility
    e.eligibility_id,
    e.eligibility_status,

    -- Coverage hierarchy
    p.product_id,
    p.line_of_business,
    p.product_type,
    bp.benefit_plan_id,
    g.group_id,
    sg.subgroup_id,

    -- Claim
    ch.claim_id,
    ch.claim_type,
    ch.service_from_date,
    ch.claim_status,

    -- Claim line
    cl.claim_line_id,
    cl.line_number,
    cl.service_category,
    cl.procedure_code,
    cl.diagnosis_code,

    CAST(cl.billed_amount AS DECIMAL(18,2))
        AS billed_amount,

    CAST(cl.allowed_amount AS DECIMAL(18,2))
        AS allowed_amount,

    CAST(cl.paid_amount AS DECIMAL(18,2))
        AS paid_amount,

    -- Provider
    prac.practitioner_id,
    pr.role_specialty,

    supp.supplier_id,
    supp.supplier_name,

    loc.supplier_location_id,
    loc.place_of_service_code

FROM payer_01_dev.bronze.member_raw m

INNER JOIN payer_01_dev.bronze.eligibility_raw e
    ON m.member_id = e.member_id

INNER JOIN payer_01_dev.bronze.product_raw p
    ON e.product_id = p.product_id

INNER JOIN payer_01_dev.bronze.benefit_plan_raw bp
    ON e.benefit_plan_id = bp.benefit_plan_id

INNER JOIN payer_01_dev.bronze.group_raw g
    ON e.group_id = g.group_id

INNER JOIN payer_01_dev.bronze.subgroup_raw sg
    ON e.subgroup_id = sg.subgroup_id

INNER JOIN payer_01_dev.bronze.claim_header_raw ch
    ON e.eligibility_id = ch.eligibility_id

INNER JOIN payer_01_dev.bronze.claim_line_raw cl
    ON ch.claim_id = cl.claim_id

INNER JOIN payer_01_dev.bronze.practitioner_role_raw pr
    ON ch.practitioner_role_id = pr.practitioner_role_id

INNER JOIN payer_01_dev.bronze.practitioner_raw prac
    ON pr.practitioner_id = prac.practitioner_id

INNER JOIN payer_01_dev.bronze.supplier_raw supp
    ON pr.supplier_id = supp.supplier_id

INNER JOIN payer_01_dev.bronze.supplier_location_raw loc
    ON pr.supplier_location_id = loc.supplier_location_id

LIMIT 500;



-- =====================================================================
-- 20. BASIC HEALTHCARE ANALYTICS:
--     CLAIM SPEND BY LINE OF BUSINESS
--
-- This is the first example of how the model eventually supports Gold.
-- =====================================================================

SELECT
    p.line_of_business,

    COUNT(DISTINCT m.member_id)
        AS distinct_members,

    COUNT(DISTINCT ch.claim_id)
        AS claim_count,

    COUNT(cl.claim_line_id)
        AS claim_line_count,

    ROUND(
        SUM(
            CAST(
                cl.billed_amount
                AS DECIMAL(18,2)
            )
        ),
        2
    ) AS total_billed,

    ROUND(
        SUM(
            CAST(
                cl.allowed_amount
                AS DECIMAL(18,2)
            )
        ),
        2
    ) AS total_allowed,

    ROUND(
        SUM(
            CAST(
                cl.paid_amount
                AS DECIMAL(18,2)
            )
        ),
        2
    ) AS total_paid,

    ROUND(
        SUM(
            CAST(
                cl.member_responsibility_amount
                AS DECIMAL(18,2)
            )
        ),
        2
    ) AS member_responsibility

FROM payer_01_dev.bronze.claim_header_raw ch

INNER JOIN payer_01_dev.bronze.claim_line_raw cl
    ON ch.claim_id = cl.claim_id

INNER JOIN payer_01_dev.bronze.member_raw m
    ON ch.member_id = m.member_id

INNER JOIN payer_01_dev.bronze.product_raw p
    ON ch.product_id = p.product_id

GROUP BY p.line_of_business

ORDER BY total_paid DESC;