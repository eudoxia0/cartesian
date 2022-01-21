import { useState } from 'react';
import { pdfjs, Document, Page } from 'react-pdf';
import 'react-pdf/dist/esm/Page/AnnotationLayer.css';

const html = ["text/html"];

const images = ["image/bmp", "image/gif", "image/jpeg", "image/png", "image/tiff", "image/webp"];

const pdf = ["application/pdf"];

pdfjs.GlobalWorkerOptions.workerSrc = `//unpkg.com/pdfjs-dist@${pdfjs.version}/legacy/build/pdf.worker.min.js`;

interface Props {
    id: number;
    mime_type: string;
}

export default function FilePreview(props: Props) {
    const mime_type = props.mime_type;
    const url = `/api/files/${props.id}/contents`;
    const [numPages, setNumPages] = useState<number>(0);

    function onDocumentLoadSuccess(e: { numPages: number }) {
        setNumPages(e.numPages);
    }

    function isType(list: Array<string>) {
        return list.some(elem => mime_type.startsWith(elem));
    }

    if (isType(images)) {
        return <img src={url} alt="File preview." />;
    } else if (isType(html)) {
        return <iframe title="preview" src={url}></iframe>;
    } else if (isType(pdf)) {
        return (
            <Document file={url} onLoadSuccess={onDocumentLoadSuccess}>
                {
                    Array.from(
                        new Array(numPages),
                        (_, index) => (
                            <Page
                                key={`page_${index + 1}`}
                                pageNumber={index + 1}
                            />
                        ),
                    )
                }
            </Document>
        );
    } else {
        return <p>No preview for this file.</p>;
    }
}