import re
from threading import Thread
from time import sleep

import requests


class SymbolsDecimals:
    """Thread what update symbols decimals"""
    symbols_data: dict
    update_time: int = 60 * 60  # Update data timeout

    def update_data(self):
        """Update symbols decimals."""
        while True:
            precision_dict = dict()
            url = 'https://fapi.binance.com/fapi/v1/exchangeInfo'
            data = requests.get(url).json()
            for i in data['symbols']:
                filters = i['filters']
                tick_size, step_size = None, None
                for f in filters:
                    if f['filterType'] == 'PRICE_FILTER':
                        tick_size = f['tickSize']
                        tick_size = list(re.sub('0+$', '', tick_size))
                        if len(tick_size) == 1:
                            tick_size = 1
                        else:
                            tick_size = len(tick_size) - 2
                    if f['filterType'] == 'MARKET_LOT_SIZE':
                        step_size = f['stepSize']
                        step_size = list(re.sub('0+$', '', step_size))
                        if len(step_size) == 1:
                            step_size = 0
                        else:
                            step_size = len(step_size) - 2
                    precision_dict[i['symbol']] = [tick_size, step_size]
            self.symbols_data = precision_dict
            sleep(self.update_time)


symbols_decimals_obj = SymbolsDecimals()
th = Thread(target=symbols_decimals_obj.update_data)
th.daemon = True
th.start()
