-- ============================================================
-- Project 01 - Healthcare Payer
-- Gold Validation Gate
--
-- File:
--   90_gold_validation_gate.sql
--
-- Purpose:
--   Fail the end-to-end Lakeflow Job if critical
--   Silver-to-Gold or Gold-detail-to-summary
--   reconciliation checks fail.
--
-- Environment:
--   DEV / TEST / PROD independent.
--
-- Parameters are supplied by the SQL Job task:
--
--   catalog
--   silver_schema
--   gold_schema
--
-- Example:
--
--   DEV
--     catalog       = payer_01_dev
--     silver_schema = silver
--     gold_schema   = gold
--
--   TEST
--     catalog       = payer_01_test
--
--   PROD
--     catalog       = payer_01_prod
-- ============================================================

USE CATALOG IDENTIFIER(:catalog);

WITH metrics AS (

    SELECT


        -- ====================================================
        -- MEMBER RECONCILIATION
        -- ====================================================

        (
            SELECT COUNT(*)

            FROM
                --{{catalog}}.{{silver_schema}}.member
                IDENTIFIER(:silver_schema || '.member')

            WHERE
                __END_AT IS NULL

        ) AS silver_current_members,


        (
            SELECT COUNT(*)

            FROM
                --{{catalog}}.{{gold_schema}}.member_current_coverage
                IDENTIFIER(:gold_schema || '.member_current_coverage')

        ) AS gold_members,


        -- ====================================================
        -- CLAIM HEADER RECONCILIATION
        -- ====================================================

        (
            SELECT COUNT(*)

            FROM
                --{{catalog}}.{{silver_schema}}.claim_header
                IDENTIFIER(:silver_schema || '.claim_header')

            WHERE
                __END_AT IS NULL

        ) AS silver_current_claims,


        (
            SELECT COUNT(*)

            FROM
                --{{catalog}}.{{gold_schema}}.claims_enriched
                IDENTIFIER(:gold_schema || '.claims_enriched')

        ) AS gold_claims,


        -- ====================================================
        -- CLAIM LINE RECONCILIATION
        -- ====================================================

        (
            SELECT COUNT(*)

            FROM
                --{{catalog}}.{{silver_schema}}.claim_line
                IDENTIFIER(:silver_schema || '.claim_line')

            WHERE
                __END_AT IS NULL

        ) AS silver_current_lines,


        (
            SELECT COUNT(*)

            FROM
                --{{catalog}}.{{gold_schema}}.claim_line_enriched
                IDENTIFIER(:gold_schema || '.claim_line_enriched')

        ) AS gold_lines,


        -- ====================================================
        -- MEMBERSHIP SUMMARY RECONCILIATION
        -- ====================================================

        (
            SELECT COUNT(*)

            FROM
                --{{catalog}}.{{gold_schema}}.member_current_coverage
                IDENTIFIER(:gold_schema || '.member_current_coverage')

            WHERE
                is_currently_covered = TRUE

        ) AS covered_members,


        (
            SELECT COALESCE(
                SUM(member_count),
                0
            )

            FROM
                --{{catalog}}.{{gold_schema}}.membership_summary
                IDENTIFIER(:gold_schema || '.membership_summary')

        ) AS membership_summary_members,


        -- ====================================================
        -- CLAIM SPEND SUMMARY COUNT RECONCILIATION
        -- ====================================================

        (
            SELECT COALESCE(
                SUM(claim_count),
                0
            )

            FROM
                --{{catalog}}.{{gold_schema}}.claim_spend_summary
                IDENTIFIER(:gold_schema || '.claim_spend_summary')

        ) AS claim_spend_summary_claims,


        -- ====================================================
        -- PROVIDER SUMMARY LINE COUNT RECONCILIATION
        -- ====================================================

        (
            SELECT COALESCE(
                SUM(claim_line_count),
                0
            )

            FROM
                --{{catalog}}.{{gold_schema}}.provider_utilization_summary
                IDENTIFIER(:gold_schema || '.provider_utilization_summary')

        ) AS provider_summary_lines,


        -- ====================================================
        -- CLAIM HEADER DETAIL FINANCIALS
        -- ====================================================

        (
            SELECT COALESCE(
                SUM(total_billed_amount),
                0
            )

            FROM
                --{{catalog}}.{{gold_schema}}.claims_enriched
                IDENTIFIER(:gold_schema || '.claims_enriched')

        ) AS claim_detail_billed,


        (
            SELECT COALESCE(
                SUM(total_allowed_amount),
                0
            )

            FROM
                --{{catalog}}.{{gold_schema}}.claims_enriched
                IDENTIFIER(:gold_schema || '.claims_enriched')

        ) AS claim_detail_allowed,


        (
            SELECT COALESCE(
                SUM(total_paid_amount),
                0
            )

            FROM
                --{{catalog}}.{{gold_schema}}.claims_enriched
                IDENTIFIER(:gold_schema || '.claims_enriched')

        ) AS claim_detail_paid,


        (
            SELECT COALESCE(
                SUM(member_responsibility_amount),
                0
            )

            FROM
                --{{catalog}}.{{gold_schema}}.claims_enriched
                IDENTIFIER(:gold_schema || '.claims_enriched')

        ) AS claim_detail_member_resp,


        -- ====================================================
        -- CLAIM SPEND SUMMARY FINANCIALS
        -- ====================================================

        (
            SELECT COALESCE(
                SUM(total_billed_amount),
                0
            )

            FROM
                --{{catalog}}.{{gold_schema}}.claim_spend_summary
                IDENTIFIER(:gold_schema || '.claim_spend_summary')

        ) AS claim_summary_billed,


        (
            SELECT COALESCE(
                SUM(total_allowed_amount),
                0
            )

            FROM
                --{{catalog}}.{{gold_schema}}.claim_spend_summary
                IDENTIFIER(:gold_schema || '.claim_spend_summary')

        ) AS claim_summary_allowed,


        (
            SELECT COALESCE(
                SUM(total_paid_amount),
                0
            )

            FROM
                --{{catalog}}.{{gold_schema}}.claim_spend_summary
                IDENTIFIER(:gold_schema || '.claim_spend_summary')

        ) AS claim_summary_paid,


        (
            SELECT COALESCE(
                SUM(member_responsibility_amount),
                0
            )

            FROM
                --{{catalog}}.{{gold_schema}}.claim_spend_summary
                IDENTIFIER(:gold_schema || '.claim_spend_summary')

        ) AS claim_summary_member_resp,


        -- ====================================================
        -- CLAIM LINE DETAIL FINANCIALS
        -- ====================================================

        (
            SELECT COALESCE(
                SUM(line_billed_amount),
                0
            )

            FROM
                --{{catalog}}.{{gold_schema}}.claim_line_enriched
                IDENTIFIER(:gold_schema || '.claim_line_enriched')

        ) AS line_detail_billed,


        (
            SELECT COALESCE(
                SUM(line_allowed_amount),
                0
            )

            FROM
                --{{catalog}}.{{gold_schema}}.claim_line_enriched
                IDENTIFIER(:gold_schema || '.claim_line_enriched')

        ) AS line_detail_allowed,


        (
            SELECT COALESCE(
                SUM(line_paid_amount),
                0
            )

            FROM
                --{{catalog}}.{{gold_schema}}.claim_line_enriched
                IDENTIFIER(:gold_schema || '.claim_line_enriched')

        ) AS line_detail_paid,


        (
            SELECT COALESCE(
                SUM(line_member_responsibility_amount),
                0
            )

            FROM
                --{{catalog}}.{{gold_schema}}.claim_line_enriched
                IDENTIFIER(:gold_schema || '.claim_line_enriched')

        ) AS line_detail_member_resp,


        -- ====================================================
        -- PROVIDER UTILIZATION SUMMARY FINANCIALS
        -- ====================================================

        (
            SELECT COALESCE(
                SUM(total_billed_amount),
                0
            )

            FROM
                --{{catalog}}.{{gold_schema}}.provider_utilization_summary
                IDENTIFIER(:gold_schema || '.provider_utilization_summary')

        ) AS provider_summary_billed,


        (
            SELECT COALESCE(
                SUM(total_allowed_amount),
                0
            )

            FROM
                --{{catalog}}.{{gold_schema}}.provider_utilization_summary
                IDENTIFIER(:gold_schema || '.provider_utilization_summary')

        ) AS provider_summary_allowed,


        (
            SELECT COALESCE(
                SUM(total_paid_amount),
                0
            )

            FROM
                --{{catalog}}.{{gold_schema}}.provider_utilization_summary
                IDENTIFIER(:gold_schema || '.provider_utilization_summary')

        ) AS provider_summary_paid,


        (
            SELECT COALESCE(
                SUM(member_responsibility_amount),
                0
            )

            FROM
                --{{catalog}}.{{gold_schema}}.provider_utilization_summary
                IDENTIFIER(:gold_schema || '.provider_utilization_summary')

        ) AS provider_summary_member_resp

)


-- ============================================================
-- VALIDATION GATE
--
-- assert_true returns NULL when all checks pass.
--
-- If ANY condition is FALSE, Databricks raises an exception
-- and therefore fails Task 07.
-- ============================================================

SELECT

    assert_true(

           silver_current_members
           =
           gold_members


       AND silver_current_claims
           =
           gold_claims


       AND silver_current_lines
           =
           gold_lines


       AND covered_members
           =
           membership_summary_members


       AND gold_claims
           =
           claim_spend_summary_claims


       AND gold_lines
           =
           provider_summary_lines


       -- ----------------------------------------------------
       -- CLAIM DETAIL VS CLAIM SUMMARY
       -- ----------------------------------------------------

       AND ABS(
           claim_detail_billed
           - claim_summary_billed
       ) <= 0.01


       AND ABS(
           claim_detail_allowed
           - claim_summary_allowed
       ) <= 0.01


       AND ABS(
           claim_detail_paid
           - claim_summary_paid
       ) <= 0.01


       AND ABS(
           claim_detail_member_resp
           - claim_summary_member_resp
       ) <= 0.01


       -- ----------------------------------------------------
       -- CLAIM LINE DETAIL VS PROVIDER SUMMARY
       -- ----------------------------------------------------

       AND ABS(
           line_detail_billed
           - provider_summary_billed
       ) <= 0.01


       AND ABS(
           line_detail_allowed
           - provider_summary_allowed
       ) <= 0.01


       AND ABS(
           line_detail_paid
           - provider_summary_paid
       ) <= 0.01


       AND ABS(
           line_detail_member_resp
           - provider_summary_member_resp
       ) <= 0.01,


       'Project 01 Gold validation FAILED. Review Gold reconciliation checks.'

    ) AS validation_result


FROM

    metrics
;