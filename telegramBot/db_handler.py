import logging

from data_handler import DataHandler
from postgresql_manager import PostgresSQLManager


class DatabaseHandler:
    @staticmethod
    def add_comment_in_storage_table(comment: str, user_id: int) -> None:
        try:
            query = """UPDATE storage SET comment=%s WHERE user_id_telegram=%s and created_at=CURRENT_DATE;"""
            with PostgresSQLManager() as db:
                db.cursor.execute(query, (comment, user_id,))
        except Exception as e:
            logging.error(e)

    @staticmethod
    def add_basic_data_in_db(username: str, user_id: int, message: str = ''):
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
                """SELECT quantity, ab, created_at, comment FROM storage WHERE user_id_telegram = %s AND created_at = CURRENT_DATE;""",
                (user_id,))
            data = db.cursor.fetchall()
            logging.warning(f'Successfully retrieved data from database.\n {result}')

            db.cursor.execute(
                """SELECT name, description FROM storage JOIN producttype ON name = ab GROUP BY description, name;""")
            en_to_ru = db.cursor.fetchall()

            db.cursor.execute(
                """SELECT jsonb_array_length(s.photo_path) FROM "storage" s WHERE s.user_id_telegram = 465686959 AND s.created_at = CURRENT_DATE AND s.ab = 'a'""")
            photos_numbers = db.cursor.fetchone()

        if not len(data):
            logging.warning('Data not exists in database.')
            return 'На сегодня данные не добавлены.'

        result = f'{(DataHandler.convert_data_in_russ(data, dict(en_to_ru)))}\n\nКоличество загруженных фото: {0 if not photos_numbers[0] else photos_numbers[0]}'
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
