from flask import Flask

from database.views import clear_all_tables, clear_category
from utils import Parser

app = Flask(__name__)


@app.route("/")
def hello_world():
    return "<p>Hello, World!</p>"


@app.get('/complete_all_tables')
def complete_all_tables():
    clear_all_tables()
    parser = Parser().complete_all_tables()
    return {'response': 'all complete'}


@app.get('/replace_category/<int:cat_id>')
def replace_category_data(cat_id: int):
    clear_category(cat_id)
    parser = Parser().replace_category_data(cat_id)
    return {"cat_id": cat_id}


if __name__ == '__main__':
    app.run('localhost', 5555, debug=True)
