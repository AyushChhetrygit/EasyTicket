"""Drop and recreate all tables. Usage: python scripts/reset_db.py"""
import sys
from pathlib import Path

sys.path.append(str(Path(__file__).resolve().parent.parent))

from app.database.database import reset_db

if __name__ == "__main__":
    confirm = input("This will DELETE all data in tickets.db. Type 'yes' to continue: ")
    if confirm.strip().lower() == "yes":
        reset_db()
        print("Database reset complete.")
    else:
        print("Aborted.")
