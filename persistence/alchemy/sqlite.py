from typing import Optional, Tuple

from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from mptt import mptt_sessionmaker
from settings import SQLITE
from models import SQLiteBase, CategoryInfoTable

folder_name = SQLITE.get('FOLDER_NAME')
db_name = SQLITE.get('DB_NAME')


class SQLiteHandler:

    def __init__(self):
        self.__url = f"sqlite:///{db_name}"
        self.__engine = create_engine(self.__url)
        SQLiteBase.metadata.create_all(self.__engine)
        self.__session = sessionmaker(bind=self.__engine)
        self.__session_mptt = mptt_sessionmaker(self.__session)

    def delete_all(self):
        pass

    def save_category_info(self, category: dict) -> Optional[tuple]:
        try:
            with self.__session_mptt() as session:
                cat = CategoryInfoTable()
                cat.name = category.get('name')
                cat.url = category.get('url')
                cat.cat_id = category.get('id')
                cat.parent_id = category.get('parent_id')
                session.add(cat)
                session.commit()
                return cat.id
        except Exception as ex:
            print(f'Exception in SQLiteHandler.create_category - data: {category}\n{ex}')
            return None

    def get_categories(self, cat_id: int) -> Tuple[int, str, str]:
        try:
            with self.__session_mptt() as session:
               category = session.query(CategoryInfoTable).get(cat_id)

        except Exception as ex:
            print(f'Exception in SQLiteHandler.get_categories - cat_id: {cat_id}\n{ex}')
            return ()

    def get_all(self):
        try:
            with self.__session() as session:
                return session.query(CategoryInfoTable).all()
        except Exception as ex:
            print(f'Exception in SQLiteHandler.get_all\n{ex}')
            return None


if __name__ == '__main__':
    cat = {'name': 'Пидорасы',
           'url': 'https://proglib.io/p/upravlenie-dannymi-s-pomoshchyu-python-sqlite-i-sqlalchemy-2020-10-216',
           'cat_id': 1006,
           'parent_id': 1}
    handler = SQLiteHandler()
    print(handler.get_all())

    # print(handler.create_category(cat))
