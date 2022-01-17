import { MouseEvent, useEffect, useState } from "react";
import Editor from "./Editor";
import FilePropWidget from "./FilePropWidget";
import { ObjectDetailRec, PropValueRec } from "./types";
import IconWidget from "./IconWidget";
import styles from "./ObjectEdit.module.css";
import { humanizeDate } from "./utils";
import DirectorySelect from "./DirectorySelect";

interface Props {
    obj: ObjectDetailRec;
}

type PropValues = { [key: string]: string | number | null; };

export default function ObjectEdit(props: Props) {
    const [title, setTitle] = useState<string>(props.obj.title);
    const [emoji, setEmoji] = useState<string>(props.obj.icon_emoji);
    const [dirId, setDirId] = useState<number | null>(props.obj.directory_id);
    const [propValues, setPropValues] = useState<PropValues>({});

    useEffect(() => {
        const initialPropValues: PropValues = {};
        for (const prop of props.obj.properties) {
            if (prop.class_prop_type === "PROP_RICH_TEXT") {
                initialPropValues[prop.class_prop_title] = prop.value_text;
            } else if (prop.class_prop_type === "PROP_FILE") {
                initialPropValues[prop.class_prop_title] = prop.value_file;
            }
        }
        setPropValues(initialPropValues);
    }, [props.obj]);

    function handleEditorChange(name: string, doc: any) {
        const newValues = Object.assign({}, propValues);
        newValues[name] = JSON.stringify(doc);
        setPropValues(newValues);
    }

    function handleFileUpload(name: string, fileId: number) {
        const newValues = Object.assign({}, propValues);
        newValues[name] = fileId;
        setPropValues(newValues);
        console.log(newValues);
    }

    function handleEmojiChange(emojiId: string) {
        setEmoji(emojiId);
    }

    function renderValue(propval: PropValueRec) {
        if (propval.class_prop_type === "PROP_RICH_TEXT") {
            const initial = JSON.parse(propval.value_text!);
            return <Editor initialDoc={initial} onChange={(doc: any) => handleEditorChange(propval.class_prop_title, doc)} />;
        } else if (propval.class_prop_type === "PROP_FILE") {
            return <FilePropWidget
                initialFileId={propval.value_file}
                onUpload={(fileId: number) => handleFileUpload(propval.class_prop_title, fileId)} />;
        }
    }

    function handleSave(event: MouseEvent<HTMLButtonElement>) {
        event.preventDefault();
        if (title.trim().length === 0) {
            window.alert("The title of an object cannot be empty.");
            return;
        }
        fetch(`http://localhost:5000/api/objects/${props.obj.title}`,
            {
                headers: {
                    "Accept": "application/json",
                    "Content-Type": "application/json"
                },
                method: "POST",
                body: JSON.stringify({
                    "title": title.trim(),
                    "directory_id": dirId,
                    "icon_emoji": emoji,
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
        <div className={styles.container}>
            <div className={styles.box}>
                <div className={styles.titleContainer}>
                    <IconWidget size={44} initialEmoji={emoji} onChange={handleEmojiChange} />
                    <input className={styles.title} type="text" value={title} onChange={(e) => setTitle(e.target.value)} />
                </div>
                <div className={styles.directoryContainer}>
                    In directory: <DirectorySelect initialValue={dirId} onChange={handleDirectoryChange} />
                </div>
                <div>
                    <table className={styles.properties}>
                        <tbody>
                            {
                                props.obj.properties.map((propval: PropValueRec) =>
                                    <tr className={styles.property} key={propval.id}>
                                        <td className={styles.propTitle}>
                                            {propval.class_prop_title}
                                        </td>
                                        <td className={styles.propValue}>
                                            {renderValue(propval)}
                                        </td>
                                    </tr>
                                )
                            }
                        </tbody>
                    </table>
                </div>
                <div className={styles.metadata}>
                    <table>
                        <tbody>
                            <tr>
                                <td className={styles.label}>
                                    Created at
                                </td>
                                <td className={styles.value}>
                                    {humanizeDate(props.obj.created_at)}
                                </td>
                            </tr>
                            <tr>
                                <td className={styles.label}>
                                    Modified at
                                </td>
                                <td className={styles.value}>
                                    {humanizeDate(props.obj.modified_at)}
                                </td>
                            </tr>
                        </tbody>
                    </table>
                </div>
            </div>
            <button className={styles.button} onClick={handleSave}>Save</button>
        </div >
    )
}