import { useState } from "react";
import CreateObjectForProps from "./CreateObjectForProps";
import DirectorySelect from "./DirectorySelect";
import { ClassRec } from "./types";

interface Props {
    defaultTitle: string;
    cls: ClassRec;
}

export default function CreateObjectForClass(props: Props) {
    const [title, setTitle] = useState<string>(props.defaultTitle);
    const [dirId, setDirId] = useState<number | null>(null);

    function handleCreate(propValues: { [key: string]: string | number | null; }) {
        if (title.trim().length === 0) {
            window.alert("The title of an object cannot be empty.");
            return;
        }
        fetch("http://localhost:5000/api/objects",
            {
                headers: {
                    "Accept": "application/json",
                    "Content-Type": "application/json"
                },
                method: "POST",
                body: JSON.stringify({
                    "title": title.trim(),
                    "class_id": props.cls.id,
                    "directory_id": dirId,
                    "icon_emoji": "",
                    "values": propValues,
                })
            }
        )
            .then(response => response.json())
            .then(data => {
                if (data.error) {
                    window.alert(data.error.title + ": " + data.error.message);
                } else {
                    console.log(data.data);
                }
            });
    }

    function handleDirectoryChange(dirId: number | null) {
        setDirId(dirId);
    }

    return (
        <div>
            Title: <input type="text" value={title} onChange={(e) => setTitle(e.target.value)} />
            <DirectorySelect onChange={handleDirectoryChange} />
            <CreateObjectForProps cls={props.cls} onCreate={handleCreate} />
        </div>
    );
};