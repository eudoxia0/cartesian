import { useEffect, useState, MouseEvent, ChangeEvent } from "react";
import SimpleContainer from "./SimpleContainer";
import styles from "./Settings.module.css";

interface State {
    loaded: boolean;
    macros: string;
}

export default function Settings() {
    const [state, setState] = useState<State>({ loaded: false, macros: "" });

    useEffect(() => {
        if (!state.loaded) {
            fetch("http://localhost:5000/api/tex-macros")
                .then(res => res.json())
                .then((data) => {
                    setState({ loaded: true, macros: data.data });
                });
        }
    });

    function handleChange(event: ChangeEvent<HTMLTextAreaElement>) {
        event.preventDefault();
        setState({
            loaded: state.loaded,
            macros: event.target.value,
        });
    }

    function handleSaveMacros(event: MouseEvent<HTMLButtonElement>) {
        event.preventDefault();
        fetch("http://localhost:5000/api/tex-macros",
            {
                headers: {
                    "Accept": "application/json",
                    "Content-Type": "application/json"
                },
                method: "POST",
                body: JSON.stringify({
                    "macros": state.macros,
                })
            }
        )
            .then(response => response.json())
            .then(data => {
                if (data.error) {
                    window.alert(data.error.title + ": " + data.error.message);
                }
            })
    }

    if (state.loaded) {
        return (
            <SimpleContainer
                title="Settings"
                body={
                    <div className={styles.settings}>
                        <h2>TeX Macros</h2>
                        <textarea value={state.macros} onChange={handleChange}></textarea>
                        <button onClick={handleSaveMacros}>
                            Save
                        </button>
                    </div>
                } />
        );
    } else {
        return (
            <SimpleContainer
                title="Settings"
                body={<p>Loading...</p>} />
        );
    }
}