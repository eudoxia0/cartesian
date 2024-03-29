pragma foreign_keys = ON;

-- A single-row table for storing configuration data.
create table configuration (
    id integer primary key,
    tex_macros text not null,

    constraint id_is_zero check (id = 0)
);

create table files (
    id integer primary key autoincrement,
    filename text not null,
    mime_type text not null,
    size integer not null,
    hash text not null,
    created_at integer not null,
    data blob not null,

    constraint mime_type_non_empty check(mime_type <> ''),
    constraint filename_non_empty check(filename <> ''),
    constraint hash_non_empty check(hash <> ''),
    constraint positive_size check(size > 0),
    constraint positive_created_at check(created_at > 0)
);

create table directories (
    id integer primary key autoincrement,
    title text not null,
    icon_emoji text not null,
    cover_id integer,
    parent_id integer,
    created_at integer not null,

    foreign key (cover_id) references files(id) on update cascade on delete set null,
    foreign key (parent_id) references directories(id) on update cascade on delete set null,

    constraint unique_title unique (title),
    constraint non_empty_title check (title <> ''),
    -- Note that this constraint is insufficient to ensure
    -- directory hierarchies don't form cycles.
    constraint non_cyclical check (id <> parent_id),
    constraint positive_created_at check(created_at > 0)
);

create table classes (
    id integer primary key autoincrement,
    title text not null,
    icon_emoji text not null,

    constraint unique_title unique (title),
    constraint non_empty_title check (title <> '')
);

create table class_props (
    id integer primary key autoincrement,
    class_id integer not null,
    title text not null,
    type integer not null,
    description text not null,
    -- If the property is of type SELECT, this is the comma-separated list of options.
    select_options text not null,

    foreign key (class_id) references classes(id) on update cascade on delete cascade,

    constraint unique_title_per_class unique (title, class_id),
    constraint non_empty_title check (title <> ''),

    -- Property types:
    --
    --   RICH_TEXT = 0
    --   FILE      = 1
    --   BOOLEAN   = 2
    --   SELECT    = 3
    --   LINK      = 4
    --   LINKS     = 5
    constraint valid_prop_type check (type in (0, 1, 2, 3, 4, 5))
);

create table objects (
    id integer primary key autoincrement,
    title text not null,
    class_id integer not null,
    directory_id integer,
    icon_emoji text not null,
    cover_id integer,
    created_at integer not null,
    modified_at integer not null,

    -- Cannot delete classes if they have objects.
    foreign key (class_id) references classes(id) on update cascade on delete cascade,
    foreign key (directory_id) references directories(id) on update cascade on delete set null,
    foreign key (cover_id) references files(id) on update cascade on delete set null,

    constraint unique_title unique (title),
    constraint non_empty_title check (title <> ''),
    constraint positive_created_at check(created_at > 0),
    constraint positive_modified_at check(modified_at > 0)
);

create table properties (
    id integer primary key autoincrement,
    class_prop_id integer not null,
    class_prop_title text not null,
    class_prop_type integer not null,
    object_id integer not null,

    value_integer integer,
    value_text text,

    foreign key (class_prop_id) references class_props(id) on update cascade on delete cascade,
    constraint non_empty_class_prop_title check (class_prop_title <> ''),
    constraint valid_class_prop_type check (class_prop_type in (0, 1, 2, 3, 4, 5)),
    foreign key (object_id) references objects(id) on update cascade on delete cascade
);

create virtual table properties_fts using fts5 (
    id,
    value_text,
    content=properties,
    content_rowid=id
);

create trigger properties_fts_insert
after insert on properties
begin
    insert into properties_fts
        (id, value_text)
    values
        (new.id, new.value_text);
end;

create trigger properties_fts_delete
after delete on properties
begin
    insert into properties_fts
        (properties_fts, id, value_text)
    values
        ('delete', old.id, old.value_text);
end;

create trigger properties_fts_update
after update on properties
begin
    insert into properties_fts
        (properties_fts, id, value_text)
    values
        ('delete', old.id, old.value_text);
    insert into properties_fts
        (id, value_text)
    values
        (new.id, new.value_text);
end;

create table property_changes (
    id integer primary key autoincrement,
    object_id integer not null,
    prop_id integer,
    -- If the property is deleted, we still want its version history, so we store the title.
    prop_title text not null,
    created_at integer not null,

    value_integer integer,
    value_text text,

    foreign key (object_id) references objects(id) on update cascade on delete cascade,
    foreign key (prop_id) references properties(id) on update cascade on delete set null,
    constraint non_empty_prop_title check (prop_title <> ''),
    constraint positive_created_at check(created_at > 0)
);

create table links (
    id integer primary key autoincrement,
    from_object_id integer not null,
    from_property_id integer not null,
    to_object_id integer not null,

    foreign key (from_object_id) references objects(id) on update cascade on delete cascade,
    foreign key (from_property_id) references properties(id) on update cascade on delete cascade,
    foreign key (to_object_id) references objects(id) on update cascade on delete cascade,
    constraint no_self_links check (from_property_id <> to_object_id),
    constraint unique_pair unique (from_property_id, to_object_id)
);

create table dangling_links (
    id integer primary key autoincrement,
    from_object_id integer not null,
    from_property_id integer not null,
    to_object_title text not null,

    foreign key (from_object_id) references objects(id) on update cascade on delete cascade,
    foreign key (from_property_id) references properties(id) on update cascade on delete cascade,
    constraint non_empty_title check (to_object_title <> '')
);

-- Initialization

insert into configuration (id, tex_macros) values (0, "");
