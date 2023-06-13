from binance_connector.MajorSignal import MajorSignal
from binance_connector.MinorSignal import MinirSignal
from bot.binance_connector.CloseSignal import CloseSignal


def main():
    kw = {
        "symbol": "XRPUSDT",
        "side": "SELL",
        "type": "close"
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


if __name__ == '__main__':
    main()
