from abc import ABC, abstractmethod
from typing import Optional, Dict, Any, List, Union


class CreatorInterface(ABC):

    @abstractmethod
    def create_all_data(self) -> Dict[int, List[int]]:
        pass


class UpdaterInterface(ABC):

    @abstractmethod
    def update_data_in_category(self, cat_id: int):
        pass


class ParserInterface(ABC):

    @classmethod
    @abstractmethod
    def get_item_data(cls, item_url: str, item_response: str) -> Optional[Dict[str, Any]]:
        pass

    @staticmethod
    @abstractmethod
    def get_categories_data(response: bytes, main_url: str) -> List[Dict[str, Union[str, list]]]:
        pass

    @staticmethod
    @abstractmethod
    def get_items_urls(response_page: str) -> Optional[List[str]]:
        pass

    @staticmethod
    @abstractmethod
    def get_amount_pages(response_page: str) -> int:
        pass
