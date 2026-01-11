# file: 06_export_gold_to_csv.py
# Purpose: Export Gold tables to SINGLE CSV FILES (not folders) in a Databricks UC Volume path.
# Strategy: write temp folder with coalesce(1) -> rename part file -> cleanup temp.

from pyspark.sql import SparkSession
import re

spark = SparkSession.builder.getOrCreate()

CATALOG = "retail_crm_analytics"
GOLD_SCHEMA = f"{CATALOG}.02_gold"

# UC Volume export directory (must exist + you must have write perms)
EXPORT_DIR = f"/Volumes/{CATALOG}/02_gold/vol_export"

TABLES = [
    "fact_customer_month_incrementality",
    "dim_customer_month_rfm",
    "agg_incrementality_month",
    "agg_incrementality_rfm",
    "agg_incrementality_active_value",
]

def rm_if_exists(path: str):
    try:
        dbutils.fs.rm(path, True)
    except Exception:
        pass

def export_table_as_single_csv(table_fqn: str, export_dir: str, out_filename: str):
    """
    Exports Spark table to a single CSV file named out_filename inside export_dir.
    """
    tmp_dir = f"{export_dir}/__tmp_{out_filename.replace('.csv','')}"
    final_path = f"{export_dir}/{out_filename}"

    # Clean up any previous output
    rm_if_exists(tmp_dir)
    rm_if_exists(final_path)

    df = spark.table(table_fqn)

    # Write to temp folder (Spark will still create a folder)
    (df.coalesce(1)
       .write
       .mode("overwrite")
       .option("header", "true")
       .csv(tmp_dir))

    # Find the single part file created by Spark
    files = dbutils.fs.ls(tmp_dir)
    part_files = [f.path for f in files if re.search(r"/part-.*\.csv$", f.path)]
    if len(part_files) != 1:
        raise RuntimeError(f"Expected exactly 1 part CSV in {tmp_dir}, found {len(part_files)}: {part_files}")

    part_path = part_files[0]

    # Move/rename part file to final named CSV
    dbutils.fs.mv(part_path, final_path)

    # Cleanup temp folder (removes _SUCCESS and remaining metadata)
    rm_if_exists(tmp_dir)

    return final_path

print(f"Export directory: {EXPORT_DIR}")

exported = []
for t in TABLES:
    table_fqn = f"{GOLD_SCHEMA}.{t}"
    out_name = f"{t}.csv"
    final_file = export_table_as_single_csv(table_fqn, EXPORT_DIR, out_name)
    exported.append(final_file)
    print(f"OK: {table_fqn} -> {final_file}")

print("\nDone. Exported files:")
for p in exported:
    print(" -", p)
