import { useProseMirror, ProseMirror } from 'use-prosemirror';
import { schema, plugins } from "./prosemirror";
import { Node } from "prosemirror-model";

interface Props {
    initialDoc: any | null;
    onChange: (doc: any) => void;
}

export default function Editor(props: Props) {
    const [state, setState] = useProseMirror({
        doc: props.initialDoc ? Node.fromJSON(schema, props.initialDoc) : null,
        schema: schema,
        plugins: plugins,
    });

    function handleChange(newState: any) {
        setState(newState);
        props.onChange(newState.doc.toJSON());
    }

    return <ProseMirror state={state} onChange={handleChange} />;
}