import { useState, MouseEvent } from "react";
import { PropRec } from "./types";

interface Props {
    id: number;
    addProperty: (prop: PropRec) => void;
}

export default function ClassNewProperty(props: Props) {
    const [title, setTitle] = useState<string>("");
    const [desc, setDesc] = useState<string>("");
    const [type, setType] = useState<string>("PROP_RICH_TEXT");

    function restoreDefaults() {
        setTitle("");
        setDesc("");
        setType("PROP_RICH_TEXT");
    }

    function handleAddProperty(event: MouseEvent<HTMLButtonElement>) {
        event.preventDefault();
        const eff_title: string = title.trim();
        const eff_desc: string = desc.trim();
        if (eff_title.length === 0) {
            window.alert("The name of a class property cannot be empty.");
            restoreDefaults();
            return;
        };
        if (eff_desc.length === 0) {
            window.alert("The description of a class property cannot be empty.");
            restoreDefaults();
            return;
        };
        fetch(`http://localhost:5000/api/classes/${props.id}/properties`,
            {
                headers: {
                    "Accept": "application/json",
                    "Content-Type": "application/json"
                },
                method: "POST",
                body: JSON.stringify({
                    "title": eff_title,
                    "type": type,
                    "description": eff_desc,
                })
            }
        )
            .then(response => response.json())
            .then(data => {
                if (data.error) {
                    window.alert(data.error.title + ": " + data.error.message);
                } else {
                    props.addProperty(data.data);
                }
            });
        restoreDefaults();
    }

    return (
        <div>
            <h2>Add a Property</h2>
            <form>
                <label>
                    Title
                    <input
                        type="text"
                        required
                        value={title}
                        onChange={e => setTitle(e.target.value)} />
                </label>
                <label>
                    Description
                    <input
                        type="text"
                        required
                        value={desc}
                        onChange={e => setDesc(e.target.value)} />
                </label>

                <label>
                    Type
                    <select value={type} onChange={e => setType(e.target.value)}>
                        <option value="PROP_RICH_TEXT">Rich Text</option>
                        <option value="PROP_FILE">File</option>
                    </select>
                </label>
                <button onClick={handleAddProperty}>
                    Add Property
                </button>
            </form>
        </div>
    )
}