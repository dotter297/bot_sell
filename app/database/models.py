from sqlalchemy import Column, Integer, String, DateTime
from sqlalchemy.ext.declarative import declarative_base
import datetime

Base = declarative_base()

class Order(Base):
    __tablename__ = "orders"
    id = Column(Integer, primary_key=True)
    name = Column(String)
    phone = Column(String)
    address = Column(String)
    salt_type = Column(String)
    quantity = Column(Integer)
    total = Column(Integer)
    payment = Column(String)
    created_at = Column(DateTime, default=datetime.datetime.utcnow)


class Subscriber(Base):
    __tablename__ = "subscribers"
    id = Column(Integer, primary_key=True)
    user_id = Column(String, unique=True)

class Product(Base):
    __tablename__ = "products"
    id = Column(Integer, primary_key=True)
    name = Column(String)
    price = Column(Integer)
    photo = Column(String)

class Feedback(Base):
    __tablename__ = "feedbacks"
    id = Column(Integer, primary_key=True)
    name = Column(String)
    text = Column(String)
