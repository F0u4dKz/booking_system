from app.auth import auth_bp
from flask import render_template, request, url_for, redirect
from werkzeug.security import generate_password_hash, check_password_hash
from app.models import User
from app import db
from flask_login import login_user, login_required, current_user

@auth_bp.route('/login', methods=['POST'])
def login(): 
    username = request.form.get('username')
    password = request.form.get('password')

    user = User.query.filter_by(username=username).first()

    # check if the user actually exists
    # take the user-supplied password, hash it, and compare it to the hashed password in the database
    if not user or not check_password_hash(user.password, password):
        
       return 'GOOO BRUVV' # if the user doesn't exist or password is wrong, reload the page

    login_user(user, remember=True)
    return redirect(url_for('main.index'))

@auth_bp.route('/login')
def loginpage(): 
    if current_user.is_authenticated:
        return redirect(url_for('main.index'))
    return render_template('login.html')

@auth_bp.route('/signup', methods=['POST'])
def signup():
    data = request.json

    # Access data from the JSON body
    username = data.get('username')
    password = data.get('password') 
    name = data.get('name') 

    print(data)


    user = User.query.filter_by(username=username).first() # if this returns a user, then the email already exists in database

    if user: # if a user is found, we want to redirect back to signup page so user can try again
        return 'user exists'

    # create a new user with the form data. Hash the password so the plaintext version isn't saved.
    new_user = User(username=username, name=name, password=generate_password_hash(password,"pbkdf2"))

    # add the new user to the database
    db.session.add(new_user)
    db.session.commit()

    

    return 'welcome in bruuuv, user saved'


    