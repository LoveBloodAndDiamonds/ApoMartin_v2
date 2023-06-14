import os
import json
from dotenv import load_dotenv

import art
import telebot

from src.utils import read_config, update_config


load_dotenv()
bot = telebot.TeleBot(os.getenv("BOT_TOKEN"), parse_mode='HTML')


def create_keyboard():
    # создаем клавиатуру с нужными кнопками
    keyboard = telebot.types.ReplyKeyboardMarkup(row_width=2)
    settings_button = telebot.types.KeyboardButton(text="Настройки ⚙️")
    how_settings_button = telebot.types.KeyboardButton(text="Как изменить настройки ❔")
    keyboard.add(settings_button, how_settings_button)
    return keyboard


def auth(func):
    """Аутентификация, бот отвечает только владельцу."""

    def wrapper(message):
        if str(message.from_user.id) != os.getenv("ADMIN_TELEGRAM_ID"):
            return bot.reply_to(message, "Denied!")
        return func(message)

    return wrapper


@bot.message_handler(commands=['start'])
@auth
def send_welcome(message):
    bot.reply_to(message, "Выберите действие:", reply_markup=create_keyboard())


@bot.message_handler(func=lambda message: message.text == "Настройки ⚙️")
@auth
def settings(message):
    cfg = read_config()
    text = 'Settings text:'
    bot.reply_to(message, text, reply_markup=create_keyboard())


@bot.message_handler(func=lambda message: message.text == "Как изменить настройки ❔")
@auth
def change_settings(message):
    # заглушка для действия "Как изменить настройки"
    curr_config = read_config()
    text = f"Как обновить настройки?\n\n" \
           f"Скопируй данные снизу кликом по ним, и заполни:\n" \
           f"<code>{json.dumps(curr_config, indent=2)}</code>\n\n" \
           f"margin_percent - процент входа в сделку от баланса.\n\n" \
           f"leverage: любое целое число, но будь внимательнее, некоторые монеты не поддерживают большие плечи.\n\n" \
           f"margin_type: CROSSED или ISOLATED, обязательно в кавычках.\n\n" \
           f"min_to_close: минимальное расстояние для закрытия позиции от средней в процентах.\n\n" \
           f"min_to_add_on: минимальное расстояние для усреднения от последнего усреднения в процентах.\n\n" \
           f"martin_kf: коэф. мартингейла, на это число будет умножаться последнее исполненое усреднение.\n\n" \
           f"max_opened_positions: максимальное количество открытых позиций.\n\n" \
           f"add_on_kf: коэф. на который умножается расстояние до усреднения при каждом ордере.\n\n" \
           f"trailing_take_profit: может быть либо true либо false, без кавычек, с маленькой буквы. " \
           f"Если true - то закрывается только верхний ордер, и выставляется тейк-профит на середину между " \
           f"ср. ценой и ценой закрытия. Если false - позиция закрывается полностью.\n\n" \
           f"ignore_symbols: обязательно в формате ['', '', ''], если допустишь ошибку, не поставишь скобку, " \
           f"кавычку или запятую - весь бот сломается, будь осторожен\n\n" \
           f"Поле того, как ты их заполнил нужными значениями просто отправь их боту."
    bot.reply_to(message, text, reply_markup=create_keyboard())


@bot.message_handler(func=lambda message: True)
@auth
def handle_json(message):
    try:
        data = json.loads(message.text)
        update_config(data)
        bot.reply_to(message, f"Вы отправили новые настройки: {json.dumps(data, indent=2)}\n\n"
                              f"Настройки успешно перезаписаны!")
    except Exception as error:
        bot.reply_to(message, f"Failed to parse JSON: {error}")


if __name__ == '__main__':
    art.tprint('Apo\nMartin\nTelegram\nBot')
    bot.infinity_polling()
