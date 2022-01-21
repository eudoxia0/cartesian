import { useCallback, useEffect, useState } from "react";
import { useDropzone } from 'react-dropzone';
import FilePreviewWidget from "./FilePreviewWidget";
import styles from "./FilePropWidget.module.css";

interface Props {
    initialFileId: number | null;
    onUpload: (fileId: number) => void;
}

export default function FilePropWidget(props: Props) {
    const [currentFileId, setCurrentFileId] = useState<number | null>(null);

    useEffect(() => setCurrentFileId(props.initialFileId), [props.initialFileId]);

    const onDrop = useCallback(acceptedFiles => {
        const file = acceptedFiles[0];
        var data = new FormData()
        data.append('data', file);
        fetch("/api/files",
            {
                method: "POST",
                body: data,
            }
        )
            .then(response => response.json())
            .then(data => {
                const fileId = data.data.id;
                setCurrentFileId(fileId);
                props.onUpload(fileId);
            });
    }, [props]);
    const { getRootProps, getInputProps, isDragActive } = useDropzone({ onDrop });

    return (
        <div className={styles.container}>
            {currentFileId ? <FilePreviewWidget id={currentFileId} /> : <div></div>}
            <br />
            <div {...getRootProps()}>
                <input {...getInputProps()} />
                {
                    isDragActive ?
                        <p>Drop the files here ...</p> :
                        <p>Drag 'n' drop some files here, or click to select files</p>
                }
            </div>
        </div>
    );
}