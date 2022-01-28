"""
Flask database utils.
"""
import sqlite3
from sqlite3 import Cursor

from flask import g, current_app

from theatre.db import Database


def get_db() -> Database:
    if "db" not in g:
        path: str = current_app.config["DB_PATH"]
        g.db = Database.connect(database_path=path)
    return g.db


def close_db(e=None):
    db: Database | None = g.pop("db", None)

    if db is not None:
        db.close()


def init_db():
    db: Database = get_db()
    with current_app.open_resource("schema.sql") as f:
        sql = f.read().decode("utf8")
        db.create_schema(sql)
