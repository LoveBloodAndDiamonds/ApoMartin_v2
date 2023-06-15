import os
import json
import logging
from threading import Thread
from dotenv import load_dotenv

import art
from flask import Flask, request, abort

from binance_connector import MajorSignal, MinorSignal, CloseSignal
from utils import read_config, logger


load_dotenv()
logging.getLogger('werkzeug').disabled = True
app = Flask(__name__)


@app.route('/ApoBot', methods=['POST'])
def sygnal_handler():
    """Handle post requests."""
    config = read_config()
    data = json.loads(request.data.decode('utf-8'))
    if data["secret"] == os.getenv("WEBHOOK_PASSCODE"):
        logger.info(f"Получен сигнал <{data['type']}> на монету <{data['symbol']}>")
        symbol = data['symbol'].split('.P')[0]
        signal_side = data['side']
        signal_type = data['type']
        if symbol not in config['ignore_symbols']:
            th = None

            match signal_type:
                case "major":
                    th = Thread(target=MajorSignal(symbol=symbol, side=signal_side).major_signal)
                case "minor":
                    th = Thread(target=MinorSignal(symbol=symbol, side=signal_side).minor_signal)
                case "close":
                    th = Thread(target=CloseSignal(symbol=symbol, side=signal_side).close_signal)

            if th:
                th.daemon = True
                th.start()

            return {}
        abort(405)


# def test():
#     from src.binance_connector.MajorSignal import MajorSignal
#     from src.binance_connector.MinorSignal import MinirSignal
#     from src.binance_connector.CloseSignal import CloseSignal
#     kw = {
#         "symbol": "XRPUSDT",
#         "side": "SELL",
#         "type": "major"
#     }
#     # ss = StartStrategy(**kw)
#     # ss.start_startegy()
#     match kw['type']:
#         case "major":
#             del kw["type"]
#             MajorSignal(**kw).major_signal()
#         case "minor":
#             del kw["type"]
#             MinirSignal(**kw).minor_signal()
#         case "close":
#             del kw["type"]
#             CloseSignal(**kw).close_signal()


def start_server():
    art.tprint('Apo\nMartin\nFlask\nServer')
    app.run(host=os.getenv("SERVER_IP"), port=80)


if __name__ == '__main__':
    start_server()
    # test()