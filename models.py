import datetime

from flask_dance.consumer.backend.sqla import OAuthConsumerMixin
from flask_login import UserMixin
from flask_marshmallow import Marshmallow
from flask_sqlalchemy import SQLAlchemy
from sqlalchemy import Column, String, DateTime, ForeignKey
from sqlalchemy.dialects.mysql import INTEGER, TEXT
from sqlalchemy.orm import relationship

# Initialize SQLAlchemy
db = SQLAlchemy()
# Initialize SQLAlchemy before marshmallow.
ma = Marshmallow()


class User(db.Model, UserMixin):
    """
    Model for the User.
    """
    __tablename__ = 'users'
    id = Column(INTEGER(unsigned=True), primary_key=True)
    name = Column(String(50))
    email = Column(String(120), unique=True)


class OAuth(OAuthConsumerMixin, db.Model):
    """
    Model for OAuth.

    Used for saving the token from an OAUTH login and linking to a User.
    """
    provider_user_id = db.Column(db.String(256), unique=True)
    user_id = db.Column(INTEGER(unsigned=True), db.ForeignKey(User.id))
    user = db.relationship(User)


class Category(db.Model):
    """
    Model for Category.

    Used for categorizing items in categories.
    """
    __tablename__ = 'categories'
    id = Column(INTEGER(unsigned=True), primary_key=True)
    name = Column(String(64), unique=True)
    items = relationship("Item", back_populates="category")


class Item(db.Model):
    """
    Model for Item.

    All items are categorized in the Category model.
    """
    __tablename__ = 'items'
    id = Column(INTEGER(unsigned=True), primary_key=True)
    name = Column(String(64), unique=True)
    description = Column(TEXT)
    created_at = Column(DateTime, default=datetime.datetime.utcnow())
    category_id = Column(INTEGER(unsigned=True), ForeignKey(Category.id))
    category = relationship(Category)


class ItemSchema(ma.ModelSchema):
    """
    Schema for Item.

    Used for JSON generation and deciding which fields should be shown when
    a Item is converted to JSON.
    """
    class Meta:
        fields = ('name', 'description')
        model = Item


class CategorySchema(ma.ModelSchema):
    """
    Schema for Category.

    Used for JSON generation and deciding which fields should be shown when
    a Category is converted to JSON.
    """
    class Meta:
        model = Category
        fields = ('name', 'items')
    items = ma.Nested(ItemSchema, many=True)


# construct schemas for item and category.
item_schema = ItemSchema()
items_schema = ItemSchema(many=True)
category_schema = CategorySchema()
categories_schema = CategorySchema(many=True)
