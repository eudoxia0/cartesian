import hashlib
import io
import unittest
from datetime import datetime

import pytz as pytz

from test.api.helpers import DatabaseMixin
from theatre.flask_db import get_db
from theatre.db import (
    create_file,
)
from freezegun import freeze_time

from theatre.server import datetime_to_millis

TIMESTAMP: datetime = datetime(year=2022, month=1, day=1, tzinfo=pytz.UTC)


class FileApiTestCase(DatabaseMixin, unittest.TestCase):
    """
    Tests of the files API.
    """

    # /api/files endpoint

    def test_no_files(self):
        """
        Test the /api/files endpoint with no files.
        """
        # Request
        response = self.client.get("/api/files")
        # Assertions
        self.assertEqual(response.status_code, 200)
        self.assertEqual(
            response.json,
            {
                "data": [],
                "error": None,
            },
        )

    def test_one_file(self):
        """
        Test the /api/files endpoint with one file.
        """
        # Test data
        kwargs: dict = {
            "filename": "test.jpg",
            "mime_type": "text/plain",
            "size": 123,
            "hash": "0x123",
            "created_at": 123,
            "blob": b"Hello, world!",
        }
        file_id: int = create_file(
            conn=get_db(),
            **kwargs,
        )
        expected: dict = kwargs.copy()
        expected.pop("blob")
        expected["id"] = file_id
        # Request
        response = self.client.get("/api/files")
        # Assertions
        self.assertEqual(response.status_code, 200)
        self.assertEqual(
            response.json,
            {
                "data": [expected],
                "error": None,
            },
        )

    @freeze_time(TIMESTAMP)
    def test_upload_file(self):
        """
        Test uploading a file.
        """
        # Test data
        filename: str = "test.txt"
        blob: bytes = b"Hello, world!"
        sha256hash: str = hashlib.sha256(blob).hexdigest()
        # Request
        data: dict = {
            "data": (io.BytesIO(blob), filename),
        }
        response = self.client.post(
            "/api/files", data=data, content_type="multipart/form-data"
        )
        # Assertions
        self.assertEqual(response.status_code, 200)
        self.assertEqual(
            response.json,
            {
                "data": {
                    "id": 1,
                    "filename": filename,
                    "mime_type": "text/plain",
                    "size": 13,
                    "hash": sha256hash,
                    "created_at": datetime_to_millis(TIMESTAMP),
                },
                "error": None,
            },
        )

    # /api/files/{id} endpoint

    def test_retrieve_one_file(self):
        """
        Test the /api/files/{id} endpoint with one file.
        """
        # Test data
        kwargs: dict = {
            "filename": "test.jpg",
            "mime_type": "text/plain",
            "size": 123,
            "hash": "0x123",
            "created_at": 123,
            "blob": b"Hello, world!",
        }
        file_id: int = create_file(
            conn=get_db(),
            **kwargs,
        )
        expected: dict = kwargs.copy()
        expected.pop("blob")
        expected["id"] = file_id
        # Request
        response = self.client.get(f"/api/files/{file_id}")
        # Assertions
        self.assertEqual(response.status_code, 200)
        self.assertEqual(
            response.json,
            {
                "data": expected,
                "error": None,
            },
        )

    def test_wrong_file(self):
        """
        Test the /api/files/{id} endpoint with an invalid ID.
        """
        # Test data
        file_id: int = 123
        # Request
        response = self.client.get(f"/api/files/{file_id}")
        # Assertions
        self.assertEqual(response.status_code, 501)
        self.assertEqual(
            response.json,
            {
                "data": None,
                "error": {
                    "title": "File Not Found",
                    "message": f"The file with the ID '{file_id}' was not found in the database.",
                },
            },
        )

    # /api/files/{id}/contents endpoint

    def test_file_contents(self):
        """
        Test the /api/files/{id}/contents endpoint.
        """
        # Test data
        kwargs: dict = {
            "filename": "test.jpg",
            "mime_type": "text/plain",
            "size": 123,
            "hash": "0x123",
            "created_at": 123,
            "blob": b"Hello, world!",
        }
        file_id: int = create_file(
            conn=get_db(),
            **kwargs,
        )
        # Request
        response = self.client.get(f"/api/files/{file_id}/contents")
        # Assertions
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.content_type, "text/plain; charset=utf-8")
        self.assertEqual(response.data, kwargs["blob"])

    # DELETE /api/files/{id}

    def test_file_deletion(self):
        """
        Test the /api/files/{id} deletion endpoint.
        """
        # Test data
        kwargs: dict = {
            "filename": "test.jpg",
            "mime_type": "text/plain",
            "size": 123,
            "hash": "0x123",
            "created_at": 123,
            "blob": b"Hello, world!",
        }
        file_id: int = create_file(
            conn=get_db(),
            **kwargs,
        )
        # Request
        response = self.client.delete(f"/api/files/{file_id}")
        # Assertions
        self.assertEqual(response.status_code, 200)
        self.assertEqual(
            response.json,
            {
                "data": True,
                "error": None,
            },
        )
