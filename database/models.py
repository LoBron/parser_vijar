from decimal import Decimal
from typing import Union
from pydantic import BaseModel
from sqlalchemy import Column, Integer, String, Text, Boolean, ForeignKey, DECIMAL
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import relationship
from database.my_sqlalchemy_mptt import BaseNestedSets

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


class Category(Base, BaseNestedSets):
    __tablename__ = 'catalog_category'
    id = Column(Integer(), primary_key=True, autoincrement=True)
    name = Column(String(50))
    slug = Column(String(50), unique=True)
    products = relationship("Product")


class PropertyValue(Base):
    __tablename__ = 'catalog_propertyvalue'
    id = Column(Integer, primary_key=True, autoincrement=True)
    product_id = Column(Integer(), ForeignKey("catalog_product.id"))
    property_id = Column(Integer(), ForeignKey("catalog_property.id"))
    value = Column(String(200))


# prop_value = Table(
#     'catalog_propertyvalue', Base.metadata,
#     Column('id', Integer(), primary_key=True, autoincrement=True),
#     Column('product_id', Integer(), ForeignKey("catalog_product.id")),
#     Column('property_id', Integer(), ForeignKey("catalog_property.id")),
#     Column('value', String(200))
# )


class Product(Base):
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
    properties = relationship("PropertyValue", backref="catalog_product")


class Property(Base):
    __tablename__ = 'catalog_property'
    id = Column(Integer, primary_key=True, autoincrement=True)
    name = Column(String(200), unique=True)
    products = relationship("PropertyValue", backref="catalog_property")

# class Category(BaseModel):
#     id: int
#     name: str
#     slug: str
#     lft: int
#     rght: int
#     tree_id: int
#     level: int
#     parent_id: Union[int, None] = None
#
#
# class Product(BaseModel):
#     id: int
#     category_id: int
#     name: str
#     slug: str
#     description: Union[str, None] = None
#     price: Decimal = 0
#     availability: bool = True
#     amount: int = 1
#     photo1: str
#     photo2: Union[str, None] = None
#     photo3: Union[str, None] = None
#     photo4: Union[str, None] = None
