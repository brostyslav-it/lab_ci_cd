import time
import uuid
from datetime import datetime, timedelta, timezone

import pytest

from app.eshop import Product, ShoppingCart, Order
from services.publisher import ShippingPublisher
from services.repository import ShippingRepository
from services.service import ShippingService


@pytest.fixture
def shipping_repo():
    return ShippingRepository()


@pytest.fixture
def shipping_publisher():
    return ShippingPublisher()


@pytest.fixture
def shipping_service(shipping_repo, shipping_publisher):
    return ShippingService(shipping_repo, shipping_publisher)


@pytest.fixture
def sample_product():
    return Product(name="Test Phone", price=1000, available_amount=10)


def test_repository_create_and_get_shipping(shipping_repo):
    shipping_id = shipping_repo.create_shipping(
        shipping_type="Нова Пошта",
        product_ids=["prod1", "prod2"],
        order_id="ord-123",
        status="created",
        due_date=datetime.now(timezone.utc) + timedelta(days=1)
    )

    item = shipping_repo.get_shipping(shipping_id)

    assert item is not None
    assert item["shipping_id"] == shipping_id
    assert item["shipping_status"] == "created"
    assert item["order_id"] == "ord-123"


def test_publisher_send_and_poll(shipping_publisher):
    test_id = str(uuid.uuid4())
    shipping_publisher.send_new_shipping(test_id)

    time.sleep(1)

    messages = shipping_publisher.poll_shipping(batch_size=10)
    assert test_id in messages


def test_cart_deducts_product_amount_on_submit(sample_product):
    cart = ShoppingCart()
    cart.add_product(sample_product, 5)

    initial_amount = sample_product.available_amount
    cart.submit_cart_order()

    assert sample_product.available_amount == initial_amount - 5
    assert len(cart.products) == 0


def test_full_flow_shipping_completion(shipping_service, sample_product):
    cart = ShoppingCart()
    cart.add_product(sample_product, 1)
    order = Order(cart, shipping_service)

    due_date = datetime.now(timezone.utc) + timedelta(minutes=5)
    shipping_id = order.place_order("Нова Пошта", due_date=due_date)

    status_after_creation = shipping_service.check_status(shipping_id)
    assert status_after_creation == shipping_service.SHIPPING_IN_PROGRESS

    time.sleep(1)
    shipping_service.process_shipping_batch()

    final_status = shipping_service.check_status(shipping_id)
    assert final_status == shipping_service.SHIPPING_COMPLETED


def test_full_flow_shipping_failed_due_to_date(shipping_service, shipping_repo, shipping_publisher):
    past_date = datetime.now(timezone.utc) - timedelta(hours=1)

    real_shipping_id = shipping_repo.create_shipping(
        "Нова Пошта", ["prod1"], "order-fail-test",
        shipping_service.SHIPPING_IN_PROGRESS, past_date
    )

    shipping_publisher.send_new_shipping(real_shipping_id)
    time.sleep(1)

    shipping_service.process_shipping_batch()

    final_status = shipping_service.check_status(real_shipping_id)
    assert final_status == shipping_service.SHIPPING_FAILED


def test_create_shipping_with_past_date_fails_validation(shipping_service):
    past_date = datetime.now(timezone.utc) - timedelta(seconds=10)

    with pytest.raises(ValueError, match="Shipping due datetime must be greater"):
        shipping_service.create_shipping(
            "Нова Пошта", ["p1"], "ord-1", past_date
        )


def test_manual_status_update_flow(shipping_repo, shipping_service):
    shipping_id = shipping_repo.create_shipping(
        "Самовивіз", ["p1"], "ord-status", "created",
        datetime.now(timezone.utc) + timedelta(days=1)
    )

    shipping_service.fail_shipping(shipping_id)
    assert shipping_service.check_status(shipping_id) == shipping_service.SHIPPING_FAILED

    shipping_service.complete_shipping(shipping_id)
    assert shipping_service.check_status(shipping_id) == shipping_service.SHIPPING_COMPLETED


def test_process_multiple_shippings_in_batch(shipping_service, sample_product):
    ids = []
    for _ in range(3):
        cart = ShoppingCart()
        cart.add_product(sample_product, 1)
        order = Order(cart, shipping_service)
        sid = order.place_order("Meest Express")
        ids.append(sid)

    time.sleep(1)
    shipping_service.process_shipping_batch()

    for sid in ids:
        status = shipping_service.check_status(sid)
        assert status == shipping_service.SHIPPING_COMPLETED


def test_process_non_existent_shipping(shipping_service, shipping_publisher):
    fake_id = str(uuid.uuid4())
    shipping_publisher.send_new_shipping(fake_id)
    time.sleep(1)

    with pytest.raises((TypeError, KeyError)):
        shipping_service.process_shipping_batch()


def test_shipping_types_availability(shipping_service):
    allowed_types = shipping_service.list_available_shipping_type()
    assert "Укр Пошта" in allowed_types

    with pytest.raises(ValueError, match="Shipping type is not available"):
        shipping_service.create_shipping(
            "DHL International", ["p1"], "ord-inv",
            datetime.now(timezone.utc) + timedelta(days=1)
        )
