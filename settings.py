from datetime import datetime

MAIN_URL = 'https://viyar.ua/catalog'

# GOOGLE_FOLDER_NAME = f'shop.catalog.images {datetime.now()}'
GOOGLE_FOLDER_NAME = f'my_new_folder_bitch'
GOOGLE_CREDENTIALS_NAME = 'credentials.json'
GOOGLE_SCOPES = ['https://www.googleapis.com/auth/drive']

POSTGRES = {
    'DATABASE_NAME': 'catalog',
    'USERNAME': 'postgres',
    'PASSWORD': '1',
    'DRIVER': 'psycopg2',
    'ASYNC_DRIVER': 'asyncpg',
    'HOST': 'localhost',
    'PORT': '5432',
}

SQLITE = {
    'FOLDER_NAME': 'project_data',
    'DB_NAME': 'categories_data.db',
}
