import { MouseEvent, useEffect, useState } from "react";
import Editor from "./Editor";
import FilePropWidget from "./FilePropWidget";
import { ClassRec, PropType } from "./types";
import { PropRec } from "./types";


interface Props {
    cls: ClassRec;
    onCreate: (props: { [key: string]: string | number | null; }) => void;
}

type PropValues = { [key: string]: string | number | null; };

export default function CreateObjectForProps(props: Props) {
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
            <h1>Creating Object for Class {props.cls.title}</h1>
            <hr />
            <table>
                <thead>
                    <tr>
                        <th>
                            Property
                        </th>
                        <th>
                            Value
                        </th>
                    </tr>
                </thead>
                <tbody>
                    {
                        props.cls.properties.map((prop: PropRec) =>
                            <tr key={prop.id}>
                                <td>
                                    {prop.title}
                                </td>
                                <td>
                                    {renderValue(prop.title, prop.type)}
                                </td>
                            </tr>
                        )
                    }
                </tbody>
            </table>
            <button onClick={handleCreate}>Create {props.cls.title}</button>
        </div>
    );
}