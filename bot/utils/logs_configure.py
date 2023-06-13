import sys

import pendulum
from loguru import logger


def set_datetime(record):
    """Set local datetime."""
    record["extra"]["datetime"] = pendulum.now("Europe/Moscow")


logger.remove(0)
logger.configure(patcher=set_datetime)
logger.add('../logs/logs.log',
           format="<white>{extra[datetime]:YYYY DD.MM HH:mm:ss}</white> | "
                  "<level>{level}</level>| "
                  "|{name} {function} line:{line}| "
                  "<bold>{message}</bold>",
           rotation="5 MB",
           compression='zip')
logger.add(sys.stderr,
           format="<white>{extra[datetime]:DD.MM HH:mm:ss}</white> | "
                  "<level>{level}</level>| "
                  "<bold>{message}</bold>",
           )


def log_arguments(func):
    def wrapper(*args, **kwargs):
        logger.debug(f"'{func.__name__}' args: {args}, kwargs: {kwargs}")
        result = func(*args, **kwargs)
        if result is not None:
            logger.debug(f"'{func.__name__}' returned: {result}")
        return result

    return wrapper
