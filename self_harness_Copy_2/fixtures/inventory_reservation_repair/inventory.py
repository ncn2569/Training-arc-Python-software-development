"""Inventory reservation helper used by the source/train calibration suite."""


def reserve(stock, reserved, sku, quantity):
    if sku not in stock:
        raise KeyError(sku)
    if quantity <= 0:
        raise ValueError("quantity must be positive")
    if stock[sku] < quantity:
        raise ValueError("insufficient stock")
    reserved[sku] = reserved.get(sku, 0) + quantity
    return reserved
