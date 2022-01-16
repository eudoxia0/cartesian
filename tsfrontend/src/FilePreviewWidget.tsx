import { useEffect, useState } from "react";
import FilePreview from "./FilePreview";
import { FileRec } from "./types";

interface Props {
    id: number;
}

interface State {
    loaded: boolean;
    file: FileRec | null;
}

export default function FilePreviewWidget(props: Props) {
    const [state, setState] = useState<State>({ loaded: false, file: null });

    useEffect(() => {
        fetch(`http://localhost:5000/api/files/${props.id}`)
            .then(res => res.json())
            .then((data) => {
                setState({ loaded: true, file: data.data });
            });
    }, [props.id]);

    if (state.file) {
        return <FilePreview id={state.file.id} mime_type={state.file.mime_type} />
    } else {
        return <p> Loading...</p >;
    }
}