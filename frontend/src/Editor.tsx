import { useProseMirror, ProseMirror } from 'use-prosemirror';
import { createSchema, createPlugins } from "./prosemirror";
import { Fragment, Node, Slice } from "prosemirror-model";
import { useNavigate } from 'react-router-dom';
import { EditorView } from "prosemirror-view";

const HTTP_LINK_REGEX = /\bhttps?:\/\/[\w_\-#\/\.]+/g
let linkify = function (fragment: Fragment): Fragment {
    var linkified: Node[] = []
    fragment.forEach(function (child: Node) {
        if (child.isText) {
            const text = child.text as string
            var pos = 0, match

            while (match = HTTP_LINK_REGEX.exec(text)) {
                var start = match.index
                var end = start + match[0].length
                var link = child.type.schema.marks['link']

                // simply copy across the text from before the match
                if (start > 0) {
                    linkified.push(child.cut(pos, start))
                }

                const urlText = text.slice(start, end)
                linkified.push(
                    child.cut(start, end).mark(link.create({ href: urlText }).addToSet(child.marks))
                )
                pos = end
            }

            // copy over whatever is left
            if (pos < text.length) {
                linkified.push(child.cut(pos))
            }
        } else {
            linkified.push(child.copy(linkify(child.content)))
        }
    })

    return Fragment.fromArray(linkified)
}

interface Props {
    initialDoc: any | null;
    onChange: (doc: any) => void;
}

export default function Editor(props: Props) {
    let navigate = useNavigate();

    function onLinkClick(title: string) {
        navigate(`/objects/${title}`);
    }

    const schema = createSchema();
    const plugins = createPlugins(schema);

    const [state, setState] = useProseMirror({
        doc: props.initialDoc ? Node.fromJSON(schema, props.initialDoc) : null,
        schema: schema,
        plugins: plugins,
    });

    function handleChange(newState: any) {
        setState(newState);
        props.onChange(newState.doc.toJSON());
    }

    return <ProseMirror
        state={state}
        onChange={handleChange}
        transformPasted={function (slice: Slice) {
            return new Slice(linkify(slice.content), slice.openStart, slice.openEnd);
        }}
        handleClick={function (view: EditorView, pos: number, event: MouseEvent): boolean {
            event.preventDefault();
            const node: any = event.target as any;
            if (node.title) {
                const title: string = node.title;
                onLinkClick(title);
            }
            return false;
        }}
    />;
}