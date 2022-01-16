"""
This module is for creating the Flask app.
"""
from flask import Flask
from theatre.server import bp
from theatre.flask_db import close_db


def create_app(database_path: str, testing: bool = False) -> object:
    app = Flask(__name__)
    app.config["DB_PATH"] = database_path
    app.config["QUIET"] = testing
    app.teardown_appcontext(close_db)
    app.register_blueprint(bp)
    return app
