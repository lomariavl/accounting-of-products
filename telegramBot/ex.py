import logging
import os
import re
from typing import List, Dict

import psycopg2
from dotenv import load_dotenv


class DataHandler:
    PRODUCT_TYPE_KEYS = {
        'а': 'a',
        'б': 'b',
        'р': 'p'
    }
    PATTERN = r'\b([abpабрАБР]+)(\d+)\b'

    @staticmethod
    def username_format(username: str, first_name, last_name) -> str:
        return '@' + username if username else first_name + ' ' + last_name

    @staticmethod
    def convert_message_in_eng(message: str) -> str:
        message = message.lower()
        result = ''
        for char in message:
            result += DataHandler.PRODUCT_TYPE_KEYS.get(char, char)
        return result

    @staticmethod
    def get_list_from_str(message: str) -> List[tuple]:
        result = re.findall(DataHandler.PATTERN, message, re.I)
        return [(letters, num) for letters, num in result]

    @staticmethod
    def convert_data_in_russ(data: list, en_to_ru: Dict) -> str:
        result = []
        for q, ab, date in data:
            ru_key = en_to_ru.get(ab, ab)
            result.append((q, ru_key, date))
        return f'На {result[0][2].strftime("%d.%m.%y")} добавлено:\n' + '\n'.join(
            f'{ab} {q}' for q, ab, d in sorted(result, key=lambda x: (len(x[1]), x[1])))


class DatabaseHandler:
    @staticmethod
    def add_data_in_db(username: str, user_id: int, message: str):
        query = """INSERT INTO storage(username, user_id_telegram, quantity, ab) VALUES(%s, %s, %s, %s);"""
        message = DataHandler.convert_message_in_eng(message)
        processed_message = DataHandler.get_list_from_str(message)

        DatabaseHandler().adding_data_based_on_condition(user_id, processed_message, query, username)

    @staticmethod
    def get_product_type_by_eng() -> set:
        required_ab = set()
        with PostgresSQLManager() as db:
            db.cursor.execute(
                """SELECT name FROM producttype;"""
            )
            required_ab = set(x[0] for x in db.cursor.fetchall())
        return required_ab

    @staticmethod
    def get_data_from_db(user_id: int) -> str:
        result = []

        with PostgresSQLManager() as db:
            db.cursor.execute(
                """SELECT quantity, ab, created_at FROM storage WHERE user_id_telegram = %s AND created_at = CURRENT_DATE;""",
                (user_id,))
            data = db.cursor.fetchall()
            logging.warning(f'Successfully retrieved data from database.\n {result}')

            db.cursor.execute(
                """SELECT name, description FROM storage JOIN producttype ON name = ab GROUP BY description, name;""")
            en_to_ru = db.cursor.fetchall()

        if not len(data):
            logging.warning('Data not exists in database.')
            return 'На сегодня данные не добавлены.'

        result = DataHandler.convert_data_in_russ(data, dict(en_to_ru))
        logging.warning(f'Successfully converted data to Russ format.\n {result}')
        return result

    def adding_data_based_on_condition(self, user_id: int, message: list, query: str, username: str) -> None:
        processed_message = message
        with PostgresSQLManager() as db:
            db.cursor.execute("""SELECT * FROM storage WHERE user_id_telegram = %s AND created_at = CURRENT_DATE;""",
                              (user_id,))
            record = db.cursor.fetchone()

            if not record:
                logging.warning('Data do not exists in database.')
                required_ab = self.get_product_type_by_eng()
                existing_keys = {key for key, _ in message}
                missing_ab = required_ab - existing_keys
                for key in missing_ab:
                    message.append((key, '0'))

                for ab, quantity in message:
                    logging.warning(f'Insert fields: {username, user_id, quantity, ab}')
                    db.cursor.execute(query, (username, user_id, quantity, ab,))

                logging.warning('Successfully added data to database.')

                return None

            logging.warning('Data exists in database.')
            query = """UPDATE storage SET quantity=%s WHERE user_id_telegram=%s AND ab=%s AND created_at = CURRENT_DATE;"""
            for ab, quantity in processed_message:
                logging.warning(f'Update fields: {quantity, user_id, ab}')
                db.cursor.execute(query, (quantity, user_id, ab,))
            return None


class PostgresSQLManager:
    def __init__(self):
        load_dotenv()
        self.db = os.getenv('DATABASE_URL')

    def __enter__(self):
        self.conn = psycopg2.connect(self.db)
        self.cursor = self.conn.cursor()
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        if exc_type is None:
            self.conn.commit()
        else:
            self.conn.rollback()
        self.cursor.close()
        self.conn.close()
