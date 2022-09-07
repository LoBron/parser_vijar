from typing import Dict

from .servises.alchemy.views import SyncHandler, AsyncHandler
from .servises.validators import *


class DbWorker:

    def __init__(self):
        self.__sync_handler = SyncHandler()
        self.__async_handler = AsyncHandler()

    def clear_category(self, cat_id: Category) -> Union[int, None]:
        return self.__sync_handler.clear_category(cat_id.id)

    def clear_all_tables(self):
        return self.__sync_handler.clear_all_tables()

    def add_category_to_db(self, category: Category):
        return self.__sync_handler.add_category_to_db(category.dict())

    def add_property_to_db(self, property_name: str):
        return self.__sync_handler.add_property_to_db(property_name)

    async def add_product_to_db(self, key: int, product: Product) -> Union[Dict[int, int], None]:
        return await self.__async_handler.add_product_to_db(key, product.dict())

    async def add_value_to_db(self, property_value: PropertyValue) -> Union[int, None]:
        return await self.__async_handler.add_value_to_db(property_value.dict())


# if __name__ == '__main__':