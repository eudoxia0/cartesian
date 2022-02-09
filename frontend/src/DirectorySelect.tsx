import { DirectoryRec } from "./types";
import { useEffect, useState } from "react";
import styles from "./DirectorySelect.module.css";

interface Props {
    initialValue: number | null;
    onChange: (id: number | null) => void;
}

interface State {
    loaded: boolean;
    directories: Array<DirectoryRec>;
}

export default function DirectorySelect(props: Props) {
    const [dirId, setDirId] = useState<number>(props.initialValue ? props.initialValue : -1);

    const [directoryList, setDirectoryList] = useState<State>({ loaded: false, directories: [] });

    useEffect(() => {
        if (!directoryList.loaded) {
            fetch("/api/directories")
                .then(res => res.json())
                .then((data) => setDirectoryList({ loaded: true, directories: data.data }));
        }
    });

    function handleChange(id: number) {
        setDirId(id);
        props.onChange((id === -1) ? null : id);
    }

    return (
        <select
            className={styles.selector}
            value={dirId}
            onChange={e => handleChange(parseInt(e.target.value, 10))}
        >
            <option value={-1} >None</option>
            {
                directoryList.directories.map((dir: DirectoryRec) => {
                    return <option key={dir.id} value={dir.id}>{dir.title}</option>
                })
            }
        </select>
    );
}