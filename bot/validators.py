"""Input validators for order parameters. Raise ValidationError on bad input."""

from __future__ import annotations

from typing import Optional, Union


class ValidationError(ValueError):
    """Raised when an order parameter fails validation."""


def validate_symbol(symbol: str) -> str:
    """Return upper-cased symbol, e.g. 'btcusdt' -> 'BTCUSDT'."""
    if not symbol or not isinstance(symbol, str):
        raise ValidationError("Symbol must be a non-empty string.")
    cleaned = symbol.strip().upper()
    if not cleaned.isalpha():
        raise ValidationError(
            f"Symbol '{cleaned}' contains invalid characters. Expected letters only (e.g. 'BTCUSDT')."
        )
    return cleaned


def validate_quantity(quantity: float, min_qty: float = 0.0) -> float:
    """Return quantity as float. Must be greater than min_qty (default 0)."""
    try:
        qty = float(quantity)
    except (TypeError, ValueError):
        raise ValidationError(f"Quantity must be a number, got: {quantity!r}")
    if qty <= min_qty:
        raise ValidationError(f"Quantity must be greater than {min_qty}, got: {qty}")
    return qty


def validate_side(side: str) -> str:
    """Return 'BUY' or 'SELL'. Raises if anything else is passed."""
    if not side or not isinstance(side, str):
        raise ValidationError("Side must be a non-empty string ('BUY' or 'SELL').")
    normalised = side.strip().upper()
    if normalised not in {"BUY", "SELL"}:
        raise ValidationError(f"Invalid side '{side}'. Must be BUY or SELL.")
    return normalised


def validate_order_type(order_type: str) -> str:
    """Return 'MARKET' or 'LIMIT'. Raises if anything else is passed."""
    if not order_type or not isinstance(order_type, str):
        raise ValidationError("Order type must be 'MARKET' or 'LIMIT'.")
    normalised = order_type.strip().upper()
    if normalised not in {"MARKET", "LIMIT"}:
        raise ValidationError(f"Invalid order type '{order_type}'. Must be MARKET or LIMIT.")
    return normalised


def validate_price_for_order_type(
    order_type: str,
    price: Optional[Union[float, int, str]],
) -> Optional[float]:
    """
    Enforce the price rule for a given order type:
      - LIMIT  -> price is required and must be > 0
      - MARKET -> price must be None
    """
    order_type = order_type.strip().upper()

    if order_type == "LIMIT":
        if price is None:
            raise ValidationError("Price is required for LIMIT orders.")
        try:
            p = float(price)
        except (TypeError, ValueError):
            raise ValidationError(f"Price must be a positive number, got: {price!r}")
        if p <= 0:
            raise ValidationError(f"Price must be greater than 0, got: {p}")
        return p

    if order_type == "MARKET":
        if price is not None:
            raise ValidationError(
                f"Price must not be set for MARKET orders (got {price!r})."
            )
        return None

    raise ValidationError(f"Unknown order type: '{order_type}'")


def validate_leverage(leverage: int, max_leverage: int = 125) -> int:
    """Return leverage as int. Must be between 1 and max_leverage."""
    try:
        lev = int(leverage)
    except (TypeError, ValueError):
        raise ValidationError(f"Leverage must be an integer, got: {leverage!r}")
    if not (1 <= lev <= max_leverage):
        raise ValidationError(f"Leverage must be between 1 and {max_leverage}, got: {lev}")
    return lev
