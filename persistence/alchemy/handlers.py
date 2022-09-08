from asyncio import create_task, gather, run, set_event_loop_policy, WindowsSelectorEventLoopPolicy
from decimal import Decimal, ROUND_UP
from typing import Union, Dict

from sqlalchemy import create_engine
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import NullPool

from .mptt import mptt_sessionmaker
from persistence.validators import Product

from settings import POSTGRES
from .models import CategoryTable, ProductTable, PropertyTable, PropertyValueTable

DATABASE = POSTGRES
database_name = DATABASE.get('DATABASE_NAME')
user = DATABASE.get('USERNAME')
password = DATABASE.get('PASSWORD')
driver = DATABASE.get('DRIVER')
async_driver = DATABASE.get('ASYNC_DRIVER')
host = DATABASE.get('HOST')
port = DATABASE.get('PORT')


class AsyncHandler:

    def __init__(self):
        self.__url = f'postgresql+{async_driver}://{user}:{password}@{host}:{port}/{database_name}'
        self.__engine = create_async_engine(self.__url, poolclass=NullPool, echo=False)
        self.__session = sessionmaker(self.__engine, expire_on_commit=False, class_=AsyncSession)

    async def add_product_to_db(self, key: int, product: dict) -> Union[Dict[int, int], None]:
        try:
            async with self.__session() as session:
                prod = ProductTable(**product)
                session.add(prod)
                await session.commit()
        except Exception as ex:
            data = {key: None}
            print(f'Exception in add_product_to_db - cat_id: {product["cat_id"]}, prod_name: {product["name"]}\n{ex}')
        else:
            data = {key: prod.id}
        return data

    async def add_value_to_db(self, property_value: dict) -> Union[int, None]:
        try:
            async with self.__session() as session:
                value = PropertyValueTable(**property_value)
                session.add(value)
                await session.commit()
        except Exception as ex:
            print(f'Exception in add_value_to_db - data: {property_value}\n{ex}')
            return None
        else:
            return value.id


class SyncHandler:

    def __init__(self):
        self.__url = f'postgresql+{driver}://{user}:{password}@{host}:{port}/{database_name}'
        self.__engine = create_engine(self.__url, echo=False)
        self.__session = sessionmaker(bind=self.__engine)
        self.__session_mptt = mptt_sessionmaker(self.__session)

    def clear_all_tables(self):
        with self.__session() as session:
            session.query(PropertyValueTable).delete(synchronize_session='fetch')
            session.commit()
            session.query(ProductTable).delete(synchronize_session='fetch')
            session.commit()
            session.query(PropertyTable).delete(synchronize_session='fetch')
            session.commit()
            session.query(CategoryTable).delete(synchronize_session='fetch')
            session.commit()

    def add_category_to_db(self, category: dict) -> int:
        with self.__session_mptt() as session:
            cat = CategoryTable()
            cat.name = category.get('name')
            cat.slug = category.get('slug')
            cat.parent_id = category.get('parent_id')
            session.add(cat)
            session.commit()
            return cat.id

    def add_property_to_db(self, name: str) -> int:
        with self.__session() as session:
            prop = PropertyTable()
            prop.name = name
            session.add(prop)
            session.commit()
            return prop.id

    def clear_category(self, cat_id: int):
        pass


if __name__ == '__main__':
    value_list = ['лох', 'пидр', 'хуй', 'чмо']

    property_id = 1177
    set_event_loop_policy(WindowsSelectorEventLoopPolicy())
    handler = AsyncHandler()


    async def main_1():
        task_list = []
        key = 1
        product = Product(category_id=33184,
                          name='rewgrewgrew312gr1egewr',
                          slug='wg1fgghg213gwdfb',
                          description='Создайте свои очереди в своей сопрограмме верхнего уровня run()и либо передайте их сопрограммам, которым они нужны, либо используйте contextvars.ContextVarобъекты , если вы должны использовать глобальные переменные.',
                          price=Decimal(13234.53).quantize(Decimal('.01'), rounding=ROUND_UP),
                          photo1='wdqwdasdasdasda2sdasd',
                          photo2=None,
                          photo3=None,
                          photo4=None)
        task_list.append(create_task(handler.add_product_to_db(key, product.dict())))
        id_list = list(await gather(*task_list))
        return id_list


    async def main(id_list: list, value_list):
        task_list = [create_task(handler.add_value_to_db({'product_id': id_list[0],
                                                          'property_id': property_id,
                                                          'value': value})) for value in value_list]
        id_list = list(await gather(*task_list))
        return id_list


    #
    #
    items_id_list = run(main_1())
    print(items_id_list)
    id_list = run(main(items_id_list, value_list))
    print(id_list)
