import { useState, useEffect } from "react";
import CreateObjectForClass from "./CreateObjectForClass";
import { ClassRec } from "./types";

interface State {
    loaded: boolean;
    classes: Array<ClassRec>;
}

function CreateObjectInternal(props: { defaultTitle: string, classes: Array<ClassRec>; }) {
    const [selected, setSelected] = useState<number>(props.classes[0].id);

    function handleChange(e: any) {
        e.preventDefault();
        const id = parseInt(e.target.value, 10);
        setSelected(id);
    }

    return (
        <div>
            Class:
            <select value={selected} onChange={handleChange}>
                {props.classes.map((cls) =>
                    <option key={cls.id} value={cls.id}>{cls.title}</option>
                )}
            </select>
            <CreateObjectForClass
                defaultTitle={props.defaultTitle}
                cls={props.classes.find((cls) => cls.id === selected)!} />
        </div >
    );
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
        <div>
            <h1>Create Object</h1>
            {
                state.classes.length > 0 ?
                    <CreateObjectInternal defaultTitle={props.defaultTitle} classes={state.classes} />
                    : <p>No templates to create an object from.</p>
            }
        </div>
    );
}