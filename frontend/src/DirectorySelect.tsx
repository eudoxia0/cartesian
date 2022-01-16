import { DirectoryRec } from "./types";
import { useAppSelector, selectDirectoryList } from "./store";
import { useState } from "react";
import styles from "./DirectorySelect.module.css";

interface Props {
    initialValue: number | null;
    onChange: (id: number | null) => void;
}

export default function DirectorySelect(props: Props) {
    const [dirId, setDirId] = useState<number>(props.initialValue ? props.initialValue : -1);

    const directoryList = useAppSelector(selectDirectoryList);

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
                directoryList.map((dir: DirectoryRec) => {
                    return <option key={dir.id} value={dir.id}>{dir.title}</option>
                })
            }
        </select>
    );
}