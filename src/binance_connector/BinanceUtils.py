import random
import time
from typing import Tuple

from binance import Client

from bot.binance_connector.CustomException import CustomException
from bot.binance_connector.SymbolsDecimals import symbols_decimals_obj
from bot.binance_connector.client_instance import binance_client
from bot.utils import log_arguments, read_config

config = read_config()


class BinanceUtils:
    binance: Client = binance_client

    @log_arguments
    def get_open_positions_count(self) -> int:
        """Returns how much opened positions now."""
        return len([el['symbol'] for el in self.binance.futures_position_information() if float(el['positionAmt'])])

    @log_arguments
    def get_open_positions(self) -> list:
        """Returns how much opened positions now."""
        return [el for el in self.binance.futures_position_information() if float(el['positionAmt'])]

    @log_arguments
    def position_info(self, symbol: str, index: int) -> dict:
        """Returns position info.
        {'symbol': 'BTCUSDT', 'positionAmt': '0.000', 'entryPrice': '0.0', 'markPrice': '26805.85111172',
        'unRealizedProfit': '0.00000000', 'liquidationPrice': '0', 'leverage': '10',
        'maxNotionalValue': '30000000', 'marginType': 'isolated', 'isolatedMargin': '0.00000000',
        'isAutoAddMargin': 'false', 'positionSide': 'BOTH', 'notional': '0', 'isolatedWallet': '0',
        'updateTime': 1683484646160}"""
        return self.binance.futures_position_information(symbol=symbol)[index]

    @log_arguments
    def get_position_margin(self, symbol: str) -> float:
        """Returns margin on position by symbol"""
        for el in self.binance.futures_account()['positions']:
            if el['symbol'] == symbol:
                return float(el['initialMargin'])

    @log_arguments
    def get_account_balance(self) -> Tuple[float, float]:
        """Returns 2 values, 1: total_balance, 2: available_balance."""
        for el in self.binance.futures_account_balance():
            if el['asset'] == 'USDT':
                return float(el['balance']), float(el['withdrawAvailable'])

    @log_arguments
    def init_symbol_leverage(self, symbol: str, leverage: int) -> None:
        """Initialize symbols leverage and change it if not availble"""
        data = self.binance.futures_leverage_bracket(symbol=symbol)
        available_leverage = int(data[0]['brackets'][0]['initialLeverage'])
        if available_leverage < leverage:
            raise CustomException(
                CustomException.SEND_ALERT,
                f'Выбрано неправильное плечо для монеты {symbol} вы указали {config["leverage"]}, а максимально '
                f'доступное: {available_leverage}')

    @log_arguments
    def init_price_and_qty(self, symbol: str, margin: float) -> Tuple[float, float]:
        """Init qty to open pos and symbols price now."""
        price = self.init_price(symbol=symbol)
        total_qty = round(margin / price, symbols_decimals_obj.symbols_data[symbol][1])
        if total_qty == 0:
            raise CustomException(
                CustomException.NOT_SEND_ALERT,
                f'Слишком маленький размер позиции по {symbol}'
            )

        return price, total_qty

    def init_price(self, symbol: str) -> float:
        return float(self.binance.futures_symbol_ticker(symbol=symbol)['price'])

    @log_arguments
    def change_leverage(self, symbol: str, leverage: int) -> None:
        """Changed leverage on symbol"""
        try:
            self.binance.futures_change_leverage(
                symbol=symbol,
                leverage=leverage
            )
        except Exception as err:
            raise CustomException(
                CustomException.NOT_SEND_ALERT,
                f"Ошибка при смене плеча на {symbol}: {err}"
            )

    @log_arguments
    def change_margin_type(self, symbol: str, margin_type: str):
        """Changes margin type on symbol."""
        try:
            self.binance.futures_change_margin_type(
                symbol=symbol,
                marginType=margin_type
            )
        except Exception as err:
            # err.code -4046 said what we do not need to change margin type.
            if err.code != -4046:
                raise CustomException(
                    CustomException.NOT_SEND_ALERT,
                    f"Ошибка при смене режима маржи на {symbol}: {err}"
                )

    @log_arguments
    def create_market_order(self, symbol: str, pos_type: str, qty: float, side: str, position_side: str) -> int:
        """Create custom market order to open/add_on/close position."""
        try:
            return self.binance.futures_create_order(
                symbol=symbol,
                type='MARKET',
                side=side,
                positionSide=position_side,
                quantity=qty,
                newClientOrderId=str(pos_type) + "_" + str(random.randint(100000, 999999))
            )['orderId']
        except Exception as err:
            raise CustomException(
                CustomException.SEND_ALERT,
                f"Ошибка при {pos_type} на {symbol}: {err}"
            )

    @log_arguments
    def create_stop_market_order(self, symbol: str, price: float, side: str = 'SELL') -> int:
        """Create limit order to close position"""
        try:
            return self.binance.futures_create_order(
                symbol=symbol,
                type='STOP_MARKET',
                side=side,
                stopPrice=price,
                closePosition=True
            )['orderId']
        except Exception as err:
            raise CustomException(
                CustomException.SEND_ALERT,
                f"Ошибка при создании лимитного ордера на {symbol}: {err}"
            )

    @log_arguments
    def create_limit_order(self, symbol: str, side: str, position_side: str, price: float, qty: float, pos_type: str):
        close_side = "SELL" if side == "BUY" else "BUY"
        try:
            return self.binance.futures_create_order(
                symbol=symbol,
                type="LIMIT",
                positionSide=position_side,
                side=close_side,
                price=price,
                quantity=qty,
                timeInForce="GTC",
                newClientOrderId=str(pos_type) + "_" + str(random.randint(100000, 999999))
            )
        except Exception as err:
            raise CustomException(
                CustomException.SEND_ALERT,
                f"Ошибка при создании лимитного ордера на {symbol}: {err}"
            )

    @log_arguments
    def get_income_history(self, symbol: str, start_time: int, end_time=False) -> Tuple[float, float]:
        """Returns comission and total profit from time to time."""
        income_history_kwargs = {"symbol": symbol, "startTime": start_time - 1000}
        if end_time:
            income_history_kwargs['endTime'] = end_time
        data = self.binance.futures_income_history(**income_history_kwargs)
        comission = sum([float(z['income']) for z in data if z['incomeType'] in ['COMMISSION', 'FUNDING_FEE']])
        total_profit = sum([float(z['income']) for z in data])

        return comission, total_profit

    @log_arguments
    def get_orders_history(self, symbol: str, signal_side: str) -> list:
        """Returns all orders history till major long.
        :param symbol: ticker
        :param signal_side: side of sygnal"""
        # start time < end time
        data = []
        end_time = int(time.time())
        start_time = int(end_time - 60 * 60 * 24 * 7)
        for _ in range(100):
            for order in reversed(self.binance.futures_get_all_orders(
                    symbol=symbol,
                    startTime=start_time * 1000,
                    endTime=end_time * 1000 + 10000)):
                client_order_id: str = order['clientOrderId']
                if signal_side in client_order_id:
                    data.append(order)
                if client_order_id.startswith(f"major_{signal_side}"):
                    return list(reversed(data))
            end_time = start_time
            start_time = int(start_time - 60 * 60 * 24 * 7)
            time.sleep(.1)  # If major order too far - we do not want to get block from binance.api
        else:
            raise CustomException(
                CustomException.SEND_ALERT,
                f"Не нашел Major Long по {symbol}"
            )

    @staticmethod
    @log_arguments
    def process_orders_history(orders_history: list) -> list:
        """Handle and process orders to understand what orders closed.
        Returns list of dicts, every order have key 'is_closed'
        [{'orderId': 1063355186, 'symbol': '1000PEPEUSDT', 'status': 'FILLED', 'clientOrderId': 'major_long', 'price': '0',
      'avgPrice': '0.0014553', 'origQty': '6867', 'executedQty': '6867', 'cumQuote': '9.9935451', 'timeInForce': 'GTC',
      'type': 'MARKET', 'reduceOnly': False, 'closePosition': False, 'side': 'BUY', 'positionSide': 'BOTH',
      'stopPrice': '0', 'workingType': 'CONTRACT_PRICE', 'priceProtect': False, 'origType': 'MARKET',
      'time': 1684950361024, 'updateTime': 1684950361024, 'is_closed': False},
        {'orderId': 1065232792, 'symbol': '1000PEPEUSDT', 'status': 'FILLED', 'clientOrderId': 'minor_long', 'price': '0',
      'avgPrice': '0.0014327', 'origQty': '8584', 'executedQty': '8584', 'cumQuote': '12.2982968', 'timeInForce': 'GTC',
      'type': 'MARKET', 'reduceOnly': False, 'closePosition': False, 'side': 'BUY', 'positionSide': 'BOTH',
      'stopPrice': '0', 'workingType': 'CONTRACT_PRICE', 'priceProtect': False, 'origType': 'MARKET',
      'time': 1684953175807, 'updateTime': 1684953175807, 'is_closed': False},
        {'orderId': 1076737696, 'symbol': '1000PEPEUSDT', 'status': 'FILLED', 'clientOrderId': 'minor_long', 'price': '0',
      'avgPrice': '0.0013669', 'origQty': '10730', 'executedQty': '10730', 'cumQuote': '14.6668370',
      'timeInForce': 'GTC', 'type': 'MARKET', 'reduceOnly': False, 'closePosition': False, 'side': 'BUY',
      'positionSide': 'BOTH', 'stopPrice': '0', 'workingType': 'CONTRACT_PRICE', 'priceProtect': False,
      'origType': 'MARKET', 'time': 1684978261033, 'updateTime': 1684978261033, 'is_closed': False}]"""
        for order in orders_history:  # add is closed tag
            order['is_closed'] = False

        open_orders = [o for o in orders_history if o['clientOrderId'] in ['major_long', 'minor_long']]
        close_orders = [o for o in orders_history if o['clientOrderId'] == 'close']

        total_close_qty = sum([float(order['origQty']) for order in close_orders])
        total_close_qty_percent = total_close_qty * 0.001

        for order in open_orders:
            if total_close_qty < total_close_qty_percent:
                break
            if total_close_qty > float(order['origQty']):
                order['is_closed'] = True
                total_close_qty -= float(order['origQty'])

        return orders_history
