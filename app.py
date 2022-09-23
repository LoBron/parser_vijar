from flask import Flask

from busines import Controller

app = Flask(__name__)


@app.get('/complete_all_tables')
def complete_all_tables():
    Controller.create_all_data()
    return {'response': 'all complete'}


@app.get('/replace_category/<int:cat_id>')
def replace_category_data(cat_id: int):
    Controller.update_data_in_category(cat_id)
    return {"cat_id": cat_id}


if __name__ == '__main__':
    app.run('localhost', 5555, debug=True)
    # Controller.create_all_data()
    # Controller.update_data_in_category(2784)
