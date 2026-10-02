from databricks.connect import DatabricksSession

print("Starting Databricks connection...")

spark = (
    DatabricksSession.builder
    .serverless()
    .profile("DATABRICKS_FREE")
    .getOrCreate()
)

print("Connected successfully to Databricks Serverless.")

print("\nCurrent Databricks context:")
spark.sql("""
    SELECT
        current_user() AS current_user,
        current_catalog() AS current_catalog,
        current_schema() AS current_schema
""").show(truncate=False)

print("\nReading sample table: samples.nyctaxi.trips")

df = spark.read.table("samples.nyctaxi.trips")

print("First 5 rows:")
df.show(5, truncate=False)

print("\nHello Databricks test completed successfully.")

print("\nLet's start file saving operations now!!!")

from pathlib import Path

# Take only a small sample for local testing.
local_df = df.limit(100).toPandas()

# Create a local output folder.
output_dir = Path("output")
output_dir.mkdir(exist_ok=True)

# Write a normal single CSV file on the laptop.
local_file = output_dir / "trips_sample.csv"

local_df.to_csv(local_file, index=False)

print(f"Local CSV created at: {local_file.resolve()}")

print("\nLet's start file saving operations on databricks volumes!!!")

volume_path = "/Volumes/gizmobox/landing/operational_data/customers/output/trips_csv"

(
    df.limit(100)
      .write
      .mode("overwrite")
      .option("header", "true")
      .csv(volume_path)
)

print(f"CSV written to Databricks Volume: {volume_path}")