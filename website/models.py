from . import db
from flask_login import UserMixin
from sqlalchemy.sql import func
from flask_wtf import FlaskForm
from wtforms import StringField, TextAreaField, IntegerField
from wtforms.validators import DataRequired, Length
from flask_wtf.file import FileField, FileAllowed, FileRequired
from wtforms.fields import MultipleFileField
from sqlalchemy.orm import relationship

class Note(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    data = db.Column(db.String(10000))
    date = db.Column(db.DateTime(timezone=True), default=func.now())
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'))

class User(db.Model, UserMixin):
   
    id = db.Column(db.Integer, primary_key=True)
    email = db.Column(db.String(150), unique=True)
    password = db.Column(db.String(150))
    first_name = db.Column(db.String(150))
    phone = db.Column(db.String(20))  # Add this line to include the phone attribute
    citizenship = db.Column(db.String(50))  # Add this line to include the citizenship attribute
    photo = db.Column(db.String(150))  # Add this line to include the photo attribute
    notes = db.relationship('Note')

class House(db.Model):
    house_name = db.Column(db.String(255), nullable=False)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    id = db.Column(db.Integer, primary_key=True)
    location = db.Column(db.String(255), nullable=False)
    owner = db.Column(db.String(255), nullable=False)
    phone = db.Column(db.String(20))
    price = db.Column(db.Float, nullable=False)
    menu = db.Column(db.String(255))
    description = db.Column(db.Text)
    street = db.Column(db.String(255))  # Add this line
    photos = db.relationship('HousePhoto', back_populates='house')

    def __repr__(self):
        return f"House('{self.location}', '{self.owner}', '{self.price}', '{self.description}')"

    
class HouseForm(FlaskForm):
    house_name = StringField('House Name', validators=[DataRequired()])
    location = StringField('Location', validators=[DataRequired(), Length(max=100)])
    phone = StringField('Phone', validators=[DataRequired(), Length(max=20)])
    price = IntegerField('Price', validators=[DataRequired()])
    menu = TextAreaField('Menu', validators=[Length(max=500)])
    description = TextAreaField('Description', validators=[Length(max=1000)])
    photos = MultipleFileField('Photos', validators=[FileAllowed(['jpg', 'png', 'gif', 'jpeg'], 'Images only, please.')])
    street = StringField('Street', validators=[DataRequired(), Length(max=100)])
    id = db.Column(db.Integer, primary_key=True)
    house_id = db.Column(db.Integer, db.ForeignKey('house.id'), nullable=False)
    filename = db.Column(db.String(255), nullable=False)
    
class HousePhoto(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    filename = db.Column(db.String(255))
    house_id = db.Column(db.Integer, db.ForeignKey('house.id'), nullable=False)
    house = db.relationship('House', back_populates='photos')

    def __repr__(self):
        return f"HousePhoto('{self.filename}')"