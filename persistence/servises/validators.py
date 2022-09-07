from decimal import Decimal
from random import choice, randint
from typing import Union, List

from pydantic import BaseModel, HttpUrl


class Category(BaseModel):
    id: Union[int, None] = None
    parent_id: Union[int, None] = None
    have_childrens: bool = False
    name: str
    slug: str
    url: Union[HttpUrl, None] = None


class Product(BaseModel):
    id: Union[int, None] = None
    category_id: int
    name: str
    slug: str
    description: Union[str, None] = None
    price: Decimal = 0
    availability: bool = choice([True] * 9 + [False])
    amount: int = randint(1, 100) if availability else 0
    photo1: str
    photo2: Union[str, None] = None
    photo3: Union[str, None] = None
    photo4: Union[str, None] = None

    class Config:
        arbitrary_types_allowed = True


class Data(BaseModel):
    categories: Union[List[Union[Category, None]]]
    products: Union[List[Product], None] = None

    class Config:
        arbitrary_types_allowed = True


class Property(BaseModel):
    name: str


class PropertyValue(BaseModel):
    product_id: int
    property_id: int
    value: str


if __name__ == '__main__':
    data = Data(
        categories=[Category(name='lox', slug='pidr', url='https://pydantic-docs.helpmanual.io/usage/dataclasses/'),
                    23], products=None)
    print(data.categories)
    data.categories = 'sdcsddc'  # Category(name='lox', slug='pidr', url='chmo')
    print(data.categories)
    # cat = Category(name='lox', slug='pidr', url='https://pydantic-docs.helpmanual.io/usage/dataclasses/')
    # print(cat)
