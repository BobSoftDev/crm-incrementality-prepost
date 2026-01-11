import os
import pandas as pd

REQUIRED_FILES = [
    "agg_incrementality_month.csv",
    "agg_incrementality_rfm.csv",
    "agg_incrementality_active_value.csv",
    "fact_customer_month_incrementality.csv",
    "dim_customer_month_rfm.csv",
]

def get_default_export_folder() -> str:
    # default: ./gold_exports inside project
    return os.path.join(os.getcwd(), "gold_exports")

def load_csv_folder(folder_path: str, filename: str) -> pd.DataFrame:
    path = os.path.join(folder_path, filename)
    if not os.path.exists(path):
        raise FileNotFoundError(
            f"Missing file: {path}\n"
            f"Expected Gold CSVs inside: {folder_path}\n"
            f"Files: {', '.join(REQUIRED_FILES)}"
        )
    return pd.read_csv(path)

def normalize_month_id(series: pd.Series) -> pd.Series:
    """
    Normalize month_id to 'yyyymm' string.
    Handles:
      - yyyymm (202502)
      - yyyymmdd (20250201) -> 202502
      - floats like 202502.0
    """
    s = series.astype(str).str.strip()

    # Drop trailing .0 from floats
    s = s.str.replace(r"\.0$", "", regex=True)

    # Keep only digits (defensive)
    s = s.str.replace(r"[^0-9]", "", regex=True)

    # If yyyymmdd -> yyyymm
    s = s.where(~s.str.match(r"^\d{8}$"), s.str.slice(0, 6))

    # If already yyyymm keep; otherwise set as 'Unknown'
    s = s.where(s.str.match(r"^\d{6}$"), "Unknown")
    return s

def month_label_from_yyyymm(series_yyyymm: pd.Series) -> pd.Series:
    """
    Convert 'yyyymm' -> 'YYYY-MM'. Unknown stays Unknown.
    """
    s = series_yyyymm.copy()
    out = s.copy()
    mask = s.str.match(r"^\d{6}$")
    out.loc[mask] = pd.to_datetime(s.loc[mask] + "01", format="%Y%m%d").dt.strftime("%Y-%m")
    return out

def ensure_month_fields(df: pd.DataFrame, month_col: str = "month_id") -> pd.DataFrame:
    """
    Adds:
      - month_id_norm: 'yyyymm' string
      - month_label:  'YYYY-MM' string
    """
    if month_col not in df.columns:
        df["month_id_norm"] = "Unknown"
        df["month_label"] = "Unknown"
        return df

    df["month_id_norm"] = normalize_month_id(df[month_col])
    df["month_label"] = month_label_from_yyyymm(df["month_id_norm"])
    return df

def sort_month(df: pd.DataFrame, month_norm_col: str = "month_id_norm") -> pd.DataFrame:
    if month_norm_col in df.columns:
        return df.sort_values(month_norm_col)
    return df
