from datetime import datetime

MAIN_URL = 'https://viyar.ua/catalog'

GOOGLE_FOLDER_NAME = f'shop.catalog.images {datetime.now()}'
GOOGLE_CREDENTIALS_NAME = 'credentials.json'

POSTGRES = {
    'DATABASE_NAME': 'test',
    'USERNAME': 'postgres',
    'PASSWORD': '1',
    'DRIVER': 'psycopg2',
    'ASYNC_DRIVER': 'asyncpg',
    'HOST': 'localhost',
    'PORT': '5432',
}
