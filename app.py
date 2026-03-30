from flask import Flask, render_template

app = Flask(__name__)

# to activate venv: .\.venv\Scripts\Activate.ps1
 
@app.route("/")
def hello_world():
    return render_template("index.html")

@app.route("/sign_in")
def sign_in():
    return render_template("sign_in.html")

@app.route("/sign_up")
def sign_up():
    return render_template("sign_up.html")