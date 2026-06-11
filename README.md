# Binance Futures Testnet Trading Bot

A command-line trading bot for the **Binance USDT-M Futures Testnet**, built in Python.
It validates all order inputs locally before submitting to the exchange, logs every
request and response to file, and presents results in a clean, colour-coded terminal output.

---

## Table of Contents

1. [Project Overview](#project-overview)
2. [Project Structure](#project-structure)
3. [Setup](#setup)
4. [Running the Bot](#running-the-bot)
5. [CLI Reference](#cli-reference)
6. [Logging](#logging)
7. [Assumptions & Limitations](#assumptions--limitations)
8. [Test Results](#test-results)
9. [Submission Checklist](#submission-checklist)

---

## Project Overview

| Feature | Detail |
|---------|--------|
| Exchange | Binance USDT-M Futures **Testnet** |
| Base URL | `https://testnet.binancefuture.com` |
| Library | `python-binance 1.0.19` |
| Auth | API Key + Secret loaded from `.env` |
| Order types | MARKET, LIMIT (GTC) |
| Validation | Symbol, side, type, quantity, and price cross-validated before any API call |
| Logging | Dual output — `bot.log` (DEBUG) + console (INFO) |
| CLI | `argparse` subcommands with colour-coded output |

---

## Project Structure

```
trading_bot/
│
├── bot/
│   ├── __init__.py          # Package marker
│   ├── client.py            # BinanceClient — connection & account helpers
│   ├── orders.py            # OrderManager — order placement & management
│   ├── validators.py        # Input validation (symbol, side, type, qty, price)
│   └── logging_config.py    # Logger (file + console with timestamps)
│
├── cli.py                   # CLI entry point (argparse subcommands)
├── test_orders.py           # Standalone smoke-test script
├── requirements.txt         # Pinned Python dependencies
├── .env.example             # API key template
├── .gitignore               # Excludes .env, logs, caches, venvs
└── README.md
```

| File | Responsibility |
|------|---------------|
| `bot/client.py` | Wraps `python-binance` with `testnet=True`. Provides `ping()`, `get_account_balance()`, and `test_connection()`. |
| `bot/orders.py` | `OrderManager` class. `place_market_order()` and `place_limit_order()` validate, log the JSON payload, call the API, log the response, and re-raise on failure. |
| `bot/validators.py` | Pure validation functions. `validate_price_for_order_type()` enforces the cross-field rule: LIMIT requires a positive price; MARKET must have `price=None`. |
| `bot/logging_config.py` | Named logger writing DEBUG+ to `bot.log` and INFO+ to stdout with `YYYY-MM-DD HH:MM:SS | LEVEL | message` format. |
| `cli.py` | Four subcommands: `place-order`, `test-connection`, `balance`, `open-orders`. Validation errors are caught and printed before any API call is made. |

---

## Setup

### Prerequisites

- Python 3.10 or later
- Binance Futures Testnet account and API keys → <https://testnet.binancefuture.com>

### 1 — Clone the repository

```bash
git clone <your-repo-url>
cd trading_bot
```

### 2 — Create and activate a virtual environment

```bash
python -m venv .venv

# Windows (PowerShell)
.venv\Scripts\Activate.ps1

# macOS / Linux
source .venv/bin/activate
```

### 3 — Install dependencies

```bash
pip install -r requirements.txt
```

### 4 — Configure API keys

```bash
copy .env.example .env   # Windows
cp .env.example .env     # macOS / Linux
```

Edit `.env`:

```dotenv
BINANCE_API_KEY=your_testnet_api_key_here
BINANCE_API_SECRET=your_testnet_api_secret_here
```

> ⚠️ **Never commit `.env` to version control.** It is already listed in `.gitignore`.

---

## Running the Bot

### Verify the connection

```bash
python cli.py test-connection
```

```
2026-06-11 23:28:27 | INFO     | BinanceClient initialised (Futures Testnet)
2026-06-11 23:28:27 | INFO     | Running connection test...
2026-06-11 23:28:27 | INFO     | Ping successful – Futures Testnet is reachable.
2026-06-11 23:28:28 | INFO     | Fetched account balance (8 asset(s))
2026-06-11 23:28:28 | INFO     | Non-zero balances:
2026-06-11 23:28:28 | INFO     |   BTC        | balance: 0.01000000 | available: 0.01000000
2026-06-11 23:28:28 | INFO     |   USDT       | balance: 5000.00000000 | available: 5000.00000000
2026-06-11 23:28:28 | INFO     |   USDC       | balance: 5000.00000000 | available: 5000.00000000

  ✅  Connection to Binance Futures Testnet is working.
```

### Place a MARKET order

```bash
python cli.py place-order --symbol BTCUSDT --side BUY --type MARKET --quantity 0.001
```

```
────────────────────────────────────────────────────────
  ORDER REQUEST SUMMARY
────────────────────────────────────────────────────────
  Symbol        : BTCUSDT
  Side          : BUY
  Type          : MARKET
  Quantity      : 0.001000
  Price         : MARKET (best available)
────────────────────────────────────────────────────────

────────────────────────────────────────────────────────
  ORDER RESULT
────────────────────────────────────────────────────────
  Order ID         : 14853565849
  Client Order ID  : DnfM8Vr797dM36z0XHXyF7
  Symbol           : BTCUSDT
  Side             : BUY
  Type             : MARKET
  Status           : NEW
  Executed Qty     : 0.000000
  Avg Fill Price   : Pending fill
────────────────────────────────────────────────────────
  ✅  Order placed successfully
```

> **Testnet behaviour:** The Binance Futures Testnet returns `status: NEW` for market orders
> instead of `FILLED`. The order is accepted and matched shortly after by the testnet engine.
> On the live exchange, market orders return `FILLED` immediately.

### Place a LIMIT order

```bash
python cli.py place-order --symbol BTCUSDT --side SELL --type LIMIT --quantity 0.001 --price 100000
```

The price `$100,000` is intentionally far above the current market so the order stays open
and can be inspected with `open-orders` without triggering a fill.

### View balances

```bash
python cli.py balance
```

### List open orders

```bash
python cli.py open-orders --symbol BTCUSDT
```

---

## CLI Reference

```
usage: cli.py [-h] {place-order,test-connection,balance,open-orders} ...

place-order flags:
  --symbol   SYMBOL      Trading pair, e.g. BTCUSDT          [required]
  --side     BUY|SELL    Order side                          [required]
  --type     MARKET|LIMIT  Order type                        [required]
  --quantity QTY         Order size in base asset units      [required]
  --price    PRICE       Limit price (required for LIMIT)    [optional]
```

---

## Logging

All activity is written to **`bot.log`** in the project root.

| Stream | Level | Format |
|--------|-------|--------|
| `bot.log` | DEBUG and above | `YYYY-MM-DD HH:MM:SS \| LEVEL \| message` |
| Console | INFO and above | Same format |

| Event | Level |
|-------|-------|
| Client initialised | INFO |
| Ping result | INFO |
| Account balance fetch | INFO |
| Order request payload (JSON) | INFO |
| Order placed (orderId, status, avgPrice) | INFO |
| Full raw API response | DEBUG |
| Validation errors | ERROR |
| API errors (code + message) | ERROR |
| Network errors | ERROR |

> `bot.log` is excluded from version control via `.gitignore`.

---

## Assumptions & Limitations

| Assumption | Detail |
|------------|--------|
| **Testnet only** | Base URL is hard-coded to `https://testnet.binancefuture.com`. Live trading requires changing `testnet=True` → `False` in `client.py`. |
| **Testnet order status** | The Futures Testnet returns `status: NEW` for market orders because its matching engine does not fill synchronously. `avgPrice` is `0` in the immediate response. This is normal testnet behaviour, not an error. |
| **USDT-M Futures** | Only USDT-margined futures are supported. |
| **Small quantities** | Test orders use `0.001 BTC` to stay within testnet margin limits. |
| **MARKET & LIMIT only** | Validators accept only `MARKET` and `LIMIT` order types. Stop-loss and take-profit orders are not implemented. |
| **No position management** | The bot places orders but does not track positions or PnL. |
| **GTC time-in-force** | LIMIT orders default to Good-Till-Cancelled. |
| **No rate-limit handling** | No exponential backoff for `429`/`418` responses. |
| **Python 3.10+** | Requires `from __future__ import annotations` f-string support. |

---

## Test Results

All tests confirmed working on Binance Futures Testnet.

### bot.log — captured during testing

```
2026-06-11 23:28:27 | INFO     | BinanceClient initialised (Futures Testnet)
2026-06-11 23:28:27 | INFO     | Running connection test...
2026-06-11 23:28:27 | INFO     | Ping successful – Futures Testnet is reachable.
2026-06-11 23:28:28 | INFO     | Fetched account balance (8 asset(s))
2026-06-11 23:28:28 | INFO     | Non-zero balances:
2026-06-11 23:28:28 | INFO     |   BTC        | balance: 0.01000000 | available: 0.01000000
2026-06-11 23:28:28 | INFO     |   USDT       | balance: 5000.00000000 | available: 5000.00000000
2026-06-11 23:28:28 | INFO     |   USDC       | balance: 5000.00000000 | available: 5000.00000000
2026-06-11 23:31:55 | INFO     | BinanceClient initialised (Futures Testnet)
2026-06-11 23:31:55 | INFO     | Sending MARKET order: {"symbol": "BTCUSDT", "side": "BUY", "type": "MARKET", "quantity": 0.001}
2026-06-11 23:31:56 | INFO     | MARKET order placed | BUY BTCUSDT qty=0.001000 | orderId=14851361815 status=NEW avgPrice=N/A
2026-06-11 23:31:56 | DEBUG    | Full response: {"orderId": 14851361815, "symbol": "BTCUSDT", "status": "NEW", ...}
2026-06-11 23:34:20 | ERROR    | Validation error: Symbol 'BTC123' contains invalid characters. Expected letters only (e.g. 'BTCUSDT').
2026-06-11 23:34:56 | ERROR    | Validation error: Quantity must be greater than 0.0, got: -0.001
2026-06-11 23:35:14 | INFO     | Sending MARKET order: {"symbol": "XYZABC", "side": "BUY", "type": "MARKET", "quantity": 0.001}
2026-06-11 23:35:15 | ERROR    | MARKET order failed | code=-1121 msg=Invalid symbol.
2026-06-11 23:40:33 | INFO     | Sending MARKET order: {"symbol": "BTCUSDT", "side": "BUY", "type": "MARKET", "quantity": 0.001}
2026-06-11 23:40:34 | INFO     | MARKET order placed | BUY BTCUSDT qty=0.001000 | orderId=14853565849 status=NEW avgPrice=N/A
```

### Test scenarios confirmed

| # | Test | Result |
|---|------|--------|
| 1 | `test-connection` | ✅ Ping + balances fetched |
| 2 | `balance` | ✅ USDT / BTC / USDC displayed |
| 3 | MARKET BUY 0.001 BTCUSDT | ✅ Order accepted (`orderId=14853565849`) |
| 4 | LIMIT SELL 0.001 BTCUSDT @ $100,000 | ✅ Order stays `NEW` |
| 5 | Bad symbol (`BTC123`) | ✅ Caught by validator before API call |
| 6 | Invalid side (`LONG`) | ✅ Caught by argparse |
| 7 | Invalid type (`STOP`) | ✅ Caught by argparse |
| 8 | LIMIT without `--price` | ✅ Caught by cross-argument guard |
| 9 | Negative quantity | ✅ Caught by validator |
| 10 | Invalid exchange symbol (`XYZABC`) | ✅ API error surfaced: `code=-1121 Invalid symbol.` |

---

## Submission Checklist

- [x] Project structure matches specification
- [x] `client.py` connects to Binance Futures Testnet and fetches account balance
- [x] `validators.py` validates symbol, side, order type, quantity, and price (with cross-field MARKET/LIMIT rule)
- [x] `orders.py` places MARKET and LIMIT orders via the API
- [x] `cli.py` accepts `--symbol`, `--side`, `--type`, `--quantity`, `--price` and prints formatted output
- [x] Pre-flight order summary printed before every API call
- [x] Success response shows `orderId`, `status`, `executedQty`, `avgPrice`
- [x] All errors caught and displayed as friendly `❌ Order failed: <reason>` messages
- [x] All activity logged to `bot.log` with timestamps and log levels
- [x] `requirements.txt` lists all dependencies with pinned versions
- [x] `.env.example` provides the key template without real values
- [x] `.gitignore` excludes `.env`, `*.log`, `__pycache__/`, `venv/`
- [x] No API keys committed to the repository
- [x] Code tested end-to-end on Binance Futures Testnet (MARKET + LIMIT orders confirmed)
