import os
import json
import logging
from threading import Thread

from flask import Flask, request, abort

# from BINANCE import MajorLongSygnal, MinorLongSygnal, CloseSygnal
from bot.utils import read_config, logger


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


def start_server():
    app.run(host=os.getenv("SERVER_IP"), port=80)
