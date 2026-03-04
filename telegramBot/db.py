import json
import os
from datetime import datetime
from typing import Annotated

from dotenv import load_dotenv
from fastapi import Depends
from sqlalchemy import Date
from sqlalchemy.dialects.postgresql import JSONB
from sqlmodel import SQLModel, Field, create_engine, Session, Relationship, Column, func, select


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


def seed_product_types_from_json(json_path: str):
    statement = select(ProductType)

    with Session(engine) as session:
        if session.exec(statement).first():
            return

        with open(json_path, 'r', encoding='utf-8') as f:
            data = json.load(f)

        default_types = data.get('default_types', {})
        for name, description in default_types.items():
            product_type = ProductType(
                name=name,
                description=description
            )
            session.add(product_type)

        session.commit()


def create_db_and_tables():
    SQLModel.metadata.create_all(engine)
    seed_product_types_from_json('test_data.json')


def get_session():
    with Session(engine) as session:
        yield session


SessionDep = Annotated[Session, Depends(get_session)]
