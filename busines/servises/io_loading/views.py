from asyncio import gather, create_task
from typing import Dict

from aiohttp import ClientSession


class AsyncLoader:

    async def get_responses(self, urls: Dict[int, str], format_: str = 'bytes'
                            ) -> Dict[int, list]:
        """Возвращает словарь response обьектов"""
        responses = {}
        if urls:
            try:
                async with ClientSession() as session:
                    task_list = [create_task(self.get_item_response(url, session,  key, format_))
                                 for key, url in urls.items()]
                    result_list = list(await gather(*task_list))
            except Exception as ex:
                print(f'Exception in get_responses - Error: {ex}')
            else:
                for result in result_list:
                    responses.update(result)
        return responses

    async def get_item_response(self,
                                item_url: str,
                                session: ClientSession,
                                key: int,
                                format_: str = 'bytes') -> Dict[int, list]:
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
                    print(f'Exception in get_item_response - item_url: {item_url}\nError: {ex}')
                    result = None
                    break
            else:
                break
        return {key: [item_url, result]}
