from datetime import datetime

from sqlalchemy import Boolean, Column, DateTime, Float, Integer, String
from sqlalchemy.orm import declarative_base

Base = declarative_base()

PRODUCTS_TABLE = "products"


class Article(Base):
    __tablename__ = PRODUCTS_TABLE

    id = Column(Integer(), primary_key=True)

    external_id = Column(String(), nullable=False, unique=True)
    name = Column(String(), nullable=False)
    brand = Column(String(), nullable=True)
    packaging = Column(String(), nullable=True)
    image_url = Column(String(), nullable=False)

    size = Column(Float(), nullable=True)
    is_approx_size = Column(Boolean(), nullable=False)
    size_format = Column(String(), nullable=False)

    price = Column(Float(), nullable=False)
    price_per_size = Column(Float(), nullable=False)
    is_pack = Column(Boolean(), nullable=False)
    total_units = Column(Integer(), nullable=True)
    unit_name = Column(String(), nullable=True)

    department = Column(String(), nullable=True)
    category = Column(String(), nullable=False)
    subcategory = Column(String(), nullable=False)
    subtype = Column(String(), nullable=False)
    vendor = Column(String(), nullable=False)

    created_at = Column(DateTime(), default=datetime.now)
    updated_at = Column(DateTime(), default=datetime.now, onupdate=datetime.now)
