#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Binance Futures Testnet Trading Bot CLI.

Usage:
    python cli.py place-order --symbol BTCUSDT --side BUY  --type MARKET --quantity 0.001
    python cli.py place-order --symbol BTCUSDT --side SELL --type LIMIT  --quantity 0.001 --price 100000
    python cli.py test-connection
    python cli.py balance
    python cli.py open-orders [--symbol BTCUSDT]
"""

from __future__ import annotations

import sys

# Windows cp1252 terminals can't print emoji — force UTF-8 output
if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")
if hasattr(sys.stderr, "reconfigure"):
    sys.stderr.reconfigure(encoding="utf-8", errors="replace")

import argparse
from typing import Optional

from bot.client import BinanceClient
from bot.logging_config import logger
from bot.orders import OrderManager
from bot.validators import (
    ValidationError,
    validate_order_type,
    validate_quantity,
    validate_side,
    validate_symbol,
)

# ANSI codes for coloured terminal output
_RESET  = "\033[0m"
_BOLD   = "\033[1m"
_DIM    = "\033[2m"
_GREEN  = "\033[92m"
_RED    = "\033[91m"
_CYAN   = "\033[96m"
_YELLOW = "\033[93m"


def _c(text: str, *codes: str) -> str:
    return "".join(codes) + str(text) + _RESET


def _divider(width: int = 56) -> str:
    return _c("─" * width, _DIM)


def _print_order_summary(
    symbol: str, side: str, order_type: str, quantity: float, price: Optional[float]
) -> None:
    side_colour = _GREEN if side == "BUY" else _RED
    print()
    print(_divider())
    print(_c("  ORDER REQUEST SUMMARY", _BOLD, _CYAN))
    print(_divider())
    print(f"  {'Symbol':<14}: {_c(symbol, _BOLD)}")
    print(f"  {'Side':<14}: {_c(side, _BOLD, side_colour)}")
    print(f"  {'Type':<14}: {_c(order_type, _BOLD)}")
    print(f"  {'Quantity':<14}: {_c(f'{quantity:.6f}', _BOLD)}")
    if price is not None:
        print(f"  {'Limit Price':<14}: {_c(f'${price:,.2f}', _BOLD, _YELLOW)}")
    else:
        print(f"  {'Price':<14}: {_c('MARKET (best available)', _DIM)}")
    print(_divider())


def _print_order_result(response: dict) -> None:
    status     = response.get("status", "N/A")
    avg_price  = response.get("avgPrice", "0")
    exec_qty   = response.get("executedQty", "0")
    status_colour = _GREEN if status in ("FILLED", "NEW") else _YELLOW

    print()
    print(_divider())
    print(_c("  ORDER RESULT", _BOLD, _GREEN))
    print(_divider())
    print(f"  {'Order ID':<16}: {_c(response.get('orderId', 'N/A'), _BOLD)}")
    print(f"  {'Client Order ID':<16}: {_c(response.get('clientOrderId', 'N/A'), _DIM)}")
    print(f"  {'Symbol':<16}: {response.get('symbol', '')}")
    print(f"  {'Side':<16}: {response.get('side', '')}")
    print(f"  {'Type':<16}: {response.get('type', '')}")
    print(f"  {'Status':<16}: {_c(status, _BOLD, status_colour)}")
    print(f"  {'Executed Qty':<16}: {float(exec_qty):.6f}")
    avg_f = float(avg_price)
    if avg_f > 0:
        print(f"  {'Avg Fill Price':<16}: ${avg_f:,.4f}")
    else:
        print(f"  {'Avg Fill Price':<16}: {_c('Pending fill', _DIM)}")
    print(_divider())
    print(_c("  ✅  Order placed successfully", _BOLD, _GREEN))
    print()


def _print_error(reason: str) -> None:
    print()
    print(_divider())
    print(_c(f"  ❌  Order failed: {reason}", _BOLD, _RED))
    print(_divider())
    print()


def cmd_place_order(client: BinanceClient, args: argparse.Namespace) -> int:
    try:
        symbol     = validate_symbol(args.symbol)
        side       = validate_side(args.side)
        order_type = validate_order_type(args.type)
        quantity   = validate_quantity(args.quantity)
        price      = args.price  # validated inside OrderManager
    except ValidationError as exc:
        _print_error(f"Validation — {exc}")
        logger.error("Validation error: %s", exc)
        return 1

    _print_order_summary(symbol, side, order_type, quantity, price)

    manager = OrderManager(client)
    try:
        if order_type == "MARKET":
            response = manager.place_market_order(symbol=symbol, side=side, quantity=quantity)
        else:
            response = manager.place_limit_order(symbol=symbol, side=side, quantity=quantity, price=price)
    except ValidationError as exc:
        _print_error(f"Validation — {exc}")
        logger.error("Validation error: %s", exc)
        return 1
    except Exception as exc:
        # BinanceAPIException has a .message attribute with the exchange's reason
        _print_error(getattr(exc, "message", None) or str(exc))
        logger.error("Order error: %s", exc)
        return 1

    _print_order_result(response)
    return 0


def cmd_test_connection(client: BinanceClient, _args: argparse.Namespace) -> int:
    if client.test_connection():
        print(_c("\n  ✅  Connection to Binance Futures Testnet is working.", _GREEN, _BOLD))
        return 0
    print(_c("\n  ❌  Connection test failed. Check bot.log for details.", _RED, _BOLD))
    return 1


def cmd_balance(client: BinanceClient, _args: argparse.Namespace) -> int:
    try:
        balances = client.get_account_balance()
    except Exception as exc:
        print(_c(f"\n  ❌  Failed to fetch balances: {exc}", _RED, _BOLD))
        return 1

    if not balances:
        print("  No balance data returned.")
        return 1

    print()
    print(_divider())
    print(_c("  FUTURES WALLET BALANCES", _BOLD, _CYAN))
    print(_divider())
    print(f"  {'Asset':<10}  {'Balance':>18}  {'Available':>18}")
    print(f"  {'-'*10}  {'-'*18}  {'-'*18}")
    for b in balances:
        bal  = float(b["balance"])
        avail = float(b["availableBalance"])
        row = f"  {b['asset']:<10}  {bal:>18.6f}  {avail:>18.6f}"
        print(_c(row, _DIM) if bal == 0 else row)
    print(_divider())
    return 0


def cmd_open_orders(client: BinanceClient, args: argparse.Namespace) -> int:
    manager = OrderManager(client)
    try:
        orders = manager.get_open_orders(symbol=args.symbol)
    except Exception as exc:
        print(_c(f"\n  ❌  Failed to fetch open orders: {exc}", _RED, _BOLD))
        return 1

    if not orders:
        sym_str = f" for {args.symbol}" if args.symbol else ""
        print(f"\n  No open orders{sym_str}.")
        return 0

    print()
    print(_divider(width=86))
    print(_c("  OPEN ORDERS", _BOLD, _CYAN))
    print(_divider(width=86))
    print(f"  {'Order ID':<14} {'Symbol':<10} {'Side':<5} {'Type':<7} {'Qty':>10} {'Price':>12} {'Status':<12}")
    print(f"  {'-'*14} {'-'*10} {'-'*5} {'-'*7} {'-'*10} {'-'*12} {'-'*12}")
    for o in orders:
        side_col = _GREEN if o["side"] == "BUY" else _RED
        print(
            f"  {str(o['orderId']):<14} {o['symbol']:<10} "
            f"{_c(o['side'], side_col):<14} {o['type']:<7} "
            f"{float(o['origQty']):>10.4f} {float(o['price']):>12.4f} {o['status']:<12}"
        )
    print(_divider(width=86))
    return 0


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="cli.py",
        description="Binance Futures Testnet — Trading Bot CLI",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog=(
            "Examples:\n"
            "  python cli.py place-order --symbol BTCUSDT --side BUY  --type MARKET --quantity 0.001\n"
            "  python cli.py place-order --symbol BTCUSDT --side SELL --type LIMIT  --quantity 0.001 --price 100000\n"
            "  python cli.py balance\n"
            "  python cli.py open-orders --symbol BTCUSDT\n"
        ),
    )
    subparsers = parser.add_subparsers(dest="command", required=True)

    po = subparsers.add_parser("place-order", help="Place a MARKET or LIMIT futures order.")
    po.add_argument("--symbol",   required=True,                            help="Trading pair, e.g. BTCUSDT.")
    po.add_argument("--side",     required=True, choices=["BUY", "SELL"],   help="BUY or SELL.", type=str.upper)
    po.add_argument("--type",     required=True, choices=["MARKET", "LIMIT"], help="MARKET or LIMIT.", type=str.upper, dest="type")
    po.add_argument("--quantity", required=True, type=float, metavar="QTY", help="Order size in base asset units.")
    po.add_argument("--price",    required=False, type=float, default=None, help="Limit price (required for LIMIT orders).")

    subparsers.add_parser("test-connection", help="Verify credentials and testnet connectivity.")
    subparsers.add_parser("balance",         help="Display futures wallet balances.")

    oo = subparsers.add_parser("open-orders", help="List open futures orders.")
    oo.add_argument("--symbol", type=str, default=None, help="Filter by trading pair (optional).")

    return parser


def main() -> None:
    parser = build_parser()
    args = parser.parse_args()

    if getattr(args, "type", None) == "LIMIT" and not getattr(args, "price", None):
        parser.error("--price is required when --type is LIMIT")

    try:
        client = BinanceClient()
    except ValueError as exc:
        print(_c(f"\n  ❌  Initialisation error: {exc}", _RED, _BOLD))
        logger.error("Initialisation error: %s", exc)
        sys.exit(1)

    handlers = {
        "place-order":     cmd_place_order,
        "test-connection": cmd_test_connection,
        "balance":         cmd_balance,
        "open-orders":     cmd_open_orders,
    }

    sys.exit(handlers[args.command](client, args))


if __name__ == "__main__":
    main()
