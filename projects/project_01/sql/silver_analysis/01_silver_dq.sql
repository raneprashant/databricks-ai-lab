-- ============================================================
-- Project 01 - Healthcare Payer
-- Silver Data Quality Validation
-- File: 01_silver_dq.sql
-- ============================================================

-- 1. SILVER ROW-COUNT / SCD2 SUMMARY
SELECT 'member' AS table_name, COUNT(*) AS total_rows,
       SUM(CASE WHEN __END_AT IS NULL THEN 1 ELSE 0 END) AS current_rows,
       SUM(CASE WHEN __END_AT IS NOT NULL THEN 1 ELSE 0 END) AS historical_rows
FROM payer_01_dev.silver.member
UNION ALL
SELECT 'product', COUNT(*), SUM(CASE WHEN __END_AT IS NULL THEN 1 ELSE 0 END), SUM(CASE WHEN __END_AT IS NOT NULL THEN 1 ELSE 0 END)
FROM payer_01_dev.silver.product
UNION ALL
SELECT 'benefit_plan', COUNT(*), SUM(CASE WHEN __END_AT IS NULL THEN 1 ELSE 0 END), SUM(CASE WHEN __END_AT IS NOT NULL THEN 1 ELSE 0 END)
FROM payer_01_dev.silver.benefit_plan
UNION ALL
SELECT 'group', COUNT(*), SUM(CASE WHEN __END_AT IS NULL THEN 1 ELSE 0 END), SUM(CASE WHEN __END_AT IS NOT NULL THEN 1 ELSE 0 END)
FROM payer_01_dev.silver.`group`
UNION ALL
SELECT 'subgroup', COUNT(*), SUM(CASE WHEN __END_AT IS NULL THEN 1 ELSE 0 END), SUM(CASE WHEN __END_AT IS NOT NULL THEN 1 ELSE 0 END)
FROM payer_01_dev.silver.subgroup
UNION ALL
SELECT 'practitioner', COUNT(*), SUM(CASE WHEN __END_AT IS NULL THEN 1 ELSE 0 END), SUM(CASE WHEN __END_AT IS NOT NULL THEN 1 ELSE 0 END)
FROM payer_01_dev.silver.practitioner
UNION ALL
SELECT 'supplier', COUNT(*), SUM(CASE WHEN __END_AT IS NULL THEN 1 ELSE 0 END), SUM(CASE WHEN __END_AT IS NOT NULL THEN 1 ELSE 0 END)
FROM payer_01_dev.silver.supplier
UNION ALL
SELECT 'supplier_location', COUNT(*), SUM(CASE WHEN __END_AT IS NULL THEN 1 ELSE 0 END), SUM(CASE WHEN __END_AT IS NOT NULL THEN 1 ELSE 0 END)
FROM payer_01_dev.silver.supplier_location
UNION ALL
SELECT 'practitioner_role', COUNT(*), SUM(CASE WHEN __END_AT IS NULL THEN 1 ELSE 0 END), SUM(CASE WHEN __END_AT IS NOT NULL THEN 1 ELSE 0 END)
FROM payer_01_dev.silver.practitioner_role
UNION ALL
SELECT 'address', COUNT(*), SUM(CASE WHEN __END_AT IS NULL THEN 1 ELSE 0 END), SUM(CASE WHEN __END_AT IS NOT NULL THEN 1 ELSE 0 END)
FROM payer_01_dev.silver.address
UNION ALL
SELECT 'entity_address', COUNT(*), SUM(CASE WHEN __END_AT IS NULL THEN 1 ELSE 0 END), SUM(CASE WHEN __END_AT IS NOT NULL THEN 1 ELSE 0 END)
FROM payer_01_dev.silver.entity_address
UNION ALL
SELECT 'claim_header', COUNT(*), SUM(CASE WHEN __END_AT IS NULL THEN 1 ELSE 0 END), SUM(CASE WHEN __END_AT IS NOT NULL THEN 1 ELSE 0 END)
FROM payer_01_dev.silver.claim_header
UNION ALL
SELECT 'claim_line', COUNT(*), SUM(CASE WHEN __END_AT IS NULL THEN 1 ELSE 0 END), SUM(CASE WHEN __END_AT IS NOT NULL THEN 1 ELSE 0 END)
FROM payer_01_dev.silver.claim_line
ORDER BY table_name;

-- 2. DUPLICATE CURRENT SCD2 BUSINESS KEYS
SELECT 'member' AS table_name, COUNT(*) AS issue_count FROM (
  SELECT member_id FROM payer_01_dev.silver.member WHERE __END_AT IS NULL GROUP BY member_id HAVING COUNT(*) > 1
)
UNION ALL SELECT 'product', COUNT(*) FROM (
  SELECT product_id FROM payer_01_dev.silver.product WHERE __END_AT IS NULL GROUP BY product_id HAVING COUNT(*) > 1
)
UNION ALL SELECT 'benefit_plan', COUNT(*) FROM (
  SELECT benefit_plan_id FROM payer_01_dev.silver.benefit_plan WHERE __END_AT IS NULL GROUP BY benefit_plan_id HAVING COUNT(*) > 1
)
UNION ALL SELECT 'group', COUNT(*) FROM (
  SELECT group_id FROM payer_01_dev.silver.`group` WHERE __END_AT IS NULL GROUP BY group_id HAVING COUNT(*) > 1
)
UNION ALL SELECT 'subgroup', COUNT(*) FROM (
  SELECT subgroup_id FROM payer_01_dev.silver.subgroup WHERE __END_AT IS NULL GROUP BY subgroup_id HAVING COUNT(*) > 1
)
UNION ALL SELECT 'practitioner', COUNT(*) FROM (
  SELECT practitioner_id FROM payer_01_dev.silver.practitioner WHERE __END_AT IS NULL GROUP BY practitioner_id HAVING COUNT(*) > 1
)
UNION ALL SELECT 'supplier', COUNT(*) FROM (
  SELECT supplier_id FROM payer_01_dev.silver.supplier WHERE __END_AT IS NULL GROUP BY supplier_id HAVING COUNT(*) > 1
)
UNION ALL SELECT 'supplier_location', COUNT(*) FROM (
  SELECT supplier_location_id FROM payer_01_dev.silver.supplier_location WHERE __END_AT IS NULL GROUP BY supplier_location_id HAVING COUNT(*) > 1
)
UNION ALL SELECT 'practitioner_role', COUNT(*) FROM (
  SELECT practitioner_role_id FROM payer_01_dev.silver.practitioner_role WHERE __END_AT IS NULL GROUP BY practitioner_role_id HAVING COUNT(*) > 1
)
UNION ALL SELECT 'address', COUNT(*) FROM (
  SELECT address_id FROM payer_01_dev.silver.address WHERE __END_AT IS NULL GROUP BY address_id HAVING COUNT(*) > 1
)
UNION ALL SELECT 'entity_address', COUNT(*) FROM (
  SELECT entity_address_id FROM payer_01_dev.silver.entity_address WHERE __END_AT IS NULL GROUP BY entity_address_id HAVING COUNT(*) > 1
)
UNION ALL SELECT 'claim_header', COUNT(*) FROM (
  SELECT claim_id FROM payer_01_dev.silver.claim_header WHERE __END_AT IS NULL GROUP BY claim_id HAVING COUNT(*) > 1
)
UNION ALL SELECT 'claim_line', COUNT(*) FROM (
  SELECT claim_line_id FROM payer_01_dev.silver.claim_line WHERE __END_AT IS NULL GROUP BY claim_line_id HAVING COUNT(*) > 1
)
ORDER BY table_name;

-- 3. TEMPORAL / DATE QUALITY
SELECT 'member.death_before_birth' AS check_name, COUNT(*) AS issue_count
FROM payer_01_dev.silver.member
WHERE __END_AT IS NULL AND death_date IS NOT NULL AND death_date < date_of_birth
UNION ALL
SELECT 'product.termination_before_effective', COUNT(*)
FROM payer_01_dev.silver.product
WHERE __END_AT IS NULL AND termination_date IS NOT NULL AND termination_date < effective_date
UNION ALL
SELECT 'benefit_plan.termination_before_effective', COUNT(*)
FROM payer_01_dev.silver.benefit_plan
WHERE __END_AT IS NULL AND termination_date IS NOT NULL AND termination_date < effective_date
UNION ALL
SELECT 'group.termination_before_effective', COUNT(*)
FROM payer_01_dev.silver.`group`
WHERE __END_AT IS NULL AND termination_date IS NOT NULL AND termination_date < effective_date
UNION ALL
SELECT 'subgroup.termination_before_effective', COUNT(*)
FROM payer_01_dev.silver.subgroup
WHERE __END_AT IS NULL AND termination_date IS NOT NULL AND termination_date < effective_date
UNION ALL
SELECT 'practitioner.termination_before_effective', COUNT(*)
FROM payer_01_dev.silver.practitioner
WHERE __END_AT IS NULL AND termination_date IS NOT NULL AND termination_date < effective_date
UNION ALL
SELECT 'supplier.contract_termination_before_effective', COUNT(*)
FROM payer_01_dev.silver.supplier
WHERE __END_AT IS NULL AND contract_termination_date IS NOT NULL AND contract_termination_date < contract_effective_date
UNION ALL
SELECT 'supplier_location.termination_before_effective', COUNT(*)
FROM payer_01_dev.silver.supplier_location
WHERE __END_AT IS NULL AND termination_date IS NOT NULL AND termination_date < effective_date
UNION ALL
SELECT 'practitioner_role.termination_before_effective', COUNT(*)
FROM payer_01_dev.silver.practitioner_role
WHERE __END_AT IS NULL AND termination_date IS NOT NULL AND termination_date < effective_date
UNION ALL
SELECT 'entity_address.termination_before_effective', COUNT(*)
FROM payer_01_dev.silver.entity_address
WHERE __END_AT IS NULL AND termination_date IS NOT NULL AND termination_date < effective_date
UNION ALL
SELECT 'eligibility.coverage_end_before_start', COUNT(*)
FROM payer_01_dev.silver.eligibility
WHERE coverage_end_date IS NOT NULL AND coverage_end_date < coverage_start_date
UNION ALL
SELECT 'claim_header.service_to_before_service_from', COUNT(*)
FROM payer_01_dev.silver.claim_header
WHERE __END_AT IS NULL AND service_to_date < service_from_date
UNION ALL
SELECT 'claim_header.discharge_before_admission', COUNT(*)
FROM payer_01_dev.silver.claim_header
WHERE __END_AT IS NULL AND admission_date IS NOT NULL AND discharge_date IS NOT NULL AND discharge_date < admission_date
UNION ALL
SELECT 'claim_header.received_before_service_end', COUNT(*)
FROM payer_01_dev.silver.claim_header
WHERE __END_AT IS NULL AND received_date < service_to_date
UNION ALL
SELECT 'claim_header.adjudication_before_received', COUNT(*)
FROM payer_01_dev.silver.claim_header
WHERE __END_AT IS NULL AND adjudication_date < received_date
ORDER BY check_name;

-- 4A. ELIGIBILITY DUPLICATE ID CHECK
SELECT COUNT(*) AS duplicate_eligibility_id_count
FROM (
  SELECT eligibility_id
  FROM payer_01_dev.silver.eligibility
  GROUP BY eligibility_id
  HAVING COUNT(*) > 1
);

-- 4B. ELIGIBILITY DUPLICATE MEMBER + VERSION CHECK
SELECT COUNT(*) AS duplicate_member_version_count
FROM (
  SELECT member_id, record_version
  FROM payer_01_dev.silver.eligibility
  GROUP BY member_id, record_version
  HAVING COUNT(*) > 1
);

-- 4C. ONE DERIVED LATEST ELIGIBILITY ROW PER MEMBER
WITH ranked_eligibility AS (
  SELECT member_id, eligibility_id, record_version, update_ts,
         ROW_NUMBER() OVER (
           PARTITION BY member_id
           ORDER BY record_version DESC, update_ts DESC, eligibility_id DESC
         ) AS rn
  FROM payer_01_dev.silver.eligibility
)
SELECT COUNT(*) AS latest_rows,
       COUNT(DISTINCT member_id) AS distinct_members
FROM ranked_eligibility
WHERE rn = 1;

-- 4D. INFORMATIONAL ONLY: MULTIPLE SOURCE-CURRENT ROWS
SELECT COUNT(*) AS members_with_multiple_source_current_rows
FROM (
  SELECT member_id
  FROM payer_01_dev.silver.eligibility
  WHERE source_current_record_flag = TRUE
  GROUP BY member_id
  HAVING COUNT(*) > 1
);

-- 5. CURRENT CLAIM HEADER DQ
SELECT 'claim_header.invalid_claim_line_count' AS check_name, COUNT(*) AS issue_count
FROM payer_01_dev.silver.claim_header
WHERE __END_AT IS NULL AND (claim_line_count IS NULL OR claim_line_count <= 0)
UNION ALL
SELECT 'claim_header.invalid_financial_order', COUNT(*)
FROM payer_01_dev.silver.claim_header
WHERE __END_AT IS NULL AND (
  total_billed_amount < total_allowed_amount OR
  total_allowed_amount < total_paid_amount OR
  total_paid_amount < 0 OR
  member_responsibility_amount < 0
)
UNION ALL
SELECT 'claim_header.financial_reconciliation_mismatch', COUNT(*)
FROM payer_01_dev.silver.claim_header
WHERE __END_AT IS NULL AND ABS(total_allowed_amount - total_paid_amount - member_responsibility_amount) > CAST(0.01 AS DECIMAL(18,2))
UNION ALL
SELECT 'claim_header.null_update_ts', COUNT(*)
FROM payer_01_dev.silver.claim_header
WHERE __END_AT IS NULL AND update_ts IS NULL
ORDER BY check_name;

-- 6. CURRENT CLAIM LINE DQ
SELECT 'claim_line.invalid_line_number' AS check_name, COUNT(*) AS issue_count
FROM payer_01_dev.silver.claim_line
WHERE __END_AT IS NULL AND (line_number IS NULL OR line_number <= 0)
UNION ALL
SELECT 'claim_line.invalid_units', COUNT(*)
FROM payer_01_dev.silver.claim_line
WHERE __END_AT IS NULL AND (units IS NULL OR units <= 0)
UNION ALL
SELECT 'claim_line.invalid_financial_order', COUNT(*)
FROM payer_01_dev.silver.claim_line
WHERE __END_AT IS NULL AND (
  billed_amount < allowed_amount OR
  allowed_amount < paid_amount OR
  paid_amount < 0 OR
  member_responsibility_amount < 0
)
UNION ALL
SELECT 'claim_line.financial_reconciliation_mismatch', COUNT(*)
FROM payer_01_dev.silver.claim_line
WHERE __END_AT IS NULL AND ABS(allowed_amount - paid_amount - member_responsibility_amount) > CAST(0.01 AS DECIMAL(18,2))
UNION ALL
SELECT 'claim_line.null_service_date', COUNT(*)
FROM payer_01_dev.silver.claim_line
WHERE __END_AT IS NULL AND service_date IS NULL
UNION ALL
SELECT 'claim_line.null_update_ts', COUNT(*)
FROM payer_01_dev.silver.claim_line
WHERE __END_AT IS NULL AND update_ts IS NULL
ORDER BY check_name;

-- 7. CLAIM HEADER VS CURRENT CLAIM LINE RECONCILIATION
WITH current_headers AS (
  SELECT * FROM payer_01_dev.silver.claim_header WHERE __END_AT IS NULL
),
current_lines AS (
  SELECT * FROM payer_01_dev.silver.claim_line WHERE __END_AT IS NULL
),
line_rollup AS (
  SELECT claim_id,
         COUNT(*) AS actual_line_count,
         SUM(billed_amount) AS line_billed_amount,
         SUM(allowed_amount) AS line_allowed_amount,
         SUM(paid_amount) AS line_paid_amount,
         SUM(member_responsibility_amount) AS line_member_responsibility_amount
  FROM current_lines
  GROUP BY claim_id
),
comparison AS (
  SELECT h.claim_id,
         h.claim_line_count,
         COALESCE(l.actual_line_count, 0) AS actual_line_count,
         h.total_billed_amount,
         COALESCE(l.line_billed_amount, CAST(0 AS DECIMAL(18,2))) AS line_billed_amount,
         h.total_allowed_amount,
         COALESCE(l.line_allowed_amount, CAST(0 AS DECIMAL(18,2))) AS line_allowed_amount,
         h.total_paid_amount,
         COALESCE(l.line_paid_amount, CAST(0 AS DECIMAL(18,2))) AS line_paid_amount,
         h.member_responsibility_amount,
         COALESCE(l.line_member_responsibility_amount, CAST(0 AS DECIMAL(18,2))) AS line_member_responsibility_amount
  FROM current_headers h
  LEFT JOIN line_rollup l ON h.claim_id = l.claim_id
)
SELECT COUNT(*) AS mismatched_claim_count
FROM comparison
WHERE claim_line_count <> actual_line_count
   OR ABS(total_billed_amount - line_billed_amount) > CAST(0.01 AS DECIMAL(18,2))
   OR ABS(total_allowed_amount - line_allowed_amount) > CAST(0.01 AS DECIMAL(18,2))
   OR ABS(total_paid_amount - line_paid_amount) > CAST(0.01 AS DECIMAL(18,2))
   OR ABS(member_responsibility_amount - line_member_responsibility_amount) > CAST(0.01 AS DECIMAL(18,2));

-- 8. CLAIM HEADER / LINE RECONCILIATION DETAIL
-- Run only if Section 7 returns a non-zero count.
WITH current_headers AS (
  SELECT * FROM payer_01_dev.silver.claim_header WHERE __END_AT IS NULL
),
current_lines AS (
  SELECT * FROM payer_01_dev.silver.claim_line WHERE __END_AT IS NULL
),
line_rollup AS (
  SELECT claim_id,
         COUNT(*) AS actual_line_count,
         SUM(billed_amount) AS line_billed_amount,
         SUM(allowed_amount) AS line_allowed_amount,
         SUM(paid_amount) AS line_paid_amount,
         SUM(member_responsibility_amount) AS line_member_responsibility_amount
  FROM current_lines
  GROUP BY claim_id
)
SELECT h.claim_id,
       h.claim_line_count AS header_line_count,
       COALESCE(l.actual_line_count, 0) AS actual_line_count,
       h.total_billed_amount AS header_billed,
       l.line_billed_amount,
       h.total_allowed_amount AS header_allowed,
       l.line_allowed_amount,
       h.total_paid_amount AS header_paid,
       l.line_paid_amount,
       h.member_responsibility_amount AS header_member_responsibility,
       l.line_member_responsibility_amount
FROM current_headers h
LEFT JOIN line_rollup l ON h.claim_id = l.claim_id
WHERE h.claim_line_count <> COALESCE(l.actual_line_count, 0)
   OR ABS(h.total_billed_amount - COALESCE(l.line_billed_amount, CAST(0 AS DECIMAL(18,2)))) > CAST(0.01 AS DECIMAL(18,2))
   OR ABS(h.total_allowed_amount - COALESCE(l.line_allowed_amount, CAST(0 AS DECIMAL(18,2)))) > CAST(0.01 AS DECIMAL(18,2))
   OR ABS(h.total_paid_amount - COALESCE(l.line_paid_amount, CAST(0 AS DECIMAL(18,2)))) > CAST(0.01 AS DECIMAL(18,2))
   OR ABS(h.member_responsibility_amount - COALESCE(l.line_member_responsibility_amount, CAST(0 AS DECIMAL(18,2)))) > CAST(0.01 AS DECIMAL(18,2))
ORDER BY h.claim_id
LIMIT 100;

-- 9. SCD2 TEMPORAL CHAIN VALIDATION (sample key domains)
WITH member_versions AS (
  SELECT member_id AS business_key, __START_AT, __END_AT,
         LEAD(__START_AT) OVER (PARTITION BY member_id ORDER BY __START_AT) AS next_start
  FROM payer_01_dev.silver.member
),
product_versions AS (
  SELECT product_id AS business_key, __START_AT, __END_AT,
         LEAD(__START_AT) OVER (PARTITION BY product_id ORDER BY __START_AT) AS next_start
  FROM payer_01_dev.silver.product
),
claim_header_versions AS (
  SELECT claim_id AS business_key, __START_AT, __END_AT,
         LEAD(__START_AT) OVER (PARTITION BY claim_id ORDER BY __START_AT) AS next_start
  FROM payer_01_dev.silver.claim_header
),
claim_line_versions AS (
  SELECT claim_line_id AS business_key, __START_AT, __END_AT,
         LEAD(__START_AT) OVER (PARTITION BY claim_line_id ORDER BY __START_AT) AS next_start
  FROM payer_01_dev.silver.claim_line
)
SELECT 'member' AS table_name, COUNT(*) AS issue_count
FROM member_versions
WHERE __END_AT IS NOT NULL AND next_start IS NOT NULL AND __END_AT <> next_start
UNION ALL
SELECT 'product', COUNT(*)
FROM product_versions
WHERE __END_AT IS NOT NULL AND next_start IS NOT NULL AND __END_AT <> next_start
UNION ALL
SELECT 'claim_header', COUNT(*)
FROM claim_header_versions
WHERE __END_AT IS NOT NULL AND next_start IS NOT NULL AND __END_AT <> next_start
UNION ALL
SELECT 'claim_line', COUNT(*)
FROM claim_line_versions
WHERE __END_AT IS NOT NULL AND next_start IS NOT NULL AND __END_AT <> next_start
ORDER BY table_name;
