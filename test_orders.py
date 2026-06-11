#!/usr/bin/env python3
"""
test_orders.py – Phase 2 smoke test for order placement.

Places:
  1. A MARKET BUY order for 0.001 BTCUSDT
  2. A LIMIT BUY order for 0.001 BTCUSDT far below the market price
     (so it stays open and can be inspected / cancelled)

Run:
    python test_orders.py

Requires a funded Binance Futures Testnet account and valid .env credentials.
"""

from __future__ import annotations

import json
import sys

from bot.client import BinanceClient
from bot.logging_config import logger
from bot.orders import OrderManager
from bot.validators import ValidationError

# ── Test parameters ────────────────────────────────────────────────────────────
SYMBOL = "BTCUSDT"
MARKET_QTY = 0.001          # Small quantity to minimise testnet balance impact
LIMIT_QTY = 0.001
# Price well below market so the order stays NEW (won't fill immediately)
LIMIT_PRICE = 10_000.0      # ~$10,000 – far below current BTC price on testnet


def _print_response(label: str, response: dict) -> None:
    """Pretty-print an API response dict."""
    print(f"\n{'─' * 60}")
    print(f"  {label}")
    print(f"{'─' * 60}")
    print(json.dumps(response, indent=2))


def test_validation_errors() -> None:
    """Run a quick battery of validator checks before touching the API."""
    print("\n[1/3] Validator smoke-tests …")
    from bot.validators import (
        validate_symbol,
        validate_side,
        validate_order_type,
        validate_quantity,
        validate_price_for_order_type,
        ValidationError,
    )

    cases = [
        # (description, callable, should_raise)
        ("Empty symbol raises", lambda: validate_symbol(""), True),
        ("Numeric symbol raises", lambda: validate_symbol("123"), True),
        ("Valid symbol ok", lambda: validate_symbol("btcusdt"), False),
        ("Invalid side raises", lambda: validate_side("LONG"), True),
        ("Valid side ok", lambda: validate_side("buy"), False),
        ("Invalid order type raises", lambda: validate_order_type("FUTURES"), True),
        ("Valid MARKET type ok", lambda: validate_order_type("MARKET"), False),
        ("Zero quantity raises", lambda: validate_quantity(0), True),
        ("Negative quantity raises", lambda: validate_quantity(-1), True),
        ("Valid quantity ok", lambda: validate_quantity(0.001), False),
        ("LIMIT without price raises", lambda: validate_price_for_order_type("LIMIT", None), True),
        ("LIMIT with negative price raises", lambda: validate_price_for_order_type("LIMIT", -1), True),
        ("LIMIT with valid price ok", lambda: validate_price_for_order_type("LIMIT", 10_000), False),
        ("MARKET with price raises", lambda: validate_price_for_order_type("MARKET", 50_000), True),
        ("MARKET with None ok", lambda: validate_price_for_order_type("MARKET", None), False),
    ]

    passed = failed = 0
    for description, fn, should_raise in cases:
        try:
            fn()
            raised = False
        except ValidationError:
            raised = True

        ok = raised == should_raise
        status = "✅ PASS" if ok else "❌ FAIL"
        if ok:
            passed += 1
        else:
            failed += 1
        print(f"  {status}  {description}")

    print(f"\n  Validators: {passed} passed, {failed} failed")
    if failed:
        print("  ⚠️  Fix validation errors before running API tests.")
        sys.exit(1)


def test_market_order(manager: OrderManager) -> dict:
    """Place a MARKET BUY order and return the response."""
    print(f"\n[2/3] Placing MARKET BUY order | {MARKET_QTY} {SYMBOL} …")
    try:
        response = manager.place_market_order(
            symbol=SYMBOL,
            side="BUY",
            quantity=MARKET_QTY,
        )
        _print_response("MARKET ORDER RESPONSE", response)
        print(f"\n  ✅ Market order accepted | orderId={response.get('orderId')} status={response.get('status')}")
        return response
    except ValidationError as exc:
        print(f"\n  ❌ Validation error: {exc}")
        sys.exit(1)
    except Exception as exc:
        print(f"\n  ❌ API error: {exc}")
        sys.exit(1)


def test_limit_order(manager: OrderManager) -> dict:
    """Place a LIMIT BUY order far below market and return the response."""
    print(f"\n[3/3] Placing LIMIT BUY order | {LIMIT_QTY} {SYMBOL} @ ${LIMIT_PRICE:,.0f} …")
    try:
        response = manager.place_limit_order(
            symbol=SYMBOL,
            side="BUY",
            quantity=LIMIT_QTY,
            price=LIMIT_PRICE,
            time_in_force="GTC",
        )
        _print_response("LIMIT ORDER RESPONSE", response)
        print(
            f"\n  ✅ Limit order accepted | orderId={response.get('orderId')} "
            f"status={response.get('status')}"
        )
        print(
            f"  ℹ️  Order status should be 'NEW' (won't fill at ${LIMIT_PRICE:,.0f}). "
            "Remember to cancel it after testing."
        )
        return response
    except ValidationError as exc:
        print(f"\n  ❌ Validation error: {exc}")
        sys.exit(1)
    except Exception as exc:
        print(f"\n  ❌ API error: {exc}")
        sys.exit(1)


def main() -> None:
    print("=" * 60)
    print("  Binance Futures Testnet – Phase 2 Order Test")
    print("=" * 60)

    # Step 1: validator smoke-tests (no API needed)
    test_validation_errors()

    # Step 2: initialise client
    print("\n  Connecting to Binance Futures Testnet …")
    try:
        client = BinanceClient()
    except ValueError as exc:
        print(f"\n  ❌ Client init error: {exc}")
        print("  Ensure BINANCE_API_KEY and BINANCE_API_SECRET are set in your .env file.")
        sys.exit(1)

    if not client.ping():
        print("\n  ❌ Cannot reach the testnet. Check your internet connection.")
        sys.exit(1)

    manager = OrderManager(client)

    # Step 3: API order tests
    market_resp = test_market_order(manager)
    limit_resp = test_limit_order(manager)

    # Summary
    print("\n" + "=" * 60)
    print("  SUMMARY")
    print("=" * 60)
    print(f"  Market order ID : {market_resp.get('orderId')}")
    print(f"  Limit  order ID : {limit_resp.get('orderId')}")
    print("\n  To cancel the open limit order, run:")
    print(f"    python cli.py open-orders --symbol {SYMBOL}")
    print("\n  All tests completed successfully. ✅")


if __name__ == "__main__":
    main()
