import { ClassRec, PropRec } from "./types";
import { useEffect, useState } from "react";
import { useParams } from "react-router-dom";
import ClassProperties from "./ClassProperties";
import ClassNewProperty from "./ClassNewProperty";

interface State {
    loaded: boolean;
    cls: ClassRec | null;
}

export default function ClassDetail() {
    const [state, setState] = useState<State>({ loaded: false, cls: null });
    let params = useParams();

    useEffect(() => {
        if (!state.loaded) {
            let id = parseInt(params.classId || "", 10);
            fetch(`http://localhost:5000/api/classes/${id}`)
                .then(res => res.json())
                .then((data) => {
                    const cls = data.data;
                    setState({ loaded: true, cls: cls, });
                });
        }
    });

    function addProperty(prop: PropRec) {
        if (state.cls) {
            setState({ loaded: state.loaded, cls: { ...state.cls, properties: [...state.cls!.properties, prop] }, });
        }
    }
    if (state.loaded) {
        if (state.cls !== null) {
            const cls: ClassRec = state.cls;

            return (
                <div>
                    <h2>Class Details</h2>
                    <div>
                        <ol>
                            <li>
                                <b>ID:</b> {cls.id}
                            </li>
                            <li>
                                <b>Title:</b> {cls.title}
                            </li>
                            <li>
                                <b>Class Properties:</b>
                                <ClassProperties classProps={state.cls.properties} />
                            </li>
                        </ol>
                        <ClassNewProperty id={cls.id} addProperty={addProperty} />
                    </div>
                </div>
            )
        }
    }

    return (
        <div>
            <h2>Class Details</h2>
            <div>
                Loading...
            </div>
        </div>
    )
}