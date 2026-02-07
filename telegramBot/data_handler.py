import re
from typing import List, Dict


class DataHandler:
    PRODUCT_TYPE_KEYS = {
        'а': 'a',
        'б': 'b',
        'р': 'p'
    }
    PATTERN = r'\b([abpабрАБР]+)(\d+)\b'

    @staticmethod
    def username_format(username: str, first_name, last_name, without_at: bool = False) -> str:
        if without_at:
            return username if username else first_name + ' ' + last_name
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
        for q, ab, date, comment in data:
            ru_key = en_to_ru.get(ab, ab)
            result.append((q, ru_key, date, comment))
        return f'На {result[0][2].strftime("%d.%m.%y")} добавлено:\n' + '\n'.join(
            f'{ab} {q}' for q, ab, d, c in
            sorted(result, key=lambda x: (len(x[1]), x[
                1]))) + f'\n\nВаш комментарий:\n{result[0][3] if result[0][3] else ""}'
