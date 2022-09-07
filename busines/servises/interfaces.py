from typing import List, Dict
from asyncio import run
from abc import ABC, abstractmethod

from .models import *
from .google.views import GoogleAPI
from .io_loading.views import AsyncLoader


class IoLoader:
    def __init__(self):
        self.__loader = AsyncLoader()

    def get_html_responses(self, urls: Dict[int, str]) -> Dict[int, list]:
        return run(self.__loader.get_responses(urls, format_='text'))

    def get_bytes_responses(self, urls: Dict[int, str]) -> Dict[int, list]:
        return run(self.__loader.get_responses(urls, format_='bytes'))


class GoogleWorkerInterface(ABC):
    @abstractmethod
    def search_files(self, category_id: CatId) -> List[str]:
        pass

    @abstractmethod
    def delete_file(self, file_id: FileId) -> Union[str, None]:
        pass

    @abstractmethod
    def upload_file(self, id_: int, image: File) -> Dict[int, Union[str, None]]:
        pass


class GoogleWorker(GoogleWorkerInterface):
    def __init__(self):
        self.__api = GoogleAPI()

    def search_files(self, category_id: CatId) -> List[str]:
        return self.__api.search_files(category_id.id)

    def delete_file(self, file_id: FileId) -> Union[str, None]:
        return self.__api.delete_file(file_id.id)

    def upload_file(self, id_: int, image: File) -> Dict[int, Union[str, None]]:
        return self.__api.upload_file(id_, image.data, image.name, image.mimetype)
