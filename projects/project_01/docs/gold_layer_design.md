# Project 01 - Gold Layer Design

## Design Goal

The Gold layer will provide business-ready healthcare payer marts for analytics, dashboards, downstream extracts, and future AI/agent use cases.

Gold will not simply copy Silver tables. It will combine conformed Silver data into business-focused datasets with clear grains.

## Gold Design Principles

- Use current SCD2 rows (`__END_AT IS NULL`) for standard current-state analytics.
- Preserve full Eligibility event history in Silver; derive current/as-of coverage in Gold.
- Use current Claim Header and Claim Line versions for normal reporting.
- Keep Claim SCD2 history in Silver for adjustment-history analysis.
- Avoid duplicating all Silver dimensions into Gold.
- Build a small number of purposeful marts first.
- Make table grain explicit and enforce it through DQ validation.
- Use business keys from Silver for Project 01 v1 rather than introducing warehouse surrogate keys.

## Proposed Gold Tables

### 1. member_current_coverage

**Grain:** One row per member.

**Purpose:** Current Member 360 / enrollment snapshot.

**Primary Silver sources:**
- member
- eligibility
- product
- benefit_plan
- group
- subgroup

**Current Eligibility derivation:**
- Consider Eligibility rows effective for the configured/as-of date.
- Prefer the highest `record_version`.
- Use `update_ts` as a tie-breaker.
- Do not rely only on `source_current_record_flag`.

**Representative columns:**
- member_id
- subscriber_id
- family_id
- relationship_to_subscriber
- member_name attributes
- date_of_birth
- gender
- member_status
- eligibility_id
- eligibility_record_version
- eligibility_status
- coverage_start_date
- coverage_end_date
- line_of_business
- product_id
- product_name
- product_type
- benefit_plan_id
- plan_name
- group_id
- group_name
- subgroup_id
- subgroup_name
- network_id
- coverage_tier
- medical_coverage_flag
- pharmacy_coverage_flag
- dental_coverage_flag
- vision_coverage_flag
- as_of_date

### 2. claims_enriched

**Grain:** One row per current Claim Header (`claim_id`).

**Purpose:** Primary claim-level analytical fact.

**Primary Silver sources:**
- claim_header current version
- exact eligibility event referenced by the claim
- current member
- current product
- current benefit_plan
- current group
- current subgroup
- current practitioner
- current practitioner_role
- current supplier
- current supplier_location

**Representative columns:**
- claim_id
- member_id
- subscriber_id
- family_id
- service_from_date
- service_to_date
- received_date
- adjudication_date
- claim_type
- claim_status
- line_of_business
- product_id
- product_name
- benefit_plan_id
- plan_name
- group_id
- group_name
- subgroup_id
- subgroup_name
- practitioner_id
- practitioner_name
- practitioner_specialty
- practitioner_role_id
- supplier_id
- supplier_name
- supplier_location_id
- location_name
- network_status
- network_tier
- place_of_service_code
- primary_diagnosis_code
- primary_diagnosis_category
- claim_line_count
- total_billed_amount
- total_allowed_amount
- total_paid_amount
- member_responsibility_amount

### 3. claim_line_enriched

**Grain:** One row per current Claim Line (`claim_line_id`).

**Purpose:** Procedure/service-level analytics.

**Primary Silver sources:**
- claim_line current version
- claims_enriched or current claim_header

**Representative columns:**
- claim_line_id
- claim_id
- line_number
- service_date
- service_category
- procedure_code
- revenue_code
- diagnosis_code
- diagnosis_category
- units
- line_status
- billed_amount
- allowed_amount
- paid_amount
- member_responsibility_amount
- member / product / plan / provider attributes inherited from Claim Header context

### 4. membership_summary

**Grain:** One row per reporting combination such as:
`as_of_date + line_of_business + product_id + benefit_plan_id + group_id`

**Purpose:** Enrollment dashboard and membership KPIs.

**Primary Gold source:**
- member_current_coverage

**Measures:**
- member_count
- subscriber_count
- dependent_count
- family_count
- active_member_count
- medical_covered_member_count
- pharmacy_covered_member_count

### 5. claim_spend_summary

**Grain:** One row per:
`service_month + line_of_business + product_id + benefit_plan_id + claim_status + network_status`

**Purpose:** Financial / claim trend dashboards.

**Primary Gold source:**
- claims_enriched

**Measures:**
- claim_count
- member_count
- billed_amount
- allowed_amount
- paid_amount
- member_responsibility_amount
- average_paid_per_claim
- allowed_to_billed_pct
- paid_to_allowed_pct

### 6. provider_utilization_summary

**Grain:** One row per:
`service_month + practitioner_id + supplier_id + supplier_location_id + service_category`

**Purpose:** Provider utilization and cost analytics.

**Primary Gold sources:**
- claims_enriched
- claim_line_enriched

**Measures:**
- claim_count
- claim_line_count
- unique_member_count
- total_units
- billed_amount
- allowed_amount
- paid_amount
- member_responsibility_amount

## Initial Gold Pipeline Dependency

Silver current dimensions + Eligibility
    -> member_current_coverage

Silver current Claim Header + dimensions + exact Eligibility
    -> claims_enriched

Silver current Claim Line + claims_enriched
    -> claim_line_enriched

member_current_coverage
    -> membership_summary

claims_enriched
    -> claim_spend_summary

claims_enriched + claim_line_enriched
    -> provider_utilization_summary

## Claim History Decision

The standard Gold marts will use only current Claim SCD2 versions:

`__END_AT IS NULL`

Historical Claim adjustment versions will remain available in Silver.

If a later use case needs claim-adjustment analytics, create a separate Gold dataset such as:

`claim_adjustment_history`

Do not mix historical and current claim versions into the main `claims_enriched` table because doing so would make ordinary claim counts and financial totals easy to double count.

## Gold v1 Scope

For the first Gold implementation, build in this order:

1. `member_current_coverage`
2. `claims_enriched`
3. `claim_line_enriched`
4. `membership_summary`
5. `claim_spend_summary`
6. `provider_utilization_summary`

The first three establish reusable business-detail marts. The final three are dashboard-oriented aggregates.

## Gold Validation

Gold DQ should verify:

- exactly one row per member in `member_current_coverage`
- exactly one row per current claim_id in `claims_enriched`
- exactly one row per current claim_line_id in `claim_line_enriched`
- no unexpected missing dimension descriptions
- Claim Header totals still reconcile to Silver current Claim Header
- Claim Line totals still reconcile to Silver current Claim Line
- summary totals reconcile to the detailed Gold marts
- no double counting caused by SCD2 history joins

## Future Consumers

The Gold layer will support:

- Databricks SQL dashboards
- scheduled extracts
- CSV / pipe / Excel output use cases
- business KPI analysis
- future schema-aware AI/agent workflows
