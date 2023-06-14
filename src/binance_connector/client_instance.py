__all__ = ['binance_client']

import os

from binance import Client

from bot.utils import logger


"""Init binance client on startup to decrease delay when app work."""
try:
    binance_client = Client(os.getenv("BINANCE_API_KEY"), os.getenv("BINANCE_API_SECRET"))
    logger.success(f"Binance client connected!")
except Exception as err:
    logger.critical(f"Cant connect to binance, err: {err}")
    exit()
