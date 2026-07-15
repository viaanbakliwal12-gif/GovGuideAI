from __future__ import annotations

from app.database.session import DATABASE_PATH, init_db


def main() -> None:
    init_db()
    print(f"GovGuideAI database migrations completed: {DATABASE_PATH}")


if __name__ == "__main__":
    main()
