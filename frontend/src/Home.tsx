import { useEffect, useState } from "react";
import styles from "./Home.module.css";

interface Stats {
    object_count: number;
    link_count: number;
    file_count: number;
}

interface State {
    loaded: boolean;
    stats: Stats | null;
}

export default function Home() {
    const [state, setState] = useState<State>({ loaded: false, stats: null });

    useEffect(() => {
        if (!state.loaded) {
            fetch(`/api/stats`)
                .then(res => res.json())
                .then((data) =>
                    setState({ loaded: true, stats: data.data })
                );
        }
    });

    return (
        <div className={styles.Home}>
            <h1>
                I am your Cartesian Theatre
                <br />
                and you are our focus.
            </h1>
            {state.stats &&
                <div className={styles.stats}>
                    {state.stats.object_count} objects, {state.stats.link_count} links, {state.stats.file_count} files
                </div>}
        </div>
    );
}
