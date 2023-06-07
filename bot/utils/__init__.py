__all__ = ["read_config", "config", "log_arguments", "logger"]

from bot.utils.configreader import read_config
from bot.utils.logs_configure import log_arguments, logger


config = read_config()
