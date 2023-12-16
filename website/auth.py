from flask import Blueprint, render_template, redirect, url_for, flash, request, abort  # Make sure you import the User model
from werkzeug.security import generate_password_hash, check_password_hash
from werkzeug.utils import secure_filename
from .models import User, Book
from . import db 
from flask_login import login_user, login_required, logout_user, current_user
from passlib.hash import sha256_crypt
from flask_bcrypt import Bcrypt
import os

bcrypt = Bcrypt()
auth = Blueprint('auth', __name__)

UPLOAD_FOLDER = 'website/static/images'  # Specify the folder where uploads will be stored
ALLOWED_EXTENSIONS = {'jpg', 'jpeg', 'png', 'gif'}

def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

@auth.route('/')
def default():
    return redirect(url_for('auth.public_home'))

@auth.route('/public-home')
@login_required
def public_home():
    return render_template('public_home.html', user=current_user)

@auth.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        email = request.form.get('email')
        password = request.form.get('password')

        user = User.query.filter_by(email=email).first()
        if user:
            if bcrypt.check_password_hash(user.password, password):
                flash('Logged in successfully!', category='success')
                login_user(user, remember=True)
                return redirect(url_for('auth.public_home'))
            else:
                flash('Incorrect password, try again.', category='error')
        else:
            flash('Email does not exist.', category='error')

    return render_template("login.html", user=current_user)

@auth.route('/logout')
@login_required
def logout():
    logout_user()
    return redirect(url_for('auth.login'))

@auth.route('/sign-up', methods=['GET', 'POST'])
def sign_up():
    if request.method == 'POST':
        email = request.form.get('email')
        first_name = request.form.get('first_name')
        password1 = request.form.get('password1')
        password2 = request.form.get('password2')
        phone = request.form.get('phone')
        citizenship = request.form.get('citizenship')
        photo = request.files['photo'] if 'photo' in request.files else None  # Ensure 'photo' is defined
        # Check if the email is already in use
        existing_user = User.query.filter_by(email=email).first()
        if existing_user:
            flash('Email already exists. Please choose a different email.', category='error')
            return redirect(url_for('auth.sign_up'))

        # Validate other fields...

        # Hash the password
        hashed_password = bcrypt.generate_password_hash(password1).decode('utf-8')

        # Save additional user details
        new_user = User(
            email=email,
            first_name=first_name,
            password=hashed_password,
            phone=phone,
            citizenship=citizenship,
        )

        # Save the user's photo if it exists and is valid
        if photo and allowed_file(photo.filename):
          filename = secure_filename(photo.filename)
          user_specified_directory = request.form.get('upload_directory')  # Assuming you have a form field for this
          photo_path = os.path.join(user_specified_directory, filename)
          photo.save(photo_path)
          new_user.photo = filename
        elif photo:
          flash('Invalid file type. Please upload a valid image.', category='error')

        db.session.add(new_user)
        db.session.commit()

        flash('Account created successfully!', category='success')
        return redirect(url_for('auth.login'))

    return render_template('sign_up.html')

@auth.route('/account')
@login_required
def account():
    user_data = {
        'email': current_user.email,
        'first_name': current_user.first_name,
        'phone': current_user.phone,
        'citizenship': current_user.citizenship,
         'photo': url_for('static', filename=f'images/{current_user.photo}') if current_user.photo else None, # Assuming you stored the photo path in the database
    }
    return render_template('account.html', user=user_data)


@auth.route('/delete_account', methods=['POST'])
@login_required
def delete_account():
    # Delete the user account and associated data
    user_id = current_user.id
    user = User.query.get(user_id)

    if user:
        # You might want to add additional cleanup tasks here, such as deleting associated data
        db.session.delete(user)
        db.session.commit()

        flash('Your account has been deleted successfully.', category='success')
        return redirect(url_for('auth.login'))
    else:
        flash('Failed to delete account. Please try again.', category='error')
        return redirect(url_for('auth.account'))

        
@auth.route('/books/<category>')
@login_required
def view_books(category):
    # Fetch and display books based on the category
    books = Book.query.filter_by(category=category).all()

    # Check if the category is valid, otherwise, return a 404 error
    valid_categories = ['fiction', 'nonfiction', 'abstract']
    if category not in valid_categories:
        abort(404)
        
    print(f'Category: {category}, Number of Books: {len(books)}')    

    return render_template(f'{category}.html', books=books, user=current_user)


@auth.route('/upload_book', methods=['GET', 'POST'])
def upload_book():
    if request.method == 'POST':
        book_name = request.form['book_name']
        author = request.form['author']
        condition = request.form['condition']
        address = request.form['address']
        phone = request.form['phone']
        price = request.form['price']
        summary = request.form['summary']
        category = request.form['category']  # Add this line to get the tag from the form

        # Validate form data (add more validation as needed)

        # Handle book photo upload
        if 'photo' not in request.files:
            flash('No file part', category='error')
            return redirect(request.url)

        book_photo = request.files['photo']
        if book_photo.filename == '':
            flash('No selected file', category='error')
            return redirect(request.url)

        if book_photo and allowed_file(book_photo.filename):
            filename = secure_filename(book_photo.filename)
            photo_path = os.path.join(UPLOAD_FOLDER, filename)

            book_photo.save(photo_path)

            # Save book details to the database
            new_book = Book(
                title=book_name,
                author=author,
                condition=condition,
                address=address,
                phone=phone,
                price=price,
                summary=summary,
                photo=filename,
                category=category,
                user_id=current_user.id  # Set the user_id to the current user's ID
            )

            db.session.add(new_book)
            db.session.commit()

            flash('Book uploaded successfully!', category='success')
            return redirect(url_for('auth.view_books', category=category))

        else:
            flash('Invalid file type. Please upload a valid image.', category='error')

    return render_template('upload_book.html')

@auth.route('/delete_book/<int:book_id>', methods=['POST'])
@login_required
def delete_book(book_id):
    book = Book.query.get_or_404(book_id)

    # Check if the user is the owner of the book
    if current_user.id == book.user_id:
        try:
            # Delete the book photo file
            photo_path = os.path.join('website', 'static', 'images', book.photo)
            os.remove(photo_path)
        except FileNotFoundError:
            pass  # Ignore if the file is not found

        # Delete the book from the database
        db.session.delete(book)
        db.session.commit()

        flash('Book deleted successfully!', category='success')
    else:
        flash('You do not have permission to delete this book.', category='error')

    return redirect(url_for('auth.view_books', category=book.category))


