import { useEffect, useState, MouseEvent } from "react";
import { Link } from "react-router-dom";
import IconWidget from "./IconWidget";
import SimpleContainer from "./SimpleContainer";
import { ClassRec } from "./types";

interface State {
    loaded: boolean;
    classes: Array<ClassRec>;
}

export default function ClassList() {
    const [classTitle, setClassTitle] = useState<string>("");
    const [state, setState] = useState<State>({ loaded: false, classes: [] });

    useEffect(() => {
        if (!state.loaded) {
            fetch("/api/classes")
                .then(res => res.json())
                .then((data) => setState({ classes: data.data, loaded: true }));
        }
    });

    function handleCreateClass(event: MouseEvent<HTMLButtonElement>) {
        event.preventDefault();
        const title = classTitle.trim();
        if (title.length === 0) {
            window.alert("The title of a class cannot be empty.");
        } else {
            fetch("/api/classes",
                {
                    headers: {
                        "Accept": "application/json",
                        "Content-Type": "application/json"
                    },
                    method: "POST",
                    body: JSON.stringify({
                        "title": title,
                        "icon_emoji": "",
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
                    setClassTitle("");
                    setState({
                        loaded: state.loaded,
                        classes: [...state.classes, data.data],
                    });
                });
        }
    }

    function handleDeleteClass(classId: number) {
        if (window.confirm("Deleting this class will delete all objects with this class. Proceed?")) {
            fetch(`/api/classes/${classId}`,
                {
                    headers: {
                        "Accept": "application/json",
                        "Content-Type": "application/json"
                    },
                    method: "DELETE",
                }
            )
                .then(response => response.json())
                .then(data => {
                    if (data.error) {
                        window.alert(data.error.title + ": " + data.error.message);
                    }
                })
        }
    }

    function handleEmojiChange(cls: ClassRec, emojiId: string) {
        fetch(`/api/classes/${cls.id}`,
            {
                headers: {
                    "Accept": "application/json",
                    "Content-Type": "application/json"
                },
                method: "POST",
                body: JSON.stringify({
                    "title": cls.title,
                    "icon_emoji": emojiId,
                })
            }
        )
            .then(response => response.json())
            .then(data => {
                if (data.error) {
                    window.alert(data.error.title + ": " + data.error.message);
                }
                const existing = state.classes.filter(c => (c.id !== cls.id));
                setState({
                    loaded: state.loaded,
                    classes: [
                        ...existing,
                        data.data
                    ],
                });
            })
    }

    if (state.loaded) {
        const { classes } = state;

        return (
            <SimpleContainer
                title={<span>All Classes</span>}
                body={
                    <div>
                        <table>
                            <thead>
                                <tr>
                                    <th>
                                        ID
                                    </th>
                                    <th>
                                        Icon
                                    </th>
                                    <th>
                                        Title
                                    </th>
                                    <th>
                                        Delete
                                    </th>
                                </tr>
                            </thead>
                            <tbody>
                                {
                                    classes.map(cls => (
                                        <tr key={cls.id}>
                                            <td>
                                                <Link to={`/classes/${cls.id}`}>
                                                    {cls.id}
                                                </Link>
                                            </td>
                                            <td>
                                                <IconWidget
                                                    size={64}
                                                    initialEmoji={cls.icon_emoji}
                                                    onChange={e => handleEmojiChange(cls, e)}
                                                />
                                            </td>
                                            <td>
                                                <Link to={`/classes/${cls.id}`}>
                                                    {cls.title}
                                                </Link>
                                            </td>
                                            <td>
                                                <button onClick={_ => handleDeleteClass(cls.id)}>
                                                    Delete Class
                                                </button>
                                            </td>
                                        </tr>
                                    ))
                                }
                            </tbody>
                        </table>
                        <div>
                            <h2>Add Class</h2>
                            <input type="text" value={classTitle} onChange={e => setClassTitle(e.target.value)} />
                            <button onClick={handleCreateClass}>Create Class</button>
                        </div>
                    </div>
                }
            />
        );
    } else {
        return (
            <SimpleContainer
                title={<span>All Classes</span>}
                body={<p>Loading...</p>}
            />
        );
    }
}