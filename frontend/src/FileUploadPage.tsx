import { useCallback } from "react";
import { useNavigate } from 'react-router-dom';
import { useDropzone } from 'react-dropzone';
import SimpleContainer from "./SimpleContainer";

export default function FileUploadPage() {
    let navigate = useNavigate();
    const onDrop = useCallback(acceptedFiles => {
        const file = acceptedFiles[0];
        var data = new FormData()
        data.append('data', file);
        fetch("http://localhost:5000/api/files",
            {
                method: "POST",
                body: data,
            }
        )
            .then(response => response.json())
            .then(data => {
                const fileId = data.data.id;
                navigate(`/files/${fileId}`);
            });
    }, [navigate]);
    const { getRootProps, getInputProps, isDragActive } = useDropzone({ onDrop });

    return (
        <SimpleContainer
            title={<span>Upload a File</span>}
            body={
                <div {...getRootProps()}>
                    <input {...getInputProps()} />
                    {
                        isDragActive ?
                            <p>Drop the files here ...</p> :
                            <p>Drag 'n' drop some files here, or click to select files</p>
                    }
                </div>
            }
        />
    );
}