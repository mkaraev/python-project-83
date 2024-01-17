import os
from contextlib import contextmanager
from datetime import datetime

import psycopg2
from psycopg2.extras import NamedTupleCursor


@contextmanager
def connection():
    database_url = os.getenv("DATABASE_URL")
    conn = psycopg2.connect(database_url)
    try:
        yield conn
    finally:
        conn.close()


def get_urls():
    with connection() as conn:
        with conn.cursor(cursor_factory=NamedTupleCursor) as curs:
            curs.execute(
                "SELECT * FROM urls ORDER BY id DESC;",
            )
            urls = curs.fetchall()  # noqa: WPS442
            return urls


def get_url_checks():
    with connection() as conn:
        with conn.cursor(cursor_factory=NamedTupleCursor) as curs:
            curs.execute(
                "SELECT DISTINCT ON (url_id) * FROM url_checks ORDER BY url_id DESC, id DESC;",
            )
            checks = curs.fetchall()
            return checks


def get_checks_by_url_id(url_id):
    with connection() as conn:
        with conn.cursor(cursor_factory=NamedTupleCursor) as check_curs:
            check_curs.execute(
                "SELECT * FROM url_checks WHERE url_id = %s ORDER BY id DESC;",
                (url_id,),
            )
            checks = check_curs.fetchall()
        return checks


def get_url_by_name(url):
    with connection() as conn:
        with conn.cursor(cursor_factory=NamedTupleCursor) as curs:
            curs.execute(
                "SELECT id, name\
                FROM urls\
                WHERE name=%s",
                (url,),
            )
            existed_url = curs.fetchone()
            return existed_url


def get_url_by_id(id):
    with connection() as conn:
        with conn.cursor(cursor_factory=NamedTupleCursor) as curs:
            curs.execute(
                "SELECT * FROM urls WHERE id = %s",
                (id,),
            )
            url = curs.fetchone()
            return url


def create_url(url):
    with connection() as conn:
        with conn.cursor(cursor_factory=NamedTupleCursor) as curs:
            curs.execute(
                "INSERT INTO urls (name, created_at)\
                VALUES (%s, %s)\
                RETURNING id;",
                (url, datetime.now()),
            )
            id = curs.fetchone().id

        conn.commit()
        return id


def create_url_check(check_data):
    with connection() as conn:
        with conn.cursor(cursor_factory=NamedTupleCursor) as check_curs:
            check_curs.execute(
                "INSERT INTO url_checks (url_id, status_code, h1, title, description, created_at)\
                VALUES (%s, %s, %s, %s, %s, %s);",  # noqa: E501
                (
                    check_data["id"],
                    check_data["status_code"],
                    check_data["h1"],
                    check_data["title"],
                    check_data["description"],
                    datetime.now(),
                ),  # noqa: E501
            )
        conn.commit()
