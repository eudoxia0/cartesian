export interface FileRec {
    id: number;
    filename: string;
    mime_type: string;
    created_at: number;
    size: number;
}

export interface ClassRec {
    id: number;
    title: string;
    icon_emoji: string;
    properties: Array<PropRec>,
}

export type PropType = "PROP_RICH_TEXT" | "PROP_FILE";

export interface PropRec {
    id: number;
    type: PropType;
    title: string;
    description: string;
}

export interface DirectoryRec {
    id: number;
    title: string;
    icon_emoji: string;
    parent_id: number;
}

export interface ObjectSummaryRec {
    id: number;
    title: string;
    class_id: number;
    directory_id: number;
    icon_emoji: string;
    created_at: number;
    modified_at: number;
}

export interface PropValueRec {
    id: number;
    object_id: number;
    class_prop_id: number;
    class_prop_title: string;
    class_prop_type: PropType;
    value_text: string | null;
    value_file: number | null;
}

export interface ObjectDetailRec {
    id: number;
    title: string;
    class_id: number;
    directory_id: number;
    icon_emoji: string;
    created_at: number;
    modified_at: number;
    properties: Array<PropValueRec>;
}
