import { FileRec } from "./types";
import { useEffect, useState } from "react";
import { humanizeDate, humanizeFileSize } from "./utils";
import { useParams } from "react-router-dom";
import FilePreview from "./FilePreview";

interface State {
    loaded: boolean;
    file: FileRec | null;
}

export default function FileDetail() {
    const [state, setState] = useState<State>({ loaded: false, file: null });
    let params = useParams();

    useEffect(() => {
        if (!state.loaded) {
            let id = parseInt(params.fileId || "", 10);
            fetch(`http://localhost:5000/api/files/${id}`)
                .then(res => res.json())
                .then((data) => {
                    setState({ loaded: true, file: data.data });
                });
        }
    });

    if (state.loaded) {
        if (state.file !== null) {
            const file: FileRec = state.file;
            return (
                <div>
                    <h2>File Details</h2>
                    <div>
                        <ol>
                            <li>
                                <b>ID:</b> {file.id}
                            </li>
                            <li>
                                <b>Filename:</b> <code>{file.filename}</code>
                            </li>
                            <li>
                                <b>MIME Type:</b> <code>{file.mime_type}</code>
                            </li>
                            <li>
                                <b>Created At:</b> {humanizeDate(file.created_at)}
                            </li>
                            <li>
                                <b>Size:</b> {humanizeFileSize(file.size)} <em>({file.size} bytes)</em>
                            </li>
                            <li>
                                <b>Download:</b>
                                <a target="_blank" rel="noreferrer" href={`http://localhost:5000/api/files/${file.id}/contents`}>
                                    Download
                                </a>
                            </li>
                        </ol>
                    </div>
                    <FilePreview id={file.id} mime_type={file.mime_type} />
                </div>
            )
        }
    }

    return (
        <div>
            <h2>File Details</h2>
            <div>
                Loading...
            </div>
        </div>
    )
}