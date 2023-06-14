import json5

from src.utils.logs_configure import logger


def read_config() -> dict:
    """Reads config.json."""
    try:
        with open(f'../../config.json5', 'r', encoding='utf-8') as file:
            return json5.load(file)
    except Exception as err:
        logger.critical(f'Не получилось прочитать config.json, ошибка: {err}')


def update_config(new_config_data):
    # Открываем и загружаем старый конфиг
    old_config = read_config()

    # Обновляем значения из новых данных в старом конфиге
    for key, value in new_config_data.items():
        old_config[key] = value

    # Перезаписываем старый конфиг с обновленными значениями
    with open('../../config.json5', 'w') as f:
        json5.dump(old_config, f, indent=2)


config = read_config()
