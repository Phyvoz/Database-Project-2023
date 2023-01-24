from flask import Flask, redirect, url_for, render_template, request, session, flash
from datetime import timedelta
from sqlalchemy import create_engine
from sqlalchemy.sql import select, text, insert, bindparam
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

def log(userId, action):
    with engine.connect() as sumbit_log:
        sql = text("INSERT INTO logs(userId, action) VALUES (:userId, :action)")
        query = sql.bindparams(userId=userId, action=action)
        sumbit_log.execute(query)

@app.route("/")
def home():
    return redirect(url_for('login'))

@app.route("/login", methods=['POST', 'GET'])
def login():
    if request.method == 'POST':
        session.permanent = True
        user = request.form['nm'].strip()
        password = encryptData(request.form['pw'])
        sql_txt = text(f"CALL login_procedure(:username, :password);")
        login_stmt = sql_txt.bindparams(username=user, password=password)
        with engine.connect() as connection:
            result = connection.execute(login_stmt)
            msg = [a for a in result]    
        if len(msg) > 0 and user == str(msg[0][0]) and password == str(msg[0][1]):
            session['user'] = user
            session['userId'] = msg[0][2]
            log(session['userId'], 'login')
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
            get_cats = text('SELECT categoryName, categoryId FROM categories WHERE userId = :userId')
            query1 = get_cats.bindparams(userId=userId)
            cats = get_categories.execute(query1)
            categories = [a for a in cats]
        if request.method == 'POST':
            note = request.form['nt']
            cat = request.form['cat']
            if len(note) > 0:
                with engine.connect() as submit_note:
                    sql_txt = text("INSERT INTO notes (userId, noteData, categoryId) VALUES (:userId, :note, :cat)")
                    query = sql_txt.bindparams(userId=userId, note=note, cat=cat)
                    submit_note.execute(query)
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
                get_cats = text('SELECT categoryName FROM categories WHERE userId=:userId')
                query1 = get_cats.bindparams(userId=userId)
                cats = get_categories.execute(query1)
                categories = [a[0] for a in cats]
            if len(cat) > 0 and cat not in categories:
                with engine.connect() as submit_cat:
                    sql_txt = text("INSERT INTO categories (userId, categoryName) VALUES (:userId, :cat)")
                    query = sql_txt.bindparams(userId=userId, cat=cat)
                    submit_cat.execute(query)
                    flash(f'Category {cat} Saved!')
            else:
                flash('Category is empty or already exists')
    else:
        flash('You are not logged in!')
        return redirect(url_for('login'))
    return render_template('categories.html')

@app.route("/logout")
def logout():
    log(session['userId'], 'logout')
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
            sql_txt = text("SELECT email FROM users WHERE email=:user")
            query = sql_txt.bindparams(user=user)
            result = connection.execute(query)
            users = [a for a in result]
        if len(users) > 0:
            flash('User already exists')
            return redirect(url_for('signup'))
        else:
            with engine.connect() as signup:
                sql_text = text("INSERT INTO users (email, password) VALUES (:user, :password)")
                query = sql_text.bindparams(user=user, password=password)
                signup.execute(query)
                flash('Successfully created user!')
                return redirect(url_for('login'))
    return render_template('signup.html')

@app.route("/mynotes", methods=['GET', 'POST'])
def mynotes():
    if 'user' in session:
        user = session['user']
        userId = session['userId']
        with engine.connect() as connection:
            sql_txt = text("CALL notes_procedure(:userId);")
            query = sql_txt.bindparams(userId=userId)
            result = connection.execute(query)
            all_notes = [a for a in result]
        return render_template('mynotes.html', notes=all_notes, categories=categories)
    else:
        flash('You are not logged in!')
        return redirect(url_for('login'))

@app.route("/delete/<id>")
def delete(id):
    if 'user' in session:
        user = session['user']
        userId = session['userId']
        with engine.connect() as get_notes:
            get_nts = text('SELECT noteId FROM notes WHERE userId=:userId')
            query1 = get_nts.bindparams(userId=userId)
            nts = get_notes.execute(query1)
            notes = [a[0] for a in nts]
        if int(id) not in notes:
            flash('You have no permission to delete this note!')
            return redirect(url_for('mynotes'))
        else:
            with engine.connect() as connection:
                sql_txt = text("DELETE FROM notes WHERE noteId=:id")
                query = sql_txt.bindparams(id=id)
                result = connection.execute(query)
            flash('Note deleted!')
            return redirect(url_for('mynotes'))
    else:
        flash('You are not logged in!')
        return redirect(url_for('login'))

@app.route("/edit/<id>", methods=['GET', 'POST'])
def edit(id):
    if 'user' in session:
        user = session['user']
        userId = session['userId']
        with engine.connect() as get_notes:
            get_nts = text('SELECT noteId, noteData FROM notes WHERE userId=:userId')
            query1 = get_nts.bindparams(userId=userId)
            nts = get_notes.execute(query1)
            notes = [a[0] for a in nts]
        if int(id) not in notes:
            flash('You have no permission to edit this note!')
            return redirect(url_for('mynotes'))
        else:
            with engine.connect() as get_note:
                get_nt = text('SELECT noteData FROM notes WHERE noteId=:id')
                query2 = get_nt.bindparams(id=id)
                nt = get_note.execute(query2)
                note = [a[0] for a in nt]
            with engine.connect() as get_categories:
                get_cats = text('SELECT categoryName, categoryId FROM categories WHERE userId=:userId')
                query1 = get_cats.bindparams(userId=userId)
                cats = get_categories.execute(query1)
                ex_categories = [a for a in cats]
            if request.method == 'POST':
                note = request.form['mod_note']
                category = request.form['cat_mod']
                with engine.connect() as connection:
                    sql_txt = text("UPDATE notes SET noteData=:note, categoryId=:category WHERE noteId=:id")
                    query = sql_txt.bindparams(note=note, category=category, id=id)
                    result = connection.execute(query)
                flash('Note updated!')
                return redirect(url_for('mynotes'))
            return render_template('edit.html', ex_categories=ex_categories, note=note)
    else:
        flash('You are not logged in!')
        return redirect(url_for('login'))


if __name__ == '__main__':
    app.run(port=5001, debug=True)

