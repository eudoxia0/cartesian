import json
import unittest
from datetime import datetime
from sqlite3 import Connection
from typing import List

import pytz as pytz

from test.api.helpers import DatabaseMixin
from theatre.flask_db import get_db
from theatre.db import (
    create_class,
    ClassRec,
    create_class_property,
    ClassPropertyRec,
    PropertyType,
    list_object_properties,
    PropertyRec,
    PropertyChangeRec,
    get_property_changes,
)
from freezegun import freeze_time

from theatre.new_text import CTDocument, Paragraph, TextFragment
from theatre.prosemirror import emit_document
from theatre.server import datetime_to_millis

TIMESTAMP: datetime = datetime(year=2022, month=1, day=1, tzinfo=pytz.UTC)


class ObjectApiTestCase(DatabaseMixin, unittest.TestCase):
    """
    Tests of the object API.
    """

    @freeze_time(TIMESTAMP)
    def test_successfully_create_object(self):
        """
        Test we can successfully create an object.
        """
        # Test data: create a simple class with a single text field.
        conn: Connection = get_db()
        cls: ClassRec = create_class(conn, title="Note", icon_emoji="")
        cls_prop: ClassPropertyRec = create_class_property(
            conn,
            class_id=cls.id,
            title="Text",
            description="The textual contents of the note.",
            prop_type=PropertyType.PROP_RICH_TEXT,
        )
        doc: CTDocument = CTDocument(
            children=[
                Paragraph(
                    children=[
                        TextFragment(
                            contents="This is just a bit of text.",
                            emphasized=False,
                            bold=False,
                            code=False,
                        )
                    ]
                )
            ]
        )
        doc_json: dict = emit_document(doc)
        note_title: str = "My New Note"
        # Request
        response = self.client.post(
            "/api/objects",
            json={
                "title": note_title,
                "class_id": cls.id,
                "directory_id": None,
                "icon_emoji": "",
                "values": {"Text": json.dumps(doc_json)},
            },
        )
        # Assertions
        self.assertEqual(response.status_code, 200)
        self.assertEqual(
            response.json,
            {
                "data": {
                    "id": 1,
                    "title": note_title,
                    "class_id": cls.id,
                    "directory_id": None,
                    "icon_emoji": "",
                    "created_at": datetime_to_millis(TIMESTAMP),
                    "modified_at": datetime_to_millis(TIMESTAMP),
                },
                "error": None,
            },
        )
        props: List[PropertyRec] = list_object_properties(conn=conn, object_id=1)
        self.assertEqual(
            props,
            [
                PropertyRec(
                    id=1,
                    class_prop_id=cls_prop.id,
                    class_prop_title="Text",
                    class_prop_type=cls_prop.type,
                    object_id=1,
                    value_text=json.dumps(doc_json),
                    value_file=None,
                )
            ],
        )
        changes: List[PropertyChangeRec] = get_property_changes(conn=conn, prop_id=1)
        self.assertEqual(
            changes,
            [
                PropertyChangeRec(
                    id=1,
                    object_id=1,
                    prop_id=1,
                    prop_title="Text",
                    created_at=datetime_to_millis(TIMESTAMP),
                    value_text=json.dumps(doc_json),
                    value_file=None,
                )
            ],
        )
        # Test object listing
        response = self.client.get("/api/objects")
        self.assertEqual(response.status_code, 200)
        self.assertEqual(
            response.json,
            {
                "data": [
                    {
                        "id": 1,
                        "title": note_title,
                        "class_id": cls.id,
                        "directory_id": None,
                        "icon_emoji": "",
                        "created_at": datetime_to_millis(TIMESTAMP),
                        "modified_at": datetime_to_millis(TIMESTAMP),
                    },
                ],
                "error": None,
            },
        )
        # Test object retrieval
        response = self.client.get(f"/api/objects/{note_title}")
        self.assertEqual(response.status_code, 200)
        self.assertEqual(
            response.json,
            {
                "data": {
                    "class_id": 1,
                    "created_at": 1640995200000,
                    "directory_id": None,
                    "icon_emoji": "",
                    "id": 1,
                    "modified_at": 1640995200000,
                    "properties": [
                        {
                            "class_prop_id": 1,
                            "class_prop_title": "Text",
                            "class_prop_type": "PROP_RICH_TEXT",
                            "id": 1,
                            "object_id": 1,
                            "value_file": None,
                            "value_text": '{"type": "doc", "content": [{"type": "paragraph", "content": [{"type": "text", "marks": [], "text": "This is just a bit of text."}]}]}',
                        }
                    ],
                    "title": "My New Note",
                },
                "error": None,
            },
        )
