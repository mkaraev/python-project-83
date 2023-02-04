import os
from datetime import datetime
from itertools import zip_longest

import psycopg2
import requests
from bs4 import BeautifulSoup
from dotenv import load_dotenv
from flask import (
    Flask,
    abort,
    flash,
    redirect,
    render_template,
    request,
    url_for,
)
from page_analyzer import urls
from psycopg2.extras import NamedTupleCursor

load_dotenv()

app = Flask(__name__, template_folder="templates")

app.config['SECRET_KEY'] = os.getenv('SECRET_KEY')
app.config['DATABASE_URL'] = os.getenv('DATABASE_URL')


def get_db():
    return psycopg2.connect(app.config['DATABASE_URL'])


@app.route('/')
def index():
    return render_template('index.html')


@app.get('/urls')
def urls_show():
    conn = get_db()
    with conn.cursor(cursor_factory=NamedTupleCursor) as curs:
        curs.execute(
            'SELECT * FROM urls ORDER BY id DESC;',
        )
        urls = curs.fetchall()  # noqa: WPS442
        curs.execute(
            'SELECT DISTINCT ON (url_id) * FROM url_checks ORDER BY url_id DESC, id DESC;',
        )
        checks = curs.fetchall()
    conn.close()

    return render_template(
        'urls/index.html',
        data=zip_longest(urls, checks),
    )


@app.post('/urls')
def post_url():
    url = request.form['url']
    errors = urls.validate(url)
    if errors:
        for error in errors:
            flash(error, 'danger')
        return render_template('index.html', url_name=url), 422

    conn = get_db()
    normalized_url = urls.normalize(url)
    with conn.cursor(cursor_factory=NamedTupleCursor) as curs:
        curs.execute(
            'SELECT id, name\
            FROM urls\
            WHERE name=%s', (normalized_url,),
        )
        existed_url = curs.fetchone()

        if existed_url:
            id = existed_url.id
            flash('Страница уже существует', 'info')
        else:
            curs.execute(
                'INSERT INTO urls (name, created_at)\
                VALUES (%s, %s)\
                RETURNING id;', (normalized_url, datetime.now()),
            )
            id = curs.fetchone().id
            flash('Страница успешно добавлена', 'success')
    conn.commit()
    conn.close()

    return redirect(url_for('url_show', id=id))


@app.route('/urls/<int:id>')
def url_show(id):
    conn = get_db()
    with conn.cursor(cursor_factory=NamedTupleCursor) as url_curs:
        url_curs.execute(
            'SELECT * FROM urls WHERE id = %s', (id,),
        )
        url = url_curs.fetchone()
        if url is None:
            abort(404)

    with conn.cursor(cursor_factory=NamedTupleCursor) as check_curs:
        check_curs.execute(
            'SELECT * FROM url_checks WHERE url_id = %s ORDER BY id DESC;', (id,),
        )
        checks = check_curs.fetchall()
    conn.close()

    return render_template(
        'urls/url.html',
        url=url,
        checks=checks,
    )


def parse_page(page):
    soup = BeautifulSoup(page, 'html.parser')
    title = soup.find('title').text if soup.find('title') else ''
    h1 = soup.find('h1').text if soup.find('h1') else ''
    description = soup.find('meta', attrs={'name': 'description'})
    if description:
        description = description['content']
    else:
        description = ''
    return {
        'title': title[:255],
        'h1': h1[:255],
        'description': description[:255],
    }


@app.route('/urls/<int:id>/checks', methods=['POST'])
def url_checks(id):
    conn = get_db()
    with conn.cursor(cursor_factory=NamedTupleCursor) as url_curs:
        url_curs.execute(
            'SELECT * FROM urls WHERE id = %s', (id,),
        )
        url = url_curs.fetchone()
    try:
        resp = requests.get(url.name)
        resp.raise_for_status()
    except requests.exceptions.RequestException:
        flash('Произошла ошибка при проверке', 'danger')
        return redirect(url_for('url_show', id=id))

    page = resp.text
    page_data = parse_page(page)

    with conn.cursor(cursor_factory=NamedTupleCursor) as check_curs:
        check_curs.execute(
            'INSERT INTO url_checks (url_id, status_code, h1, title, description, created_at)\
            VALUES (%s, %s, %s, %s, %s, %s);',  # noqa: E501
            (id, resp.status_code, page_data['h1'], page_data['title'], page_data['description'], datetime.now()),  # noqa: E501
        )
        flash('Страница успешно проверена', 'success')
    conn.commit()
    conn.close()

    return redirect(url_for('url_show', id=id))


@app.errorhandler(404)
def page_not_found(error):
    return render_template('errors/404.html'), 404


@app.errorhandler(500)
def server_error(error):
    return render_template('errors/500.html'), 500
