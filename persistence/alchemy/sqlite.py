from typing import Optional, Tuple

from sqlalchemy import create_engine, and_
from sqlalchemy.orm import sessionmaker

from settings import SQLITE

from .models import SQLiteBase, CategoryInfoTable

folder_name = SQLITE.get('FOLDER_NAME')
db_name = SQLITE.get('DB_NAME')


class SQLiteHandler:

    def __init__(self):
        self.__url = f"sqlite:///{db_name}"
        self.__engine = create_engine(self.__url)
        SQLiteBase.metadata.create_all(self.__engine)
        self.__session = sessionmaker(bind=self.__engine)
        # self.__session_mptt = mptt_sessionmaker(self.__session)

    def clear_category_table(self):
        try:
            with self.__session() as session:
                session.query(CategoryInfoTable).delete(synchronize_session='fetch')
                session.commit()
        except Exception as ex:
            print(f'Exception in SQLiteHandler.delete_categories\n{ex}')

    def save_category_info(self, category: dict) -> Optional[int]:
        try:
            with self.__session() as session:
                cat = CategoryInfoTable()
                cat.name = category.get('name')
                cat.url = category.get('url')
                cat.cat_id = category.get('id')
                cat.level = category.get('level')
                # cat.parent_id = category.get('parent_id')
                session.add(cat)
                session.commit()
                return cat.id
        except Exception as ex:
            print(f'Exception in SQLiteHandler.save_category_info - data: {category}\n{ex}')
            return None

    def get_category(self, cat_id: int) -> Optional[CategoryInfoTable]:
        try:
            with self.__session() as session:
                category = session.query(CategoryInfoTable).filter(and_(CategoryInfoTable.cat_id == cat_id,
                                                                        CategoryInfoTable.url != None
                                                                        )).first()
        except Exception as ex:
            print(f'Exception in SQLiteHandler.get_categories - cat_id: {cat_id}\n{ex}')
            return None
        else:
            return category

    def get_all(self):
        try:
            with self.__session() as session:
                return session.query(CategoryInfoTable).all()
        except Exception as ex:
            print(f'Exception in SQLiteHandler.get_all\n{ex}')
            return None




if __name__ == '__main__':
    # cat = {'name': 'Пидорасы',
    #        'url': 'https://proglib.io/p/upravlenie-dannymi-s-pomoshchyu-python-sqlite-i-sqlalchemy-2020-10-216',
    #        'cat_id': 1006,
    #        'parent_id': 1}
    handler = SQLiteHandler()
    print(handler.get_category(2793).url)

    # print(handler.create_category(cat))
