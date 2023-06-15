from src.binance_connector.BinanceUtils import BinanceUtils
from src.binance_connector.CustomException import CustomException
from src.utils import read_config, logger, send_telegram_alert


class CloseSignal(BinanceUtils):

    def __init__(self, symbol: str, side: str):
        super().__init__()
        self.symbol = symbol
        self.side = side
        self.position_side = "LONG" if side == "BUY" else "SHORT"
        self.i = 1 if side == "BUY" else 2  # index to get data from hedge mode
        self.config = read_config()

    def close_signal(self):
        try:
            position_info = self.position_info(symbol=self.symbol, index=self.i)

            if not float(position_info['positionAmt']):
                '''Here is no opened position'''
                logger.info(f'Нет открытой позиции по {self.symbol};')
                return

            current_price = self.init_price(symbol=self.symbol)

            # Проверка на пройденное расстояние для закрытия
            wrong_distance_flag = False
            if self.side == "BUY":
                if current_price < (float(position_info['entryPrice']) * (1 + self.config['min_to_close'] / 100)):
                    wrong_distance_flag = True
            elif self.side == "SELL":
                if current_price > (float(position_info['entryPrice']) * (1 - self.config['min_to_close'] / 100)):
                    wrong_distance_flag = True
            if wrong_distance_flag:
                logger.debug('Не пройдено расстояние для закрытия позиции;')
                return

            close_qty = float(position_info['positionAmt'])
            close_side = "SELL" if close_qty > 0 else "BUY"
            order_id = self.create_market_order(symbol=self.symbol, qty=abs(close_qty), side=close_side,
                                                pos_type=f'close_{self.position_side}',
                                                position_side=self.position_side)

            text = (f"Закрыл позицию по <b>{self.symbol}</b>.\n"
                    f"Тип сигнала: <b>Close</b>\n"
                    f"Цена закрытия: <b>{current_price}</b>\n"
                    f"Размер закрытия: <b>{close_qty}</b>\n"
                    f"ID ордера: <b>{order_id}</b>\n")
            logger.success(text)
            send_telegram_alert(text)

        except CustomException as error:
            if error.SEND_ALERT:
                send_telegram_alert(f"Ошибка!\n"
                                    f"Major, {self.symbol}, {self.side}, {self.position_side}\n"
                                    f"{error}")
            else:
                logger.error(error)
