import os
from datetime import datetime
from typing import Annotated

from dotenv import load_dotenv
from fastapi import Depends
from sqlalchemy import Date
from sqlalchemy.dialects.postgresql import JSONB
from sqlmodel import SQLModel, Field, create_engine, Session, Relationship, Column, func


class ProductType(SQLModel, table=True):
    name: str = Field(default=None, primary_key=True)
    description: str = Field(default=None)
    storages: list['Storage'] = Relationship(back_populates="producttype")


class Storage(SQLModel, table=True):
    id: int | None = Field(default=None, primary_key=True)
    username: str
    user_id_telegram: int
    created_at: datetime = Field(
        sa_column=Column(Date, server_default=func.current_date())
    )
    quantity: int
    comment: str | None = Field(default=None)
    photo_path: list[str] | None = Field(
        default=None,
        sa_column=Column(JSONB, nullable=True)
    )

    ab: str = Field(foreign_key='producttype.name')
    producttype: ProductType = Relationship(back_populates='storages')


load_dotenv()
sqlite_url = os.getenv('DATABASE_URL')
engine = create_engine(sqlite_url)


def create_db_and_tables():
    SQLModel.metadata.create_all(engine)


def get_session():
    with Session(engine) as session:
        yield session


# def flip_table(session: Session):
#     session = get_session()
#     result = session.execute(
#     """
#    SELECT
#         created_at,
#         username,
#         SUM(CASE WHEN ab = 'A' THEN quantity END) AS A,
#         SUM(CASE WHEN ab = 'B' THEN quantity END) AS B,
#         SUM(CASE WHEN ab = 'A1' THEN quantity END) AS A1,
#         SUM(CASE WHEN ab = 'B1' THEN quantity END) AS B1
#     FROM storage
#     GROUP BY created_at, username
#     ORDER BY created_at, username;""").all()
#     return result

SessionDep = Annotated[Session, Depends(get_session)]
