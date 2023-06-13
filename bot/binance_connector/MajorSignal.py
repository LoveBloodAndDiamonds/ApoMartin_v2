from bot.binance_connector.BinanceUtils import BinanceUtils
from bot.binance_connector.CustomException import CustomException
from bot.utils import read_config, logger, send_telegram_alert


class MajorSignal(BinanceUtils):

    def __init__(self, symbol: str, side: str):
        super().__init__()
        self.symbol = symbol
        self.side = side
        self.position_side = "LONG" if side == "BUY" else "SHORT"
        self.i = 1 if side == "BUY" else 2  # index to get data from hedge mode
        self.config = read_config()

    def major_signal(self) -> None:
        """
        Major signal
        :return:
        """
        try:
            position_info: list = self.binance.futures_position_information(symbol=self.symbol)
            curr_pos: dict = position_info[self.i]
            curr_pos_leverage = int(curr_pos["leverage"])
            reversed_pos: dict = position_info[2 if self.i == 1 else 1]

            # Если позиция уже открыта, то игнорируем вход.
            if float(curr_pos['positionAmt']):
                logger.info(f"{self.symbol} уже есть открытая позиция в сторону {self.position_side}")
                return

            balance, _ = self.get_account_balance()

            # Если открыта позиция в противположную сторону - игнорируем
            # фильтры и открываем позицию в любом случае.
            if not float(reversed_pos['positionAmt']):
                opened_positions: list = self.binance.futures_position_information()  # All opened positions
                total_positions_amount: float = sum(  # Margin sum in all opened positions in curr side
                    [float(p["positionAmt"]) * float(p["entryPrice"]) for p in opened_positions
                     if p["positionSide"] == self.position_side])
                total_pnl: float = sum([float(p["unRealizedProfit"]) for p in opened_positions])

                # Проверка на то, допустимое ли соотношение лонговых позицйий к балансу аккаунта
                if not balance * self.config[
                    f"{self.position_side.lower()}_positions_amount"] / 100 >= total_positions_amount:
                    logger.info(
                        f"{self.symbol}, {self.side}, {self.position_side} соотношение по открытым позициям превышено.")
                    return

                # Проверка на то, допустимая ли сейчас просадка, для открытия новых ордеров
                if not total_pnl > -(balance * self.config["available_drawdown"]) / 100:
                    logger.info(f"{self.symbol}, {self.side}, {self.position_side} превышен размер просадки.")
                    return

            # Ищем подходящее плечо
            total_qty_usdt: float = balance * self.config['margin_percent'] / 100
            leverage_bracket: list = self.binance.futures_leverage_bracket(symbol=self.symbol)[0]["brackets"]
            for bracket in leverage_bracket:
                leverage: int = bracket['initialLeverage']
                if bracket['notionalCap'] > total_qty_usdt:
                    break
            else:
                raise CustomException(CustomException.SEND_ALERT, f"Не найдено подходящее плечо на {self.symbol}.")

            if curr_pos_leverage != leverage:
                self.change_leverage(symbol=self.symbol, leverage=leverage)
            open_price, total_qty = self.init_price_and_qty(symbol=self.symbol, margin=total_qty_usdt)
            order_id = self.create_market_order(symbol=self.symbol, qty=total_qty, side=self.side,
                                                pos_type=f'major_{self.position_side}',
                                                position_side=self.position_side)
            text = (f"Открыл позицию по <b>{self.symbol}</b>.\n"
                    f"Тип сигнала: <b>Major {self.position_side}</b>\n"
                    f"Цена открытия: <b>{open_price}</b> $\n"
                    f"Плечо: <b>{leverage}</b> X\n"
                    f"Размер позиции: <b>{total_qty}</b>\n"
                    f"Размер позиции: <b>{total_qty_usdt}</b> $\n"
                    f"ID ордера: <b>{order_id}</b>\n"
                    f"Баланс на аккаунте: <b>{balance}</b> $")
            logger.success(text)
            send_telegram_alert(text)
        except CustomException as error:
            if error.SEND_ALERT:
                send_telegram_alert(f"Ошибка!\n"
                                    f"Major, {self.symbol}, {self.side}, {self.position_side}\n"
                                    f"{error}")
            else:
                logger.error(error)
