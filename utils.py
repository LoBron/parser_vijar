import requests
import time
from threading import *


def download_img(url, root):
    p = requests.get(url)
    img = open(root, "wb")
    img.write(p.content)
    img.close()

class DataProducts:
    def __init__(self, name):
        self.name = name
        self.data = {}

    def add_data(self, name_category, data):
        self.data[name_category] = data

    def get_data(self, name_category=None):
        if name_category:
            return self.data.get(name_category)
        else:
            return self.data

def get_data(name, data):
    print(f"{name} - {data}")
    time.sleep(5)