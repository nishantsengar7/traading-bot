"""
Binance Futures Testnet API client.
Loads credentials from .env and wraps python-binance.
"""

from __future__ import annotations

import os
from typing import Any, Dict, List

from binance.client import Client
from binance.exceptions import BinanceAPIException, BinanceRequestException
from dotenv import load_dotenv

from .logging_config import logger

FUTURES_TESTNET_BASE_URL = "https://testnet.binancefuture.com"


class BinanceClient:
    """Connection to the Binance USDT-M Futures Testnet."""

    def __init__(self, env_file: str = ".env") -> None:
        load_dotenv(env_file)

        self.api_key: str = os.getenv("BINANCE_API_KEY", "")
        self.api_secret: str = os.getenv("BINANCE_API_SECRET", "")

        if not self.api_key or not self.api_secret:
            raise ValueError(
                "BINANCE_API_KEY and BINANCE_API_SECRET must be set in your .env file."
            )

        self.futures_client = Client(
            api_key=self.api_key,
            api_secret=self.api_secret,
            testnet=True,
        )

        # Explicitly pin to testnet URLs as a safety net
        self.futures_client.FUTURES_URL = FUTURES_TESTNET_BASE_URL + "/fapi"
        self.futures_client.API_URL = FUTURES_TESTNET_BASE_URL

        logger.info("BinanceClient initialised (Futures Testnet)")

    def ping(self) -> bool:
        """Return True if the testnet is reachable."""
        try:
            self.futures_client.futures_ping()
            logger.info("Ping successful – Futures Testnet is reachable.")
            return True
        except (BinanceAPIException, BinanceRequestException) as exc:
            logger.error("Ping failed: %s", exc)
            return False

    def get_account_balance(self) -> List[Dict[str, Any]]:
        """Return futures wallet balances for all assets."""
        try:
            balances: List[Dict[str, Any]] = self.futures_client.futures_account_balance()
            logger.info("Fetched account balance (%d asset(s))", len(balances))
            return balances
        except (BinanceAPIException, BinanceRequestException) as exc:
            logger.error("Failed to fetch account balance: %s", exc)
            raise

    def test_connection(self) -> bool:
        """Ping the server and log non-zero balances. Returns True on success."""
        logger.info("Running connection test...")

        if not self.ping():
            return False

        try:
            balances = self.get_account_balance()
            non_zero = [b for b in balances if float(b.get("balance", 0)) > 0]
            if non_zero:
                logger.info("Non-zero balances:")
                for b in non_zero:
                    logger.info(
                        "  %-10s | balance: %s | available: %s",
                        b["asset"], b["balance"], b["availableBalance"],
                    )
            else:
                logger.info("All balances are zero (testnet account may need funding).")
            return True
        except Exception as exc:
            logger.error("Connection test failed: %s", exc)
            return False
