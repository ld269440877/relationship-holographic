import os
import sys
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[1]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

TEST_DB_PATH = PROJECT_ROOT / "data" / "test_relationship_training.db"
TEST_DB_PATH.parent.mkdir(exist_ok=True)
for suffix in ("", "-wal", "-shm"):
    candidate = Path(f"{TEST_DB_PATH}{suffix}")
    if candidate.exists():
        candidate.unlink()

os.environ.setdefault("DATABASE_URL", f"sqlite:///{TEST_DB_PATH}")
