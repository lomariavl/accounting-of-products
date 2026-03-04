import datetime
import logging
from pathlib import Path

from sqlalchemy import cast
from sqlalchemy import update, and_, case
from sqlalchemy.dialects.postgresql import JSONB
from sqlmodel import Session

from db import Storage
from db import engine


class FileManager:
    DIRECTORY_IMGS = Path('imgs')

    @staticmethod
    def save_file(username, photo_bytes, user_id):
        counter = 1

        try:
            path = FileManager.DIRECTORY_IMGS.joinpath(str(datetime.date.today()))
            path.mkdir(parents=True, exist_ok=True)
            logging.warning(path)

            while True:
                file_path = path.joinpath(f'{username}_{counter:03}.jpg')
                logging.warning(file_path)

                if not file_path.exists():
                    break

                counter += 1

            logging.warning(file_path.as_posix())
            with open(file_path, 'wb') as new_file:
                new_file.write(photo_bytes)

            stmt = (
                update(Storage)
                .where(
                    and_(
                        Storage.user_id_telegram == user_id,
                        Storage.created_at == str(datetime.date.today())
                    )
                )
                .values(
                    photo_path=case(
                        (Storage.photo_path.is_(None),
                         cast([file_path.as_posix()], JSONB)),
                        (Storage.photo_path.op("@>")(cast([file_path.as_posix()], JSONB)),
                         Storage.photo_path),
                        else_=Storage.photo_path.op("||")(
                            cast([file_path.as_posix()], JSONB)
                        )
                    )
                )
            )
            with Session(engine) as session:
                session.exec(stmt)
                session.commit()

        except Exception as e:
            logging.error(e)
            raise
