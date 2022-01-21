import { useCallback } from "react";
import { useNavigate } from 'react-router-dom';
import { useDropzone } from 'react-dropzone';
import SimpleContainer from "./SimpleContainer";
import { FileRec } from "./types";

interface Props {
    onSuccess: (file: FileRec) => void;
}

export default function FileUploadWidget(props: Props) {
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
                if (data.error) {
                    window.alert(data.error.title + ": " + data.error.message);
                } else {
                    props.onSuccess(data.data);
                }
            });
    }, [props]);
    const { getRootProps, getInputProps, isDragActive } = useDropzone({ onDrop });

    return (
        <div {...getRootProps()}>
            <input {...getInputProps()} />
            {
                isDragActive ?
                    <p>Drop the files here ...</p> :
                    <p>Drag 'n' drop some files here, or click to select files</p>
            }
        </div>
    );
}