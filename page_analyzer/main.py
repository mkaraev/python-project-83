import os
from itertools import zip_longest

import requests
from bs4 import BeautifulSoup
from dotenv import load_dotenv
from flask import (Flask, abort, flash, redirect, render_template, request,
                   url_for)

from page_analyzer import db, urls

load_dotenv()

app = Flask(__name__, template_folder="templates")

app.config["SECRET_KEY"] = os.getenv("SECRET_KEY", "test-key")
app.config["DATABASE_URL"] = os.getenv("DATABASE_URL")


@app.route("/")
def index():
    return render_template("index.html")


@app.get("/urls")
def urls_show():
    urls = db.get_urls()
    checks = db.get_url_checks()

    return render_template(
        "urls/index.html",
        data=zip_longest(urls, checks),
    )


@app.post("/urls")
def post_url():
    url = request.form["url"]
    errors = urls.validate(url)
    if errors:
        for error in errors:
            flash(error, "danger")
        return render_template("index.html", url_name=url), 422

    normalized_url = urls.normalize(url)
    existed_url = db.get_url_by_name(normalized_url)

    if existed_url:
        id = existed_url.id
        flash("Страница уже существует", "info")
    else:
        id = db.create_url(normalized_url)
        flash("Страница успешно добавлена", "success")

    return redirect(url_for("url_show", id=id))


@app.route("/urls/<int:id>")
def url_show(id):
    url = db.get_url_by_id(id)
    if url is None:
        abort(404)

    checks = db.get_checks_by_url_id(id)

    return render_template(
        "urls/url.html",
        url=url,
        checks=checks,
    )


def parse_page(page):
    soup = BeautifulSoup(page, "html.parser")
    title = soup.find("title").text if soup.find("title") else ""
    h1 = soup.find("h1").text if soup.find("h1") else ""
    description = soup.find("meta", attrs={"name": "description"})
    if description:
        description = description["content"]
    else:
        description = ""
    return {
        "title": title[:255],
        "h1": h1[:255],
        "description": description[:255],
    }


@app.route("/urls/<int:id>/checks", methods=["POST"])
def url_checks(id):
    url = db.get_url_by_id(id)
    try:
        resp = requests.get(url.name)
        resp.raise_for_status()
    except requests.exceptions.RequestException:
        flash("Произошла ошибка при проверке", "danger")
        return redirect(url_for("url_show", id=id))

    page = resp.text
    check_data = {"id": id, "status_code": resp.status_code, **parse_page(page)}

    db.create_url_check(check_data)
    flash("Страница успешно проверена", "success")

    return redirect(url_for("url_show", id=id))


@app.errorhandler(404)
def page_not_found(error):
    return render_template("errors/404.html"), 404


@app.errorhandler(500)
def server_error(error):
    return render_template("errors/500.html"), 500
