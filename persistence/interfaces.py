from abc import ABC, abstractmethod
from typing import Optional, List, Tuple, Dict

from .alchemy.models import CategoryInfoTable
from .validators import Category, Product, PropertyValue


class DbWorkerInterface(ABC):

    @abstractmethod
    def clear_category(self, cat_id: Category) -> Optional[int]:
        pass

    @abstractmethod
    def complate_category(self, cat_id: Category):
        pass

    @abstractmethod
    def clear_all_tables(self):
        pass

    @abstractmethod
    def add_category_to_db(self, category: Category):
        pass

    @abstractmethod
    def add_property_to_db(self, property_name: str):
        pass

    @abstractmethod
    def add_products_to_db(self, products: List[Tuple[int, Product]]):
        pass

    @abstractmethod
    def add_values_to_db(self, property_values: List[PropertyValue]):
        pass

    @abstractmethod
    def save_category_info(self, category: Category):
        pass

    @abstractmethod
    def clear_category_table(self):
        pass

    @abstractmethod
    def get_category(self, cat_id: int) -> Optional[CategoryInfoTable]:
        pass

    @abstractmethod
    def delete_cat_data(self, cat_id) -> Dict[int, Tuple[str]]:
        pass

    @abstractmethod
    def get_properties(self) -> Dict[str, int]:
        pass
