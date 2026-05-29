from pathlib import Path
import yaml

ROOT_DIR = Path(__file__).resolve().parents[2]
DATA_DIR = ROOT_DIR / "data"
DB_PATH = DATA_DIR / "classvision.db"
CONFIG_PATH = ROOT_DIR / "config.yaml"


def load_config() -> dict:
    if CONFIG_PATH.exists():
        return yaml.safe_load(CONFIG_PATH.read_text(encoding="utf-8"))
    return {}


def ensure_directories() -> None:
    for folder in ["raw", "raw/uploads", "raw/annotated", "bronze", "silver", "gold", "catalog", "reports", "demo", "audio"]:
        (DATA_DIR / folder).mkdir(parents=True, exist_ok=True)
