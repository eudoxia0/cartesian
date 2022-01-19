import { useEffect, useState } from "react";
import { Link } from "react-router-dom";
import SimpleContainer from "./SimpleContainer";
import { ObjectSummaryRec } from "./types";
import { humanizeDate } from "./utils";

export default function SearchPage() {
    const [query, setQuery] = useState<string>("");
    const [results, setResults] = useState<Array<ObjectSummaryRec>>([]);

    useEffect(() => {
        const effQuery: string = query.trim();
        if (effQuery.length > 0) {
            console.log("Querying: ", effQuery);
            fetch("http://localhost:5000/api/object-search",
                {
                    headers: {
                        "Accept": "application/json",
                        "Content-Type": "application/json"
                    },
                    method: "POST",
                    body: JSON.stringify({
                        "query": effQuery,
                    })
                })
                .then(res => res.json())
                .then((data) => {
                    setResults(data.data);
                })
        }
    }, [query]);

    return (
        <SimpleContainer
            title={<span>Search</span>}
            body={
                <div>
                    <input type="text" value={query} onChange={e => setQuery(e.target.value)} />
                    <div>
                        Search results:
                        <table>
                            <thead>
                                <tr>
                                    <th>
                                        Title
                                    </th>
                                    <th>
                                        Class
                                    </th>
                                    <th>
                                        Directory
                                    </th>
                                    <th>
                                        Created At
                                    </th>
                                    <th>
                                        Modified At
                                    </th>
                                </tr>
                            </thead>
                            <tbody>
                                {
                                    results.map((obj: ObjectSummaryRec) => (
                                        <tr key={obj.id}>
                                            <td>
                                                <Link to={`/objects/${obj.title}`}>
                                                    <code>{obj.title}</code>
                                                </Link>
                                            </td>
                                            <td>
                                                <code>{obj.class_id}</code>
                                            </td>
                                            <td>
                                                <code>{obj.directory_id}</code>
                                            </td>
                                            <td>
                                                {humanizeDate(obj.created_at)}
                                            </td>
                                            <td>
                                                {humanizeDate(obj.modified_at)}
                                            </td>
                                        </tr>
                                    ))
                                }
                            </tbody>
                        </table>
                    </div>
                </div>
            }
        />
    );
}
