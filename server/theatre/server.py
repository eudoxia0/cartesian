"""
This module implements the HTTP server.
"""
import json
import traceback
from datetime import datetime
import tempfile
import hashlib
import subprocess
from sqlite3 import Connection, Cursor
from typing import Optional, List, Set

from flask import make_response, Response, current_app, g
from theatre.error import CTError
from theatre.extract_links import extract_links
from theatre.flask_db import get_db
from theatre.db import (
    get_tex_macros,
    set_tex_macros,
    directory_exists,
    list_classes,
    get_class,
    create_class,
    class_exists,
    ClassPropertyRec,
    get_class_properties,
    create_class_property,
    PropertyType,
    file_exists,
    create_file,
    ClassRec,
    get_object_by_title,
    create_object,
    create_property,
    create_property_change,
    ObjectRec,
    list_objects,
    PropertyRec,
    list_object_properties,
    create_link,
    get_object_property,
    delete_links_from,
    edit_property, update_object, class_property_exists, delete_class_property,
)

from flask import (
    Blueprint,
    request,
)

from werkzeug.utils import secure_filename

from theatre.new_text import CTDocument
from theatre.prosemirror import parse_document, emit_document

from theatre.db import delete_class

bp = Blueprint("api", __name__, url_prefix="")


#
# Tex macro endpoints
#


@bp.route("/api/tex-macros", methods=["GET"])
def get_tex_macros_endpoint():
    """
    ```
    $> curl "http://localhost:5000/api/tex-macros"
    {
      "data": "test",
      "error": null,
    }
    ```
    """
    return {
        "error": None,
        "data": get_tex_macros(get_db()),
    }


@bp.route("/api/tex-macros", methods=["POST"])
def update_tex_macros():
    """
    ```
    $> curl -X POST "http://localhost:5000/api/tex-macros" -H 'Content-Type: application/json' -d '{ "macros": "test" }'
    {
      "data": null,
      "error": null,
    }
    ```
    """
    set_tex_macros(get_db(), request.json["macros"])
    return {
        "error": None,
        "data": None,
    }


#
# File endpoints
#


@bp.route("/api/files", methods=["GET"])
def list_files():
    """
    # File List Endpoint

    ## Description

    List all files.

    ## Output

    The `data` property is an array of objects with these properties:

    | Property | Type | Description |
    | `id` | Integer | The file ID. |
    | `filename` | String | The filename. |
    | `mime_type` | String | The MIME type of the file. |
    | `size` | Integer | The size of the file in bytes. |
    | `hash` | String | The SHA256 hash of the file contents. |
    | `created_at` | Timestamp | A Unix timestamp in milliseconds of the time when the file was uploaded. |

    ## Example

    ```
    $ curl "http://localhost:5000/api/files"
    {
      "data": [
        {
          "created_at": 1640537314080,
          "filename": "derp",
          "hash": "a68c20a73f6220485486191a7828d3cd36a6c4c796815d606f47c84aaedbd952",
          "id": 1,
          "mime_type": "image/png",
          "size": 1451277
        }
      ],
      "error": null,
    }
    ```
    """
    db = get_db()
    cur = db.cursor()
    results = cur.execute(
        """
        select
            id, filename, mime_type, size, hash, created_at
        from
            files
        order by
            created_at desc;
        """
    ).fetchall()
    return {
        "error": None,
        "data": [
            {
                "id": row[0],
                "filename": row[1],
                "mime_type": row[2],
                "size": row[3],
                "hash": row[4],
                "created_at": row[5],
            }
            for row in results
        ],
    }


@bp.route("/api/files/<int:file_id>", methods=["GET"])
def get_file(file_id: int):
    """
    # File Retrieval Endpoint

    ## Description

    Return the metadata associated with a file.

    ## URL Parameters

    - `id`: The integer ID of the file to retrieve.

    ## Output

    The `data` property is an object with these properties:

    | Property | Type | Description |
    | `id` | Integer | The file ID. |
    | `filename` | String | The filename. |
    | `mime_type` | String | The MIME type of the file. |
    | `size` | Integer | The size of the file in bytes. |
    | `hash` | String | The SHA256 hash of the file contents. |
    | `created_at` | Timestamp | A Unix timestamp in milliseconds of the time when the file was uploaded. |

    ## Example

    ```
    $ curl -v "http://localhost:5000/api/files/3/contents" -o file.png
    [...]
    < Content-Type: image/png
    [...]

    $ curl "http://localhost:5000/api/files/7"
    {
      "data": {
        "created_at": 1640539572771,
        "filename": "kustodiev.png",
        "hash": "a68c20a73f6220485486191a7828d3cd36a6c4c796815d606f47c84aaedbd952",
        "id": 7,
        "mime_type": "image/png",
        "size": 1451277
      },
      "error": null
    }

    $ curl "http://localhost:5000/api/files/8"
    {
      "data": null,
      "error": {
        "message": "The file with the ID '8' was not found in the database.",
        "title": "File Not Found"
      }
    }
    ```
    """
    db = get_db()
    cur = db.cursor()
    results = cur.execute(
        """
        select
            filename, mime_type, size, hash, created_at
        from
            files
        where
            id = :id;
        """,
        {
            "id": file_id,
        },
    ).fetchall()
    if results:
        row = results[0]
        return {
            "data": {
                "id": file_id,
                "filename": row[0],
                "mime_type": row[1],
                "size": row[2],
                "hash": row[3],
                "created_at": row[4],
            },
            "error": None,
        }
    else:
        raise CTError(
            "File Not Found",
            f"The file with the ID '{file_id}' was not found in the database.",
        )


@bp.route("/api/files/<int:file_id>/contents", methods=["GET"])
def file_contents(file_id: int):
    """
    # File Contents Endpoint

    ## Description

    Retrieve the byte stream of a file's data.

    ## URL Parameters

    - `id`: The integer ID of the file to retrieve.

    ## Output

    The byte stream of the underlying file, or a JSON document containing an error message.

    ## Example

    ```
    $ curl -v "http://localhost:5000/api/files/3/contents" -o file.png
    [...]
    < Content-Type: image/png
    [...]

    $ curl "http://localhost:5000/api/files/123/contents"
    {
      "data": null,
      "error": {
        "title": "File Not Found",
        "message": "The file with the ID '123' was not found in the database."
      }
    }
    ```
    """
    db = get_db()
    cur = db.cursor()
    results = cur.execute(
        """
        select
            mime_type, data
        from
            files
        where
            id = :id;
        """,
        {
            "id": file_id,
        },
    ).fetchall()
    if results:
        mime_type, blob = results[0]
        assert isinstance(mime_type, str)
        assert isinstance(blob, bytes)
        return Response(blob, mimetype=mime_type)
    else:
        raise CTError(
            "File Not Found",
            f"The file with the ID '{file_id}' was not found in the database.",
        )


@bp.route("/api/files", methods=["POST"])
def upload_file():
    """
    # File Upload Endpoint

    ## Description

    Upload a file.

    ## Request Body

    The POST body must be the file contents.

    ## Output

    The `data` property is an object with these properties:

    | Property | Type | Description |
    | `id` | Integer | The file ID. |
    | `filename` | String | The filename. |
    | `mime_type` | String | The MIME type of the file. |
    | `size` | Integer | The size of the file in bytes. |
    | `hash` | String | The SHA256 hash of the file contents. |
    | `created_at` | Timestamp | A Unix timestamp in milliseconds of the time when the file was uploaded. |

    ## Example

    ```
    $ curl -X POST "http://localhost:5000/api/files" -F "data=@/home/eudoxia/pic.png"
    {
      "data": {
        "created_at": 1640536346827,
        "filename": "pic.png",
        "hash": "a68c20a73f6220485486191a7828d3cd36a6c4c796815d606f47c84aaedbd952",
        "id": 6,
        "size": 1451277
      },
      "error": null
    }
    ```

    """
    # Extract file data, put it in a temporary file.
    file_data = request.files["data"]
    filename: str = secure_filename(file_data.filename)
    blob = file_data.read()
    assert isinstance(blob, bytes)
    # Store the file in the database
    mime_type: str = determine_mime_type(blob)
    size: int = len(blob)
    sha256hash: str = hashlib.sha256(blob).hexdigest()
    created_at: int = now_millis()
    db = get_db()
    file_id: int = create_file(
        conn=db,
        filename=filename,
        mime_type=mime_type,
        size=size,
        hash=sha256hash,
        created_at=created_at,
        blob=blob,
    )
    # Return file data
    return {
        "data": {
            "id": file_id,
            "filename": filename,
            "mime_type": mime_type,
            "size": size,
            "hash": sha256hash,
            "created_at": created_at,
        },
        "error": None,
    }


@bp.route("/api/files/<int:file_id>", methods=["DELETE"])
def delete_file(file_id: int):
    """
    # File Deletion Endpoint

    ## Description

    Endpoint to delete a file.

    ## URL Parameters

    - `id`: The integer ID of the file to retrieve.

    ## Output

    The `data` property is a boolean that is `true` on success`, and `null` otherwise.

    ## Example

    ```
    $  curl -X DELETE "http://localhost:5000/api/files/8"
    {
      "data": true,
      "error": null
    }

    $> curl -X DELETE "http://localhost:5000/api/files/8"
    {
      "data": null,
      "error": {
        "message": "The file with the ID '8' was not found in the database.",
        "title": "File Not Found"
      }
    }
    ```

    """
    db: Connection = get_db()
    cur: Cursor = db.cursor()
    cur.execute(
        """
        select
            id
        from
            files
        where
            id = :id;
        """,
        {
            "id": file_id,
        },
    )
    if cur.fetchall():
        cur.execute(
            """
            delete from
                files
            where
                id = :id
            """,
            {
                "id": file_id,
            },
        )
        db.commit()
        return {
            "data": True,
            "error": None,
        }
    else:
        raise CTError(
            "File Not Found",
            f"The file with the ID '{file_id}' was not found in the database.",
        )


#
# Directory endpoints
#


@bp.route("/api/directories", methods=["GET"])
def list_directories():
    db = get_db()
    cur = db.cursor()
    results = cur.execute(
        """
        select
            id, title, icon_emoji, parent_id, created_at
        from
            directories;
        """
    ).fetchall()
    return {
        "error": None,
        "data": [
            {
                "id": row["id"],
                "title": row["title"],
                "icon_emoji": row["icon_emoji"],
                "parent_id": row["parent_id"],
                "created_at": row["created_at"],
            }
            for row in results
        ],
    }


@bp.route("/api/directories/<int:dir_id>", methods=["GET"])
def get_directory(dir_id: int):
    db = get_db()
    cur = db.cursor()
    results = cur.execute(
        """
        select
            title, icon_emoji, parent_id, created_at
        from
            directories;
        where
            id = :id;
        """,
        {
            "id": dir_id,
        },
    ).fetchall()
    if results:
        row = results[0]
        return {
            "data": {
                "id": dir_id,
                "title": row["title"],
                "icon_emoji": row["icon_emoji"],
                "parent_id": row["parent_id"],
                "created_at": row["created_at"],
            },
            "error": None,
        }
    else:
        raise CTError(
            "Directory Not Found",
            f"The directory with the ID '{dir_id}' was not found in the database.",
        )


@bp.route("/api/directories", methods=["POST"])
def new_directory():
    form: dict = request.json
    title: str = form["title"].strip()
    icon_emoji: str = form["icon_emoji"].strip()
    parent_id: Optional[int] = form["parent_id"]
    db = get_db()
    cur = db.cursor()
    if parent_id:
        if not directory_exists(db, parent_id):
            raise CTError(
                "Directory Not Found",
                f"The directory with the ID '{parent_id}' was not found in the database.",
            )
    created_at: int = now_millis()
    results = cur.execute(
        """
        insert into directories
            (title, icon_emoji, parent_id, created_at)
        values
            (:title, :icon_emoji, :parent_id, :created_at)
        returning id;
        """,
        {
            "title": title,
            "icon_emoji": icon_emoji,
            "parent_id": parent_id,
            "created_at": created_at,
        },
    )
    dir_id: int = list(results)[0][0]
    db.commit()
    # Return file data
    return {
        "data": {
            "id": dir_id,
            "title": title,
            "icon_emoji": icon_emoji,
            "parent_id": parent_id,
            "created_at": created_at,
        },
        "error": None,
    }


@bp.route("/api/directories/<int:dir_id>", methods=["POST"])
def edit_directory(dir_id: int):
    form: dict = request.json
    title: str = form["title"].strip()
    icon_emoji: str = form["icon_emoji"].strip()
    parent_id: Optional[int] = form["parent_id"]
    db = get_db()
    cur = db.cursor()
    if parent_id:
        if not directory_exists(db, parent_id):
            raise CTError(
                "Directory Not Found",
                f"The directory with the ID '{parent_id}' was not found in the database.",
            )
    cur.execute(
        """
        update directories
        set
            title = :title,
            icon_emoji = :icon_emoji,
            parent_id = :parent_id
        where
            id = :id;
        """,
        {
            "title": title,
            "icon_emoji": icon_emoji,
            "parent_id": parent_id,
            "id": dir_id,
        },
    )
    db.commit()
    # Return directory data
    return {
        "data": {
            "id": dir_id,
            "title": title,
            "icon_emoji": icon_emoji,
            "parent_id": parent_id,
        },
        "error": None,
    }


@bp.route("/api/directories/<int:dir_id>", methods=["DELETE"])
def delete_directory(dir_id: int):
    db = get_db()
    cur = db.cursor()
    results = cur.execute(
        """
        select
            id
        from
            files
        where
            id = :id;
        """,
        {
            "id": dir_id,
        },
    ).fetchall()
    if results:
        cur.execute(
            """
            delete from
                directories
            where
                id = :id
            """,
            {
                "id": dir_id,
            },
        )
        db.commit()
        return {
            "data": True,
            "error": None,
        }
    else:
        raise CTError(
            "Directory Not Found",
            f"The directory with the ID '{dir_id}' was not found in the database.",
        )


#
# Class endpoints
#


@bp.route("/api/classes", methods=["GET"])
def list_classes_endpoint():
    conn: Connection = get_db()
    records: List[ClassRec] = list_classes(conn)
    jsons: List[dict] = [rec.to_json() for rec in records]
    for rec in jsons:
        rec["properties"] = [p.to_json() for p in get_class_properties(conn, rec["id"])]
    return {
        "error": None,
        "data": jsons,
    }


@bp.route("/api/classes/<int:cls_id>", methods=["GET"])
def get_class_endpoint(cls_id: int):
    conn: Connection = get_db()
    rec: Optional[ClassRec] = get_class(conn, cls_id)
    if rec is not None:
        obj = rec.to_json()
        obj["properties"] = [p.to_json() for p in get_class_properties(conn, rec.id)]
        return {
            "data": obj,
            "error": None,
        }
    else:
        raise CTError(
            "Class Not Found",
            f"The class with the ID '{cls_id}' was not found in the database.",
        )


@bp.route("/api/classes", methods=["POST"])
def new_class_endpoint():
    conn: Connection = get_db()
    form: dict = request.json
    title: str = form["title"].strip()
    icon_emoji: str = form["icon_emoji"].strip()
    rec: ClassRec = create_class(conn, title, icon_emoji)
    obj = rec.to_json()
    obj["properties"] = [p.to_json() for p in get_class_properties(conn, rec.id)]
    return {
        "data": obj,
        "error": None,
    }


@bp.route("/api/classes/<int:cls_id>/properties", methods=["GET"])
def get_class_properties_endpoint(cls_id: int):
    conn: Connection = get_db()
    if not class_exists(conn, cls_id):
        raise CTError(
            "Class Not Found",
            f"The class with the ID '{cls_id}' was not found in the database.",
        )
    else:
        records: List[ClassPropertyRec] = get_class_properties(conn, cls_id)
        return {
            "error": None,
            "data": [rec.to_json() for rec in records],
        }


@bp.route("/api/classes/<int:cls_id>/properties", methods=["POST"])
def new_class_property_endpoint(cls_id: int):
    conn: Connection = get_db()
    if not class_exists(conn, cls_id):
        raise CTError(
            "Class Not Found",
            f"The class with the ID '{cls_id}' was not found in the database.",
        )
    else:
        form: dict = request.json
        title: str = form["title"].strip()
        prop_ty: PropertyType = PropertyType(form["type"])
        description: str = form["description"].strip()
        rec: ClassPropertyRec = create_class_property(
            conn=conn,
            class_id=cls_id,
            title=title,
            prop_type=prop_ty,
            description=description,
        )
        return {
            "error": None,
            "data": rec.to_json(),
        }

@bp.route("/api/classes/<int:cls_id>/properties/<int:cls_prop_id>", methods=["DELETE"])
def delete_class_property_endpoint(cls_id: int, cls_prop_id: int):
    conn: Connection = get_db()
    if not class_exists(conn, cls_id):
        raise CTError(
            "Class Not Found",
            f"The class with the ID '{cls_id}' was not found in the database.",
        )
    if not class_property_exists(conn, cls_prop_id):
        raise CTError(
            "Class Property Not Found",
            f"The class property with the ID '{cls_prop_id}' was not found in the database.",
        )
    else:
        delete_class_property(conn, cls_prop_id)
        return {
            "data": None,
            "error": None,
        }


@bp.route("/api/classes/<int:cls_id>", methods=["DELETE"])
def delete_class_endpoint(cls_id: int):
    conn: Connection = get_db()
    rec: Optional[ClassRec] = get_class(conn, cls_id)
    if rec is not None:
        delete_class(conn, rec.id)
        return {
            "data": None,
            "error": None,
        }
    else:
        raise CTError(
            "Class Not Found",
            f"The class with the ID '{cls_id}' was not found in the database.",
        )

#
# Object endpoints
#


@bp.route("/api/objects", methods=["POST"])
def new_object_endpoint():
    # Parse input
    form: dict = request.json
    title: str = form["title"].strip()
    class_id: int = form["class_id"]
    directory_id: Optional[int] = form["directory_id"]
    icon_emoji: str = form["icon_emoji"].strip()
    property_values: dict = form["values"]
    # If an object with this title exists, reject it
    conn: Connection = get_db()
    if get_object_by_title(conn, title) is not None:
        raise CTError(
            "Duplicate Title",
            f"An object with the title '{title}' already exists.",
        )
    # Find the class
    cls: Optional[ClassRec] = get_class(conn, class_id)
    if cls is None:
        raise CTError(
            "Class Not Found",
            f"The class with the ID '{id}' was not found in the database.",
        )

    # Find the directory, if any
    if directory_id is not None:
        if not directory_exists(conn, directory_id):
            raise CTError(
                "Directory Not Found",
                f"The directory with the ID '{id}' was not found in the database.",
            )
    # Find the set of class properties
    cls_props: List[ClassPropertyRec] = get_class_properties(conn, class_id)
    # Check: the dictionary of values provided by the client has all the keys we expect
    input_keys: Set[str] = set(property_values.keys())
    expected_keys: Set[str] = set([prop.title for prop in cls_props])
    for expected_key in expected_keys:
        if expected_key not in input_keys:
            raise CTError(
                "Property Not Provided",
                f"No value provided for the property '{expected_key}'.",
            )
    # Create the object
    created_at: int = now_millis()
    print(created_at)
    object_id: int = create_object(
        conn=conn,
        title=title,
        class_id=class_id,
        directory_id=directory_id,
        icon_emoji=icon_emoji,
        created_at=created_at,
        modified_at=created_at,
    )
    # Create the properties
    for prop_title, prop_value in property_values.items():
        # Find the corresponding class property
        cls_prop: ClassPropertyRec = [
            prop for prop in cls_props if prop.title == prop_title
        ][0]
        # Dispatch on the type of the class property
        value_text: Optional[str]
        value_file: Optional[int]
        create_link_set: Set[str] = set()
        if cls_prop.type == PropertyType.PROP_RICH_TEXT:
            if prop_value is None:
                # Make this value unbound.
                value_text = None
                value_file = None
            else:
                assert isinstance(prop_value, str)
                # The value should be a JSON string of a ProseMirror document.
                doc: CTDocument = parse_document(json.loads(prop_value))
                # If parsing succeeded, serialize the document.
                json_value: dict = emit_document(doc)
                json_string: str = json.dumps(json_value)
                # Set the values
                value_text = json_string
                value_file = None
                # Find the set of links to create
                create_link_set: Set[str] = extract_links(doc)
        elif cls_prop.type == PropertyType.PROP_FILE:
            if prop_value is None:
                # Make this value unbound.
                value_text = None
                value_file = None
            else:
                # The value should be an integer ID of a file.
                assert isinstance(prop_value, int)
                # Find the file with this ID
                if not file_exists(conn, prop_value):
                    raise CTError(
                        "File Not Found",
                        f"The file with the ID '{prop_value}' was not found in the database.",
                    )
                # Set the values
                value_text = None
                value_file = prop_value
        else:
            raise CTError(
                "Unknown Property Type",
                f"I don't know what to do with the property '{prop_title}', which has type '{cls_prop.type}'.",
            )
        # Create the property in the database, and the initial property change object.
        prop_id: int = create_property(
            conn=conn,
            class_prop_id=cls_prop.id,
            class_prop_title=prop_title,
            class_prop_type=cls_prop.type,
            object_id=object_id,
            value_text=value_text,
            value_file=value_file,
        )
        create_property_change(
            conn=conn,
            object_id=object_id,
            prop_id=prop_id,
            prop_title=prop_title,
            created_at=created_at,
            value_text=value_text,
            value_file=value_file,
        )
        # Create links from this property to other objects
        for link_title in create_link_set:
            links_to: Optional[ObjectRec] = get_object_by_title(conn, link_title)
            if links_to is not None:
                create_link(
                    conn=conn, from_property_id=prop_id, to_object_id=links_to.id
                )
    # Return
    obj: ObjectRec = ObjectRec(
        id=object_id,
        title=title,
        class_id=class_id,
        directory_id=directory_id,
        icon_emoji=icon_emoji,
        created_at=created_at,
        modified_at=created_at,
    )
    return {
        "data": obj.to_json(),
        "error": None,
    }


@bp.route("/api/objects", methods=["GET"])
def list_objects_endpoint():
    return {
        "error": None,
        "data": [obj.to_json() for obj in list_objects(get_db())],
    }


@bp.route("/api/objects/<path:title>", methods=["GET"])
def object_details(title: str):
    conn: Connection = get_db()
    obj: Optional[ObjectRec] = get_object_by_title(conn, title)
    if obj is not None:
        obj_dict: dict = obj.to_json()
        props: List[PropertyRec] = list_object_properties(conn=conn, object_id=obj.id)
        obj_dict["properties"] = [prop.to_json() for prop in props]
        return {
            "error": None,
            "data": obj_dict,
        }
    else:
        raise CTError(
            "Object Not Found",
            f"The object with the title '{title}' was not found in the database.",
        )


@bp.route("/api/objects/<path:title>", methods=["POST"])
def edit_object_endpoint(title: str):
    # Retrieve the object
    conn: Connection = get_db()
    obj: Optional[ObjectRec] = get_object_by_title(conn, title)
    if obj is None:
        raise CTError(
            "Object Not Found",
            f"The object with the title '{title}' was not found in the database.",
        )
    # Parse the input
    form: dict = request.json
    new_title: str = form["title"].strip()
    new_directory_id: Optional[int] = form["directory_id"]
    new_icon_emoji: str = form["icon_emoji"].strip()
    property_values: dict = form["values"]

    # Find the directory, if any
    if new_directory_id is not None:
        if not directory_exists(conn, new_directory_id):
            raise CTError(
                "Directory Not Found",
                f"The directory with the ID '{id}' was not found in the database.",
            )

    # Find the set of class properties
    cls_props: List[ClassPropertyRec] = get_class_properties(conn, obj.class_id)

    # Mark modification time
    modified_at: int = now_millis()

    # Edit the object
    update_object(
        conn=conn,
        obj=obj,
        new_title=new_title,
        new_directory_id=new_directory_id,
        new_icon_emoji=new_icon_emoji,
        modified_at=modified_at
    )

    # Change the provided values
    for prop_title, prop_value in property_values.items():
        # Find the corresponding class property
        cls_prop: ClassPropertyRec = [
            prop for prop in cls_props if prop.title == prop_title
        ][0]
        # Find the existing property
        existing_prop: Optional[PropertyRec] = get_object_property(
            conn=conn, object_id=obj.id, class_prop_id=cls_prop.id
        )
        if existing_prop is None:
            raise CTError(
                "No Existing Property",
                f"Can't edit a property that doens't exist: '{prop_title}', which has type '{cls_prop.type}'.",
            )
        # Dispatch on the type of the class property
        value_text: Optional[str]
        value_file: Optional[int]
        create_link_set: Set[str] = set()
        if cls_prop.type == PropertyType.PROP_RICH_TEXT:
            if prop_value is None:
                # Make this value unbound.
                value_text = None
                value_file = None
            else:
                assert isinstance(prop_value, str)
                # The value should be a JSON string of a ProseMirror document.
                doc: CTDocument = parse_document(json.loads(prop_value))
                # If parsing succeeded, serialize the document.
                json_value: dict = emit_document(doc)
                json_string: str = json.dumps(json_value)
                # Set the values
                value_text = json_string
                value_file = None
                create_link_set = extract_links(doc)
        elif cls_prop.type == PropertyType.PROP_FILE:
            if prop_value is None:
                # Make this value unbound.
                value_text = None
                value_file = None
            else:
                # The value should be an integer ID of a file.
                assert isinstance(prop_value, int)
                # Find the file with this ID
                if not file_exists(conn, prop_value):
                    raise CTError(
                        "File Not Found",
                        f"The file with the ID '{prop_value}' was not found in the database.",
                    )
                # Set the values
                value_text = None
                value_file = prop_value
        else:
            raise CTError(
                "Unknown Property Type",
                f"I don't know what to do with the property '{prop_title}', which has type '{cls_prop.type}'.",
            )
        # Edit the property
        edit_property(
            conn=conn,
            property_id=existing_prop.id,
            value_text=value_text,
            value_file=value_file,
        )
        # Create the property change
        create_property_change(
            conn=conn,
            object_id=obj.id,
            prop_id=existing_prop.id,
            prop_title=prop_title,
            created_at=modified_at,
            value_text=value_text,
            value_file=value_file,
        )
        # Delete old links from this property to any other object
        delete_links_from(conn=conn, property_id=existing_prop.id)
        # Create new links from this property
        for link_title in create_link_set:
            links_to: Optional[ObjectRec] = get_object_by_title(conn, link_title)
            if links_to is not None:
                create_link(
                    conn=conn,
                    from_property_id=existing_prop.id,
                    to_object_id=links_to.id,
                )
    # Return
    obj: Optional[ObjectRec] = get_object_by_title(conn, new_title)
    assert obj is not None
    return {
        "data": obj.to_json(),
        "error": None,
    }


#
# Error handling
#


@bp.errorhandler(CTError)
def handle_ct_error(e: CTError):
    """
    Error handler for the CTError class.
    """
    if not current_app.config["QUIET"]:
        current_app.logger.error(e)
        print(traceback.format_exc())
    resp = make_response(
        {
            "data": None,
            "error": {
                "title": e.title,
                "message": e.message,
            },
        },
        501,
    )
    return resp


@bp.errorhandler(Exception)
def handle_ct_error(e: Exception):
    """
    Error handler for all other errors.
    """
    if not current_app.config["QUIET"]:
        current_app.logger.error(e)
        print(traceback.format_exc())
    resp = make_response(
        {
            "data": None,
            "error": {
                "title": "Internal Error",
                "message": "An unknown internal error has occured.",
            },
        },
        501,
    )
    return resp


# Utils


def now_millis() -> int:
    return datetime_to_millis(datetime.now())


def datetime_to_millis(stamp: datetime) -> int:
    """
    Convert a datetime to Unix time in milliseconds.
    """
    return int(stamp.timestamp() * 1000)


def millis_to_datetime(millis: int) -> datetime:
    """
    Convert a Unix time in milliseconds to a datetime.
    """
    return datetime.fromtimestamp(float(millis) / 1000)


def determine_mime_type(blob: bytes) -> str:
    """
    Determine the MIME type of a byte stream.
    """
    # Write the contents to a temporary file
    stream = tempfile.NamedTemporaryFile()
    stream.write(blob)
    stream.flush()
    # Shell out to the `file` tool to extract the MIME type.
    mime_type: str = (
        subprocess.check_output(["file", "-b", "--mime-type", stream.name])
        .decode("utf-8")
        .strip()
    )
    # Close the stream, deleting the file.
    stream.close()
    return mime_type


def get_query_param(req, name: str) -> str:
    try:
        value = req.args.get(name).strip()
        assert isinstance(value, str)
        assert len(value.strip()) > 0
        return value
    except Exception:
        raise CTError(
            "Bad Request",
            f"Missing '{name}' query parameter when trying to upload a file.",
        )


# Public interface


@bp.after_request
def apply_cors(response):
    response.headers["Access-Control-Allow-Origin"] = "*"
    response.headers["Access-Control-Allow-Methods"] = "*"
    response.headers["Access-Control-Allow-Headers"] = "*"
    response.headers["Access-Control-Max-Age"] = 1728000
    return response
