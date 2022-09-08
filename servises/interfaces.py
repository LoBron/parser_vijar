from typing import List, Dict, Optional
from abc import ABC, abstractmethod

from .models import *


class IoLoaderInterface(ABC):

    @abstractmethod
    def get_html_responses(self, urls: Dict[int, str]) -> Dict[int, list]:
        pass

    @abstractmethod
    def get_bytes_responses(self, urls: Dict[int, str]) -> Dict[int, list]:
        pass

    @abstractmethod
    def get_item_response(self, item_url: str):
        pass


class GoogleWorkerInterface(ABC):
    @abstractmethod
    def search_files(self, category_id: CatId) -> List[str]:
        pass

    @abstractmethod
    def delete_file(self, file_id: FileId) -> Optional[str]:
        pass

    @abstractmethod
    def upload_file(self, id_: int, image: File) -> Dict[int, Optional[str]]:
        pass
