from bot.binance_connector.BinanceUtils import BinanceUtils
from bot.binance_connector.SymbolsDecimals import symbols_decimals_obj
from bot.utils import read_config, logger


class MinirSignal(BinanceUtils):
    signal_type: str = "minor"

    def __init__(self, symbol: str, side: str):
        super().__init__()
        self.symbol = symbol
        self.side = side
        self.position_side = "LONG" if side == "BUY" else "SHORT"
        self.i = 1 if side == "BUY" else 2  # index to get data from hedge mode
        self.config = read_config()

    def minor_signal(self):
        """
        Minor signal
        :return:
        """
        position_info: list = self.binance.futures_position_information(symbol=self.symbol)
        curr_pos: dict = position_info[self.i]

        # Если позиция уже открыта, то игнорируем вход.
        if not float(curr_pos['positionAmt']):
            logger.info(f"{self.symbol} нет открытой позиции в сторону {self.position_side}")
            return

        orders_history = self.get_orders_history(symbol=self.symbol, signal_side=self.position_side)
        position_history = self.process_orders_history(orders_history=orders_history)
        open_orders = [o for o in position_history if \
                       o['clientOrderId'].startswith("major_") or o['clientOrderId'].startswith("minor_")]
        close_orders = [o for o in position_history if o['clientOrderId'].startswith("close_")]
        # if close_orders:
        #     logger.debug(f"{self.symbol} position already have closed order")
        #     return

        prev_order = open_orders[-1]
        prev_order_price = float(prev_order['avgPrice'])
        prev_order_qty = float(prev_order['origQty'])
        prev_order_avg_price = float(prev_order['avgPrice'])
        current_price = self.init_price(symbol=self.symbol)

        min_to_add_on = self.config['min_to_add_on'] * (self.config['add_on_kf'] ** (len(open_orders) - 1))
        print(f'{min_to_add_on=}')
        print(f'{prev_order_price=}')
        is_good_distance = True
        if self.side == "BUY":
            if prev_order_price * (1 - min_to_add_on / 100) < current_price:
                is_good_distance = False
        elif self.side == "SELL":
            if prev_order_price * (1 + min_to_add_on / 100) > current_price:
                is_good_distance = False
        if not is_good_distance:
            logger.debug('Цена не прошла достаточное расстояние для усреднения.')
            return

        last_order_margin = prev_order_qty * prev_order_avg_price
        martin_order_margin = last_order_margin * self.config['martin_kf']
        martin_order_qty = martin_order_margin / current_price
        martin_order_qty = round(martin_order_qty, symbols_decimals_obj.symbols_data[self.symbol][1])

        order_id = self.create_market_order(symbol=self.symbol, qty=martin_order_qty, side=self.side,
                                            position_side=self.position_side, pos_type=f'minor_{self.position_side}')
        text = (f"Открыл позицию по <b>{self.symbol}</b>.\n"
                f"Тип сигнала: <b>Minor {self.position_side}</b>\n"
                f"Цена открытия: <b>{current_price}</b>\n"
                f"Размер добавления: <b>{martin_order_margin}</b> $\n"
                f"Размер добавления: <b>{martin_order_qty}</b>\n"
                f"ID ордера: <b>{order_id}</b>\n")
        logger.success(text)
        all_open_orders = self.binance.futures_get_open_orders(symbol=self.symbol)
        for order in all_open_orders:
            order_id = order["orderId"]
            client_order_id: str = order["clientOrderId"]
            if client_order_id.startswith(f"close_{self.position_side}"):
                try:
                    self.binance.futures_cancel_order(symbol=self.symbol, orderId=order_id)
                except Exception as err:
                    logger.error(err)

        if self.config["take_profit"]:
            position_info: list = self.binance.futures_position_information(symbol=self.symbol)
            curr_pos_info: dict = position_info[self.i]
            curr_pos_amt = abs(float(curr_pos_info["positionAmt"]))
            curr_open_price = float(curr_pos_info["entryPrice"])
            if self.side == "BUY":
                tp_price = curr_open_price * (1 + self.config["take_profit"] / 100)
            elif self.side == "SELL":
                tp_price = curr_open_price * (1 - self.config["take_profit"] / 100)
            tp_price = round(tp_price, symbols_decimals_obj.symbols_data[self.symbol][0])
            self.create_limit_order(symbol=self.symbol, side=self.side, position_side=self.position_side,
                                    price=tp_price, qty=curr_pos_amt, pos_type=f"close_{self.position_side}")
