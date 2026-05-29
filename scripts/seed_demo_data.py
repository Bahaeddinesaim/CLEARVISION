import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from app.core.settings import ensure_directories
from app.data.simulator import generate_demo_data
from app.data.database import init_db, persist_dataframe

ensure_directories()
dfs = generate_demo_data(100, 60)
init_db()
for name, df in dfs.items():
    persist_dataframe(df, name)
print("Demo data generated successfully.")
