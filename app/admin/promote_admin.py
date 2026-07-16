from __future__ import annotations

import argparse
import sys

from dotenv import load_dotenv

from app.admin.services import (
    AdminPromotionError,
    promote_email_admin,
    safe_promotion_label,
)
from app.database.session import init_db


def main() -> int:
    parser = argparse.ArgumentParser(
        description="Promote the local user matching ADMIN_EMAIL to GovGuideAI admin."
    )
    parser.add_argument("email", help="The account email that must match ADMIN_EMAIL")
    arguments = parser.parse_args()

    load_dotenv()
    init_db()
    try:
        user_id, changed = promote_email_admin(arguments.email)
    except AdminPromotionError as error:
        print(f"Admin promotion refused: {error}", file=sys.stderr)
        return 1

    action = "Promoted" if changed else "Already an admin"
    print(f"{action}: user ID {user_id} ({safe_promotion_label(arguments.email)})")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
