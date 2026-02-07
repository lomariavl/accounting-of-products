import logging
import os

import telebot
from dotenv import load_dotenv
from telebot.types import Message, BotCommand

from data_handler import DataHandler
from db_handler import DatabaseHandler
from file_manager import FileManager

load_dotenv()
bot = telebot.TeleBot(os.getenv('TELEGRAMBOT'))

commands = [
    BotCommand('info', 'Узнать о текущих добавлениях'),
    BotCommand('help', 'Посмотреть формат ввода данных'),
]

bot.set_my_commands(commands)


@bot.message_handler(commands=['info'])
def send_info_about_data(message):
    user_id = message.from_user.id
    text = DatabaseHandler.get_data_from_db(user_id)
    bot.reply_to(message, text=text)


@bot.message_handler(commands=['help'])
def help_user(message):
    bot.reply_to(message, ('Нужно ввести данные в формате, где бр - "сумма брака А и Б".\n'
                           'Каждое значение через пробел, порядок не важен.\n'
                           'Пример:'))
    bot.reply_to(message, 'а0 б0 бр0')
    bot.reply_to(message,
                 'Текст сообщения без структуры \'а0 б0 бр0\', будет добавлен как комментарий сегодняшнего дня. '
                 'Исправить его можно, просто отправьте новое сообщение.')


@bot.message_handler(content_types=['photo'])
def get_photo(message):
    from_user = message.from_user
    username = DataHandler.username_format(from_user.username, from_user.first_name, from_user.last_name)
    try:
        photo = message.photo[-1]
        file = bot.get_file(photo.file_id)
        photo_bytes = bot.download_file(file.file_path)

        DatabaseHandler.add_basic_data_in_db(username, from_user.id)

        username = DataHandler.username_format(from_user.username, from_user.first_name, from_user.last_name, True)
        FileManager.save_file(username, photo_bytes, from_user.id)
        bot.reply_to(message, 'Фотография получена.')

        if message.caption:
            logging.warning(f'Caption was got: {message.caption}')
            DatabaseHandler.add_comment_in_storage_table(message.caption, from_user.id)
            bot.reply_to(message, text=f'Комментарий, что Вы отправили сегодня:\n{message.caption}')

    except Exception as e:
        logging.error(e)
        bot.send_message(message.chat.id, f'Что-то пошло не так.')
        raise


@bot.message_handler(regexp=DataHandler.PATTERN)
def get_ab(message: Message):
    try:
        from_user = message.from_user
        username = DataHandler.username_format(from_user.username, from_user.first_name, from_user.last_name)
        user_id = from_user.id
        text_message = message.text
        logging.warning(f'Data was got.\n{username} {user_id}\ntext_message={text_message}')

        DatabaseHandler.add_basic_data_in_db(username, user_id, text_message)
        text = DatabaseHandler.get_data_from_db(user_id)
        bot.send_message(chat_id=message.chat.id, text=text, reply_to_message_id=message.id)
    except Exception:
        bot.send_message(message.chat.id, f'Что-то пошло не так.')
        logging.error(Exception)
        raise


@bot.message_handler()
def get_comment(message):
    try:
        comment = message.text
        logging.warning(f'Today comment is "{comment}".')
        username = DataHandler.username_format(message.from_user.username, message.from_user.first_name,
                                               message.from_user.last_name)
        DatabaseHandler.add_basic_data_in_db(username, message.from_user.id)
        DatabaseHandler.add_comment_in_storage_table(comment, message.from_user.id)
        bot.send_message(chat_id=message.chat.id, text=f'Комментарий, что Вы отправили сегодня:\n{comment}',
                         reply_to_message_id=message.id)
    except Exception:
        bot.send_message(
            message.chat.id,
            'Что-то пошло не так. Посмотрите команду /help'
        )
        logging.error(Exception)
        raise


bot.infinity_polling()
