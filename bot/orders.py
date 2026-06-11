"""Order placement and management for Binance Futures Testnet."""

from __future__ import annotations

import json
from typing import Any, Dict, Optional

import requests.exceptions
from binance.exceptions import BinanceAPIException, BinanceRequestException

from .client import BinanceClient
from .logging_config import logger
from .validators import (
    ValidationError,
    validate_leverage,
    validate_price_for_order_type,
    validate_quantity,
    validate_side,
    validate_symbol,
)


class OrderManager:
    """Handles order placement, cancellation, and status checks."""

    def __init__(self, client: BinanceClient) -> None:
        self.futures = client.futures_client

    def set_leverage(self, symbol: str, leverage: int) -> Dict[str, Any]:
        symbol = validate_symbol(symbol)
        leverage = validate_leverage(leverage)
        try:
            response = self.futures.futures_change_leverage(symbol=symbol, leverage=leverage)
            logger.info("Leverage set to %sx for %s", leverage, symbol)
            return response
        except BinanceAPIException as exc:
            logger.error("Failed to set leverage: %s", exc)
            raise

    def place_market_order(self, symbol: str, side: str, quantity: float) -> Dict[str, Any]:
        symbol   = validate_symbol(symbol)
        side     = validate_side(side)
        quantity = validate_quantity(quantity)

        payload = dict(symbol=symbol, side=side, type="MARKET", quantity=quantity)
        logger.info("Sending MARKET order: %s", json.dumps(payload))

        try:
            order = self.futures.futures_create_order(**payload)
            logger.info(
                "MARKET order placed | %s %s qty=%.6f | orderId=%s status=%s avgPrice=%s",
                side, symbol, quantity,
                order.get("orderId"), order.get("status"), order.get("avgPrice", "N/A"),
            )
            logger.debug("Full response: %s", json.dumps(order))
            return order
        except BinanceAPIException as exc:
            logger.error("MARKET order failed | code=%s msg=%s", exc.code, exc.message)
            raise
        except BinanceRequestException as exc:
            logger.error("MARKET order failed | request error: %s", exc)
            raise
        except requests.exceptions.RequestException as exc:
            logger.error("MARKET order failed | network error: %s", exc)
            raise

    def place_limit_order(
        self,
        symbol: str,
        side: str,
        quantity: float,
        price: float,
        time_in_force: str = "GTC",
    ) -> Dict[str, Any]:
        symbol          = validate_symbol(symbol)
        side            = validate_side(side)
        quantity        = validate_quantity(quantity)
        validated_price = validate_price_for_order_type("LIMIT", price)

        payload = dict(
            symbol=symbol, side=side, type="LIMIT",
            quantity=quantity, price=validated_price, timeInForce=time_in_force,
        )
        logger.info("Sending LIMIT order: %s", json.dumps(payload))

        try:
            order = self.futures.futures_create_order(**payload)
            logger.info(
                "LIMIT order placed | %s %s qty=%.6f @ %.4f | orderId=%s status=%s",
                side, symbol, quantity, validated_price,
                order.get("orderId"), order.get("status"),
            )
            logger.debug("Full response: %s", json.dumps(order))
            return order
        except BinanceAPIException as exc:
            logger.error("LIMIT order failed | code=%s msg=%s", exc.code, exc.message)
            raise
        except BinanceRequestException as exc:
            logger.error("LIMIT order failed | request error: %s", exc)
            raise
        except requests.exceptions.RequestException as exc:
            logger.error("LIMIT order failed | network error: %s", exc)
            raise

    def cancel_order(self, symbol: str, order_id: int) -> Dict[str, Any]:
        symbol = validate_symbol(symbol)
        logger.info("Cancelling order %s for %s", order_id, symbol)
        try:
            response = self.futures.futures_cancel_order(symbol=symbol, orderId=order_id)
            logger.info("Order %s cancelled", order_id)
            logger.debug("Cancel response: %s", json.dumps(response))
            return response
        except BinanceAPIException as exc:
            logger.error("Cancel failed | code=%s msg=%s", exc.code, exc.message)
            raise
        except BinanceRequestException as exc:
            logger.error("Cancel failed | request error: %s", exc)
            raise
        except requests.exceptions.RequestException as exc:
            logger.error("Cancel failed | network error: %s", exc)
            raise

    def get_open_orders(self, symbol: Optional[str] = None) -> list:
        kwargs = {"symbol": validate_symbol(symbol)} if symbol else {}
        try:
            orders = self.futures.futures_get_open_orders(**kwargs)
            logger.info("Fetched %d open order(s)", len(orders))
            return orders
        except BinanceAPIException as exc:
            logger.error("Failed to fetch open orders: %s", exc)
            raise

    def get_order_status(self, symbol: str, order_id: int) -> Dict[str, Any]:
        symbol = validate_symbol(symbol)
        try:
            order = self.futures.futures_get_order(symbol=symbol, orderId=order_id)
            logger.info("Order %s status: %s", order_id, order.get("status", "UNKNOWN"))
            return order
        except BinanceAPIException as exc:
            logger.error("Failed to fetch order status: %s", exc)
            raise
