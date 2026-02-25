Feature: Order processing
  We want to test that order placement works correctly

  Scenario: Successful order placement
    Given A product with availability of 10
    And A shopping cart with 3 items of the product
    And An order created from the cart
    When I place the order
    Then Product availability should be 7
    And Shopping cart should be empty

  Scenario: Order placement with multiple products
    Given A product with availability of 5
    And Another product with availability of 8
    And A shopping cart with 2 items of the product
    And A shopping cart with 3 items of the second product
    And An order created from the cart
    When I place the order
    Then First product availability should be 3
    And Second product availability should be 5
    And Shopping cart should be empty

  Scenario: Order placement with empty cart
    Given An empty shopping cart
    And An order created from the cart
    When I place the order
    Then Shopping cart should be empty

  Scenario: Order placement reduces availability exactly to zero
    Given A product with availability of 3
    And A shopping cart with 3 items of the product
    And An order created from the cart
    When I place the order
    Then Product availability should be 0
    And Shopping cart should be empty

  Scenario: Order placement does not validate availability
    Given A product with availability of 2
    And A shopping cart with 2 items of the product
    And An order created from the cart
    When I place the order
    Then Product availability should be 0
