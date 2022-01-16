import { PropRec, PropType } from "./types";

interface Props {
    classId: number;
    classProps: Array<PropRec>;
}

function humanizeType(type: PropType) {
    if (type === "PROP_RICH_TEXT") {
        return "Text";
    } else if (type === "PROP_FILE") {
        return "File";
    }
}

export default function ClassProperties(props: Props) {
    const properties = props.classProps;

    function handleDeleteProp(propId: number) {
        if (window.confirm("Deleting this class property will delete all instances of this property across all objects of this class. Proceed?")) {
            fetch(`http://localhost:5000/api/classes/${props.classId}/properties/${propId}`,
                {
                    headers: {
                        "Accept": "application/json",
                        "Content-Type": "application/json"
                    },
                    method: "DELETE",
                }
            )
                .then(response => response.json())
                .then(data => {
                    if (data.error) {
                        window.alert(data.error.title + ": " + data.error.message);
                    }
                })
        }
    }

    return (
        <table>
            <thead>
                <tr>
                    <th>
                        ID
                    </th>
                    <th>
                        Type
                    </th>
                    <th>
                        Name
                    </th>
                    <th>
                        Description
                    </th>
                    <th>
                        Delete
                    </th>
                </tr>
            </thead>
            <tbody>
                {
                    properties.map(prop => (
                        <tr key={prop.id}>
                            <td>
                                {prop.id}
                            </td>
                            <td>
                                {humanizeType(prop.type)}
                            </td>
                            <td>
                                {prop.title}
                            </td>
                            <td>
                                {prop.description}
                            </td>
                            <td>
                                <button onClick={_ => handleDeleteProp(prop.id)}>
                                    Delete Property
                                </button>
                            </td>
                        </tr>
                    ))
                }
            </tbody>
        </table>
    );

}