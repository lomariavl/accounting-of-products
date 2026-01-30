import os
import re
from re import findall
from typing import Dict

import psycopg2
from dotenv import load_dotenv


class DataProcessing:
    load_dotenv()
    DB = os.getenv('DATABASE_URL')
    PATTERN = r'([abpабрАБР]+)(\d+)'
    db_keys = {
        'а': 'a',
        'б': 'b',
        'р': 'p'
    }

    @staticmethod
    def user_format(username: str, first_name, last_name) -> str:
        return '@' + username if username else first_name + ' ' + last_name

    @staticmethod
    def get_current_data_from_db(user_id) -> str:
        conn = psycopg2.connect(DataProcessing.DB)
        cursor = conn.cursor()

        cursor.execute(
            """SELECT quantity, ab, created_at FROM storage WHERE user_id_telegram = %s AND created_at = CURRENT_DATE;""",
            (user_id,))
        result = cursor.fetchall()

        cursor.close()
        conn.close()

        if not len(result):
            return 'На сегодня данные не добавлены.'

        data = f'На {result[0][2].strftime("%d.%m.%y")} добавлено:\n' + '\n'.join(
            f'{ab} {q}' for q, ab, d in sorted(result, key=lambda x: (len(x[1]), x[1])))
        return data

    def fill_data_in_db(self, username: str, user_id: int, text: str) -> None:
        text = text.lower()
        conn = psycopg2.connect(DataProcessing.DB)
        cursor = conn.cursor()
        cursor.execute("""SELECT * FROM storage WHERE user_id_telegram = %s AND created_at = CURRENT_DATE;""",
                       (user_id,))
        exists = cursor.fetchone()

        if exists:
            data = self.data_conversion(text)
            query = """UPDATE storage SET quantity=%s WHERE user_id_telegram=%s AND ab=%s AND created_at = CURRENT_DATE;"""
            for ab, quantity in data.items():
                cursor.execute(query,
                               (quantity, user_id, ab,)
                               )
        else:
            data = self.adding_null_value_to_data(text)
            query = """INSERT INTO storage(username, user_id_telegram, quantity, ab) VALUES(%s, %s, %s, %s);"""
            for ab, quantity in data.items():
                cursor.execute(query,
                               (username, user_id, quantity, ab,)
                               )
        conn.commit()
        cursor.close()
        conn.close()

    @staticmethod
    def data_conversion(text: str) -> Dict:
        new_text = ''
        for k, v in DataProcessing.db_keys.items():
            new_text = text.replace(k, v)
        result = findall(DataProcessing.PATTERN, text, re.I)
        data = {(DataProcessing.db_keys[k] if k in DataProcessing.db_keys else k): v for k, v in dict(result).items()}
        return data

    @staticmethod
    def adding_null_value_to_data(text: str) -> Dict:
        conn = psycopg2.connect(DataProcessing.DB)
        cursor = conn.cursor()
        cursor.execute(
            """SELECT name FROM producttype;"""
        )
        required_ab = set(x[0] for x in cursor.fetchall())
        cursor.close()
        conn.close()

        data = DataProcessing.data_conversion(text)
        for ab in required_ab:
            data.setdefault(ab, '0')

        return data

    # @staticmethod
    # def get_key_by_value(d, value):
    #     for k, v in d.items():
    #         if v == value:
    #             return k
    #     return None

    # @staticmethod
    # def get_product_type_from_db() -> set:
    #     conn = psycopg2.connect(DataProcessing.DB)
    #     cursor = conn.cursor()
    #     cursor.execute(
    #         """SELECT name FROM producttype;"""
    #     )
    #     product_type = set(x[0] for x in cursor.fetchall())
    #     cursor.close()
    #     conn.close()
    #
    #     return product_type
    #
    # @staticmethod
    # def get_dict_product_type() -> Dict:
    #     product_type = DataProcessing.get_product_type_from_db()
    #     product_type_russian = {'а', 'б', 'бр'}
    #     data = {product_type_russian: product_type}
    #     return data
