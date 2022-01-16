"""
Flask database utils.
"""
import sqlite3
from flask import g, current_app


def get_db():
    if "db" not in g:
        path: str = current_app.config["DB_PATH"]
        g.db = sqlite3.connect(path)
        g.db.row_factory = sqlite3.Row
    return g.db


def close_db(e=None):
    db = g.pop("db", None)

    if db is not None:
        db.close()


def init_db():
    db = get_db()

    with current_app.open_resource("schema.sql") as f:
        sql = f.read().decode("utf8")
        db.executescript(sql)
