from decimal import Decimal
from random import choice, randint
from typing import Union

from sqlalchemy import create_engine
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession
from sqlalchemy.orm import sessionmaker

from database.my_sqlalchemy_mptt import mptt_sessionmaker
from .models import Cat, Prod, Prop, PropValue

DATABASE_URL = 'postgresql+psycopg2://postgres:1@localhost:5432/test'
engine = create_engine(DATABASE_URL, echo=False)
Session = sessionmaker(bind=engine)

Session_mptt = mptt_sessionmaker(sessionmaker(bind=engine))

ASYNC_DATABASE_URL = 'postgresql+asyncpg://postgres:1@localhost:5432/test'
async_engine = create_async_engine(ASYNC_DATABASE_URL, echo=False)
async_session = sessionmaker(async_engine, expire_on_commit=False, class_=AsyncSession)


def add_category_to_db(cat_data: dict, parent_id: Union[int, None] = None):
    with Session_mptt() as session:
        cat = Cat()
        cat.name = cat_data.get('name')
        cat.slug = cat_data.get('slug')
        cat.parent_id = parent_id
        session.add(cat)
        session.commit()
        return cat.id


async def add_product_to_db(product_data: dict, cat_id: int) -> dict:
    async with async_session() as session:
        async with session.begin():
            prod = Prod()
            prod.category_id = cat_id
            prod.name = product_data['name']
            prod.slug = product_data['slug']
            prod.description = product_data['description']
            prod.price = Decimal(product_data['price'])
            prod.availability = choice([True, False, True, True, True])
            if prod.availability:
                prod.amount = randint(1, 100)
            else:
                prod.amount = 0
            prod.photo1 = product_data['photos'].get('photo1')
            prod.photo2 = product_data['photos'].get('photo2')
            prod.photo3 = product_data['photos'].get('photo3')
            prod.photo4 = product_data['photos'].get('photo4')
            session.add(prod)
        await session.commit()
        return {'prod_id': prod.id, 'properties': product_data['properties']}


def add_property_to_db(name: str) -> int:
    with Session() as session:
        prop = Prop()
        prop.name = name
        session.add(prop)
        session.commit()
        return prop.id


async def add_value_to_db(product_id: int, property_id: int, value: str) -> None:
    async with async_session() as session:
        async with session.begin():
            prop_value = PropValue()
            prop_value.product_id = product_id
            prop_value.property_id = property_id
            prop_value.value = value
            session.add(prop_value)
        await session.commit()
