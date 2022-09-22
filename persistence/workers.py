from typing import Tuple

from .alchemy.postgresql import PostgresHandler, PostgresAsyncHandler
from .alchemy.sqlite import SQLiteHandler
from .interfaces import DbWorkerInterface
from .validators import *


class DbWorker(DbWorkerInterface):

    def __init__(self):
        self.__pg_handler = PostgresHandler()
        # self.__pg_async_handler = PostgresAsyncHandler()
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

    def add_products_to_db(self, products: List[Tuple[int, Product]]):
        return self.__pg_handler.add_products_to_db([(product[0], product[1].dict()) for product in products])

    def add_values_to_db(self, property_values: List[PropertyValue]):
        return self.__pg_handler.add_values_to_db([value.dict() for value in property_values])

    def save_category_info(self, category: Category):
        return self.__sl_handler.save_category_info(category.dict())

    def delete_category_info(self) -> None:
        return self.__sl_handler.delete_category_info()


# if __name__ == '__main__':
