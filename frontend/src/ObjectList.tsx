import { useEffect, useState } from "react";
import { Link } from "react-router-dom";
import SimpleContainer from "./SimpleContainer";
import { ObjectSummaryRec } from "./types";
import { humanizeDate } from "./utils";

interface State {
    loaded: boolean;
    objects: Array<ObjectSummaryRec>;
}

export default function ObjectList() {
    const [state, setState] = useState<State>({ loaded: false, objects: [] });

    useEffect(() => {
        if (!state.loaded) {
            fetch("/api/objects")
                .then(res => res.json())
                .then((data) => setState({ loaded: true, objects: data.data }));
        }
    });

    if (state.loaded) {
        const { objects } = state;

        return (
            <SimpleContainer
                title={<span>List of Objects</span>}
                body={
                    <table>
                        <thead>
                            <tr>
                                <th>
                                    ID
                                </th>
                                <th>
                                    Title
                                </th>
                                <th>
                                    Class
                                </th>
                                <th>
                                    Directory
                                </th>
                                <th>
                                    Created At
                                </th>
                                <th>
                                    Modified At
                                </th>
                            </tr>
                        </thead>
                        <tbody>
                            {
                                objects.map(obj => (
                                    <tr key={obj.id}>
                                        <td>
                                            <Link to={`/objects/${obj.title}`}>
                                                {obj.id}
                                            </Link>
                                        </td>
                                        <td>
                                            <Link to={`/objects/${obj.title}`}>
                                                <code>{obj.title}</code>
                                            </Link>
                                        </td>
                                        <td>
                                            <code>{obj.class_id}</code>
                                        </td>
                                        <td>
                                            <code>{obj.directory_id}</code>
                                        </td>
                                        <td>
                                            {humanizeDate(obj.created_at)}
                                        </td>
                                        <td>
                                            {humanizeDate(obj.modified_at)}
                                        </td>
                                    </tr>
                                ))
                            }
                        </tbody>
                    </table>
                }
            />
        );
    } else {
        return (
            <SimpleContainer
                title={<span>List of Objects</span>}
                body={<p>Loading...</p>}
            />
        );
    }
}