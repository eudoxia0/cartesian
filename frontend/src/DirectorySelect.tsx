import { DirectoryRec } from "./types";
import { useAppSelector, selectDirectoryList } from "./store";
import { useState } from "react";

interface Props {
    onChange: (id: number) => void;
}

export default function DirectorySelect(props: Props) {
    const [dirId, setDirId] = useState<number>(-1);

    const directoryList = useAppSelector(selectDirectoryList);
    console.log(directoryList);

    return (
        <select value={dirId} onChange={e => setDirId(parseInt(e.target.value, 10))}>
            <option value={-1}>None</option>
            {
                directoryList.map((dir: DirectoryRec) => {
                    return <option value={dir.id}>{dir.title}</option>
                })
            }
        </select>
    );
}