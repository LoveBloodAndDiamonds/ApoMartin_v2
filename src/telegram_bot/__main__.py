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
    try:
        cfg = read_config()
        keys = {
              "margin_type": "Режим маржи: ",
              "margin_percent": "Процент маржи в позицию: ",
              "long_positions_amount": "Соотношение лонгов: ",
              "short_positions_amount": "Соотношение шортов: ",
              "available_drawdown": "Допустимая просадка: ",
              "min_to_close":  "Мин. % для закрытия: ",
              "min_to_add_on": "Мин. % для добавления: ",
              "add_on_kf": "Коэф. добавления: ",
              "martin_kf": "Коэф. мартингейла: ",
              "take_profit": "Тейк-профит от ср.: ",
              "take_profits_qty": "Количество тейков: ",
              "ignore_symbols": "Игнорируемые тикеры: "
        }
        text = '<b>Текущие настройки:</b>\n'
        for el in cfg:
            text += f"{keys[el]}<b>{cfg[el]}</b>\n"
        bot.reply_to(message, text, reply_markup=create_keyboard())
    except Exception as error:
        bot.reply_to(message, text=f"{error}")


@bot.message_handler(func=lambda message: message.text == "Как изменить настройки ❔")
@auth
def change_settings(message):
    # заглушка для действия "Как изменить настройки"
    curr_config = read_config()
    keys = {
        "margin_type": "режим маржи.",
        "margin_percent": "процент входа в сделку от баланса.",
        "long_positions_amount": "соотношение лонговых и шортовых позиций, считается так: "
                                 "balance * long_positions_amount / 100, и если общий размер всех лонговых позиций "
                                 "меньше, чем получившееся число - то открываем позицию.",
        "short_positions_amount": "соотношение лонговых и шортовых позиций, считается так: "
                                 "balance * long_positions_amount / 100, и если общий размер всех шортовых позиций "
                                 "меньше, чем получившееся число - то открываем позицию.",
        "available_drawdown": "допустимая просадка по PNL, при которой можно открывать позицию.",
        "min_to_close": "минимальное расстояние для закрытия позиции от средней в процентах.",
        "min_to_add_on": "минимальное расстояние для усреднения от последнего усреднения в процентах.",
        "add_on_kf": "коэф. на который умножается расстояние до усреднения при каждом ордере.",
        "martin_kf": "коэф. мартингейла, на это число будет умножаться последнее исполненое усреднение.",
        "take_profit": "расстояние от средней до тейк-профита, пересчитывается при каждом мажоре и миноре.",
        "take_profits_qty": "количество тейк-профитов.",
        "ignore_symbols": "обязательно в формате ['', '', ''], если допустишь ошибку, не поставишь скобку, "
                          "кавычку или запятую - весь бот сломается, будь осторожен."
    }
    text = f"Как обновить настройки?\n\n" \
           f"Скопируй данные снизу кликом по ним, и заполни:\n" \
           f"<code>{json.dumps(curr_config, indent=2)}</code>\n\n" \

    for key in curr_config:
        text += f"<b>{key}</b>: {keys[key]}\n\n"

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
