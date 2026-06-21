from flask import Flask, render_template, session
from flask import request, redirect, url_for
from functools import wraps
from flask import g, redirect
import sqlite3

app = Flask(__name__)

def login_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        # Check if user ID is in session
        if 'user_id' not in session:
            return redirect(url_for('sign_in', next=request.url))
        return f(*args, **kwargs)
    return decorated_function

# to activate venv: .\.venv\Scripts\Activate.ps1

# code to connect database to flask app
DATABASE = 'hsk.db'
app.secret_key = 'the random string'

def make_dicts(cursor, row):
    return dict((cursor.description[idx][0], value)
                for idx, value in enumerate(row))

# code to start database connection
def get_db():
    db = getattr(g, '_database', None)
    if db is None:
        db = g._database = sqlite3.connect(DATABASE)
    db.row_factory = make_dicts
    return db

progress_description = {
    1: "Not Learned Yet",
    2: "Learning",
    3: "Learned"
}

@app.teardown_appcontext
def close_connection(exception):
    db = getattr(g, '_database', None)
    if db is not None:
        db.close()
 
@app.route("/")
def hello_world():
    db = get_db()
    cur = db.cursor()
    return render_template("index.html")

@app.route("/sign_in", methods = ["POST", "GET"])
def sign_in():
    db = get_db()
    cur = db.cursor()
    if request.method == "POST":
        email = request.form.get('email')
        password = request.form.get('password')
        # check if email and password match
        query = "SELECT * FROM users WHERE email = ?;"
        data = (email,)
        cur.execute(query, data)
        result = cur.fetchone()
        if result:
            if(result['password'] == password):
                # get user id number
                cur.execute("SELECT user_id FROM users WHERE email = ?;", (email,))
                session['user_id'] = cur.fetchone()['user_id']
                return redirect(url_for("user_home"))
    return render_template("sign_in.html")

@app.route("/sign_up", methods = ["POST", "GET"])
def sign_up():
    db = get_db()
    cur = db.cursor()
    if request.method == "POST":
        email = request.form.get('email')
        password = request.form.get('password')
        name = request.form.get('name')
        query = "INSERT INTO users (email, password, name) VALUES (?, ?, ?)"
        data = (email, password, name)
        cur.execute(query, data)   
        db.commit()     
    return render_template("sign_up.html")

@app.route("/user_home", methods = ["POST", "GET"])
@login_required
def user_home():
    db = get_db()
    cur = db.cursor()
    # get list of words to display
    cur.execute("SELECT * FROM words;")
    words = cur.fetchall()
    id = session['user_id']
    cur.execute("SELECT name FROM users WHERE user_id = ?", (id,))
    name = cur.fetchone()['name']
    # get list of word_id, progress level
    cur.execute("SELECT word_id, progress_level FROM users_words_progress WHERE user_id = ?;", (id,))
    words_progress = cur.fetchall()
    print(words_progress)
    progress_message = {}
    for i in words_progress:
        progress_message[i['word_id']]=  progress_description[i['progress_level']]
    print(progress_message)
    return render_template("user_home.html", progress_message=progress_message, words = words, name = name)