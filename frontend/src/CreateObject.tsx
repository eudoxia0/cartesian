import { MouseEvent, useState, useEffect } from "react";
import { ClassRec, PropRec, PropType } from "./types";
import styles from "./CreateObject.module.css";
import SimpleContainer from "./SimpleContainer";
import { Emoji } from "emoji-mart";
import Editor from "./Editor";
import FilePropWidget from "./FilePropWidget";
import DirectorySelect from "./DirectorySelect";

interface Props2 {
    cls: ClassRec;
    onCreate: (props: { [key: string]: string | number | null; }) => void;
}

type PropValues = { [key: string]: string | number | null; };

function CreateObjectForProps(props: Props2) {
    const [propValues, setPropValues] = useState<PropValues>({});

    useEffect(() => {
        const initialPropValues: PropValues = {};
        for (const prop of props.cls.properties) {
            initialPropValues[prop.title] = null;
        }
        setPropValues(initialPropValues);
    }, [props.cls]);

    function handleEditorChange(name: string, doc: any) {
        const newValues = Object.assign({}, propValues);
        newValues[name] = JSON.stringify(doc);
        setPropValues(newValues);
        console.log(newValues);
    }

    function handleFileUpload(name: string, fileId: number) {
        const newValues = Object.assign({}, propValues);
        newValues[name] = fileId;
        setPropValues(newValues);
        console.log(newValues);
    }

    function renderValue(name: string, ty: PropType) {
        if (ty === "PROP_RICH_TEXT") {
            return <Editor
                initialDoc={null}
                onChange={(doc: any) => handleEditorChange(name, doc)} />;
        } else if (ty === "PROP_FILE") {
            return <FilePropWidget
                initialFileId={null}
                onUpload={(fileId: number) => handleFileUpload(name, fileId)} />;
        }
    }

    function handleCreate(event: MouseEvent<HTMLButtonElement>) {
        event.preventDefault();
        props.onCreate(propValues);
    }

    return (
        <div>
            <table className={styles.properties}>
                <tbody>
                    {
                        props.cls.properties.map((prop: PropRec) =>
                            <tr className={styles.property} key={prop.id}>
                                <td className={styles.propTitle}>
                                    {prop.title}
                                </td>
                                <td className={styles.propValue}>
                                    {renderValue(prop.title, prop.type)}
                                </td>
                            </tr>
                        )
                    }
                </tbody>
            </table>
            <button className={styles.button} onClick={handleCreate}>Create {props.cls.title}</button>
        </div>
    );
}

interface Props {
    defaultTitle: string;
    cls: ClassRec;
}

function CreateObjectForClass(props: Props) {
    const [title, setTitle] = useState<string>(props.defaultTitle);
    const [dirId, setDirId] = useState<number | null>(null);

    function handleCreate(propValues: { [key: string]: string | number | null; }) {
        if (title.trim().length === 0) {
            window.alert("The title of an object cannot be empty.");
            return;
        }
        fetch("/api/objects",
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
                    "cover_id": null,
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
                    <input className={styles.title} type="text" value={title} onChange={(e) => setTitle(e.target.value)} />
                </div>
                <div className={styles.menuBar}>
                    <div className={styles.directoryContainer}>
                        In directory: <DirectorySelect initialValue={dirId} onChange={handleDirectoryChange} />
                    </div>
                </div>
                <CreateObjectForProps cls={props.cls} onCreate={handleCreate} />
            </div>
        </div>
    );
};

function CreateObjectInternal(props: { defaultTitle: string, classes: Array<ClassRec>; }) {
    const [selected, setSelected] = useState<number>(props.classes[0].id);

    return (
        <div className={styles.createObject}>
            <div className={styles.leftPane}>
                <h2>Select Class</h2>
                <ul>
                    {
                        props.classes.map((cls: ClassRec) =>
                            <li key={cls.id} onClick={_ => setSelected(cls.id)}>
                                {(cls.icon_emoji !== "")
                                    ?
                                    <Emoji emoji={cls.icon_emoji!} size={24} native={true} />
                                    : <img src="/classes.png" alt="" />
                                }
                                {cls.title}
                            </li>
                        )
                    }
                </ul>
            </div>
            <div className={styles.rightPane}>
                <CreateObjectForClass
                    defaultTitle={props.defaultTitle}
                    cls={props.classes.find((cls) => cls.id === selected)!} />
            </div>
        </div >
    );
}

interface State {
    loaded: boolean;
    classes: Array<ClassRec>;
}

export default function CreateObject(props: { defaultTitle: string }) {
    const [state, setState] = useState<State>({ loaded: false, classes: [] });

    useEffect(() => {
        if (!state.loaded) {
            fetch("/api/classes")
                .then(res => res.json())
                .then((data) => setState({ loaded: true, classes: data.data }));
        }
    });

    return (
        <SimpleContainer
            title="Create Object"
            body={
                state.classes.length > 0 ?
                    <CreateObjectInternal defaultTitle={props.defaultTitle} classes={state.classes} />
                    : <p>No templates to create an object from.</p>
            }
        />
    );
}