from behave import given, when, then
from app.eshop import Product, ShoppingCart, Order
from services import ShippingService
from services.publisher import ShippingPublisher
from services.repository import ShippingRepository


@given('A product with availability of {amount}')
def step_create_product(context, amount):
    context.product = Product(
        name="TestProduct",
        price=100,
        available_amount=int(amount)
    )


@given('Another product with availability of {amount}')
def step_create_second_product(context, amount):
    context.product2 = Product(
        name="SecondProduct",
        price=50,
        available_amount=int(amount)
    )


@given('A shopping cart with {count} items of the product')
def step_cart_with_product(context, count):
    if not hasattr(context, "cart"):
        context.cart = ShoppingCart()
    context.cart.add_product(context.product, int(count))


@given('A shopping cart with {count} items of the second product')
def step_cart_with_second_product(context, count):
    if not hasattr(context, "cart"):
        context.cart = ShoppingCart()
    context.cart.add_product(context.product2, int(count))


@given('An order created from the cart')
def step_create_order(context):
    context.order = Order(context.cart, ShippingService(ShippingRepository(), ShippingPublisher()))


@when('I place the order')
def step_place_order(context):
    context.order.place_order()


@then('Product availability should be {remaining}')
def step_check_product_remaining(context, remaining):
    assert context.product.available_amount == int(remaining), \
        f"Expected {remaining}, got {context.product.available_amount}"


@then('First product availability should be {remaining}')
def step_check_first_product(context, remaining):
    assert context.product.available_amount == int(remaining)


@then('Second product availability should be {remaining}')
def step_check_second_product(context, remaining):
    assert context.product2.available_amount == int(remaining)


@then('Shopping cart should be empty')
def step_cart_empty(context):
    assert context.cart.calculate_total() == 0
    assert len(context.cart.products) == 0
