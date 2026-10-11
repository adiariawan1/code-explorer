def validate_item(price):
    if price < 0:
        raise ValueError('negative price')
    return price


# trace-args: {"items": [10, 20, 30], "discount": 0.1}
def calculate_total(items, discount):
    total = 0
    for price in items:
        total += validate_item(price)
    total = total * (1 - discount)
    return total


def checkout(items):
    amount = calculate_total(items, 0.1)
    return f'Total: {amount}'


def unused_helper():
    return 'never called'


def main():
    print(checkout([10, 20, 30]))


if __name__ == '__main__':
    main()
