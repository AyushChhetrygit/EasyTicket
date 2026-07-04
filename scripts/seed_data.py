"""Load sample customers and tickets from data/*.json into the database.
Usage: python scripts/seed_data.py
"""
import json
import sys
from pathlib import Path

sys.path.append(str(Path(__file__).resolve().parent.parent))

from sqlmodel import Session

from app.database.database import engine, init_db
from app.models.customer import Customer
from app.models.ticket import Ticket

DATA_DIR = Path(__file__).resolve().parent.parent / "data"


def seed():
    init_db()
    with Session(engine) as session:
        customers_path = DATA_DIR / "customers.json"
        if customers_path.exists():
            customers = json.loads(customers_path.read_text())
            for c in customers:
                if not session.get(Customer, c["customer_id"]):
                    session.add(Customer(**c))
            session.commit()
            print(f"Seeded {len(customers)} customers.")

        tickets_path = DATA_DIR / "sample_tickets.json"
        if tickets_path.exists():
            tickets = json.loads(tickets_path.read_text())
            for t in tickets:
                if not session.get(Ticket, t.get("ticket_id")):
                    session.add(Ticket(**t))
            session.commit()
            print(f"Seeded {len(tickets)} tickets.")


if __name__ == "__main__":
    seed()
