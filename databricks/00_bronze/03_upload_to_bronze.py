# file: 03_upload_to_bronze.py
# Purpose: Load synthetic CSVs from UC Volume into Bronze Delta tables with stable schema.
# Fixes: DELTA_FAILED_TO_MERGE_FIELDS by enforcing explicit schemas + overwriteSchema.

from pyspark.sql import SparkSession
from pyspark.sql.types import (
    StructType, StructField,
    LongType, IntegerType, DoubleType, StringType, DateType, TimestampType
)
from pyspark.sql.functions import col, to_date, to_timestamp

spark = SparkSession.builder.getOrCreate()

# =======================
# CONFIG
# =======================
CATALOG = "retail_crm_analytics"
BRONZE_SCHEMA = "00_bronze"

# UC Volume folder where CSVs are placed
VOL_INPUT_DIR = f"/Volumes/{CATALOG}/{BRONZE_SCHEMA}/vol_input"

# Set to True if you want to drop/recreate tables before load (safest if schema drift happened)
DROP_AND_RECREATE = False

# =======================
# TARGET TABLES + SCHEMAS
# =======================

schemas = {
    "dim_customer": StructType([
        StructField("customer_id", LongType(), True),
        StructField("signup_date", DateType(), True),
        StructField("is_active", IntegerType(), True),
        StructField("is_high_value", IntegerType(), True),
        StructField("value_score", DoubleType(), True),
        StructField("activity_score", DoubleType(), True),
    ]),
    "dim_date": StructType([
        StructField("date", DateType(), True),
        StructField("date_id", IntegerType(), True),
        StructField("month_id", IntegerType(), True),
    ]),
    "fact_transaction": StructType([
        StructField("transaction_id", LongType(), True),
        StructField("customer_id", LongType(), True),
        StructField("transaction_ts", TimestampType(), True),
        StructField("channel", StringType(), True),
        StructField("revenue", DoubleType(), True),
        StructField("items", IntegerType(), True),
        StructField("transaction_date", DateType(), True),
        StructField("date_id", IntegerType(), True),
        StructField("month_id", IntegerType(), True),
    ]),
    "fact_crm_exposure": StructType([
        StructField("exposure_id", LongType(), True),
        StructField("customer_id", LongType(), True),
        StructField("exposure_ts", TimestampType(), True),
        StructField("message_channel", StringType(), True),
        StructField("campaign_name", StringType(), True),
        StructField("is_responder", IntegerType(), True),  # synthetic-only; kept for Bronze parity
        StructField("exposure_date", DateType(), True),
        StructField("date_id", IntegerType(), True),
        StructField("month_id", IntegerType(), True),
    ]),
}

files_and_tables = {
    "dim_customer": {
        "csv": f"{VOL_INPUT_DIR}/dim_customer.csv",
        "table": f"`{CATALOG}`.`{BRONZE_SCHEMA}`.`dim_customer_bronze`"
    },
    "dim_date": {
        "csv": f"{VOL_INPUT_DIR}/dim_date.csv",
        "table": f"`{CATALOG}`.`{BRONZE_SCHEMA}`.`dim_date_bronze`"
    },
    "fact_transaction": {
        "csv": f"{VOL_INPUT_DIR}/fact_transaction.csv",
        "table": f"`{CATALOG}`.`{BRONZE_SCHEMA}`.`fact_transaction_bronze`"
    },
    "fact_crm_exposure": {
        "csv": f"{VOL_INPUT_DIR}/fact_crm_exposure.csv",
        "table": f"`{CATALOG}`.`{BRONZE_SCHEMA}`.`fact_crm_exposure_bronze`"
    }
}

# =======================
# HELPERS
# =======================

def read_csv_with_schema(path: str, schema: StructType):
    """
    Read CSV using an explicit schema to avoid type inference inconsistencies.
    """
    df = (
        spark.read
        .option("header", "true")
        .option("mode", "FAILFAST")
        .schema(schema)
        .csv(path)
    )
    return df

def normalize_datetime_columns(df, key: str):
    """
    Ensure date/timestamp columns are parsed correctly even if CSV stores them as strings.
    (Schema usually handles this, but this adds robustness.)
    """
    if key == "dim_customer":
        # signup_date may arrive as string in some exports
        df = df.withColumn("signup_date", to_date(col("signup_date")))
    elif key == "dim_date":
        df = df.withColumn("date", to_date(col("date")))
    elif key == "fact_transaction":
        df = df.withColumn("transaction_ts", to_timestamp(col("transaction_ts")))
        df = df.withColumn("transaction_date", to_date(col("transaction_date")))
    elif key == "fact_crm_exposure":
        df = df.withColumn("exposure_ts", to_timestamp(col("exposure_ts")))
        df = df.withColumn("exposure_date", to_date(col("exposure_date")))
    return df

def optional_drop_table(table_fqn: str):
    spark.sql(f"DROP TABLE IF EXISTS {table_fqn}")

# =======================
# EXECUTION
# =======================

spark.sql(f"USE CATALOG `{CATALOG}`")
spark.sql(f"USE `{CATALOG}`.`{BRONZE_SCHEMA}`")

for key, meta in files_and_tables.items():
    csv_path = meta["csv"]
    table_fqn = meta["table"]

    print(f"\n=== Loading {key} ===")
    print(f"CSV : {csv_path}")
    print(f"TABLE: {table_fqn}")

    if DROP_AND_RECREATE:
        print("Dropping existing table (DROP_AND_RECREATE=True)...")
        optional_drop_table(table_fqn)

    df = read_csv_with_schema(csv_path, schemas[key])
    df = normalize_datetime_columns(df, key)

    # Write safely: overwrite + overwriteSchema prevents schema-merge conflicts
    (
        df.write
        .format("delta")
        .mode("overwrite")
        .option("overwriteSchema", "true")
        .saveAsTable(table_fqn)
    )

    # Lightweight validation
    cnt = spark.table(table_fqn).count()
    print(f"Loaded OK. Row count = {cnt}")

print("\nAll Bronze loads completed successfully.")
