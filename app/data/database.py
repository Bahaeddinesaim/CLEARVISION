import sqlite3
from pathlib import Path
import pandas as pd
import numpy as np
from app.core.settings import DB_PATH, DATA_DIR

SQLITE_INT_MIN = -(2**63)
SQLITE_INT_MAX = 2**63 - 1


def init_db() -> None:
    DB_PATH.parent.mkdir(parents=True, exist_ok=True)
    con = sqlite3.connect(DB_PATH)
    sql_path = DATA_DIR.parent / "sql" / "schema.sql"
    if sql_path.exists():
        con.executescript(sql_path.read_text(encoding="utf-8"))
    con.commit()
    con.close()


def _sqlite_safe_dataframe(df: pd.DataFrame) -> pd.DataFrame:
    """Return a SQLite-safe copy.

    SQLite INTEGER is signed 64-bit. Some generated IDs/hash-like values can be
    interpreted by pandas as huge integers on Windows, causing:
    OverflowError: Python int too large to convert to SQLite INTEGER.
    CSV files keep their original values; only the DB persistence copy is sanitized.
    """
    safe = df.copy()
    for col in safe.columns:
        s = safe[col]

        # Unsigned integers can exceed SQLite signed INTEGER range.
        if pd.api.types.is_unsigned_integer_dtype(s):
            safe[col] = s.astype("string").fillna("")
            continue

        # Object/string columns may contain huge numeric-looking IDs.
        if pd.api.types.is_object_dtype(s) or pd.api.types.is_string_dtype(s):
            def clean_value(v):
                if pd.isna(v):
                    return None
                if isinstance(v, int) and (v > SQLITE_INT_MAX or v < SQLITE_INT_MIN):
                    return str(v)
                return v
            safe[col] = s.map(clean_value)
            continue

        # Signed integers: convert unsafe values to string column.
        if pd.api.types.is_integer_dtype(s):
            try:
                if ((s.dropna() > SQLITE_INT_MAX) | (s.dropna() < SQLITE_INT_MIN)).any():
                    safe[col] = s.astype("string").fillna("")
            except Exception:
                safe[col] = s.astype("string").fillna("")
            continue

        # Normalize numpy scalar/object oddities.
        if pd.api.types.is_float_dtype(s):
            safe[col] = s.replace([np.inf, -np.inf], np.nan)

    return safe


def persist_dataframe(df: pd.DataFrame, table: str) -> None:
    if df is None or df.empty:
        return
    con = sqlite3.connect(DB_PATH)
    try:
        safe_df = _sqlite_safe_dataframe(df)
        safe_df.to_sql(table, con, if_exists="replace", index=False)
        con.commit()
    finally:
        con.close()


def persist_all(datasets: dict[str, pd.DataFrame]) -> None:
    init_db()
    for name, df in datasets.items():
        if isinstance(df, pd.DataFrame) and not df.empty:
            persist_dataframe(df, name)
