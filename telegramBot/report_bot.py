import logging
import os

import telebot
from dotenv import load_dotenv
from telebot.types import Message, BotCommand

from data_processing import DataProcessing

load_dotenv()
bot = telebot.TeleBot(os.getenv('TELEGRAMBOT'))

commands = [
    BotCommand('info', 'Узнать о текущих добавлениях'),
    BotCommand('help', 'Посмотреть формат данных для ввода'),
]

bot.set_my_commands(commands)


@bot.message_handler(commands=['info'])
def send_welcome(message):
    user_id = message.from_user.id
    text = DataProcessing.get_current_data_from_db(user_id)
    bot.reply_to(message, text=text)


@bot.message_handler(commands=['help'])
def send_welcome(message):
    bot.reply_to(message, ('Нужно ввести данные в формате, где бр - "сумма брака А и Б".\n'
                           'Каждое значение через пробел, порядок не важен.\n'
                           'Пример:'))
    bot.reply_to(message, 'а0 б0 бр0')


@bot.message_handler(content_types=['photo'])
def get_photo(message):
    if bot.send_chat_action(
            chat_id=message.chat.id, action='upload_photo'):
        photo = bot.get_file(message.photo[-1].file_id)
        text = message.text
        print(text)
        photo_bytes = bot.download_file(photo.file_path)
        with open('image.jpg', 'wb') as new_file:
            new_file.write(photo_bytes)


@bot.message_handler(regexp=DataProcessing.PATTERN)
def get_data(message: Message):
    try:
        from_user = message.from_user
        user = DataProcessing.user_format(from_user.username, from_user.first_name, from_user.last_name)
        text = message.text
        user_id = from_user.id
        # logging.info(from_user, user, text, user_id, ' successful get.')

        DataProcessing().fill_data_in_db(user, user_id, text)
        text = DataProcessing.get_current_data_from_db(user_id)
        bot.send_message(chat_id=message.chat.id, text=text, reply_to_message_id=message.id)
    except Exception:
        bot.send_message(message.chat.id, f'Что-то пошло не так.')
        raise


@bot.message_handler()
def handle_wrong(message):
    bot.send_message(
        message.chat.id,
        'Неверный формат ввода.\n'
        'Пожалуйста, введите данные в правильном формате. Посмотрите команду /help'
    )


bot.infinity_polling()
