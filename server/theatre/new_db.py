"""
This module implements the persistence layer.
"""
import json
from dataclasses import dataclass
from enum import Enum
from typing import List, Iterable, Dict, Tuple, Set
from sqlite3 import Connection, Cursor, Row, connect

from theatre.new_text import CTDocument
from theatre.prosemirror import parse_document, emit_document
from theatre.rename_link import rename_link


#
# Utility types
#


class PropertyType(Enum):
    PROP_RICH_TEXT = "PROP_RICH_TEXT"
    PROP_FILE = "PROP_FILE"
    PROP_BOOLEAN = "PROP_BOOLEAN"
    PROP_SELECT = "PROP_SELECT"
    PROP_LINK = "PROP_LINK"
    PROP_LINKS = "PROP_LINKS"

    def to_int(self) -> int:
        mapping = {
            self.PROP_RICH_TEXT: 0,
            self.PROP_FILE: 1,
            self.PROP_BOOLEAN: 2,
            self.PROP_SELECT: 3,
            self.PROP_LINK: 4,
            self.PROP_LINKS: 5,
        }
        return mapping[self]

    @staticmethod
    def from_int(value: int) -> "PropertyType":
        mapping = {
            0: PropertyType.PROP_RICH_TEXT,
            1: PropertyType.PROP_FILE,
            2: PropertyType.PROP_BOOLEAN,
            3: PropertyType.PROP_SELECT,
            4: PropertyType.PROP_LINK,
            5: PropertyType.PROP_LINKS,
        }
        return mapping[value]


#
# Dataclasses to represent database rows
#


@dataclass(frozen=True)
class FileRec:
    id: int
    filename: str
    mime_type: str
    size: int
    hash: str
    created_at: int

    def to_json(self) -> dict:
        return {
            "id": self.id,
            "filename": self.filename,
            "mime_type": self.mime_type,
            "size": self.size,
            "hash": self.hash,
            "created_at": self.created_at,
        }


@dataclass(frozen=True)
class DirRec:
    id: int
    title: str
    icon_emoji: str
    cover_id: int | None
    parent_id: int | None
    created_at: int

    def to_json(self) -> dict:
        return {
            "id": self.id,
            "title": self.title,
            "icon_emoji": self.icon_emoji,
            "cover_id": self.cover_id,
            "parent_id": self.parent_id,
            "created_at": self.created_at,
        }


@dataclass(frozen=True)
class ClassRec:
    id: int
    title: str
    icon_emoji: str

    def to_json(self) -> dict:
        return {
            "id": self.id,
            "title": self.title,
            "icon_emoji": self.icon_emoji,
        }


@dataclass(frozen=True)
class ClassPropRec:
    id: int
    class_id: int
    title: str
    type: PropertyType
    description: str
    select_options: List[str]

    def to_json(self) -> dict:
        return {
            "id": self.id,
            "class_id": self.class_id,
            "title": self.title,
            "type": self.type.value,
            "description": self.description,
            "select_options": self.select_options,
        }


@dataclass(frozen=True)
class ClassDetailRec:
    """
    Represents a class plus its property map.
    """

    cls: ClassRec
    props: List[ClassPropRec]

    def to_json(self) -> dict:
        d: dict = self.cls.to_json()
        d["properties"] = [p.to_json() for p in self.props]
        return d


@dataclass(frozen=True)
class ObjectRec:
    id: int
    title: str
    class_id: int
    directory_id: int | None
    icon_emoji: str
    cover_id: int | None
    created_at: int
    modified_at: int

    def to_json(self) -> dict:
        return {
            "id": self.id,
            "title": self.title,
            "class_id": self.class_id,
            "directory_id": self.directory_id,
            "icon_emoji": self.icon_emoji,
            "cover_id": self.cover_id,
            "created_at": self.created_at,
            "modified_at": self.modified_at,
        }


@dataclass(frozen=True)
class PropRec:
    id: int
    object_id: int
    class_prop_id: int
    class_prop_title: str
    class_prop_type: PropertyType
    value_integer: int | None
    value_text: str | None

    def to_json(self) -> dict:
        return {
            "id": self.id,
            "object_id": self.object_id,
            "class_prop_id": self.class_prop_id,
            "class_prop_title": self.class_prop_title,
            "class_prop_type": self.class_prop_type,
            "value": self._value_json(),
        }

    def _value_json(self):
        if self.class_prop_type == PropertyType.PROP_RICH_TEXT:
            assert self.value_text is not None
            return self.value_text
        elif self.class_prop_type == PropertyType.PROP_FILE:
            assert self.value_integer is not None
            return self.value_integer
        elif self.class_prop_type == PropertyType.PROP_BOOLEAN:
            assert self.value_integer is not None
            return bool(self.value_integer)
        elif self.class_prop_type == PropertyType.PROP_LINK:
            assert self.value_text is not None
            return self.value_text
        elif self.class_prop_type == PropertyType.PROP_LINKS:
            assert self.value_text is not None
            return set(self.value_text.split(";"))


class BaseProperty(object):
    """
    Base class of property values.
    """

    id: int
    object_id: int
    class_prop_id: int
    class_prop_title: str
    class_prop_type: PropertyType


class RichTextProperty(BaseProperty):
    doc: CTDocument

    def __init__(
        self,
        prop_id: int,
        object_id: int,
        class_prop_id: int,
        class_prop_title: str,
        class_prop_type: PropertyType,
        doc: CTDocument,
    ):
        self.id = prop_id
        self.object_id = object_id
        self.class_prop_id = class_prop_id
        self.class_prop_title = class_prop_title
        self.class_prop_type = class_prop_type
        self.doc = doc


class FileProperty(BaseProperty):
    file_id: int

    def __init__(
        self,
        prop_id: int,
        object_id: int,
        class_prop_id: int,
        class_prop_title: str,
        class_prop_type: PropertyType,
        file_id: int,
    ):
        self.id = prop_id
        self.object_id = object_id
        self.class_prop_id = class_prop_id
        self.class_prop_title = class_prop_title
        self.class_prop_type = class_prop_type
        self.file_id = file_id


class BooleanProperty(BaseProperty):
    value: bool

    def __init__(
        self,
        prop_id: int,
        object_id: int,
        class_prop_id: int,
        class_prop_title: str,
        class_prop_type: PropertyType,
        value: bool,
    ):
        self.id = prop_id
        self.object_id = object_id
        self.class_prop_id = class_prop_id
        self.class_prop_title = class_prop_title
        self.class_prop_type = class_prop_type
        self.value = value


class SelectProperty(BaseProperty):
    option: str

    def __init__(
        self,
        prop_id: int,
        object_id: int,
        class_prop_id: int,
        class_prop_title: str,
        class_prop_type: PropertyType,
        option: str,
    ):
        self.id = prop_id
        self.object_id = object_id
        self.class_prop_id = class_prop_id
        self.class_prop_title = class_prop_title
        self.class_prop_type = class_prop_type
        self.option = option


class LinkProperty(BaseProperty):
    title: str

    def __init__(
        self,
        prop_id: int,
        object_id: int,
        class_prop_id: int,
        class_prop_title: str,
        class_prop_type: PropertyType,
        title: str,
    ):
        self.id = prop_id
        self.object_id = object_id
        self.class_prop_id = class_prop_id
        self.class_prop_title = class_prop_title
        self.class_prop_type = class_prop_type
        self.title = title


class LinksProperty(BaseProperty):
    titles: Set[str]

    def __init__(
        self,
        prop_id: int,
        object_id: int,
        class_prop_id: int,
        class_prop_title: str,
        class_prop_type: PropertyType,
        titles: Set[str],
    ):
        self.id = prop_id
        self.object_id = object_id
        self.class_prop_id = class_prop_id
        self.class_prop_title = class_prop_title
        self.class_prop_type = class_prop_type
        self.titles = titles


@dataclass(frozen=True)
class PropChangeRec:
    id: int
    object_id: int
    prop_id: int | None
    prop_title: str
    created_at: int

    value_integer: int | None
    value_text: str | None


@dataclass(frozen=True)
class LinkRec:
    id: int
    from_object_id: int
    from_property_id: int
    to_object_id: int


@dataclass(frozen=True)
class DanglingLinkRec:
    id: int
    from_object_id: int
    from_property_id: int
    to_object_title: str


@dataclass(frozen=True)
class LinkRepr:
    """
    The data we need to show a link to a user.
    """

    title: str

    def to_json(self) -> dict:
        return {
            "title": self.title,
        }


@dataclass(frozen=True)
class ObjectDetailRec:
    """
    Represents an object together with its property map and links.
    """

    obj: ObjectRec
    props: List[PropRec]
    links: List[LinkRepr]

    def to_json(self) -> dict:
        d: dict = self.obj.to_json()
        d["properties"] = [p.to_json() for p in self.props]
        d["links"] = [l.to_json() for l in self.links]
        return d


#
# Database object
#


class Database(object):
    """
    The database access object for Cartesian databases.
    """

    conn: Connection

    def __init__(self, conn: Connection):
        self.conn = conn

    @staticmethod
    def connect(database_path: str) -> "Database":
        conn: Connection = connect(database_path)
        conn.row_factory = Row
        cur: Cursor = conn.cursor()
        cur.execute("pragma foreign_keys=on;")
        conn.commit()
        return Database(conn=conn)

    def close(self):
        self.conn.close()

    def create_schema(self, sql: str):
        self.conn.executescript(sql)

    #
    # File methods
    #

    def create_file(
        self,
        filename: str,
        mime_type: str,
        size: int,
        sha256hash: str,
        created_at: int,
        blob: bytes,
    ) -> int:
        """
        Create a file.
        """
        cur: Cursor = self.conn.cursor()
        results: List[Row] = cur.execute(
            """
            insert into files
                (filename, mime_type, size, hash, created_at, data)
            values
                (:filename, :mime_type, :size, :hash, :created_at, :data)
            returning id;
            """,
            {
                "filename": filename,
                "mime_type": mime_type,
                "size": size,
                "hash": sha256hash,
                "created_at": created_at,
                "data": blob,
            },
        ).fetchall()
        file_id: int = results[0]["id"]
        self.conn.commit()
        return file_id

    def file_exists(self, file_id: int) -> bool:
        """
        Check whether a file exists.
        """
        cur: Cursor = self.conn.cursor()
        rows: List[Row] = cur.execute(
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
        ).fetchall()
        return bool(rows)

    def list_files(self) -> List[FileRec]:
        """
        List all files in the database.
        """
        cur: Cursor = self.conn.cursor()
        rows: List[Row] = cur.execute(
            """
            select
                id, filename, mime_type, size, hash, created_at
            from
                files;
            """
        ).fetchall()
        return [
            FileRec(
                id=row["id"],
                filename=row["filename"],
                mime_type=row["mime_type"],
                size=row["size"],
                hash=row["hash"],
                created_at=row["created_at"],
            )
            for row in rows
        ]

    def get_file_by_id(self, file_id: int) -> FileRec | None:
        """
        Retrieve a file by its ID.
        """
        cur: Cursor = self.conn.cursor()
        rows: List[Row] = cur.execute(
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
        if rows:
            row: Row = rows[0]
            return FileRec(
                id=file_id,
                filename=row["filename"],
                mime_type=row["mime_type"],
                size=row["size"],
                hash=row["hash"],
                created_at=row["created_at"],
            )
        else:
            return None

    def get_file_data(self, file_id: int) -> Tuple[str, bytes] | None:
        """
        Retrieve a file's MIME type and data.
        """
        cur: Cursor = self.conn.cursor()
        rows: List[Row] = cur.execute(
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
        if rows:
            row: Row = rows[0]
            return row["mime_type"], row["data"]
        else:
            return None

    def delete_file(self, file_id: int):
        """
        Delete a file.
        """
        cur: Cursor = self.conn.cursor()
        cur.execute(
            """
            delete from
                files
            where
                id = :file_id;
            """,
            {
                "file_id": file_id,
            },
        )
        self.conn.commit()

    #
    # Directory methods
    #

    def create_directory(
        self,
        title: str,
        icon_emoji: str,
        cover_id: int | None,
        parent_id: int | None,
        created_at: int,
    ) -> int:
        cur: Cursor = self.conn.cursor()
        rows: List[Row] = cur.execute(
            """
            insert into directories
                (title, icon_emoji, cover_id, parent_id, created_at)
            values
                (:title, :icon_emoji, :cover_id, :parent_id, :created_at)
            returning id;
            """,
            {
                "title": title,
                "icon_emoji": icon_emoji,
                "cover_id": cover_id,
                "parent_id": parent_id,
                "created_at": created_at,
            },
        ).fetchall()
        dir_id: int = rows[0]["id"]
        self.conn.commit()
        return dir_id

    def directory_exists(self, dir_id: int) -> bool:
        """
        Check whether a directory exists.
        """
        cur: Cursor = self.conn.cursor()
        rows: List[Row] = cur.execute(
            """
            select
                id
            from
                directories
            where
                id = :id;
            """,
            {
                "id": dir_id,
            },
        ).fetchall()
        return bool(rows)

    def list_directories(self) -> Iterable[DirRec]:
        """
        Return the list of all directories.
        """
        cur: Cursor = self.conn.cursor()
        rows: List[Row] = cur.execute(
            """
            select
                id, title, icon_emoji, cover_id, parent_id, created_at
            from
                directories;
            """
        ).fetchall()
        return [
            DirRec(
                id=row["id"],
                title=row["title"],
                icon_emoji=row["icon_emoji"],
                cover_id=row["cover_id"],
                parent_id=row["parent_id"],
                created_at=row["created_at"],
            )
            for row in rows
        ]

    def get_directory(self, dir_id: int) -> DirRec | None:
        """
        Return the list of all directories.
        """
        cur: Cursor = self.conn.cursor()
        rows: List[Row] = cur.execute(
            """
            select
                title, icon_emoji, cover_id, parent_id, created_at
            from
                directories
            where
                id = :id;
            """,
            {
                "id": dir_id,
            },
        ).fetchall()
        if rows:
            row = rows[0]
            return DirRec(
                id=dir_id,
                title=row["title"],
                icon_emoji=row["icon_emoji"],
                cover_id=row["cover_id"],
                parent_id=row["parent_id"],
                created_at=row["created_at"],
            )
        else:
            return None

    def edit_directory(
        self,
        dir_id: int,
        title: str,
        icon_emoji: str,
        cover_id: int | None,
        parent_id: int | None,
    ):
        cur: Cursor = self.conn.cursor()
        cur.execute(
            """
            update
                directories
            set
                title = :title,
                icon_emoji = :icon_emoji,
                cover_id = :cover_id,
                parent_id = :parent_id
            where
                id = :id;
            """,
            {
                "id": dir_id,
                "title": title,
                "icon_emoji": icon_emoji,
                "cover_id": cover_id,
                "parent_id": parent_id,
            },
        )
        self.conn.commit()

    def delete_directory(self, dir_id: int):
        """
        Delete a directory.
        """
        cur: Cursor = self.conn.cursor()
        cur.execute(
            """
            delete from
                directories
            where
                id = :dir_id;
            """,
            {
                "dir_id": dir_id,
            },
        )
        self.conn.commit()

    #
    # Class methods
    #

    def class_exists(self, cls_id: int) -> bool:
        """
        Check whether a class exists.
        """
        cur: Cursor = self.conn.cursor()
        return bool(
            cur.execute(
                "select id from classes where id = :id;", {"id": cls_id}
            ).fetchall()
        )

    def list_classes(self) -> Iterable[ClassRec]:
        """
        Return the list of all classes.
        """
        cur: Cursor = self.conn.cursor()
        rows: List[Row] = cur.execute(
            """
            select
                id, title, icon_emoji
            from
                classes
            order by
                id asc;
            """
        ).fetchall()
        return [
            ClassRec(id=row["id"], title=row["title"], icon_emoji=row["icon_emoji"])
            for row in rows
        ]

    def get_class(self, cls_id: int) -> ClassRec | None:
        """
        Retrieve a class by ID.
        """
        cur: Cursor = self.conn.cursor()
        rows: List[Row] = cur.execute(
            """
            select
                id, title, icon_emoji
            from
                classes
            where
                id = :id;
            """,
            {
                "id": cls_id,
            },
        ).fetchall()
        if rows:
            row: Row = rows[0]
            return ClassRec(
                id=row["id"], title=row["title"], icon_emoji=row["icon_emoji"]
            )
        else:
            return None

    def create_class(self, title: str, icon_emoji: str) -> ClassRec:
        """
        Create a class.
        """
        cur: Cursor = self.conn.cursor()
        rows: List[Row] = cur.execute(
            """
            insert into classes
                (title, icon_emoji)
            values
                (:title, :icon_emoji)
            returning id;
            """,
            {
                "title": title,
                "icon_emoji": icon_emoji,
            },
        ).fetchall()
        cls_id: int = rows[0]["id"]
        self.conn.commit()
        return ClassRec(id=cls_id, title=title, icon_emoji=icon_emoji)

    def update_class(
        self, cls_id: int, new_title: str, new_icon_emoji: str
    ) -> ClassRec:
        """
        Update a class.
        """
        cur: Cursor = self.conn.cursor()
        cur.execute(
            """
            update
                classes
            set
                title = :title,
                icon_emoji = :icon_emoji
            where
                id = :id;
            """,
            {
                "id": cls_id,
                "title": new_title,
                "icon_emoji": new_icon_emoji,
            },
        )
        self.conn.commit()
        return ClassRec(id=cls_id, title=new_title, icon_emoji=new_icon_emoji)

    def delete_class(self, cls_id: int):
        """
        Delete a class.
        """
        cur: Cursor = self.conn.cursor()
        cur.execute(
            """
            delete from
                classes
            where
                id = :cls_id;
            """,
            {
                "cls_id": cls_id,
            },
        )
        self.conn.commit()

    #
    # Class property methods
    #

    def class_property_exists(self, cls_prop_id: int) -> bool:
        """
        Check whether a class property exists.
        """
        cur: Cursor = self.conn.cursor()
        return bool(
            cur.execute(
                "select id from class_props where id = :id;", {"id": cls_prop_id}
            ).fetchall()
        )

    def get_class_properties(self, class_id: int) -> List[ClassPropRec]:
        """
        Retrieve a class property by ID.
        """
        cur: Cursor = self.conn.cursor()
        rows: List[Row] = cur.execute(
            """
            select
                id, title, type, description, select_options
            from
                class_props
            where
                class_id = :class_id;
            """,
            {
                "class_id": class_id,
            },
        ).fetchall()
        return [
            ClassPropRec(
                id=row["id"],
                class_id=class_id,
                title=row["title"],
                type=PropertyType.from_int(row["type"]),
                description=row["description"],
                select_options=row["select_options"].split(","),
            )
            for row in rows
        ]

    def create_class_property(
        self,
        class_id: int,
        title: str,
        prop_type: PropertyType,
        description: str,
        select_options: List[str],
    ) -> ClassPropRec:
        """
        Create a class property.
        """
        cur: Cursor = self.conn.cursor()
        rows: Cursor = cur.execute(
            """
            insert into class_props
                (class_id, title, type, description, select_options)
            values
                (:class_id, :title, :type, :description, :select_options)
            returning id;
            """,
            {
                "class_id": class_id,
                "title": title,
                "type": prop_type.to_int(),
                "description": description,
                "select_options": ",".join(select_options),
            },
        )
        cls_prop_id: int = list(rows)[0][0]
        self.conn.commit()
        return ClassPropRec(
            id=cls_prop_id,
            class_id=class_id,
            title=title,
            type=prop_type,
            description=description,
            select_options=select_options,
        )

    def delete_class_property(self, cls_prop_id: int):
        """
        Delete a class property.
        """
        cur: Cursor = self.conn.cursor()
        cur.execute("delete from class_props where id = :id", {"id": cls_prop_id})
        self.conn.commit()

    #
    # Object methods
    #

    def list_objects(self) -> List[ObjectRec]:
        """
        Retrieve all objects.
        """
        cur: Cursor = self.conn.cursor()
        rows: List[Row] = cur.execute(
            """
            select
                id, title, class_id, directory_id, icon_emoji, cover_id, created_at, modified_at
            from
                objects
            order by
                id asc;
            """
        ).fetchall()
        return [
            ObjectRec(
                id=row["id"],
                title=row["title"],
                class_id=row["class_id"],
                directory_id=row["directory_id"],
                icon_emoji=row["icon_emoji"],
                cover_id=row["cover_id"],
                created_at=row["created_at"],
                modified_at=row["modified_at"],
            )
            for row in rows
        ]

    def list_objects_in_directory(self, dir_id: int) -> List[ObjectRec]:
        """
        Retrieve all objects in a directory.
        """
        cur: Cursor = self.conn.cursor()
        rows: List[Row] = cur.execute(
            """
            select
                id, title, class_id, icon_emoji, cover_id, created_at, modified_at
            from
                objects
            where
                directory_id = :directory_id 
            order by
                id asc;
            """,
            {
                "directory_id": dir_id,
            },
        ).fetchall()
        return [
            ObjectRec(
                id=row["id"],
                title=row["title"],
                class_id=row["class_id"],
                directory_id=dir_id,
                icon_emoji=row["icon_emoji"],
                cover_id=row["cover_id"],
                created_at=row["created_at"],
                modified_at=row["modified_at"],
            )
            for row in rows
        ]

    def list_uncategorized_objects(self) -> List[ObjectRec]:
        """
        Retrieve all objects not in any directories.
        """
        cur: Cursor = self.conn.cursor()
        rows: List[Row] = cur.execute(
            """
            select
                id, title, class_id, icon_emoji, cover_id, created_at, modified_at
            from
                objects
            where
                directory_id is null 
            order by
                id asc;
            """
        ).fetchall()
        return [
            ObjectRec(
                id=row["id"],
                title=row["title"],
                class_id=row["class_id"],
                directory_id=None,
                icon_emoji=row["icon_emoji"],
                cover_id=row["cover_id"],
                created_at=row["created_at"],
                modified_at=row["modified_at"],
            )
            for row in rows
        ]

    def get_object_by_title(self, title: str) -> ObjectRec | None:
        """
        Retrieve an object by title.
        """
        cur: Cursor = self.conn.cursor()
        rows: List[Row] = cur.execute(
            """
            select
                id, class_id, directory_id, icon_emoji, cover_id, created_at, modified_at
            from
                objects
            where
                title = :title;
            """,
            {
                "title": title,
            },
        ).fetchall()
        if rows:
            row: Row = rows[0]
            return ObjectRec(
                id=row["id"],
                title=title,
                class_id=row["class_id"],
                directory_id=row["directory_id"],
                icon_emoji=row["icon_emoji"],
                cover_id=row["cover_id"],
                created_at=row["created_at"],
                modified_at=row["modified_at"],
            )
        else:
            return None

    def create_object(
        self,
        title: str,
        class_id: int,
        directory_id: int | None,
        icon_emoji: str,
        cover_id: int | None,
        created_at: int,
        modified_at: int,
    ) -> id:
        """
        Create an object.
        """
        cur: Cursor = self.conn.cursor()
        cur.execute(
            """
            insert into objects
                (title, class_id, directory_id, icon_emoji, cover_id, created_at, modified_at)
            values
                (:title, :class_id, :directory_id, :icon_emoji, :cover_id, :created_at, :modified_at)
            returning id;
            """,
            {
                "title": title,
                "class_id": class_id,
                "directory_id": directory_id,
                "icon_emoji": icon_emoji,
                "cover_id": cover_id,
                "created_at": created_at,
                "modified_at": modified_at,
            },
        )
        obj_id: int = list(cur)[0][0]
        self.conn.commit()
        return obj_id

    def delete_object(self, obj_id: int):
        """
        Delete an object.
        """
        cur: Cursor = self.conn.cursor()
        cur.execute(
            """
            delete from
                objects
            where
                id = :obj_id
            """,
            {
                "obj_id": obj_id,
            },
        )
        self.conn.commit()

    def update_object(
        self,
        obj: ObjectRec,
        new_title: str,
        new_directory_id: int | None,
        new_icon_emoji: str,
        new_cover_id: int,
        modified_at: int,
    ):
        # Update the object itself
        cur: Cursor = self.conn.cursor()
        cur.execute(
            """
            update
                objects
            set
                title = :title,
                directory_id = :directory_id,
                icon_emoji = :icon_emoji,
                cover_id = :cover_id,
                modified_at = :modified_at
            where
                id = :object_id;
            """,
            {
                "object_id": obj.id,
                "title": new_title,
                "directory_id": new_directory_id,
                "icon_emoji": new_icon_emoji,
                "cover_id": new_cover_id,
                "modified_at": modified_at,
            },
        ).fetchall()
        self.conn.commit()
        # If the title is different, rename links.
        if obj.title != new_title:
            links: List[LinkRec] = self.get_links_to(to_object_id=obj.id)
            for link in links:
                prop: PropRec | None = self.get_property_by_id(link.from_property_id)
                assert prop is not None
                if prop.value_text is not None:
                    doc = parse_document(json.loads(prop.value_text))
                    new_doc = rename_link(
                        doc=doc, old_title=obj.title, new_title=new_title
                    )
                    json_value: dict = emit_document(new_doc)
                    new_value_text: str = json.dumps(json_value)
                    self.edit_property(
                        property_id=prop.id,
                        value_integer=prop.value_integer,
                        value_text=new_value_text,
                    )
                    self.create_property_change(
                        object_id=obj.id,
                        prop_id=prop.id,
                        prop_title=prop.class_prop_title,
                        created_at=modified_at,
                        value_integer=prop.value_integer,
                        value_text=new_value_text,
                    )

    #
    # Object property methods
    #

    def list_object_properties(
        self,
        object_id: int,
    ) -> List[PropRec]:
        """
        Retrieve the list of properties for an object.
        """
        cur: Cursor = self.conn.cursor()
        rows: List[Row] = cur.execute(
            """
            select
                id,
                class_prop_id,
                class_prop_title,
                class_prop_type,
                value_integer,
                value_text
            from
                properties
            where
                object_id = :object_id
            """,
            {
                "object_id": object_id,
            },
        ).fetchall()
        return [
            PropRec(
                id=row["id"],
                class_prop_id=row["class_prop_id"],
                class_prop_title=row["class_prop_title"],
                class_prop_type=PropertyType.from_int(row["class_prop_type"]),
                object_id=object_id,
                value_integer=row["value_integer"],
                value_text=row["value_text"],
            )
            for row in rows
        ]

    def get_object_property(self, object_id: int, class_prop_id: int) -> PropRec | None:
        """
        Retrieve an object property by the object ID and the ID of the class property.
        """
        cur: Cursor = self.conn.cursor()
        rows: List[Row] = cur.execute(
            """
            select
                id,
                class_prop_title,
                class_prop_type,
                value_integer,
                value_text
            from
                properties
            where
                (object_id = :object_id)
                AND
                (class_prop_id = :class_prop_id);
            """,
            {
                "object_id": object_id,
                "class_prop_id": class_prop_id,
            },
        ).fetchall()
        if rows:
            row: Row = rows[0]
            return PropRec(
                id=row["id"],
                class_prop_id=class_prop_id,
                class_prop_title=row["class_prop_title"],
                class_prop_type=PropertyType.from_int(row["class_prop_type"]),
                object_id=object_id,
                value_integer=row["value_integer"],
                value_text=row["value_text"],
            )
        else:
            return None

    def get_property_by_id(self, property_id: int) -> PropRec | None:
        """
        Retrieve an object property by its ID.
        """
        cur: Cursor = self.conn.cursor()
        rows: List[Row] = cur.execute(
            """
            select
                class_prop_id,
                class_prop_title,
                class_prop_type,
                object_id,
                value_integer,
                value_text,
            from
                properties
            where
                object_id = :object_id
            """,
            {
                "property_id": property_id,
            },
        ).fetchall()
        if rows:
            row: Row = rows[0]
            return PropRec(
                id=row["id"],
                class_prop_id=row["class_prop_id"],
                class_prop_title=row["class_prop_title"],
                class_prop_type=PropertyType.from_int(row["class_prop_type"]),
                object_id=row["object_id"],
                value_integer=row["value_integer"],
                value_text=row["value_text"],
            )
        else:
            return None

    def create_property(
        self,
        class_prop_id: int,
        class_prop_title: str,
        class_prop_type: PropertyType,
        object_id: int,
        value_integer: int | None,
        value_text: str | None,
    ) -> id:
        cur: Cursor = self.conn.cursor()
        cur.execute(
            """
            insert into properties
                (class_prop_id, class_prop_title, class_prop_type, object_id, value_integer, value_text)
            values
                (:class_prop_id, :class_prop_title, :class_prop_type, :object_id, :value_integer, :value_text)
            returning id;
            """,
            {
                "class_prop_id": class_prop_id,
                "class_prop_title": class_prop_title,
                "class_prop_type": class_prop_type.to_int(),
                "object_id": object_id,
                "value_integer": value_integer,
                "value_text": value_text,
            },
        )
        prop_id: int = list(cur)[0][0]
        self.conn.commit()
        return prop_id

    def edit_property(
        self,
        property_id: int,
        value_integer: int | None,
        value_text: str | None,
    ):
        cur: Cursor = self.conn.cursor()
        cur.execute(
            """
            update
                properties
            set
                value_integer = :value_integer,
                value_text = :value_text
            where
                id = :property_id;
            """,
            {
                "property_id": property_id,
                "value_integer": value_integer,
                "value_text": value_text,
            },
        )
        self.conn.commit()

    #
    # Property change methods
    #

    def get_property_changes(self, prop_id: int) -> List[PropChangeRec]:
        cur: Cursor = self.conn.cursor()
        rows: List[Row] = cur.execute(
            """
            select
                id, object_id, prop_title, created_at, value_integer, value_text
            from
                property_changes
            where
                prop_id = :prop_id;
            """,
            {
                "prop_id": prop_id,
            },
        ).fetchall()
        return [
            PropChangeRec(
                id=row["id"],
                object_id=row["object_id"],
                prop_id=prop_id,
                prop_title=row["prop_title"],
                created_at=row["created_at"],
                value_integer=row["value_integer"],
                value_text=row["value_text"],
            )
            for row in rows
        ]

    def create_property_change(
        self,
        object_id: int,
        prop_id: int,
        prop_title: str,
        created_at: int,
        value_integer: int | None,
        value_text: str | None,
    ) -> id:
        cur: Cursor = self.conn.cursor()
        cur.execute(
            """
            insert into property_changes
                (object_id, prop_id, prop_title, created_at, value_integer, value_text)
            values
                (:object_id, :prop_id, :prop_title, :created_at, :value_integer, :value_text,)
            returning id;
            """,
            {
                "object_id": object_id,
                "prop_id": prop_id,
                "prop_title": prop_title,
                "created_at": created_at,
                "value_integer": value_integer,
                "value_text": value_text,
            },
        )
        prop_change_id: int = list(cur)[0][0]
        self.conn.commit()
        return prop_change_id

    #
    # Link methods
    #

    def get_links_to(self, to_object_id: int) -> List[LinkRec]:
        """
        Retrieve links that point to a given object.
        """
        cur: Cursor = self.conn.cursor()
        rows: List[Row] = cur.execute(
            """
            select
                id, from_object_id, from_property_id
            from
                links
            where
                to_object_id = :to_object_id;
            """,
            {
                "to_object_id": to_object_id,
            },
        ).fetchall()
        return [
            LinkRec(
                id=row["id"],
                from_object_id=row["from_object_id"],
                from_property_id=row["from_property_id"],
                to_object_id=to_object_id,
            )
            for row in rows
        ]

    def create_link(
        self,
        from_object_id: int,
        from_property_id: int,
        to_object_id: int,
    ) -> id:
        """
        Create a link.
        """
        cur: Cursor = self.conn.cursor()
        cur.execute(
            """
            insert into links
                (from_object_id, from_property_id, to_object_id)
            values
                (:from_object_id, :from_property_id, :to_object_id)
            returning id;
            """,
            {
                "from_object_id": from_object_id,
                "from_property_id": from_property_id,
                "to_object_id": to_object_id,
            },
        )
        link_id: int = list(cur)[0][0]
        self.conn.commit()
        return link_id

    def delete_links_from(self, property_id: int):
        """
        Delete links from a given property.
        """
        cur: Cursor = self.conn.cursor()
        cur.execute(
            """
            delete from
                links
            where
                from_property_id = :property_id
            """,
            {
                "property_id": property_id,
            },
        )
        self.conn.commit()

    def get_links_to_object(self, obj_id: int) -> List[LinkRepr]:
        """
        Retrieve the links to an object as link representation objects.
        """
        cur: Cursor = self.conn.cursor()
        rows: List[Row] = cur.execute(
            """
            select distinct
                objects.title
            from
                links as links
            join
                objects as objects
            on
                objects.id = links.from_object_id
            where
                to_object_id = :to_object_id;
            """,
            {
                "to_object_id": obj_id,
            },
        ).fetchall()
        return [
            LinkRepr(
                title=row["title"],
            )
            for row in rows
        ]

    #
    # Dangling link methods
    #

    def create_dangling_link(
        self,
        from_object_id: int,
        from_property_id: int,
        to_object_title: str,
    ) -> id:
        """
        Create a dangling link.
        """
        cur: Cursor = self.conn.cursor()
        cur.execute(
            """
            insert into dangling_links
                (from_object_id, from_property_id, to_object_title)
            values
                (:from_object_id, :from_property_id, :to_object_title)
            returning id;
            """,
            {
                "from_object_id": from_object_id,
                "from_property_id": from_property_id,
                "to_object_title": to_object_title,
            },
        )
        link_id: int = list(cur)[0][0]
        self.conn.commit()
        return link_id

    def get_dangling_links_to_title(
        self, to_object_title: str
    ) -> List[DanglingLinkRec]:
        """
        Retrieve dangling links to an object with the given title.
        """
        cur: Cursor = self.conn.cursor()
        rows: List[Row] = cur.execute(
            """
            select
                id, from_object_id, from_property_id
            from
                dangling_links
            where
                to_object_title = :to_object_title;
            """,
            {
                "to_object_title": to_object_title,
            },
        ).fetchall()
        return [
            DanglingLinkRec(
                id=row["id"],
                from_object_id=row["from_object_id"],
                from_property_id=row["from_property_id"],
                to_object_title=to_object_title,
            )
            for row in rows
        ]

    def delete_dangling_link(self, link_id: int):
        """
        Delete a dangling link.
        """
        cur: Cursor = self.conn.cursor()
        cur.execute(
            """
            delete from
                dangling_links
            where
                id = :link_id
            """,
            {
                "link_id": link_id,
            },
        )
        self.conn.commit()

    #
    # Search methods
    #

    def search_objects(self, query: str) -> Iterable[ObjectRec]:
        a: List[ObjectRec] = self._search_objects_by_title(query)
        b: List[ObjectRec] = self._search_objects_by_property_text(query)
        d: Dict[int, ObjectRec] = {obj.id: obj for obj in a}
        for obj in b:
            if obj.id not in d:
                d[obj.id] = obj
        return d.values()

    def _search_objects_by_title(self, title: str) -> List[ObjectRec]:
        cur: Cursor = self.conn.cursor()
        rows: List[Row] = cur.execute(
            """
            select
                id, title, class_id, directory_id, icon_emoji, cover_id, created_at, modified_at
            from
                objects
            where
                title like :title;
            """,
            {
                "title": f"%{title}%",
            },
        ).fetchall()
        return [
            ObjectRec(
                id=row["id"],
                title=row["title"],
                class_id=row["class_id"],
                directory_id=row["directory_id"],
                icon_emoji=row["icon_emoji"],
                cover_id=row["cover_id"],
                created_at=row["created_at"],
                modified_at=row["modified_at"],
            )
            for row in rows
        ]

    def _search_objects_by_property_text(self, query: str) -> List[ObjectRec]:
        cur: Cursor = self.conn.cursor()
        rows: List[Row] = cur.execute(
            """
            select
                objects.id as id,
                objects.title as title,
                objects.class_id as class_id,
                objects.directory_id as directory_id,
                objects.icon_emoji as icon_emoji,
                objects.cover_id as cover_id,
                objects.created_at as created_at,
                objects.modified_at as modified_at
            from
                properties as properties
            join
                objects as objects
            on
                properties.object_id = objects.id
            where
                properties.id in (
                    select
                        id
                    from
                        properties_fts
                    where
                        properties_fts match :query
                );
            """,
            {
                "query": query,
            },
        ).fetchall()
        return [
            ObjectRec(
                id=row["id"],
                title=row["title"],
                class_id=row["class_id"],
                directory_id=row["directory_id"],
                icon_emoji=row["icon_emoji"],
                cover_id=row["cover_id"],
                created_at=row["created_at"],
                modified_at=row["modified_at"],
            )
            for row in rows
        ]
