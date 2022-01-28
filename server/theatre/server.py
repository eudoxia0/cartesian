"""
This module implements the HTTP server.
"""
import json
import traceback
from datetime import datetime
import tempfile
import hashlib
import subprocess
from typing import Optional, List, Set, Tuple

from flask import make_response, Response, current_app, g
from theatre.error import (
    CTError,
    file_not_found,
    directory_not_found,
    class_not_found,
    class_prop_not_found,
    object_not_found,
)
from theatre.extract_links import extract_links
from theatre.flask_db import get_db

from flask import (
    Blueprint,
    request,
)

from werkzeug.utils import secure_filename

from theatre.new_db import (
    Database,
    FileRec,
    DirRec,
    ClassDetailRec,
    ClassPropRec,
    ClassRec,
    PropertyType,
    ObjectRec,
    PropRec,
    ObjectDetailRec,
)
from theatre.new_text import CTDocument
from theatre.prosemirror import parse_document, emit_document

bp = Blueprint("api", __name__, url_prefix="")


#
# File endpoints
#


@bp.route("/api/files", methods=["GET"])
def list_files():
    return {
        "error": None,
        "data": [rec.to_json() for rec in get_db().list_files()],
    }


@bp.route("/api/files/<int:file_id>", methods=["GET"])
def get_file(file_id: int):
    file: FileRec | None = get_db().get_file_by_id(file_id)
    if file is not None:
        return {
            "data": file.to_json(),
            "error": None,
        }
    else:
        raise file_not_found(file_id)


@bp.route("/api/files/<int:file_id>/contents", methods=["GET"])
def file_contents(file_id: int):
    data: Tuple[str, bytes] | None = get_db().get_file_data(file_id)
    if data is not None:
        mime_type, blob = data
        return Response(blob, mimetype=mime_type)
    else:
        raise file_not_found(file_id)


@bp.route("/api/files", methods=["POST"])
def upload_file():
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
    file_id: int = get_db().create_file(
        filename=filename,
        mime_type=mime_type,
        size=size,
        sha256hash=sha256hash,
        created_at=created_at,
        blob=blob,
    )
    rec: FileRec = FileRec(
        id=file_id,
        filename=filename,
        mime_type=mime_type,
        size=size,
        hash=sha256hash,
        created_at=created_at,
    )
    # Return file data
    return {
        "data": rec.to_json(),
        "error": None,
    }


@bp.route("/api/files/<int:file_id>", methods=["DELETE"])
def delete_file(file_id: int):
    db: Database = get_db()
    if db.file_exists(file_id):
        db.delete_file(file_id)
        return {
            "data": True,
            "error": None,
        }
    else:
        raise file_not_found(file_id)


#
# Directory endpoints
#


@bp.route("/api/directories", methods=["GET"])
def list_directories():
    return {
        "error": None,
        "data": [rec.to_json() for rec in get_db().list_directories()],
    }


@bp.route("/api/directories/<int:dir_id>", methods=["GET"])
def get_directory(dir_id: int):
    dir_rec: DirRec | None = get_db().get_directory(dir_id)
    if dir_rec is not None:
        return {
            "data": dir_rec.to_json(),
            "error": None,
        }
    else:
        raise directory_not_found(dir_id)


@bp.route("/api/directories", methods=["POST"])
def new_directory():
    form: dict = request.json
    title: str = form["title"].strip()
    icon_emoji: str = form["icon_emoji"].strip()
    parent_id: Optional[int] = form["parent_id"]
    db: Database = get_db()
    if parent_id:
        if not db.directory_exists(parent_id):
            raise directory_not_found(parent_id)
    created_at: int = now_millis()
    dir_id: int = db.create_directory(
        title=title,
        icon_emoji=icon_emoji,
        cover_id=None,
        parent_id=parent_id,
        created_at=created_at,
    )
    dir_rec: DirRec = DirRec(
        id=dir_id,
        title=title,
        icon_emoji=icon_emoji,
        cover_id=None,
        parent_id=parent_id,
        created_at=created_at,
    )
    # Return directory data
    return {
        "data": dir_rec.to_json(),
        "error": None,
    }


@bp.route("/api/directories/<int:dir_id>", methods=["POST"])
def edit_directory(dir_id: int):
    form: dict = request.json
    title: str = form["title"].strip()
    icon_emoji: str = form["icon_emoji"].strip()
    parent_id: Optional[int] = form["parent_id"]
    db: Database = get_db()
    if parent_id:
        if not db.directory_exists(parent_id):
            raise directory_not_found(parent_id)
    db.edit_directory(
        dir_id=dir_id,
        title=title,
        icon_emoji=icon_emoji,
        cover_id=None,
        parent_id=parent_id,
    )
    # Return directory data
    return {
        "data": db.get_directory(dir_id).to_json(),
        "error": None,
    }


@bp.route("/api/directories/<int:dir_id>", methods=["DELETE"])
def delete_directory(dir_id: int):
    db: Database = get_db()
    if db.directory_exists(dir_id):
        db.delete_directory(dir_id)
        return {
            "data": True,
            "error": None,
        }
    else:
        raise directory_not_found(dir_id)


@bp.route("/api/directories/<int:dir_id>/objects", methods=["GET"])
def list_objects_in_directory_endpoint(dir_id: int):
    return {
        "data": [
            obj.to_json() for obj in get_db().list_objects_in_directory(dir_id=dir_id)
        ],
        "error": None,
    }


@bp.route("/api/uncategorized-objects", methods=["GET"])
def list_uncategorized_objects_endpoint():
    return {
        "data": [obj.to_json() for obj in get_db().list_uncategorized_objects()],
        "error": None,
    }


#
# Class endpoints
#


@bp.route("/api/classes", methods=["GET"])
def list_classes_endpoint():
    db: Database = get_db()
    details: List[ClassDetailRec] = [
        ClassDetailRec(cls=cls, props=db.get_class_properties(cls.id))
        for cls in db.list_classes()
    ]
    return {
        "error": None,
        "data": [d.to_json() for d in details],
    }


@bp.route("/api/classes/<int:cls_id>", methods=["GET"])
def get_class_endpoint(cls_id: int):
    db: Database = get_db()
    cls: ClassRec | None = db.get_class(cls_id)
    if cls is not None:
        return {
            "data": ClassDetailRec(cls=cls, props=db.get_class_properties(cls.id)).to_json(),
            "error": None,
        }
    else:
        raise class_not_found(cls_id)


@bp.route("/api/classes", methods=["POST"])
def new_class_endpoint():
    # Parse input
    form: dict = request.json
    title: str = form["title"].strip()
    icon_emoji: str = form["icon_emoji"].strip()
    # Create
    db: Database = get_db()
    cls: ClassRec = db.create_class(title=title, icon_emoji=icon_emoji)
    return {
        "data": ClassDetailRec(cls=cls, props=db.get_class_properties(cls.id)).to_json(),
        "error": None,
    }


@bp.route("/api/classes/<int:cls_id>/properties", methods=["GET"])
def get_class_properties_endpoint(cls_id: int):
    db: Database = get_db()
    if not db.class_exists(cls_id):
        raise class_not_found(cls_id)
    else:
        records: List[ClassPropRec] = db.get_class_properties(cls_id)
        return {
            "error": None,
            "data": [rec.to_json() for rec in records],
        }


@bp.route("/api/classes/<int:cls_id>/properties", methods=["POST"])
def new_class_property_endpoint(cls_id: int):
    db: Database = get_db()
    if not db.class_exists(cls_id):
        raise class_not_found(cls_id)
    else:
        form: dict = request.json
        title: str = form["title"].strip()
        prop_ty: PropertyType = PropertyType(form["type"])
        description: str = form["description"].strip()
        select_options: List[str] = form["select_options"]
        rec: ClassPropRec = db.create_class_property(
            class_id=cls_id,
            title=title,
            prop_type=prop_ty,
            description=description,
            select_options=select_options,
        )
        return {
            "error": None,
            "data": rec.to_json(),
        }


@bp.route("/api/classes/<int:cls_id>/properties/<int:cls_prop_id>", methods=["DELETE"])
def delete_class_property_endpoint(cls_id: int, cls_prop_id: int):
    db: Database = get_db()
    if not db.class_exists(cls_id):
        raise class_not_found(cls_id)
    if not db.class_property_exists(cls_prop_id):
        raise class_prop_not_found(cls_prop_id)
    else:
        db.delete_class_property(cls_prop_id)
        return {
            "data": None,
            "error": None,
        }


@bp.route("/api/classes/<int:cls_id>", methods=["DELETE"])
def delete_class_endpoint(cls_id: int):
    db: Database = get_db()
    if db.class_exists(cls_id):
        db.delete_class(cls_id)
        return {
            "data": True,
            "error": None,
        }
    else:
        raise class_not_found(cls_id)


@bp.route("/api/classes/<int:cls_id>", methods=["POST"])
def update_class_endpoint(cls_id: int):
    db: Database = get_db()
    if db.class_exists(cls_id):
        form: dict = request.json
        title: str = form["title"].strip()
        icon_emoji: str = form["icon_emoji"].strip()
        rec: ClassRec = db.update_class(
            cls_id=cls_id, new_title=title, new_icon_emoji=icon_emoji
        )
        return {
            "data": ClassDetailRec(
                cls=rec, props=db.get_class_properties(rec.id)
            ).to_json(),
            "error": None,
        }
    else:
        raise class_not_found(cls_id)


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
    cover_id: Optional[int] = form["directory_id"]
    property_values: dict = form["values"]
    # If an object with this title exists, reject it
    db: Database = get_db()
    if db.get_object_by_title(title) is not None:
        raise CTError(
            "Duplicate Title",
            f"An object with the title '{title}' already exists.",
        )
    # Find the class
    cls: Optional[ClassRec] = db.get_class(class_id)
    if cls is None:
        raise class_not_found(class_id)

    # Find the directory, if any
    if directory_id is not None:
        if not db.directory_exists(directory_id):
            raise directory_not_found(directory_id)
    # Find the set of class properties
    cls_props: List[ClassPropRec] = db.get_class_properties(class_id)
    # Check: the dictionary of values provided by the client has all the keys we expect
    input_keys: Set[str] = set(property_values.keys())
    expected_keys: Set[str] = set([prop.title for prop in cls_props])
    for expected_key in expected_keys:
        if expected_key not in input_keys:
            raise CTError(
                "Property Not Provided",
                f"No value provided for the property '{expected_key}'.",
            )
    # Effective emoji
    effective_icon_emoji: str = icon_emoji
    if (icon_emoji == "") and (cls.icon_emoji != ""):
        effective_icon_emoji = cls.icon_emoji
    # Create the object
    created_at: int = now_millis()
    object_id: int = db.create_object(
        title=title,
        class_id=class_id,
        directory_id=directory_id,
        icon_emoji=effective_icon_emoji,
        cover_id=cover_id,
        created_at=created_at,
        modified_at=created_at,
    )
    # Create the properties
    for prop_title, prop_value in property_values.items():
        # Find the corresponding class property
        cls_prop: ClassPropRec = [
            prop for prop in cls_props if prop.title == prop_title
        ][0]
        # These variables store the property's value
        value_integer: int | None = None
        value_text: str | None = None
        # This stores the set of links we have to create from this property.
        create_link_set: Set[str] = set()
        # Dispatch on the type of the class property
        if prop_value is not None:
            if cls_prop.type == PropertyType.PROP_RICH_TEXT:
                assert isinstance(prop_value, str)
                # The value should be a JSON string of a ProseMirror document.
                doc: CTDocument = parse_document(json.loads(prop_value))
                # If parsing succeeded, serialize the document.
                json_value: dict = emit_document(doc)
                json_string: str = json.dumps(json_value)
                # Set the values
                value_text = json_string
                # Find the set of links to create
                create_link_set: Set[str] = extract_links(doc)
            elif cls_prop.type == PropertyType.PROP_FILE:
                # The value should be an integer ID of a file.
                assert isinstance(prop_value, int)
                # Find the file with this ID
                if not db.file_exists(prop_value):
                    raise CTError(
                        "File Not Found",
                        f"The file with the ID '{prop_value}' was not found in the database.",
                    )
                # Set the values
                value_integer = prop_value
            elif cls_prop.type == PropertyType.PROP_BOOLEAN:
                # The value should be a boolean value.
                assert isinstance(prop_value, bool)
                # Set the value
                value_integer = int(prop_value)
            elif cls_prop.type == PropertyType.PROP_SELECT:
                # The value should be a string value.
                assert isinstance(prop_value, str)
                # The value should be part of the class property's select list
                if not prop_value in cls_prop.select_options:
                    raise CTError(
                        "Invalid Option",
                        f"The string '{prop_value}' is not part of the valid options for this property.",
                    )
                # Set the value
                value_text = prop_value
            elif cls_prop.type == PropertyType.PROP_LINK:
                # The value should be the title of an object.
                assert isinstance(prop_value, str)
                linked_title: str = prop_value
                linked_obj: ObjectRec | None = db.get_object_by_title(linked_title)
                if linked_obj is not None:
                    value_text = linked_title
                    create_link_set = {linked_title}
                else:
                    # The linked object does not exist. This is an error: dangling links are only allowed in text.
                    raise object_not_found(linked_title)
            elif cls_prop.type == PropertyType.PROP_LINKS:
                # The value should be an array of object titles
                assert isinstance(prop_value, list)
                linked_titles: Set[str] = set(prop_value)
                for linked_title in linked_titles:
                    assert isinstance(linked_titles, str)
                    linked_obj: ObjectRec | None = db.get_object_by_title(linked_title)
                    if linked_obj is None:
                        # The linked object does not exist. This is an error: dangling links are only allowed in text.
                        raise object_not_found(linked_title)
                value_text = ";".join(list(linked_titles))
                create_link_set = linked_titles
            else:
                raise CTError(
                    "Unknown Property Type",
                    f"I don't know what to do with the property '{prop_title}', which has type '{cls_prop.type}'.",
                )
        # Create the property in the database, and the initial property change object.
        prop_id: int = db.create_property(
            class_prop_id=cls_prop.id,
            class_prop_title=prop_title,
            class_prop_type=cls_prop.type,
            object_id=object_id,
            value_integer=value_integer,
            value_text=value_text,
        )
        db.create_property_change(
            object_id=object_id,
            prop_id=prop_id,
            prop_title=prop_title,
            created_at=created_at,
            value_integer=value_integer,
            value_text=value_text,
        )
        # Create links from this property to other objects
        for link_title in create_link_set:
            links_to: Optional[ObjectRec] = db.get_object_by_title(link_title)
            if links_to is not None:
                db.create_link(
                    from_object_id=object_id,
                    from_property_id=prop_id,
                    to_object_id=links_to.id,
                )
            else:
                db.create_dangling_link(
                    from_object_id=object_id,
                    from_property_id=prop_id,
                    to_object_title=link_title,
                )
    # If there are any dangling links to this object, delete them and replace them with real links.
    for link in db.get_dangling_links_to_title(to_object_title=title):
        # Create the actual link
        db.create_link(
            from_object_id=link.from_object_id,
            from_property_id=link.from_property_id,
            to_object_id=object_id,
        )
        # Delete the dangling link
        db.delete_dangling_link(link.id)
    # Return
    obj: ObjectRec = ObjectRec(
        id=object_id,
        title=title,
        class_id=class_id,
        directory_id=directory_id,
        icon_emoji=effective_icon_emoji,
        cover_id=cover_id,
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
        "data": [obj.to_json() for obj in get_db().list_objects()],
    }


@bp.route("/api/objects/<path:title>", methods=["GET"])
def object_details(title: str):
    db: Database = get_db()
    obj: Optional[ObjectRec] = db.get_object_by_title(title)
    if obj is not None:
        return {
            "error": None,
            "data": ObjectDetailRec(
                obj=obj,
                props=db.list_object_properties(obj.id),
                links=db.get_links_to_object(obj.id),
            ).to_json(),
        }
    else:
        raise object_not_found(title)


@bp.route("/api/objects/<path:title>", methods=["POST"])
def edit_object_endpoint(title: str):
    # Retrieve the object
    db: Database = get_db()
    obj: Optional[ObjectRec] = db.get_object_by_title(title)
    if obj is None:
        raise object_not_found(title)
    # Parse the input
    form: dict = request.json
    new_title: str = form["title"].strip()
    new_directory_id: Optional[int] = form["directory_id"]
    new_icon_emoji: str = form["icon_emoji"].strip()
    new_cover_id: Optional[int] = form["cover_id"]
    property_values: dict = form["values"]

    # Find the directory, if any
    if new_directory_id is not None:
        if not db.directory_exists(new_directory_id):
            raise directory_not_found(new_directory_id)

    # Find the set of class properties
    cls_props: List[ClassPropRec] = db.get_class_properties(obj.class_id)

    # Mark modification time
    modified_at: int = now_millis()

    # Edit the object
    db.update_object(
        obj=obj,
        new_title=new_title,
        new_directory_id=new_directory_id,
        new_icon_emoji=new_icon_emoji,
        new_cover_id=new_cover_id,
        modified_at=modified_at,
    )

    # Change the provided values
    for prop_title, prop_value in property_values.items():
        # Find the corresponding class property
        cls_prop: ClassPropRec = [
            prop for prop in cls_props if prop.title == prop_title
        ][0]
        # Find the existing property
        existing_prop: Optional[PropRec] = db.get_object_property(
            object_id=obj.id, class_prop_id=cls_prop.id
        )
        if existing_prop is None:
            raise CTError(
                "No Existing Property",
                f"Can't edit a property that does not exist: '{prop_title}', which has type '{cls_prop.type}'.",
            )
        # Dispatch on the type of the class property
        value_integer: int | None = None
        value_text: str | None = None
        create_link_set: Set[str] = set()
        if prop_value is not None:
            if cls_prop.type == PropertyType.PROP_RICH_TEXT:
                assert isinstance(prop_value, str)
                # The value should be a JSON string of a ProseMirror document.
                doc: CTDocument = parse_document(json.loads(prop_value))
                # If parsing succeeded, serialize the document.
                json_value: dict = emit_document(doc)
                json_string: str = json.dumps(json_value)
                # Set the values
                value_text = json_string
                create_link_set = extract_links(doc)
            elif cls_prop.type == PropertyType.PROP_FILE:
                # The value should be an integer ID of a file.
                assert isinstance(prop_value, int)
                # Find the file with this ID
                if not db.file_exists(prop_value):
                    raise file_not_found(prop_value)
                # Set the values
                value_file = prop_value
            elif cls_prop.type == PropertyType.PROP_BOOLEAN:
                # The value should be a boolean value.
                assert isinstance(prop_value, bool)
                # Set the value
                value_integer = int(prop_value)
            elif cls_prop.type == PropertyType.PROP_SELECT:
                # The value should be a string value.
                assert isinstance(prop_value, str)
                # The value should be part of the class property's select list
                if not prop_value in cls_prop.select_options:
                    raise CTError(
                        "Invalid Option",
                        f"The string '{prop_value}' is not part of the valid options for this property.",
                    )
                # Set the value
                value_text = prop_value
            elif cls_prop.type == PropertyType.PROP_LINK:
                # The value should be the title of an object.
                assert isinstance(prop_value, str)
                linked_title: str = prop_value
                linked_obj: ObjectRec | None = db.get_object_by_title(linked_title)
                if linked_obj is not None:
                    value_text = linked_title
                    create_link_set = {linked_title}
                else:
                    # The linked object does not exist. This is an error: dangling links are only allowed in text.
                    raise object_not_found(linked_title)
            elif cls_prop.type == PropertyType.PROP_LINKS:
                # The value should be an array of object titles
                assert isinstance(prop_value, list)
                linked_titles: Set[str] = set(prop_value)
                for linked_title in linked_titles:
                    assert isinstance(linked_titles, str)
                    linked_obj: ObjectRec | None = db.get_object_by_title(linked_title)
                    if linked_obj is None:
                        # The linked object does not exist. This is an error: dangling links are only allowed in text.
                        raise object_not_found(linked_title)
                value_text = ";".join(list(linked_titles))
                create_link_set = linked_titles
            else:
                raise CTError(
                    "Unknown Property Type",
                    f"I don't know what to do with the property '{prop_title}', which has type '{cls_prop.type}'.",
                )
        # Edit the property
        db.edit_property(
            property_id=existing_prop.id,
            value_integer=value_integer,
            value_text=value_text,
        )
        # Create the property change
        db.create_property_change(
            object_id=obj.id,
            prop_id=existing_prop.id,
            prop_title=prop_title,
            created_at=modified_at,
            value_integer=value_integer,
            value_text=value_text,
        )
        # Delete old links from this property to any other object
        db.delete_links_from(property_id=existing_prop.id)
        # Create new links from this property
        for link_title in create_link_set:
            links_to: Optional[ObjectRec] = db.get_object_by_title(link_title)
            if links_to is not None:
                db.create_link(
                    from_object_id=obj.id,
                    from_property_id=existing_prop.id,
                    to_object_id=links_to.id,
                )
            else:
                db.create_dangling_link(
                    from_object_id=obj.id,
                    from_property_id=existing_prop.id,
                    to_object_title=link_title,
                )
    # Return
    obj: Optional[ObjectRec] = db.get_object_by_title(new_title)
    assert obj is not None
    return {
        "data": obj.to_json(),
        "error": None,
    }


@bp.route("/api/objects/<path:title>", methods=["DELETE"])
def delete_object_endpoint(title: str):
    # Retrieve the object
    db: Database = get_db()
    obj: ObjectRec | None = db.get_object_by_title(title)
    if obj is not None:
        db.delete_object(obj.id)
        return {
            "data": None,
            "error": None,
        }
    else:
        raise object_not_found(title)


@bp.route("/api/object-search", methods=["POST"])
def object_search_endpoint():
    # Parse the input
    form: dict = request.json
    query: str = form["query"].strip()
    # Return results
    return {
        "data": [obj.to_json() for obj in get_db().search_objects(query=query)],
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
    Determine the MIME-type of a byte stream.
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
