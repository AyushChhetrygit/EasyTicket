from sqlmodel import Session

from app.models.customer import Customer


class CustomerNotFoundError(Exception):
    """Raised when a customer_id does not exist in the database."""

    def __init__(self, customer_id: str):
        self.customer_id = customer_id
        super().__init__(f"Customer '{customer_id}' was not found.")


def get_customer_by_id(session: Session, customer_id: str) -> Customer:
    customer = session.get(Customer, customer_id)
    if customer is None:
        raise CustomerNotFoundError(customer_id)
    return customer
