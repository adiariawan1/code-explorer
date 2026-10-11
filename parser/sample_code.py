# sample_code.py — used to test the Code Flow Explorer parser
# Contains: 3 functions that call each other, a loop modifying a variable,
# and 1 dead-code function (never called).

TAX_RATE = 0.1


def validate_item(item):
    """Check that an item has a positive price."""
    if item.get("price", 0) <= 0:
        raise ValueError(f"Invalid price for item: {item}")
    return True


def calculate_total(items, discount):
    """Sum item prices, apply discount, then add tax."""
    total = 0
    for item in items:
        validate_item(item)
        total += item["price"]

    total *= 1 - discount
    total += total * TAX_RATE
    return total


def process_order(order):
    """Entry-point: validate order dict then compute the final amount."""
    items = order["items"]
    discount = order.get("discount", 0)
    amount = calculate_total(items, discount)
    return amount


def debug_dump(data):
    """Utility for debugging — never called anywhere (dead code)."""
    output = []
    for key, value in data.items():
        output.append(f"{key}: {value}")
    result = "\n".join(output)
    return result
