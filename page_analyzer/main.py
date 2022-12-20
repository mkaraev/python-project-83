from flask import Flask, render_template

import urls

app = Flask(__name__, template_folder="templates")


@app.route("/healthcheck")
def hello_world():
    return "App is running"


@app.route("/")
def index():
    return render_template("index.html")

@app.route("/urls", methods=["POST"])
def post_url():
