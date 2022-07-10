from decimal import Decimal
from typing import Union
from pydantic import BaseModel
from sqlalchemy import MetaData, Table, Column, Integer, String, Text, Boolean, ForeignKey, DECIMAL

metadata = MetaData()

cat = Table('catalog_category', metadata,
            Column('id', Integer(), primary_key=True, autoincrement=True),
            Column('name', String(50)),
            Column('slug', String(50), unique=True),
            Column('lft', Integer()),
            Column('rght', Integer()),
            Column('rght', Integer()),
            Column('tree_id', Integer()),
            Column('level', Integer()),
            Column('parent_id', Integer(), nullable=True),
            )

prod = Table('catalog_product', metadata,
             Column('id', Integer(), primary_key=True, autoincrement=True),
             Column('category_id', ForeignKey("catalog_category.id")),
             Column('name', String(100)),
             Column('description', Text(), nullable=True),
             Column('price', DECIMAL(7, 2), default=0),
             Column('availability', Boolean(), default=True),
             Column('amount', Integer(), default=1),
             Column('tree_id', Integer()),
             Column('main_photo', String()),
             Column('additional_photo_01', String(), nullable=True),
             Column('additional_photo_02', String(), nullable=True),
             Column('additional_photo_03', String(), nullable=True),
             )


class Category(BaseModel):
    id: int
    name: str
    slug: str
    lft: int
    rght: int
    tree_id: int
    level: int
    parent_id: Union[int, None] = None


class Prod(BaseModel):
    id: int
    category_id: int
    name: str
    slug: str
    description: Union[str, None] = None
    price: Decimal = 0
    availability: bool = True
    amount: int = 1
    main_photo: str
    additional_photo_01: Union[str, None] = None
    additional_photo_02: Union[str, None] = None
    additional_photo_03: Union[str, None] = None
