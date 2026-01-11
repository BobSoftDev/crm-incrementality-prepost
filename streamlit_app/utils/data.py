# streamlit_app/utils/data.py
from __future__ import annotations

from pathlib import Path
import pandas as pd


def get_repo_root() -> Path:
    """
    Works both locally and on Streamlit Cloud.
    Assumes this file is located at: streamlit_app/utils/data.py
    """
    return Path(__file__).resolve().parents[2]  # repo root


def get_default_export_folder() -> str:
    """
    Default location for Gold exports.
    Prefer repo-level /data/gold_exports first.
    """
    root = get_repo_root()
    candidates = [
        root / "data" / "gold_exports",
        root / "streamlit_app" / "data" / "gold_exports",
    ]
    for c in candidates:
        if c.exists() and c.is_dir():
            return str(c)
    # fall back to repo-level even if it doesn't exist yet
    return str(candidates[0])


def _candidate_folders(user_folder: str | None) -> list[Path]:
    """
    Order matters: user folder first (if given), then common repo paths.
    """
    root = get_repo_root()

    candidates: list[Path] = []
    if user_folder:
        candidates.append(Path(user_folder))

    candidates.extend([
        root / "data" / "gold_exports",
        root / "streamlit_app" / "data" / "gold_exports",
        Path.cwd() / "data" / "gold_exports",
        Path.cwd() / "gold_exports",
    ])

    # Deduplicate while preserving order
    seen = set()
    uniq: list[Path] = []
    for c in candidates:
        key = str(c)
        if key not in seen:
            seen.add(key)
            uniq.append(c)
    return uniq


def load_csv_folder(folder: str, filename: str, required: bool = True) -> pd.DataFrame:
    """
    Loads a CSV from the provided folder with robust fallback paths.

    - If required=True: raises FileNotFoundError with a detailed message.
    - If required=False: returns empty DataFrame if not found.
    """
    candidates = _candidate_folders(folder)

    tried_paths = []
    for base in candidates:
        path = base / filename
        tried_paths.append(str(path))
        if path.exists() and path.is_file():
            return pd.read_csv(path)

    msg = (
        f"Missing required file: '{filename}'.\n\n"
        f"Tried these locations:\n- " + "\n- ".join(tried_paths) + "\n\n"
        f"Fix options:\n"
        f"1) Export Gold CSVs into one of the folders above, OR\n"
        f"2) Update the sidebar 'Gold export folder' to the correct path, OR\n"
        f"3) Put CSVs under repo 'data/gold_exports' for Streamlit Cloud.\n"
    )

    if required:
        raise FileNotFoundError(msg)

    return pd.DataFrame()


def ensure_month_fields(df: pd.DataFrame, month_col: str) -> pd.DataFrame:
    """
    Adds normalized month fields used for sorting and selection:
    - month_id_norm: string month key
    - month_label: display label (falls back to month_id_norm)
    """
    if df is None or df.empty:
        # keep consistent columns even when empty
        cols = list(df.columns) if df is not None else []
        for extra in ["month_id_norm", "month_label"]:
            if extra not in cols:
                cols.append(extra)
        return pd.DataFrame(columns=cols)

    out = df.copy()

    if month_col not in out.columns:
        out["month_id_norm"] = "Unknown"
        out["month_label"] = "Unknown"
        return out

    out["month_id_norm"] = out[month_col].astype(str).fillna("Unknown")

    if "month_label" not in out.columns:
        out["month_label"] = out["month_id_norm"]
    else:
        out["month_label"] = out["month_label"].astype(str).fillna(out["month_id_norm"])

    return out


def sort_month(df: pd.DataFrame) -> pd.DataFrame:
    """
    Sorts by month_id_norm if present; otherwise returns as-is.
    Handles 'YYYYMM' and 'YYYY-MM' formats.
    """
    if df is None or df.empty:
        return df

    if "month_id_norm" not in df.columns:
        return df

    def _key(x: str) -> str:
        s = str(x)
        if len(s) == 7 and s[4] == "-":  # YYYY-MM
            return s.replace("-", "")
        return s

    out = df.copy()
    out["_sort_key"] = out["month_id_norm"].map(_key)
    out = out.sort_values("_sort_key").drop(columns=["_sort_key"])
    return out
