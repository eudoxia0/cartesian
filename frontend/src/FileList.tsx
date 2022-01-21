import { useEffect, useState } from "react";
import { humanizeDate, humanizeFileSize } from "./utils";
import { Link } from "react-router-dom";
import { FileRec } from "./types";
import SimpleContainer from "./SimpleContainer";

interface State {
    loaded: boolean;
    files: Array<FileRec>;
}

export default function FileList() {
    const [state, setState] = useState<State>({ loaded: false, files: [] });

    useEffect(() => {
        if (!state.loaded) {
            fetch("/api/files")
                .then(res => res.json())
                .then((data) => setState({ files: data.data, loaded: true }));
        }
    });

    if (state.loaded) {
        const { files } = state;


        return (
            <SimpleContainer
                title={<span>All Files</span>}
                body={
                    <table>
                        <thead>
                            <tr>
                                <th>
                                    ID
                                </th>
                                <th>
                                    Filename
                                </th>
                                <th>
                                    MIME Type
                                </th>
                                <th>
                                    Created At
                                </th>
                                <th>
                                    Size
                                </th>
                            </tr>
                        </thead>
                        <tbody>
                            {
                                files.map(file => (
                                    <tr key={file.id}>
                                        <td>
                                            <Link to={`/files/${file.id}`}>
                                                {file.id}
                                            </Link>
                                        </td>
                                        <td>
                                            <Link to={`/files/${file.id}`}>
                                                <code>{file.filename}</code>
                                            </Link>
                                        </td>
                                        <td>
                                            <code>{file.mime_type}</code>
                                        </td>
                                        <td>
                                            {humanizeDate(file.created_at)}
                                        </td>
                                        <td>
                                            {humanizeFileSize(file.size)}
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
                title={<span>All Files</span>}
                body={<p>Loading...</p>}
            />
        );
    }
}