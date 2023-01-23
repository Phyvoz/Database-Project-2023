from flask import Flask, redirect, url_for, render_template, request, session, flash
from datetime import timedelta
from sqlalchemy import create_engine
from sqlalchemy.sql import select, text, insert
import hashlib
import re 

app = Flask(__name__)
app.secret_key = 'pwr'
app.permanent_session_lifetime = timedelta(minutes=5)
engine = create_engine("mysql+mysqlconnector://root:password@localhost/progressApp")

def encryptData(password):
    hashed_string = hashlib.sha256(password.encode('utf-8')).hexdigest()
    return hashed_string

def validateEmail(email):
    if len(email) > 7:
        if re.match("^.+@(\\[?)[a-zA-Z0-9\\-\\.]+\\.([a-zA-Z]{2,3}|[0-9]{1,3})(]?)$", email) != None:
            return True
    else:
        return False

@app.route("/")
def home():
    return redirect(url_for('login'))

@app.route("/login", methods=['POST', 'GET'])
def login():
    if request.method == 'POST':
        session.permanent = True
        user = request.form['nm'].strip()
        password = encryptData(request.form['pw'])
        sql_txt = f"CALL login_procedure('{user}', '{password}');"
        login_stmt = text(sql_txt)
        with engine.connect() as connection:
            result = connection.execute(login_stmt)
            msg = [a for a in result]    
        if len(msg) > 0 and user == str(msg[0][0]) and password == str(msg[0][1]):
            session['user'] = user
            session['userId'] = msg[0][2]
        else:
            flash(message='Wrong email or Password')
            return redirect(url_for('login'))
        flash(message=str(msg), category="info")
        return redirect(url_for('user', usr=user))
    else:
        if 'user' in session:
            flash('Already Logged In')
            return redirect(url_for('user'))
        return render_template("login.html")

@app.route("/user", methods=['POST', 'GET'])
def user():
    if 'user' in session:
        user = session['user']
        userId = session['userId']
        with engine.connect() as get_categories:
            get_cats = f'SELECT c.categoryName, c.categoryId FROM users AS u LEFT JOIN categories AS c ON u.userId=c.userId WHERE c.userId={userId}'
            query1 = text(get_cats)
            cats = get_categories.execute(query1)
            categories = [a for a in cats]
        if request.method == 'POST':
            note = request.form['nt']
            cat = request.form['cat']
            if len(note) > 0:
                with engine.connect() as submit_note:
                    sql_txt = f"INSERT INTO notes (userId, noteData, categoryId) VALUES ('{userId}', {repr(note)}, {cat})"
                    submit_note.execute(sql_txt)
                    flash('Progress Saved!')
            else:
                flash('Note is empty')
    else:
        flash('You are not logged in!')
        return redirect(url_for('login'))
    return render_template('user.html', user=user, categories=categories)

@app.route("/categories", methods=['GET', 'POST'])
def categories():
    if 'user' in session:
        user = session['user']
        userId = session['userId']
        if request.method == 'POST':
            cat = request.form['ct']
            with engine.connect() as get_categories:
                get_cats = f'SELECT categoryName FROM categories WHERE userId={userId}'
                query1 = text(get_cats)
                cats = get_categories.execute(query1)
                categories = [a[0] for a in cats]
            if len(cat) > 0 and cat not in categories:
                with engine.connect() as submit_cat:
                    sql_txt = f"INSERT INTO categories (userId, categoryName) VALUES ('{userId}', {repr(cat)})"
                    submit_cat.execute(sql_txt)
                    flash(f'Category {cat} Saved!')
            else:
                flash('Category is empty or already exists')
    else:
        flash('You are not logged in!')
        return redirect(url_for('login'))
    return render_template('categories.html')

@app.route("/logout")
def logout():
    session.pop('user', None)
    session.pop('userId', None)
    flash('You have been logged out')
    return redirect(url_for('login'))

@app.route("/signup", methods=['POST', 'GET'])
def signup():
    if request.method == 'POST':
        user = request.form['nm_register'].strip()
        password = request.form['pw_register']
        if not validateEmail(user):
            flash('Invalid email')
            return redirect(url_for('signup'))
        password = encryptData(password)
        with engine.connect() as connection:
            sql_txt = f"SELECT email FROM users WHERE email='{user}'"
            result = connection.execute(sql_txt)
            users = [a for a in result]
        if len(users) > 0:
            flash('User already exists')
            return redirect(url_for('signup'))
        else:
            with engine.connect() as signup:
                sql_text = f"INSERT INTO users (email, password) VALUES ('{user}', '{password}')"
                signup.execute(sql_text)
                flash('Successfully created user!')
                return redirect(url_for('login'))
    return render_template('signup.html')

@app.route("/mynotes", methods=['GET'])
def mynotes():
    if 'user' in session:
        user = session['user']
        userId = session['userId']
        with engine.connect() as connection:
            sql_txt = f"CALL notes_procedure({userId});"
            result = connection.execute(sql_txt)
            notes = [a for a in result]        
        return render_template('mynotes.html', notes=notes)
    else:
        flash('You are not logged in!')
        return redirect(url_for('login'))


if __name__ == '__main__':
    app.run(debug=True)

