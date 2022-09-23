from typing import List, Dict, Optional, Tuple
from asyncio import run

from requests import Response

from .interfaces import IoLoaderInterface, GoogleWorkerInterface
from .models import *
from .google.drive_api import DriveAPI
from .io_loading.loaders import AsyncLoader, SyncLoader


class IoLoader(IoLoaderInterface):
    def __init__(self):
        self.__async_loader = AsyncLoader
        self.__sync_loader = SyncLoader

    def get_html_responses(self, urls: Dict[int, str]) -> Dict[int, Tuple[str, str]]:
        return run(self.__async_loader.get_responses(urls, format_='text'))

    def get_bytes_responses(self, urls: Dict[int, str]) -> Dict[int, Tuple[str, bytes]]:
        return run(self.__async_loader.get_responses(urls, format_='bytes'))

    def get_item_response(self, item_url: str) -> Tuple[str, Optional[Response]]:
        return self.__sync_loader.get_item_response(item_url)


class GoogleWorker(GoogleWorkerInterface):
    def __init__(self):
        self.__drive = DriveAPI()

    def search_files(self, category_id: CatId) -> List[str]:
        return self.__drive.search_files(category_id.id)

    def delete_file(self, file_id: str) -> Optional[str]:
        return self.__drive.delete_file(file_id)

    def upload_file(self, id_: int, image: File) -> Dict[int, Optional[str]]:
        return self.__drive.upload_file(id_, image.data, image.name, image.mimetype)
