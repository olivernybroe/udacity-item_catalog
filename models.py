from flask_dance.consumer.backend.sqla import OAuthConsumerMixin, SQLAlchemyBackend
from flask_login import UserMixin, current_user
from flask_sqlalchemy import SQLAlchemy
from sqlalchemy import Column, Integer, String, DateTime, text, ForeignKey
from sqlalchemy.dialects.mysql import INTEGER, TEXT
from sqlalchemy.orm import relationship
import datetime

db = SQLAlchemy()


class User(db.Model, UserMixin):
    __tablename__ = 'users'
    id = Column(INTEGER(unsigned=True), primary_key=True)
    name = Column(String(50))
    username = Column(String(64), unique=True, index=True)
    password = Column(String(256))
    email = Column(String(120), unique=True)


class OAuth(OAuthConsumerMixin, db.Model):
    provider_user_id = db.Column(db.String(256), unique=True)
    user_id = db.Column(INTEGER(unsigned=True), db.ForeignKey(User.id))
    user = db.relationship(User)


class Category(db.Model):
    __tablename__ = 'categories'
    id = Column(INTEGER(unsigned=True), primary_key=True)
    name = Column(String(64), unique=True)
    items = relationship("Item", back_populates="category")


class Item(db.Model):
    __tablename__ = 'items'
    id = Column(INTEGER(unsigned=True), primary_key=True)
    name = Column(String(64), unique=True)
    description = Column(TEXT)
    created_at = Column(DateTime, default=datetime.datetime.utcnow())
    category_id = Column(INTEGER(unsigned=True), ForeignKey(Category.id))
    category = relationship(Category)

