import "@benrbray/prosemirror-math/style/math.css";
import "prosemirror-view/style/prosemirror.css";
import "katex/dist/katex.min.css";

import { Schema } from "prosemirror-model";
import { addListNodes } from "prosemirror-schema-list";
import { tableNodes } from "prosemirror-tables";
import { exampleSetup } from "./editor";

const image_mime_types = ["image/bmp", "image/gif", "image/jpeg", "image/png", "image/tiff", "image/webp"];

function isMimeType(list, mime_type) {
    return list.some(elem => mime_type.startsWith(elem));
}

function makeFilePreview(file_id, mime_type) {
    if (isMimeType(image_mime_types, mime_type)) {
        return [
            "img",
            { "src": `/api/files/${file_id}/contents` },
        ];
    } else {
        return [
            "span",
            {},
            "No preview available."
        ];
    }
}

function makeFileEmbed(file_id, filename, mime_type) {
    return [
        "div",
        { "class": "file-embed-container" },
        [
            "div", { "class": "file-embed-preview" },
            makeFilePreview(file_id, mime_type),
        ],
        [
            "div", { "class": "file-embed-label" },
            `File: ${filename}`,
        ],
    ];
}

export function createSchema() {
    let blockquoteDOM = ["blockquote", 0];
    let hrDOM = ["hr"];
    let preDOM = ["pre", ["code", 0]];
    var emDOM = ["em", 0], strongDOM = ["strong", 0], codeDOM = ["code", 0];

    let baseNodes = {
        doc: {
            content: "block+"
        },

        paragraph: {
            content: "inline*",
            group: "block",
            parseDOM: [{ tag: "p" }],
            toDOM() { return ["p", 0]; }
        },

        blockquote: {
            content: "block+",
            group: "block",
            defining: true,
            parseDOM: [{ tag: "blockquote" }],
            toDOM: function toDOM() { return blockquoteDOM; }
        },

        horizontal_rule: {
            group: "block",
            parseDOM: [{ tag: "hr" }],
            toDOM: function toDOM() { return hrDOM; }
        },

        math_inline: {               // important!
            group: "inline math",
            content: "text*",        // important!
            inline: true,            // important!
            atom: true,              // important!
            toDOM: () => ["math-inline", { class: "math-node" }, 0],
            parseDOM: [{
                tag: "math-inline"   // important!
            }]
        },

        math_display: {              // important!
            group: "block math",
            content: "text*",        // important!
            atom: true,              // important!
            code: true,              // important!
            toDOM: () => ["math-display", { class: "math-node" }, 0],
            parseDOM: [{
                tag: "math-display"  // important!
            }]
        },

        code_block: {
            content: "text*",
            marks: "",
            group: "block",
            code: true,
            defining: true,
            parseDOM: [{ tag: "pre", preserveWhitespace: "full" }],
            toDOM: function toDOM() { return preDOM; }
        },

        text: {
            group: "inline"
        },

        wikilinknode: {
            attrs: { title: {} },
            inline: true,
            group: "inline",
            draggable: false,
            atom: true,

            toDOM: (node) => [
                "span",
                {
                    class: "wikilink",
                    title: node.attrs.title,
                },
                node.attrs.title
            ],
            parseDOM: [{
                tag: "span.wikilink",
                getAttrs: (dom) => {
                    let title = dom.getAttribute("title");
                    if ((title !== null) && (title.length > 0)) {
                        return { title };
                    } else {
                        return false;
                    }
                }
            }]
        },

        checkbox: {
            inline: true,
            group: "inline",
            attrs: {
                checked: false,
            },
            draggable: false,
            atom: true,
            parseDOM: [{ tag: "checkbox" }],
            toDOM() {
                return ["checkbox"];
            },
        },

        file_embed: {
            group: "block",
            attrs: {
                file_id: {},
                filename: {},
                mime_type: {},
            },
            draggable: false,
            parseDOM: [
                {
                    tag: "file-embed", getAttrs(dom) {
                        return {
                            file_id: dom.getAttribute("file-id"),
                            filename: dom.getAttribute("filename"),
                            mime_type: dom.getAttribute("mime-type"),
                        };
                    }
                }
            ],
            toDOM(node) {
                let { file_id, filename, mime_type } = node.attrs;
                let child = makeFileEmbed(file_id, filename, mime_type);
                return [
                    "file-embed",
                    {
                        "file-id": file_id,
                        "filename": filename,
                        "mime-type": mime_type
                    },
                    child,
                ];
            }
        }
    };

    baseNodes = Object.assign({}, baseNodes, tableNodes({}));

    const schema = new Schema({
        nodes: baseNodes,
        marks: {
            // :: MarkSpec A link. Has `href` and `title` attributes. `title`
            // defaults to the empty string. Rendered and parsed as an `<a>`
            // element.
            link: {
                attrs: {
                    href: {},
                },
                inclusive: false,
                parseDOM: [{
                    tag: "a[href]", getAttrs(dom) {
                        return { href: dom.getAttribute("href") };
                    }
                }],
                toDOM(node) {
                    let { href } = node.attrs;
                    return [
                        "a",
                        {
                            href: href,
                            "onClick": `window.open("${href}", '_blank');`,
                        },
                        0
                    ];
                }
            },

            wikilinkmark: {
                attrs: { title: {} },
                toDOM(node) {
                    return [
                        "span",
                        {
                            class: "wikilinkmark",
                            title: node.attrs.href,
                            "onClick": `window.location.href = '/objects/${node.attrs.title}';`
                        },
                        0];
                },
                parseDOM: [{ tag: "span", getAttrs(dom) { return { title: dom.title }; } }],
                inclusive: false
            },

            // :: MarkSpec An emphasis mark. Rendered as an `<em>` element.
            // Has parse rules that also match `<i>` and `font-style: italic`.
            em: {
                parseDOM: [{ tag: "i" }, { tag: "em" }, { style: "font-style=italic" }],
                toDOM: function toDOM() { return emDOM; }
            },

            // :: MarkSpec A strong mark. Rendered as `<strong>`, parse rules
            // also match `<b>` and `font-weight: bold`.
            strong: {
                parseDOM: [{ tag: "strong" },
                // This works around a Google Docs misbehavior where
                // pasted content will be inexplicably wrapped in `<b>`
                // tags with a font-weight normal.
                { tag: "b", getAttrs: function (node) { return node.style.fontWeight != "normal" && null; } },
                { style: "font-weight", getAttrs: function (value) { return /^(bold(er)?|[5-9]\d{2,})$/.test(value) && null; } }],
                toDOM: function toDOM() { return strongDOM; }
            },

            // :: MarkSpec Code font mark. Represented as a `<code>` element.
            code: {
                parseDOM: [{ tag: "code" }],
                toDOM: function toDOM() { return codeDOM; }
            }
        },
    });

    return new Schema({
        nodes: addListNodes(schema.spec.nodes, "paragraph block*", "block"),
        marks: schema.spec.marks,
    });
}

export function createPlugins(schema) {
    return exampleSetup({ schema: schema, menuBar: false });
}