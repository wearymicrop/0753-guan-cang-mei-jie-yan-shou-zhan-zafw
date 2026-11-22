import os
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
TITLE = "馆藏媒介验收站"
PROJECT = "gb-0753"
RULESET = "gb-0753/1.0"
SIGNATURE_TITLE = "复核封存"
SAMPLES = {"dirty": "现场样例", "clean": "干净样例"}
MAX_ROWS = 2500


def database_path():
    return Path(os.getenv("WORKBENCH_DB", ROOT / "instance" / "workbench.sqlite3"))
