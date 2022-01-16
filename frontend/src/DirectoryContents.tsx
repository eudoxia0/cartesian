import { useParams } from "react-router-dom";
import ObjectListInDirectory from "./ObjectListInDirectory";

export default function DirectoryContents() {
    let params = useParams();
    const id: number = parseInt(params.dirId!, 10);

    return <ObjectListInDirectory id={id} />;
}