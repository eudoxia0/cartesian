import { PropRec } from "./types";

export default function ClassProperties(props: { classProps: Array<PropRec> }) {
    const properties = props.classProps;

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
                                {prop.type}
                            </td>
                            <td>
                                {prop.title}
                            </td>
                            <td>
                                {prop.description}
                            </td>
                        </tr>
                    ))
                }
            </tbody>
        </table>
    );

}