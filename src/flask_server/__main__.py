import os
import json
import logging
from threading import Thread
from dotenv import load_dotenv

import art
from flask import Flask, request, abort

from src.utils import read_config, logger


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
        side = data['type']
        if symbol not in config['ignore_symbols']:
            print(symbol, side)
            th = Thread()
            th.daemon = True
            th.start()

            return {}
        abort(405)


def test():
    from src.binance_connector.MajorSignal import MajorSignal
    from src.binance_connector.MinorSignal import MinirSignal
    from src.binance_connector.CloseSignal import CloseSignal
    kw = {
        "symbol": "XRPUSDT",
        "side": "SELL",
        "type": "major"
    }
    # ss = StartStrategy(**kw)
    # ss.start_startegy()
    match kw['type']:
        case "major":
            del kw["type"]
            MajorSignal(**kw).major_signal()
        case "minor":
            del kw["type"]
            MinirSignal(**kw).minor_signal()
        case "close":
            del kw["type"]
            CloseSignal(**kw).close_signal()


def start_server():
    art.tprint('Apo\nMartin\nFlask\nServer')
    app.run(host=os.getenv("SERVER_IP"), port=80)


if __name__ == '__main__':
    # start_server()  # todo
    test()