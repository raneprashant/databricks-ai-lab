# Project 01 - Command Reference

This file summarizes the main commands used while building and operating **Project 01 - Healthcare Payer Data Platform**.

Current learning environment:

- Repository: `C:\Projects\databricks-ai-lab`
- Databricks target: `dev`
- Databricks CLI profile: `DATABRICKS_FREE`
- DEV catalog: `payer_01_dev`
- Single Databricks workspace with simulated `dev`, `test`, and `prod` bundle targets

Run the commands from the repository root unless otherwise noted:

```powershell
cd C:\Projects\databricks-ai-lab
```

---

## 1. Validate the Databricks Bundle

### DEV

```powershell
databricks bundle validate `
  --target dev `
  --profile DATABRICKS_FREE
```

**Purpose:** Checks YAML syntax, bundle variables, resource references, paths, and target configuration. It does not deploy or run anything.

Typical success message:

```text
Validation OK!
```

### TEST

```powershell
databricks bundle validate `
  --target test `
  --profile DATABRICKS_FREE
```

### PROD

```powershell
databricks bundle validate `
  --target prod `
  --profile DATABRICKS_FREE
```

---

## 2. Preview Changes with `bundle plan`

### Plan the full DEV target

```powershell
databricks bundle plan `
  --target dev `
  --profile DATABRICKS_FREE
```

**Purpose:** Shows what Databricks intends to add, change, delete, or leave unchanged before deployment.

Example:

```text
Plan: 0 to add, 1 to change, 0 to delete
```

### Plan only the end-to-end Job

```powershell
databricks bundle plan `
  --select jobs.payer_01_end_to_end `
  --target dev `
  --profile DATABRICKS_FREE
```

### Plan only the Gold pipeline

```powershell
databricks bundle plan `
  --select pipelines.payer_01_gold `
  --target dev `
  --profile DATABRICKS_FREE
```

### Plan only the dashboard

```powershell
databricks bundle plan `
  --select dashboards.project_01_healthcare_payer_analytics `
  --target dev `
  --profile DATABRICKS_FREE
```

**Important:** Investigate unexpected `delete` or `recreate` actions before deploying.

---

## 3. Deploy Bundle Resources

### Deploy the full DEV bundle

```powershell
databricks bundle deploy `
  --target dev `
  --profile DATABRICKS_FREE
```

**Purpose:** Creates or updates bundle-managed resources and workspace files. Deployment changes definitions; it does not automatically run pipelines.

### Deploy only the Gold pipeline

```powershell
databricks bundle deploy `
  --select pipelines.payer_01_gold `
  --target dev `
  --profile DATABRICKS_FREE
```

### Deploy only the end-to-end Job

```powershell
databricks bundle deploy `
  --select jobs.payer_01_end_to_end `
  --target dev `
  --profile DATABRICKS_FREE
```

### Force deployment when the dashboard was edited remotely

```powershell
databricks bundle deploy `
  --select jobs.payer_01_end_to_end `
  --force `
  --target dev `
  --profile DATABRICKS_FREE
```

**Purpose:** Allows the local dashboard definition to overwrite remote dashboard edits.

**Use carefully:** Only use `--force` after confirming the local `.lvdash.json` contains the dashboard version you want to preserve.

---

## 4. Run Bundle Resources

### Run the complete end-to-end Job

```powershell
databricks bundle run payer_01_end_to_end `
  --target dev `
  --profile DATABRICKS_FREE
```

**Purpose:** Runs the full Project 01 orchestration:

```text
Bronze Ingestion
        |
        +-----------------------+
        |                       |
Silver Member/Reference   Silver Provider
        |                       |
        +----> Silver Eligibility
                    |
              Silver Claims
                    |
                  Gold
                    |
          Gold Validation Gate
                    |
           Dashboard Refresh
```

This is the main command to use after new incremental files have been uploaded to the landing Volume.

### Run the Gold pipeline only

```powershell
databricks bundle run payer_01_gold `
  --target dev `
  --profile DATABRICKS_FREE
```

**Purpose:** Useful when testing Gold SQL/materialized-view changes without running Bronze and Silver.

### Run Bronze only

```powershell
databricks bundle run payer_01_bronze_ingestion `
  --target dev `
  --profile DATABRICKS_FREE
```

### Run individual Silver pipelines

```powershell
databricks bundle run payer_01_silver_member_reference `
  --target dev `
  --profile DATABRICKS_FREE
```

```powershell
databricks bundle run payer_01_silver_provider `
  --target dev `
  --profile DATABRICKS_FREE
```

```powershell
databricks bundle run payer_01_silver_eligibility `
  --target dev `
  --profile DATABRICKS_FREE
```

```powershell
databricks bundle run payer_01_silver_claims `
  --target dev `
  --profile DATABRICKS_FREE
```

**Purpose:** Direct pipeline execution is useful during development and troubleshooting. Normal end-to-end operation should use `payer_01_end_to_end`.

---

## 5. Target Selection

The `--target` argument determines which logical environment the bundle uses.

### DEV

```powershell
databricks bundle run payer_01_end_to_end `
  --target dev `
  --profile DATABRICKS_FREE
```

### TEST

```powershell
databricks bundle run payer_01_end_to_end `
  --target test `
  --profile DATABRICKS_FREE
```

### PROD

```powershell
databricks bundle run payer_01_end_to_end `
  --target prod `
  --profile DATABRICKS_FREE
```

**Concept:** The logical resource name is the same across targets, but each target can resolve to a different physical Job, Pipeline, Dashboard, catalog, and bundle deployment state.

---

## 6. Bind an Existing Manual Resource to the Bundle

The end-to-end Job was first created manually in the Databricks UI and then adopted by the bundle.

```powershell
databricks bundle deployment bind `
  payer_01_end_to_end `
  461583194558795 `
  --target dev `
  --profile DATABRICKS_FREE
```

**Purpose:** Tells the bundle that the logical resource:

```text
resources.jobs.payer_01_end_to_end
```

is the same existing Databricks Job with ID:

```text
461583194558795
```

This prevents the bundle from creating a duplicate Job. Future deployments update the bound Job.

---

## 7. Dashboard Commands

### Get dashboard metadata

```powershell
databricks lakeview get `
  01f1c27698e9117990ba705754e513c7 `
  --profile DATABRICKS_FREE `
  -o json
```

**Purpose:** Returns dashboard metadata including `dashboard_id`, `display_name`, `parent_path`, lifecycle information, and serialized dashboard data.

### Pull dashboard UI changes back into the local bundle

```powershell
databricks bundle generate dashboard `
  --resource project_01_healthcare_payer_analytics `
  --force `
  --target dev `
  --profile DATABRICKS_FREE
```

**Purpose:** Refreshes the local `.lvdash.json` from the current Databricks dashboard after manual UI edits.

Typical workflow:

```text
Edit dashboard in Databricks UI
        |
Test and Publish
        |
bundle generate dashboard --force
        |
Local .lvdash.json updated
        |
Validate / Plan / Deploy / Git commit
```

### Dashboard execution concept

A dashboard is deployed by the bundle, but is not normally run with:

```text
databricks bundle run <dashboard>
```

Project 01 refreshes the dashboard using the final Dashboard task inside `payer_01_end_to_end`.

---

## 8. Incremental Data Commands

These are Python/PowerShell commands rather than Databricks CLI commands, but they are part of the Project 01 operating flow.

### Create a batch ID

```powershell
$batchId = Get-Date -Format "yyyyMMdd_HHmmss"
```

### Generate incremental data

```powershell
python .\projects\project_01\data_generator\generate_incremental.py `
  --scale medium `
  --batch-id $batchId
```

**Purpose:** Creates a new local incremental source batch. It does not upload files or execute Databricks.

### Display the incremental manifest

```powershell
Import-Csv `
  ".\projects\project_01\generated_data\medium\incremental\$batchId\batch_manifest.csv" |
  Format-Table
```

**Purpose:** Reviews row counts, change types, and generated filenames before upload.

### Upload the incremental batch

```powershell
python .\projects\project_01\data_generator\upload_to_landing.py `
  --scale medium `
  --batch-id $batchId
```

**Purpose:** Uploads the generated batch to the DEV Bronze landing Volume.

### Run the full workflow after upload

```powershell
databricks bundle run payer_01_end_to_end `
  --target dev `
  --profile DATABRICKS_FREE
```

---

## 9. Complete Incremental Execution Sequence

```powershell
# 1. Create a new batch ID
$batchId = Get-Date -Format "yyyyMMdd_HHmmss"

# 2. Generate incremental source data
python .\projects\project_01\data_generator\generate_incremental.py `
  --scale medium `
  --batch-id $batchId

# 3. Review the manifest
Import-Csv `
  ".\projects\project_01\generated_data\medium\incremental\$batchId\batch_manifest.csv" |
  Format-Table

# 4. Upload the batch
python .\projects\project_01\data_generator\upload_to_landing.py `
  --scale medium `
  --batch-id $batchId

# 5. Run Bronze -> Silver -> Gold -> Validation -> Dashboard

databricks bundle run payer_01_end_to_end `
  --target dev `
  --profile DATABRICKS_FREE
```

---


## Base Data Generation Commands

These commands generate the original synthetic source dataset before incremental batches are created.

### Show the planned row counts

```powershell
python .\projects\project_01\data_generator\generate_data.py `
  --scale medium `
  --domain summary
```

**Purpose:** Shows the configured row counts for the selected scale without generating data.

### Generate all base data in dependency order

```powershell
python .\projects\project_01\data_generator\generate_all.py `
  --scale medium
```

**Purpose:** Generates the complete Project 01 base dataset in the required dependency order.

The orchestrated generation order is:

```text
member
supplier
supplier_location
practitioner
practitioner_role
address
entity_address
payer_reference
eligibility
claims
```

### Generate only one domain

Examples:

```powershell
python .\projects\project_01\data_generator\generate_data.py `
  --scale medium `
  --domain member
```

```powershell
python .\projects\project_01\data_generator\generate_data.py `
  --scale medium `
  --domain payer_reference
```

```powershell
python .\projects\project_01\data_generator\generate_data.py `
  --scale medium `
  --domain claims
```

**Purpose:** Regenerates only the selected source domain during development or troubleshooting.

---

## Base Data Validation Commands

Run the local validators after base generation and before uploading files to Databricks.

### Validate Product / Plan / Group / Subgroup relationships

```powershell
python .\projects\project_01\data_generator\validate_payer_reference.py `
  --scale medium
```

### Validate Eligibility history and relationships

```powershell
python .\projects\project_01\data_generator\validate_eligibility.py `
  --scale medium
```

### Validate Address and Entity Address relationships

```powershell
python .\projects\project_01\data_generator\validate_addresses.py `
  --scale medium
```

### Validate Claim Header and Claim Line data

```powershell
python .\projects\project_01\data_generator\validate_claims.py `
  --scale medium
```

Recommended validation order:

```text
generate_all.py
      ↓
validate_payer_reference.py
      ↓
validate_eligibility.py
      ↓
validate_addresses.py
      ↓
validate_claims.py
      ↓
upload_to_landing.py
```

---

## Upload Base Files to the Databricks Landing Volume

```powershell
python .\projects\project_01\data_generator\upload_to_landing.py `
  --scale medium
```

**Purpose:** Uploads the generated base CSV files for all Project 01 domains to the Bronze landing Volume.

Default target pattern:

```text
/Volumes/payer_01_dev/bronze/landing/<domain>/
```

Examples:

```text
/Volumes/payer_01_dev/bronze/landing/member/
/Volumes/payer_01_dev/bronze/landing/eligibility/
/Volumes/payer_01_dev/bronze/landing/claim_header/
/Volumes/payer_01_dev/bronze/landing/claim_line/
```

The upload script copies files only. It does not run Bronze, Silver, Gold, or the end-to-end Job.

---

## Complete Base-Load Workflow

```powershell
# 1. Go to the repository root
cd C:\Projects\databricks-ai-lab

# 2. Review configured row counts
python .\projects\project_01\data_generator\generate_data.py `
  --scale medium `
  --domain summary

# 3. Generate the full base dataset
python .\projects\project_01\data_generator\generate_all.py `
  --scale medium

# 4. Validate payer reference data
python .\projects\project_01\data_generator\validate_payer_reference.py `
  --scale medium

# 5. Validate Eligibility
python .\projects\project_01\data_generator\validate_eligibility.py `
  --scale medium

# 6. Validate Address relationships
python .\projects\project_01\data_generator\validate_addresses.py `
  --scale medium

# 7. Validate Claims
python .\projects\project_01\data_generator\validate_claims.py `
  --scale medium

# 8. Upload the base source files
python .\projects\project_01\data_generator\upload_to_landing.py `
  --scale medium

# 9. Run the complete Databricks workflow
databricks bundle run payer_01_end_to_end `
  --target dev `
  --profile DATABRICKS_FREE
```

**Important:** A true environment rebuild may also require resetting existing Bronze/Silver/Gold state before reprocessing base files. Do not treat the base upload as an ordinary incremental load into an already-populated environment.

---

## Incremental Data Generation Commands

### Create a timestamp-based Batch ID

```powershell
$batchId = Get-Date -Format "yyyyMMdd_HHmmss"
```

Example:

```text
20261008_153701
```

### Generate a new incremental batch

```powershell
python .\projects\project_01\data_generator\generate_incremental.py `
  --scale medium `
  --batch-id $batchId
```

**Purpose:** Generates the next incremental source batch locally.

The generator uses:

- the original base data,
- prior incremental batches,
- the latest known versions of dimension-like business entities,
- new Eligibility events,
- mixed Claim inserts and updates.

### Generate using an explicit Batch ID

```powershell
python .\projects\project_01\data_generator\generate_incremental.py `
  --scale medium `
  --batch-id 20261008_153701
```

### Display the Batch ID

```powershell
$batchId
```

### Review the batch manifest

```powershell
Import-Csv `
  ".\projects\project_01\generated_data\medium\incremental\$batchId\batch_manifest.csv" |
  Format-Table
```

**Purpose:** Reviews domain row counts, change types, and generated filenames before upload.

---

## Upload Incremental Files to the Databricks Landing Volume

```powershell
python .\projects\project_01\data_generator\upload_to_landing.py `
  --scale medium `
  --batch-id $batchId
```

**Purpose:** Uploads only the selected incremental batch into the existing Bronze landing domain folders.

After the upload succeeds, run the full end-to-end Job:

```powershell
databricks bundle run payer_01_end_to_end `
  --target dev `
  --profile DATABRICKS_FREE
```

That processes:

```text
Incremental files
      ↓
Bronze Auto Loader
      ↓
Silver CDC / SCD Type 2
      ↓
Gold materialized views
      ↓
Gold validation gate
      ↓
Dashboard refresh
```

---

## Complete Incremental Batch Workflow

```powershell
# 1. Go to repository root
cd C:\Projects\databricks-ai-lab

# 2. Create a new Batch ID
$batchId = Get-Date -Format "yyyyMMdd_HHmmss"

# 3. Generate the incremental batch
python .\projects\project_01\data_generator\generate_incremental.py `
  --scale medium `
  --batch-id $batchId

# 4. Review the batch manifest
Import-Csv `
  ".\projects\project_01\generated_data\medium\incremental\$batchId\batch_manifest.csv" |
  Format-Table

# 5. Upload the incremental batch
python .\projects\project_01\data_generator\upload_to_landing.py `
  --scale medium `
  --batch-id $batchId

# 6. Run the complete Databricks workflow
databricks bundle run payer_01_end_to_end `
  --target dev `
  --profile DATABRICKS_FREE
```

This is the normal Project 01 process for Batch 001, Batch 002, Batch 003, and future incremental batches.

---


# Git Commands

## 10. Check repository status

```powershell
git status
```

**Purpose:** Shows modified, untracked, staged, and unstaged files plus branch status.

Use this frequently before staging and committing.

---

## 11. Review changes

### All unstaged changes

```powershell
git diff
```

### One file

```powershell
git diff -- databricks.yml
```

Example for the Job YAML:

```powershell
git diff -- resources\payer_01_end_to_end.job.yml
```

**Purpose:** Shows exactly what changed before you stage or commit it.

---

## 12. Stage files

### Stage everything

```powershell
git add .
```

### Stage one file

```powershell
git add databricks.yml
```

or:

```powershell
git add resources\payer_01_end_to_end.job.yml
```

After staging, run:

```powershell
git status
```

again to verify what will be committed.

---

## 13. Commit changes locally

```powershell
git commit -m "Complete Project 01 end-to-end payer data platform"
```

Other useful milestone examples:

```powershell
git commit -m "Add Gold layer and validation SQL"
```

```powershell
git commit -m "Add healthcare analytics dashboard"
```

```powershell
git commit -m "Add end-to-end Lakeflow orchestration job"
```

**Concept:** `git commit` saves the staged changes to the local Git repository.

---

## 14. Push commits to GitHub

```powershell
git push
```

**Purpose:** Sends local commits to the tracked remote branch, normally `origin/main`.

Remember:

```text
git commit = save locally
git push   = send committed changes to GitHub
```

---

## 15. View recent commits

```powershell
git log --oneline -10
```

**Purpose:** Shows the ten most recent commits in compact form.

---

# PowerShell File-Inspection Commands

## 16. List bundle resource YAML files

```powershell
Get-ChildItem .\resources
```

**Purpose:** Shows Pipeline, Job, and Dashboard YAML files in the root `resources` folder.

### List dashboard source files

```powershell
Get-ChildItem .\projects\project_01\dashboards
```

### Display the dashboard resource YAML

```powershell
Get-Content .\resources\project_01_healthcare_payer_analytics.dashboard.yml
```

---

# Project 01 Logical Resource Keys

## Pipelines

```text
payer_01_bronze_ingestion
payer_01_silver_member_reference
payer_01_silver_provider
payer_01_silver_eligibility
payer_01_silver_claims
payer_01_gold
```

## Job

```text
payer_01_end_to_end
```

## Dashboard

```text
project_01_healthcare_payer_analytics
```

---

# Key Command Meanings

## `databricks bundle validate`

Checks configuration validity.

```text
No deployment.
No pipeline execution.
No data processing.
```

## `databricks bundle plan`

Previews deployment changes.

```text
No deployment yet.
```

## `databricks bundle deploy`

Creates or updates Databricks resources and uploaded bundle files.

```text
Deploys definitions.
Does not automatically process new source data.
```

## `databricks bundle run`

Executes a runnable bundle resource such as a Job or Lakeflow pipeline.

## `databricks bundle deployment bind`

Adopts an existing manually-created resource so that the bundle manages that same physical resource instead of creating a duplicate.

## `databricks bundle generate dashboard`

Pulls the current dashboard definition from Databricks into the local `.lvdash.json` file.

---

# Recommended Development Workflow

For a normal code, SQL, or YAML change:

```powershell
# 1. Inspect local changes
git status
git diff

# 2. Validate configuration
databricks bundle validate `
  --target dev `
  --profile DATABRICKS_FREE

# 3. Review what deployment will do
databricks bundle plan `
  --target dev `
  --profile DATABRICKS_FREE

# 4. Deploy
databricks bundle deploy `
  --target dev `
  --profile DATABRICKS_FREE

# 5. Run the required resource
databricks bundle run payer_01_end_to_end `
  --target dev `
  --profile DATABRICKS_FREE

# 6. Review final repository changes
git status
git diff

# 7. Stage
git add .

# 8. Verify staged files
git status

# 9. Commit
git commit -m "Describe the change"

# 10. Push
git push
```

---

# Safety Habits

1. Run `bundle validate` before deployment.
2. Run `bundle plan` before important deployments.
3. Investigate unexpected `delete` or `recreate` operations.
4. Use `--force` only when you intentionally want local dashboard state to replace remote edits.
5. Use `--select` when you want to limit a plan/deployment to a particular resource.
6. Do not use Full Refresh for normal incremental processing.
7. Generate and inspect incremental data before uploading it.
8. Let `payer_01_end_to_end` control the normal Bronze -> Silver -> Gold -> validation -> dashboard sequence.
9. Run `git status` before and after `git add .`.
10. Remember that `git commit` is local and `git push` sends the commit to GitHub.

---

# High-Level Project Command Flow

```text
Edit code / YAML / SQL
        |
        v
bundle validate
        |
        v
bundle plan
        |
        v
bundle deploy
        |
        v
bundle run
        |
        v
Validate results
        |
        v
git status / git diff
        |
        v
git add .
        |
        v
git commit
        |
        v
git push
```

This is the basic development, deployment, execution, and source-control cycle used throughout Project 01.
