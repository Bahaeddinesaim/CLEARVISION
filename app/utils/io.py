from pathlib import Path
import pandas as pd


def safe_read_csv(path: Path) -> pd.DataFrame:
    try:
        return pd.read_csv(path) if path.exists() and path.stat().st_size > 0 else pd.DataFrame()
    except Exception:
        return pd.DataFrame()


def write_csv(df: pd.DataFrame, path: Path) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    df.to_csv(path, index=False, encoding="utf-8")


def prepend_csv(new_df: pd.DataFrame, path: Path, dedupe_subset: list[str] | None = None) -> pd.DataFrame:
    """Save new rows at the TOP of an existing CSV and return the full dataframe."""
    path.parent.mkdir(parents=True, exist_ok=True)
    old_df = safe_read_csv(path)
    if old_df.empty:
        full = new_df.copy()
    elif new_df.empty:
        full = old_df.copy()
    else:
        full = pd.concat([new_df, old_df], ignore_index=True, sort=False)
    if dedupe_subset:
        subset = [c for c in dedupe_subset if c in full.columns]
        if subset:
            full = full.drop_duplicates(subset=subset, keep="first")
    full.to_csv(path, index=False, encoding="utf-8")
    return full
