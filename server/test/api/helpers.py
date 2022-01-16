from flask.testing import FlaskClient

from theatre.app import create_app
from theatre.flask_db import init_db


class DatabaseMixin(object):
    def setUp(self):
        super().setUp()
        self.app = create_app(database_path=":memory:", testing=True)
        self.ctx = self.app.app_context()
        self.ctx.__enter__()
        init_db()
        self.client: FlaskClient = self.app.test_client()

    def tearDown(self):
        self.ctx.__exit__(None, None, None)
