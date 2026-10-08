# Project 01 - Silver Validation Notes

## Purpose

This document records the Silver-layer validation status, known source-data issues, and important implementation decisions for Project 01.

It is intended to accompany:

- `projects/project_01/sql/silver_analysis/01_silver_dq.sql`
- `projects/project_01/sql/silver_analysis/02_silver_referential_integrity.sql`

## Current Silver Status

The Silver layer is complete for all 14 source domains:

1. Member
2. Product
3. Benefit Plan
4. Group
5. Subgroup
6. Eligibility
7. Practitioner
8. Supplier
9. Supplier Location
10. Practitioner Role
11. Address
12. Entity Address
13. Claim Header
14. Claim Line

Batch 001 and Batch 002 have both been processed through Bronze.

All Silver pipelines have processed Batch 002.

## Silver Processing Patterns

### SCD Type 2

The following domains use Databricks AUTO CDC with SCD Type 2:

- Member
- Product
- Benefit Plan
- Group
- Subgroup
- Practitioner
- Supplier
- Supplier Location
- Practitioner Role
- Address
- Entity Address
- Claim Header
- Claim Line

For these tables:

- `__END_AT IS NULL` identifies the current row.
- Historical business versions are retained.
- Technical metadata columns such as `update_ts`, `_source_file`, `_ingest_timestamp`, etc. are excluded from business-history comparison where appropriate.

### Eligibility

Eligibility is not modeled as SCD Type 2.

Eligibility already contains its own event/history structure through:

- `eligibility_id`
- `record_version`
- `event_type`
- `event_effective_date`
- `transaction_date`

Silver preserves all valid Eligibility events.

The Bronze source field `current_record_flag` is retained in Silver as:

`source_current_record_flag`

This field represents what the source record claimed was current when it arrived.

Because the source feed is append-oriented, older rows are not rewritten from `Y` to `N`. Therefore, the true current Eligibility record must be derived using the latest `record_version`, with `update_ts` as a sequencing/tie-break attribute.

## Batch 002 Incremental Validation

Batch 002 demonstrated repeatable incremental processing across all 14 domains.

The Claim portion intentionally contained:

- 70 new Claim Headers
- 30 updates to existing Claim Headers
- 210 new Claim Lines
- 90 updates to existing Claim Lines

Claim Header SCD Type 2 validation produced:

- 150,200 total versions
- 150,170 current rows
- 30 historical rows

Claim Line SCD Type 2 validation produced:

- 450,595 total versions
- 450,510 current rows
- 85 historical rows

The difference between 90 incoming Claim Line updates and 85 new historical versions is intentional and valid.

Five updated lines were already denied with:

- allowed amount = 0
- paid amount = 0
- member responsibility = 0

Those five messages changed only technical metadata such as `update_ts`. Since technical metadata is excluded from SCD Type 2 business-history tracking, no unnecessary historical version was created.

This demonstrates the distinction between:

- an incoming CDC update message, and
- a true business-state change that warrants a new SCD Type 2 version.

## Known Synthetic Source-Data Issues

### Subgroup Date Defect

The original Medium dataset contained 3 Subgroup rows where:

`termination_date < effective_date`

Root cause:

The original generator selected a Benefit Plan using Line of Business but did not ensure the selected Benefit Plan had a valid temporal overlap with the Group.

Impact:

- Bronze retained all source rows.
- Silver DQ correctly rejected the 3 invalid Subgroup rows.
- Current Silver Subgroup count is therefore 1,497 instead of 1,500.

Generator fix:

`payer_reference_generator.py` was updated so the selected Benefit Plan must temporally overlap the Group period.

A safety check now prevents generation of a Subgroup where:

`termination_date < effective_date`

The existing Medium base dataset was not regenerated in order to avoid rebuilding the entire Bronze and Silver environment.

### Entity Address Date Defect

The original Medium dataset contained 5,082 Entity Address rows where:

`termination_date < effective_date`

Impact:

- Bronze retained all source rows.
- Silver DQ correctly rejected these invalid rows.
- Current Silver Entity Address count is therefore lower than the 300,000 base-source row count.

Generator fix:

`entity_address_generator.py` was updated so an impossible Entity Address relationship is not created when:

`termination_date < effective_date`

The generator can fill remaining target volume using valid alternate correspondence relationships.

The existing Medium base dataset was not regenerated.

## Incremental Generator Improvements

`generate_incremental.py` was updated so later batches:

1. Read the original base data plus all prior incremental batches.
2. Generate new IDs using the cumulative historical state.
3. Update the latest known version of dimension-like business keys.
4. Derive the latest Eligibility row per Member using `record_version`, rather than blindly trusting `current_record_flag`.
5. Generate a mixture of new Claims and updates to existing Claims.
6. Preserve existing `claim_id` and `claim_line_id` values for Claim adjustments so Silver SCD Type 2 can be tested.
7. Mark Claim incremental files as `MIXED_INSERT_UPDATE` in the batch manifest.

## Silver Data Quality Validation

The SQL file:

`01_silver_dq.sql`

validates:

- Silver row counts
- one current SCD Type 2 row per business key
- null/blank business keys
- invalid date ranges
- Eligibility version quality
- Claim financial ordering and reconciliation
- Claim Header versus Claim Line reconciliation
- SCD Type 2 temporal-chain consistency

Validation completed successfully.

## Silver Referential Integrity Validation

The SQL file:

`02_silver_referential_integrity.sql`

validates:

- Product / Benefit Plan / Group / Subgroup hierarchy
- Eligibility relationships
- Provider hierarchy
- Entity Address relationships
- Claim-to-Member
- Claim-to-Eligibility
- Claim-to-Product / Plan / Group / Subgroup
- Claim-to-Practitioner / Supplier / Supplier Location / Practitioner Role
- Claim Line to Claim Header
- Claim service dates against Eligibility coverage
- Claim service dates against Practitioner Role effective periods

Validation completed successfully.

Any non-zero relationship counts caused solely by the known dropped Subgroup source defects are considered understood synthetic-data exceptions until the Medium base dataset is regenerated.

## Gold-Layer Readiness

Silver is considered ready to serve as the conformed foundation for Gold.

Gold should consume:

- current SCD Type 2 dimension rows where `__END_AT IS NULL`
- full Eligibility history where required
- derived current Eligibility for current-state reporting
- current Claim Header and Claim Line versions for standard analytics
- historical Claim versions only for adjustment-history use cases
