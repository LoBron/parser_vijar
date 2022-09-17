from sqlalchemy import Column, Integer, String, Text, Boolean, ForeignKey, DECIMAL
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import relationship
from persistence.alchemy.mptt import BaseNestedSets

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


PostgresBase = declarative_base()


class CategoryTable(PostgresBase, BaseNestedSets):
    __tablename__ = 'catalog_category'
    id = Column(Integer(), primary_key=True, autoincrement=True)
    name = Column(String(50))
    slug = Column(String(50), unique=True)
    products = relationship("ProductTable")


class PropertyValueTable(PostgresBase):
    __tablename__ = 'catalog_propertyvalue'
    id = Column(Integer, primary_key=True, autoincrement=True)
    product_id = Column(Integer(), ForeignKey("catalog_product.id"))
    property_id = Column(Integer(), ForeignKey("catalog_property.id"))
    value = Column(String(200))


class ProductTable(PostgresBase):
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
    properties = relationship("PropertyValueTable", backref="catalog_product")


class PropertyTable(PostgresBase):
    __tablename__ = 'catalog_property'
    id = Column(Integer, primary_key=True, autoincrement=True)
    name = Column(String(200), unique=True)
    products = relationship("PropertyValueTable", backref="catalog_property")


SQLiteBase = declarative_base()


class CategoryInfoTable(SQLiteBase):
    __tablename__ = 'category'
    id = Column(Integer(), primary_key=True, autoincrement=True)
    name = Column(String(50))
    url = Column(String(200), unique=True)
    cat_id = Column(Integer, unique=True)
