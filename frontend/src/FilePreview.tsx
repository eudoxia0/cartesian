const html = ["text/html"];

const images = ["image/bmp", "image/gif", "image/jpeg", "image/png", "image/tiff", "image/webp"];

interface Props {
    id: number;
    mime_type: string;
}

export default function FilePreview(props: Props) {
    const mime_type = props.mime_type;
    const url = `http://localhost:5000/api/files/${props.id}/contents`;

    function isType(list: Array<string>) {
        return list.some(elem => mime_type.startsWith(elem));
    }

    if (isType(images)) {
        return <img src={url} alt="File preview." />;
    } else if (isType(html)) {
        return <iframe title="preview" src={url}></iframe>;
    } else {
        return <p>No preview for this file.</p>;
    }
}