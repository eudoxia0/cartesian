import json
from typing import List, Tuple, Optional
from sqlite3 import Connection, Cursor
from dataclasses import dataclass
from enum import Enum


#
# Configuration functions
#
from theatre.prosemirror import parse_document, emit_document
from theatre.rename_link import rename_link


def get_tex_macros(conn: Connection) -> str:
    cur: Cursor = conn.cursor()
    rows: List[Tuple] = cur.execute(
        """
        select
            tex_macros
        from
            configuration;
        """
    ).fetchall()
    return rows[0][0]


def set_tex_macros(conn: Connection, macros: str):
    cur: Cursor = conn.cursor()
    cur.execute(
        """
        update
            configuration
        set
            tex_macros = :macros;
        """,
        {"macros": macros},
    ).fetchall()
    conn.commit()


#
# File functions
#


def create_file(
    conn: Connection,
    filename: str,
    mime_type: str,
    size: int,
    hash: str,
    created_at: int,
    blob: bytes,
) -> int:
    cur: Cursor = conn.cursor()
    results = cur.execute(
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
            "hash": hash,
            "created_at": created_at,
            "data": blob,
        },
    )
    id: int = list(results)[0][0]
    conn.commit()
    return id


def file_exists(conn: Connection, id: int):
    cur: Cursor = conn.cursor()
    rows: List[Tuple] = cur.execute(
        """
        select
            id
        from
            files
        where
            id = :id;
        """,
        {
            "id": id,
        },
    ).fetchall()
    return bool(rows)


#
# Directory functions
#


def directory_exists(conn: Connection, id: int) -> bool:
    cur: Cursor = conn.cursor()
    rows: List[Tuple] = cur.execute(
        """
        select
            id
        from
            directories
        where
            id = :id;
        """,
        {
            "id": id,
        },
    ).fetchall()
    return bool(rows)


#
# Class functions
#


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


def class_exists(conn: Connection, id: int) -> bool:
    cur: Cursor = conn.cursor()
    rows: List[Tuple] = cur.execute(
        """
        select
            id
        from
            classes
        where
            id = :id;
        """,
        {
            "id": id,
        },
    ).fetchall()
    return bool(rows)


def list_classes(conn: Connection) -> List[ClassRec]:
    cur: Cursor = conn.cursor()
    rows: List[Tuple] = cur.execute(
        """
        select
            id, title, icon_emoji
        from
            classes
        order by
            id asc;
        """
    ).fetchall()
    return [ClassRec(id=row["id"], title=row["title"], icon_emoji=row["icon_emoji"]) for row in rows]


def get_class(conn: Connection, id: int) -> Optional[ClassRec]:
    cur: Cursor = conn.cursor()
    rows: List[Tuple] = cur.execute(
        """
        select
            id, title, icon_emoji
        from
            classes
        where
            id = :id;
        """,
        {
            "id": id,
        },
    ).fetchall()
    if rows:
        row: Tuple = rows[0]
        return ClassRec(id=row["id"], title=row["title"], icon_emoji=row["icon_emoji"])
    else:
        return None


def create_class(conn: Connection, title: str, icon_emoji: str) -> ClassRec:
    cur: Cursor = conn.cursor()
    cur.execute(
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
    )
    cls_id: int = list(cur)[0][0]
    conn.commit()
    return ClassRec(id=cls_id, title=title, icon_emoji=icon_emoji)

def delete_class(conn: Connection, cls_id: int):
    cur: Cursor = conn.cursor()
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
    conn.commit()

#
# Class property functions
#


class PropertyType(Enum):
    PROP_RICH_TEXT = "PROP_RICH_TEXT"
    PROP_FILE = "PROP_FILE"

    def to_int(self) -> int:
        mapping = {
            self.PROP_RICH_TEXT: 0,
            self.PROP_FILE: 1,
        }
        return mapping[self]


def property_type_from_int(value: int) -> "PropertyType":
    mapping = {
        0: PropertyType.PROP_RICH_TEXT,
        1: PropertyType.PROP_FILE,
    }
    return mapping[value]


@dataclass(frozen=True)
class ClassPropertyRec:
    id: int
    class_id: int
    title: str
    type: PropertyType
    description: str

    def to_json(self) -> dict:
        return {
            "id": self.id,
            "class_id": self.class_id,
            "title": self.title,
            "description": self.description,
            "type": self.type.value,
        }

def class_property_exists(conn: Connection, cls_prop_id: int) -> bool:
    cur: Cursor = conn.cursor()
    rows: List[Tuple] = cur.execute(
        """
        select
            id
        from
            class_props
        where
            id = :id;
        """,
        {
            "id": cls_prop_id,
        },
    ).fetchall()
    return bool(rows)


def get_class_properties(conn: Connection, class_id: int) -> List[ClassPropertyRec]:
    cur: Cursor = conn.cursor()
    rows: List[Tuple] = cur.execute(
        """
        select
            id, class_id, title, type, description
        from
            class_props
        where
            class_id = :class_id
        order by
            id asc;
        """,
        {
            "class_id": class_id,
        },
    ).fetchall()
    return [
        ClassPropertyRec(
            id=id,
            class_id=class_id,
            title=title,
            type=property_type_from_int(type),
            description=description,
        )
        for id, class_id, title, type, description in rows
    ]


def create_class_property(
    conn: Connection,
    class_id: int,
    title: str,
    description: str,
    prop_type: PropertyType,
) -> ClassPropertyRec:
    cur: Cursor = conn.cursor()
    rows: Cursor = cur.execute(
        """
        insert into class_props
            (class_id, title, type, description)
        values
            (:class_id, :title, :type, :description)
        returning id;
        """,
        {
            "class_id": class_id,
            "title": title,
            "type": prop_type.to_int(),
            "description": description,
        },
    )
    cls_prop_id: int = list(rows)[0][0]
    conn.commit()
    return ClassPropertyRec(
        id=cls_prop_id,
        class_id=class_id,
        title=title,
        type=prop_type,
        description=description,
    )

def delete_class_property(conn: Connection, cls_prop_id: int):
    cur: Cursor = conn.cursor()
    cur.execute(
        """
        delete from
            class_props
        where
            id = :id
        """,
        {
            "id": cls_prop_id,
        }
    )
    conn.commit()

#
# Object functions
#


@dataclass(frozen=True)
class ObjectRec:
    id: int
    title: str
    class_id: int
    directory_id: Optional[int]
    icon_emoji: str
    created_at: int
    modified_at: int

    def to_json(self) -> dict:
        return {
            "id": self.id,
            "title": self.title,
            "class_id": self.class_id,
            "directory_id": self.directory_id,
            "icon_emoji": self.icon_emoji,
            "created_at": self.created_at,
            "modified_at": self.modified_at,
        }


def list_objects(conn: Connection) -> List[ObjectRec]:
    cur: Cursor = conn.cursor()
    rows: List[Tuple] = cur.execute(
        """
        select
            id, title, class_id, directory_id, icon_emoji, created_at, modified_at
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
            created_at=row["created_at"],
            modified_at=row["modified_at"],
        )
        for row in rows
    ]


def list_objects_in_directory(conn: Connection, dir_id: int) -> List[ObjectRec]:
    cur: Cursor = conn.cursor()
    rows: List[Tuple] = cur.execute(
        """
        select
            id, title, class_id, icon_emoji, created_at, modified_at
        from
            objects
        where
            directory_id = :directory_id 
        order by
            id asc;
        """,
        {
            "directory_id": dir_id,
        }
    ).fetchall()
    return [
        ObjectRec(
            id=row["id"],
            title=row["title"],
            class_id=row["class_id"],
            directory_id=dir_id,
            icon_emoji=row["icon_emoji"],
            created_at=row["created_at"],
            modified_at=row["modified_at"],
        )
        for row in rows
    ]


def get_object_by_title(conn: Connection, title: str) -> Optional[ObjectRec]:
    cur: Cursor = conn.cursor()
    rows: List[Tuple] = cur.execute(
        """
        select
            id, class_id, directory_id, icon_emoji, created_at, modified_at
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
        row: Tuple = rows[0]
        return ObjectRec(
            id=row["id"],
            title=title,
            class_id=row["class_id"],
            directory_id=row["directory_id"],
            icon_emoji=row["icon_emoji"],
            created_at=row["created_at"],
            modified_at=row["modified_at"],
        )
    else:
        return None


def create_object(
    conn: Connection,
    title: str,
    class_id: int,
    directory_id: Optional[int],
    icon_emoji: str,
    created_at: int,
    modified_at: int,
) -> id:
    cur: Cursor = conn.cursor()
    cur.execute(
        """
        insert into objects
            (title, class_id, directory_id, icon_emoji, created_at, modified_at)
        values
            (:title, :class_id, :directory_id, :icon_emoji, :created_at, :modified_at)
        returning id;
        """,
        {
            "title": title,
            "class_id": class_id,
            "directory_id": directory_id,
            "icon_emoji": icon_emoji,
            "created_at": created_at,
            "modified_at": modified_at,
        },
    )
    obj_id: int = list(cur)[0][0]
    conn.commit()
    return obj_id


#
# Object property functions
#


@dataclass(frozen=True)
class PropertyRec:
    id: int
    class_prop_id: int
    class_prop_title: str
    class_prop_type: PropertyType
    object_id: int
    value_text: Optional[str]
    value_file: Optional[int]

    def to_json(self) -> dict:
        return {
            "id": self.id,
            "class_prop_id": self.class_prop_id,
            "class_prop_title": self.class_prop_title,
            "class_prop_type": self.class_prop_type.value,
            "object_id": self.object_id,
            "value_text": self.value_text,
            "value_file": self.value_file,
        }


def list_object_properties(
    conn: Connection,
    object_id: int,
) -> List[PropertyRec]:
    cur: Cursor = conn.cursor()
    rows: List[Tuple] = cur.execute(
        """
        select
            id, class_prop_id, class_prop_title, class_prop_type, value_text, value_file
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
        PropertyRec(
            id=row["id"],
            class_prop_id=row["class_prop_id"],
            class_prop_title=row["class_prop_title"],
            class_prop_type=property_type_from_int(row["class_prop_type"]),
            object_id=object_id,
            value_text=row["value_text"],
            value_file=row["value_file"],
        )
        for row in rows
    ]


def get_object_property(
    conn: Connection, object_id: int, class_prop_id: int
) -> Optional[PropertyRec]:
    cur: Cursor = conn.cursor()
    rows: List[Tuple] = cur.execute(
        """
        select
            id, class_prop_title, class_prop_type, value_text, value_file
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
        row: Tuple = rows[0]
        return PropertyRec(
            id=row["id"],
            class_prop_id=class_prop_id,
            class_prop_title=row["class_prop_title"],
            class_prop_type=property_type_from_int(row["class_prop_type"]),
            object_id=object_id,
            value_text=row["value_text"],
            value_file=row["value_file"],
        )
    else:
        return None


def get_property_by_id(conn: Connection, property_id: int) -> Optional[PropertyRec]:
    cur: Cursor = conn.cursor()
    rows: List[Tuple] = cur.execute(
        """
        select
            class_prop_id, class_prop_title, class_prop_type, object_id, value_text, value_file
        from
            properties
        where
            id = :property_id;
        """,
        {
            "property_id": property_id,
        },
    ).fetchall()
    if rows:
        row: Tuple = rows[0]
        return PropertyRec(
            id=property_id,
            class_prop_id=row["class_prop_id"],
            class_prop_title=row["class_prop_title"],
            class_prop_type=property_type_from_int(row["class_prop_type"]),
            object_id=row["object_id"],
            value_text=row["value_text"],
            value_file=row["value_file"],
        )
    else:
        return None


def create_property(
    conn: Connection,
    class_prop_id: int,
    class_prop_title: str,
    class_prop_type: PropertyType,
    object_id: int,
    value_text: Optional[str],
    value_file: Optional[int],
) -> id:
    cur: Cursor = conn.cursor()
    cur.execute(
        """
        insert into properties
            (class_prop_id, class_prop_title, class_prop_type, object_id, value_text, value_file)
        values
            (:class_prop_id, :class_prop_title, :class_prop_type, :object_id, :value_text, :value_file)
        returning id;
        """,
        {
            "class_prop_id": class_prop_id,
            "class_prop_title": class_prop_title,
            "class_prop_type": class_prop_type.to_int(),
            "object_id": object_id,
            "value_text": value_text,
            "value_file": value_file,
        },
    )
    prop_id: int = list(cur)[0][0]
    conn.commit()
    return prop_id


#
# Property change functions
#


@dataclass(frozen=True)
class PropertyChangeRec:
    id: int
    object_id: int
    prop_id: int
    prop_title: str
    created_at: int
    value_text: Optional[str]
    value_file: Optional[int]

    def to_json(self) -> dict:
        return {
            "id": self.id,
            "object_id": self.object_id,
            "prop_id": self.prop_id,
            "prop_title": self.prop_title,
            "created_at": self.created_at,
            "value_text": self.value_text,
            "value_file": self.value_file,
        }


def get_property_changes(conn: Connection, prop_id: int) -> List[PropertyChangeRec]:
    cur: Cursor = conn.cursor()
    rows: List[Tuple] = cur.execute(
        """
        select
            id, object_id, prop_title, created_at, value_text, value_file
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
        PropertyChangeRec(
            id=row["id"],
            object_id=row["object_id"],
            prop_id=prop_id,
            prop_title=row["prop_title"],
            created_at=row["created_at"],
            value_text=row["value_text"],
            value_file=row["value_file"],
        )
        for row in rows
    ]


def create_property_change(
    conn: Connection,
    object_id: int,
    prop_id: int,
    prop_title: str,
    created_at: int,
    value_text: Optional[str],
    value_file: Optional[int],
) -> id:
    cur: Cursor = conn.cursor()
    cur.execute(
        """
        insert into property_changes
            (object_id, prop_id, prop_title, created_at, value_text, value_file)
        values
            (:object_id, :prop_id, :prop_title, :created_at, :value_text, :value_file)
        returning id;
        """,
        {
            "object_id": object_id,
            "prop_id": prop_id,
            "prop_title": prop_title,
            "created_at": created_at,
            "value_text": value_text,
            "value_file": value_file,
        },
    )
    prop_change_id: int = list(cur)[0][0]
    conn.commit()
    return prop_change_id


#
# Link functions
#


@dataclass(frozen=True)
class LinkRec:
    id: int
    from_property_id: int
    to_object_id: int

    def to_json(self) -> dict:
        return {
            "id": self.id,
            "from_property_id": self.from_property_id,
            "to_object_id": self.to_object_id,
        }


def get_links_from(conn: Connection, from_property_id: int) -> List[LinkRec]:
    cur: Cursor = conn.cursor()
    rows: List[Tuple] = cur.execute(
        """
        select
            id, to_object_id
        from
            links
        where
            from_property_id = :from_property_id;
        """,
        {
            "from_property_id": from_property_id,
        },
    ).fetchall()
    return [
        LinkRec(
            id=row["id"],
            from_property_id=from_property_id,
            to_object_id=row["to_object_id"],
        )
        for row in rows
    ]


def get_links_to(conn: Connection, to_object_id: int) -> List[LinkRec]:
    cur: Cursor = conn.cursor()
    rows: List[Tuple] = cur.execute(
        """
        select
            id, from_property_id
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
            from_property_id=row["from_property_id"],
            to_object_id=to_object_id,
        )
        for row in rows
    ]


def create_link(
    conn: Connection,
    from_property_id: int,
    to_object_id: int,
) -> id:
    cur: Cursor = conn.cursor()
    cur.execute(
        """
        insert into links
            (from_property_id, to_object_id)
        values
            (:from_property_id, :to_object_id)
        returning id;
        """,
        {
            "from_property_id": from_property_id,
            "to_object_id": to_object_id,
        },
    )
    link_id: int = list(cur)[0][0]
    conn.commit()
    return link_id


def delete_links_from(conn: Connection, property_id: int):
    cur: Cursor = conn.cursor()
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
    conn.commit()


def edit_property(
    conn: Connection,
    property_id: int,
    value_text: Optional[str],
    value_file: Optional[int],
):
    cur: Cursor = conn.cursor()
    cur.execute(
        """
        update
            properties
        set
            value_text = :value_text,
            value_file = :value_file
        where
            id = :property_id;
        """,
        {
            "property_id": property_id,
            "value_text": value_text,
            "value_file": value_file,
        },
    )
    conn.commit()


def update_object(
    conn: Connection,
    obj: ObjectRec,
    new_title: str,
    new_directory_id: Optional[int],
    new_icon_emoji: str,
    modified_at: int,
):
    # Update the object itself
    cur: Cursor = conn.cursor()
    cur.execute(
        """
        update
            objects
        set
            title = :title,
            directory_id = :directory_id,
            icon_emoji = :icon_emoji,
            modified_at = :modified_at
        where
            id = :object_id;
        """,
        {
            "object_id": obj.id,
            "title": new_title,
            "directory_id": new_directory_id,
            "icon_emoji": new_icon_emoji,
            "modified_at": modified_at,
        },
    ).fetchall()
    conn.commit()
    # If the title is different, rename links.
    if obj.title != new_title:
        links: List[LinkRec] = get_links_to(conn=conn, to_object_id=obj.id)
        for link in links:
            prop: Optional[PropertyRec] = get_property_by_id(
                conn, link.from_property_id
            )
            assert prop is not None
            if prop.value_text is not None:
                doc = parse_document(json.loads(prop.value_text))
                new_doc = rename_link(doc=doc, old_title=obj.title, new_title=new_title)
                json_value: dict = emit_document(new_doc)
                new_value_text: str = json.dumps(json_value)
                edit_property(
                    conn=conn,
                    property_id=prop.id,
                    value_text=new_value_text,
                    value_file=prop.value_file,
                )
                create_property_change(
                    conn=conn,
                    object_id=obj.id,
                    prop_id=prop.id,
                    prop_title=prop.class_prop_title,
                    created_at=modified_at,
                    value_text=new_value_text,
                    value_file=prop.value_file,
                )