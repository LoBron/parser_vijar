from asyncio import gather, create_task
from typing import Dict, Optional, Tuple, Union

from aiohttp import ClientSession
from requests import get, Response


class AsyncLoader:

    @classmethod
    async def get_responses(cls,
                            urls: Dict[int, str],
                            format_: str = 'bytes'
                            ) -> Dict[int, Tuple[str, Union[str, bytes]]]:
        """Возвращает словарь response обьектов"""
        responses = {}
        if urls:
            try:
                async with ClientSession() as session:
                    task_list = [create_task(cls._get_item_response(url, session, key, format_))
                                 for key, url in urls.items()]
                    result_list = list(await gather(*task_list))
            except Exception as ex:
                print(f'Exception in AsyncLoader.get_responses - Error: {ex}')
            else:
                for result in result_list:
                    responses.update(result)
        return responses

    @staticmethod
    async def _get_item_response(item_url: str,
                                 session: ClientSession,
                                 key: int,
                                 format_: str = 'bytes') -> Dict[int, Tuple[str, Union[str, bytes]]]:
        """Возвращает response обьект"""
        n = 1
        while True:
            try:
                async with session.get(item_url) as response:
                    if format_ == 'text':
                        result = await response.text()
                    elif format_ == 'bytes':
                        result = await response.read()
            except Exception as ex:
                n += 1
                if n > 5:
                    print(f'Exception in AsyncLoader._get_item_response - item_url: {item_url}\nError: {ex}')
                    result = None
                    break
            else:
                break
        return {key: (item_url, result)}


class SyncLoader:

    @staticmethod
    def get_item_response(item_url: str) -> Tuple[str, Optional[Response]]:
        n = 1
        while True:
            try:
                data = get(item_url)
            except Exception as ex:
                n += 1
                if n > 5:
                    print(f'Exception in SyncLoader.get_item_response - item_url: {item_url}\nError: {ex}')
                    data = None
                    break
            else:
                break
        return item_url, data
