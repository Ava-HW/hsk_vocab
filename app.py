from flask import Flask, render_template, session, jsonify
from flask import request, redirect, url_for
from functools import wraps
from flask import g, redirect
import sqlite3
import random

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
    1: "Not Learned",
    2: "Learning",
    3: "Learned"
}

description_progress = {
    "Not learned" : 1,
    "Learning" : 2, 
    "Learned" : 3,
    "not_learned" : 1,
    "learning" : 2, 
    "learned": 3
}

@app.teardown_appcontext
def close_connection(exception):
    db = getattr(g, '_database', None)
    if db is not None:
        db.close()

 
@app.route("/")
def index():
    db = get_db()
    cur = db.cursor()
    session.clear()
    return render_template("index.html")

@app.route("/logout")
def logout():
    session.clear()
    return redirect(url_for('index'))

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
            print(result)
            if(result['password'] == password):
                # get user id number
                cur.execute("SELECT user_id, hsk_level FROM users WHERE email = ?;", (email,))
                details = cur.fetchone()
                session['user_id'] = details['user_id']
                session['hsk_level'] = details['hsk_level']
                print(details)
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
        hsk_level = request.form.get('hsk_level').replace("level_", "")
        query = "INSERT INTO users (email, password, name, hsk_level) VALUES (?, ?, ?, ?);"
        if hsk_level:
            hsk_level = int(hsk_level)
        else:
            return render_template("sign_up.html")
        data = (email, password, name, hsk_level)
        try:
            cur.execute(query, data)   
        except:
            return render_template("sign_up.html")
        # set all words to not learned initially
        cur.execute("SELECT * FROM words;")
        word_list = cur.fetchall()
        cur.execute("SELECT user_id FROM users WHERE email = ?;", (email,))
        id = cur.fetchone()
        user_id = id['user_id']
        for i in word_list:
            data = (i['word_id'], user_id, 1)
            cur.execute("INSERT INTO users_words_progress (word_id, user_id, progress_level) VALUES (?, ?, ?);", data)
        db.commit()     
    return render_template("sign_up.html")

@app.route("/update_progress", methods=['POST'])
def update_progress():
    data = request.get_json()
    word_id = data.get('word_id')
    status = data.get('status')
    print("changing", word_id, "to", status)
    # update status in database
    db = get_db()
    cur = db.cursor()
    user_id = session['user_id']
    cur = db.cursor()
    old_status = 1
    # check if word is already in database
    query = "SELECT * FROM users_words_progress WHERE user_id = ? AND word_id = ?;"
    data = (user_id, word_id)
    cur.execute(query, data)
    word_entry = cur.fetchone()
    if word_entry:
        old_status = word_entry['progress_level']
        query = "UPDATE users_words_progress SET progress_level = ? WHERE user_id = ? AND word_id = ?"
        placeholders = (description_progress[status], user_id, word_id)
        cur.execute(query, placeholders)
    else:
        old_status = 1
        query = "INSERT INTO users_words_progress (user_id, word_id, progress_level) VALUES (?, ?, ?);"
        data = (user_id, word_id, description_progress[status])
        cur.execute(query, data)
    # update word learning and progress tallies
    query = "SELECT * FROM words WHERE word_id = ?;"
    cur.execute(query, (word_id,))
    word_details = cur.fetchone()
    word_level = word_details['hsk_level']
    print("word details are", word_details)
    # remove one from old status tally
    old_status = progress_description[old_status]
    column = f"level_{word_level}_{old_status.lower().replace(" ", "_")}"
    query = f"""
    UPDATE users
    SET {column} = {column} - 1
    WHERE user_id = ?;
    """
    data = (session['user_id'],)
    print("runnining", query)
    try:
        db.execute(query, data)
    except:
        pass
    # add one to new status tally
    column = f"level_{word_level}_{status.lower().replace(" ", "_")}"
    query = f"""
    UPDATE users
    SET {column} = {column} + 1
    WHERE user_id = ?;
    """
    data = (session['user_id'],)
    print("running", query, data)
    try:
        db.execute(query, data)
    except:
        pass
    db.commit()
    return jsonify({'success': True})

@app.route("/start_quiz", methods = ["POST", "GET"])
@login_required
def start_quiz():
    db = get_db()
    cur = db.cursor()
    if request.method == "POST":
        num_questions = int(request.form.get('num_questions'))
        progress_level = request.form.get('progress_level')
        show_pinyin = request.form.get('show_pinyin')
        if(show_pinyin):
            session['show_pinyin'] = True
        else:
            session['show_pinyin'] = False
        # get suitable list of words
        question_list = []
        query = ""
        if progress_level != "all_progress_levels":
            progress_num = description_progress[progress_level]
            query = """
                SELECT words.* FROM words
                INNER JOIN users_words_progress ON words.word_id = users_words_progress.word_id
                WHERE users_words_progress.progress_level = ?
                AND words.hsk_level <= ?
                ORDER BY random()
                LIMIT ?;
            """ 
            data = (progress_num, session['hsk_level'], num_questions)
        else:
            query = """
                SELECT * FROM words
                ORDER BY random()
                LIMIT ?;
            """
            data = (num_questions,)
        cur.execute(query, data)
        words_list = cur.fetchall()
        quiz_questions = []
        for i in words_list:
            answer = i['english']
            pinyin = i['pinyin']
            hanzi = i['hanzi']
            # pick 3 random other words to use as wrong answers
            options = []
            query = """
                SELECT english 
                FROM words
                WHERE english != ?
                ORDER BY random()
                LIMIT 3;
            """
            cur.execute(query, (answer,))
            temp = cur.fetchall()
            for j in temp:
                options.append(j['english'])
            options.append(answer)
            question = {}
            question['answer'] = answer
            question['hanzi'] = hanzi
            question['pinyin'] = pinyin
            random.shuffle(options)
            question['options'] = options
            quiz_questions.append(question)
        session['quiz_questions'] = quiz_questions
        return redirect(url_for('quiz'))
    return render_template("start_quiz.html")

@login_required
@app.route("/quiz", methods=["GET", "POST"])
def quiz():
    return render_template("quiz.html")

@login_required
@app.route("/submit_quiz", methods=["GET", "POST"])
def submit_quiz():
    submitted_answers = []
    score = 0
    if request.method == "POST":
        # get list of submitted answers
        for i in session['quiz_questions']:
            response = request.form.get(i['pinyin'])
            submitted_answers.append(response)
            if response == i['answer']:
                score += 1
    return render_template("submit_quiz.html", score=score, submitted_answers=submitted_answers)

@app.route("/progress")
@login_required
def progress():
    db = get_db()
    cur = db.cursor()
    # find no. of total words
    cur.execute("SELECT * FROM words WHERE hsk_level <= ?;", (session['hsk_level'],))
    words_list = cur.fetchall()
    total_words = len(words_list)
    # find no. of learned words
    learned = 0
    for i in range(1, session['hsk_level'] + 1):
        query = f"""
        SELECT level_{i}_learned 
        FROM users
        WHERE user_id = ?;
        """
        data = (session['user_id'],)
        cur.execute(query, data)
        amount = cur.fetchone()
        if amount[f'level_{i}_learned']: 
            learned += amount[f'level_{i}_learned']
    # find no. of learning words
    learning = 0
    for i in range(1, session['hsk_level'] + 1):
        query = f"""
        SELECT level_{i}_learning 
        FROM users
        WHERE user_id = ?;
        """
        data = (session['user_id'],)
        cur.execute(query, data)
        amount = cur.fetchone()
        if amount[f'level_{i}_learning']: 
            learning += amount[f'level_{i}_learning']
    # calculate no. of not learned words
    not_learned = total_words - learning - learned
    return render_template("progress.html", learned=learned, learning=learning, not_learned=not_learned, total_words=total_words)

@app.route("/user_home", methods = ["POST", "GET"])
@login_required
def user_home():
    db = get_db()
    cur = db.cursor()
    # get list of words to display
    cur.execute("SELECT * FROM words;")
    words = []
    temp = cur.fetchall()
    for i in temp:
        if i['hsk_level'] <= session['hsk_level']:
            words.append(i)
    id = session['user_id']
    cur.execute("SELECT name FROM users WHERE user_id = ?", (id,))
    name = cur.fetchone()['name']
    # get list of word_id, progress level
    data = (id,)
    cur.execute("SELECT word_id, progress_level FROM users_words_progress WHERE user_id = ?;", data)
    words_progress = cur.fetchall()
    progress_message = {}
    for i in words_progress:
        progress_message[i['word_id']]=  progress_description[i['progress_level']]
    return render_template("user_home.html", progress_message=progress_message, words = words, name = name)