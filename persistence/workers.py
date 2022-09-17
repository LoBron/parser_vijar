from typing import Dict

from .alchemy.postgresql import PostgresHandler, PostgresAsyncHandler
from .alchemy.sqlite import SQLiteHandler
from .interfaces import DbWorkerInterface
from .validators import *


class DbWorker(DbWorkerInterface):

    def __init__(self):
        self.__pg_handler = PostgresHandler()
        self.__pg_async_handler = PostgresAsyncHandler()
        self.__sl_handler = SQLiteHandler()

    def clear_category(self, cat_id: Category) -> Union[int, None]:
        return self.__pg_handler.clear_category(cat_id.id)

    def complate_category(self, cat_id: Category):
        pass

    def clear_all_tables(self):
        return self.__pg_handler.clear_all_tables()

    def add_category_to_db(self, category: Category):
        return self.__pg_handler.add_category_to_db(category.dict())

    def add_property_to_db(self, property_name: str):
        return self.__pg_handler.add_property_to_db(property_name)

    async def add_product_to_db(self, key: int, product: Product) -> Union[Dict[int, int], None]:
        return await self.__pg_async_handler.add_product_to_db(key, product.dict())

    async def add_value_to_db(self, property_value: PropertyValue) -> Union[int, None]:
        return await self.__pg_async_handler.add_value_to_db(property_value.dict())

    def save_category_info(self, category: Category):
        return self.__sl_handler.save_category_info(category.dict())

    def delete_category_info(self) -> None:
        return self.__sl_handler.delete_category_info()


# if __name__ == '__main__':
