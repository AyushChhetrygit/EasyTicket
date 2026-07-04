from app.services.customer_service import get_customer_by_id, CustomerNotFoundError


def test_get_customer_by_id(session, sample_customer):
    customer = get_customer_by_id(session, sample_customer.customer_id)
    assert customer.customer_id == sample_customer.customer_id


def test_get_customer_invalid_id_raises(session):
    try:
        get_customer_by_id(session, "CUST-DOES-NOT-EXIST")
        assert False, "expected CustomerNotFoundError"
    except CustomerNotFoundError:
        pass
