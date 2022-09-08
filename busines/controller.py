from typing import Optional

from .utils import Updater, Creator
from .interfaces import CreatorInterface, UpdaterInterface


class Controller:
    def __init__(self,
                 creator: Optional[CreatorInterface] = None,
                 updater: Optional[UpdaterInterface] = None):
        self.__creator = creator
        self.__updater = updater

    @classmethod
    def create_all_data(cls):
        creator = Creator()
        return cls(creator=creator).__creator.create_all_data()

    @classmethod
    def update_data_in_category(cls, cat_id: int):
        updater = Updater()
        return cls(updater=updater).__updater.update_data_in_category(cat_id)
