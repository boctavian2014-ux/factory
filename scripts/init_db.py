"""
Create PostgreSQL tables from SQLAlchemy models.
Run from repo root:
  python -m scripts.init_db
Or with env set:
  set DATABASE_URL=postgresql://postgres:postgres@localhost:5432/ai_content_factory
  python -m scripts.init_db
"""
import sys
from pathlib import Path

# Ensure project root is on path when run as script
_root = Path(__file__).resolve().parent.parent
if str(_root) not in sys.path:
    sys.path.insert(0, str(_root))


def main() -> None:
    from shared.database import init_db

    init_db()
    print("Database tables created successfully.")


if __name__ == "__main__":
    main()
