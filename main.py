from fastapi import FastAPI

from persistence.servises import clear_all_tables
from busines.parser import Parser

app = FastAPI(title='parser_api')


# @app.on_event("startup")
# async def startup():
#     await engine.connect()
#
#
# @app.on_event('shutdown')
# async def shutdown():
#     await engine.dispose()

#
# @app.get("/category/{cat_id}", response_model=Category)
# async def get_cat(cat_id: int):
#     query = cat.select().where(cat.с.id == cat_id)
#     rs = await engine.execute(query)
#     return {'id': rs.id,
#             'name': rs.name,
#             'slug': rs.slug,
#             'lft': rs.lft,
#             'rght': rs.rght,
#             'tree_id': rs.tree_id,
#             'level': rs.level,
#             'parent_id': rs.parent_id}


#
# 
@app.get('/complete_all_tables')
async def complete_all_tables():
    clear_all_tables()
    parser = Parser().complete_all_tables()
    return {'response': 'all complete'}
# if __name__ == '__main__':
#     s = time()
#     main_url = 'https://viyar.ua/catalog'

#
#     data = get_categories_info(main_url)
#     add_products_data(data, main_url, path)
#     print(f'затраченное время {time() - s}')
