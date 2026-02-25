from behave import given, when, then
from app.eshop import Product


@given('The product with name "{name}" has availability of "{amount}"')
def step_impl(context, name, amount):
    context.product = Product(name=name, price=0.0, available_amount=int(amount))


@when('I check if product is available in amount "{amount}"')
def step_impl(context, amount):
    context.check_result = context.product.is_available(int(amount))


@then('Product is available')
def step_impl(context):
    assert context.check_result is True, f"Expected product to be available, but it was not."


@then('Product is not available')
def step_impl(context):
    assert context.check_result is False, f"Expected product to be unavailable, but it was available."
