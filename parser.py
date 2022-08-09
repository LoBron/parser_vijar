from fastapi import FastAPI
from sqlalchemy.ext.asyncio import create_async_engine
from database.models import *
from sqlalchemy import *


DATABASE_URL = 'postgresql+asyncpg://postgres:1@localhost:5432/test'
engine = create_async_engine(DATABASE_URL, echo=True)

app = FastAPI(title='parser_api')


@app.on_event("startup")
async def startup():
    await engine.connect()


@app.on_event('shutdown')
async def shutdown():
    await engine.dispose()


@app.get("/category/{cat_id}", response_model=Category)
async def get_cat(cat_id: int):
    query = cat.select().where(cat.с.id == cat_id)
    rs = await engine.execute(query)
    return {'id': rs.id,
            'name': rs.name,
            'slug': rs.slug,
            'lft': rs.lft,
            'rght': rs.rght,
            'tree_id': rs.tree_id,
            'level': rs.level,
            'parent_id': rs.parent_id}
# 
# 
@app.get('/start')
async def start():
    pass

# if __name__ == '__main__':
#     s = time()
#     main_url = 'https://viyar.ua/catalog'

#
#     data = get_categories_info(main_url)
#     add_products_data(data, main_url, path)
#     print(f'затраченное время {time() - s}')
