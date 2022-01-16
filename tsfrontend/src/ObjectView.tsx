import { useState, useEffect } from "react";
import { ObjectDetailRec } from "./types";
import { useParams } from "react-router-dom";
import CreateObject from "./CreateObject";
import ObjectEdit from "./ObjectEdit";

interface State {
    loaded: boolean;
    obj: ObjectDetailRec | null;
}

export default function ObjectView() {
    const [state, setState] = useState<State>({ loaded: false, obj: null });
    let params = useParams();

    useEffect(() => {
        if (!state.loaded) {
            fetch(`http://localhost:5000/api/objects/${params.title}`)
                .then(res => res.json())
                .then((data) => {
                    if (data.data) {
                        setState({ loaded: true, obj: data.data });
                    } else {
                        setState({ loaded: true, obj: null });
                    }
                });
        }
    });

    if (state.loaded) {
        if (state.obj) {
            return (
                <ObjectEdit obj={state.obj} />
            );
        } else {
            return (
                <CreateObject defaultTitle={params.title || ""} />
            );
        }
    } else {
        return <p>Loading...</p>
    }
}