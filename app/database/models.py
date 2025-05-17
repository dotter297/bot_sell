from sqlalchemy import Column, Integer, String, DateTime, ForeignKey, Text, BigInteger, Boolean
from sqlalchemy.orm import relationship, declarative_base
import datetime

Base = declarative_base()

class Order(Base):
    __tablename__ = "orders"

    id = Column(Integer, primary_key=True)
    user_id = Column(BigInteger)
    name = Column(String)
    phone = Column(String)
    address = Column(String)
    salt_type = Column(String, nullable=True)
    quantity = Column(Integer, nullable=True)
    total = Column(Integer)
    payment = Column(String)
    confirmed = Column(Boolean, default=False)  # Новое поле
    ttn = Column(String, nullable=True)  # Новое поле
    rejection_reason = Column(String, nullable=True)  # Новое поле
    created_at = Column(DateTime, default=datetime.datetime.utcnow)

    items = relationship("OrderItem", back_populates="order", cascade="all, delete")

class OrderItem(Base):
    __tablename__ = "order_items"

    id = Column(Integer, primary_key=True)
    order_id = Column(Integer, ForeignKey("orders.id"))
    product_id = Column(Integer)
    product_name = Column(String)
    product_price = Column(Integer)
    quantity = Column(Integer)

    order = relationship("Order", back_populates="items")

class Subscriber(Base):
    __tablename__ = "subscribers"
    __table_args__ = {'extend_existing': True}

    user_id = Column(BigInteger, primary_key=True)
    subscribed = Column(Boolean, default=True)
    created_at = Column(DateTime, default=datetime.datetime.utcnow)

class Product(Base):
    __tablename__ = "products"
    id = Column(Integer, primary_key=True)
    name = Column(String)
    price = Column(Integer)
    photo = Column(String)

class UserQuestion(Base):
    __tablename__ = "questions"

    id = Column(Integer, primary_key=True)
    user_id = Column(BigInteger, nullable=False)
    username = Column(String)
    question = Column(Text, nullable=False)
    created_at = Column(DateTime, default=datetime.datetime.utcnow)

class Feedback(Base):
    __tablename__ = "feedback"

    id = Column(Integer, primary_key=True)
    user_id = Column(BigInteger, nullable=False)
    name = Column(String, nullable=True)
    feedback = Column(Text, nullable=False)
    confirmed = Column(Boolean, default=False)
    created_at = Column(DateTime, default=datetime.datetime.utcnow)