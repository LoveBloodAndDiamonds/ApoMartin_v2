from bot.binance_connector.BinanceUtils import BinanceUtils

from bot.utils import logger, read_config
from bot.telegram_bot import send_telegram_alert


class StartStrategy(BinanceUtils):

    def __init__(self, symbol: str, side: str):
        super().__init__()
        self.symbol = symbol
        self.side = side
        self.i = 0 if side == "LONG" else 1  # index to get data from hedge mode
        self.config = read_config()
        self.try_again_if_error = True

    def start_startegy(self):
        # Меняем режим на хедж мод

        # Если позы нет - то это мажор сценарий, если есть - то это минор сценарий

        # Настройка сколько открытых лонговых и шортовых позиций, усреднять можно всегда, открывать новые - нельзя если
        # соотношение превышено. Смотреть тут надо на размер позиций (количество монет в позе * стоимость монеты)
        # и актуальный баланс.

        #  Ограничение по просадке, если стоит 5 процентов при балансе 1000, то нельзя открывать новые позиции если
        # PNL < -50$, усреднять позиции можно.

        # На каждой монете ставить максимальное плечо

        # Тейк профит пересчитывается каждый раз при создании ордера или при усреднении. При усреднении - нужно
        # отменять старый ТП, смотреть новую среднюю цену покупки сейчас, и выставлять новый.

        # Если размер позиции слишком большой - то нужно разбить тейк-профит на несколько кусочков с шагом
        position_info = self.position_info(self.symbol, self.i)

        if not float(position_info["positionAmt"]):
            logger.info(f"{self.symbol} major case")
            self.major_case(position_info)
        else:
            logger.info(f"{self.symbol} minir case")
            self.minor_case(position_info)

    def major_case(self, position_info: dict):
        balance, _ = self.get_account_balance()
        opened_short_positions = []
        opened_long_poisitions = []


    def minor_case(self, position_info: dict):
        ...
