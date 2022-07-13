from decimal import Decimal
from typing import Union
from pydantic import BaseModel
from sqlalchemy import MetaData, Table, Column, Integer, String, Text, Boolean, ForeignKey, DECIMAL
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import relationship, declared_attr
from sqlalchemy_mptt.mixins import BaseNestedSets

# metadata = MetaData()
#
# cat = Table('catalog_category', metadata,
#             Column('id', Integer(), primary_key=True, autoincrement=True),
#             Column('name', String(50)),
#             Column('slug', String(50), unique=True),
#             Column('lft', Integer()),
#             Column('rght', Integer()),
#             Column('tree_id', Integer()),
#             Column('level', Integer()),
#             Column('parent_id', Integer(), nullable=True),
#             )
#
# prod = Table('catalog_product', metadata,
#              Column('id', Integer(), primary_key=True, autoincrement=True),
#              Column('category_id', ForeignKey("catalog_category.id")),
#              Column('name', String(100)),
#              Column('description', Text(), nullable=True),
#              Column('price', DECIMAL(7, 2), default=0),
#              Column('availability', Boolean(), default=True),
#              Column('amount', Integer(), default=1),
#              Column('photo1', String()),
#              Column('photo2', String(), nullable=True),
#              Column('photo3', String(), nullable=True),
#              Column('photo4', String(), nullable=True),
#              )


Base = declarative_base()


class Cat(Base, BaseNestedSets):
    __tablename__ = 'catalog_category'
    id = Column(Integer(), primary_key=True, autoincrement=True)
    name = Column(String(50))
    slug = Column(String(50), unique=True)
    sqlalchemy_mptt_default_level = 0
    products = relationship("Prod")

    @declared_attr
    def right(self):
        return Column("rght", Integer, nullable=False)


class Prod(Base):
    __tablename__ = 'catalog_product'
    id = Column(Integer, primary_key=True, autoincrement=True)
    category_id = Column(Integer, ForeignKey("catalog_category.id"))
    name = Column(String(100))
    slug = Column(String(100))
    description = Column(Text, nullable=True)
    price = Column(DECIMAL(7, 2), default=0)
    availability = Column(Boolean(), default=True)
    amount = Column(Integer, default=1)
    photo1 = Column(String)
    photo2 = Column(String, nullable=True)
    photo3 = Column(String, nullable=True)
    photo4 = Column(String, nullable=True)


class Category(BaseModel):
    id: int
    name: str
    slug: str
    lft: int
    rght: int
    tree_id: int
    level: int
    parent_id: Union[int, None] = None


class Product(BaseModel):
    id: int
    category_id: int
    name: str
    slug: str
    description: Union[str, None] = None
    price: Decimal = 0
    availability: bool = True
    amount: int = 1
    photo1: str
    photo2: Union[str, None] = None
    photo3: Union[str, None] = None
    photo4: Union[str, None] = None
