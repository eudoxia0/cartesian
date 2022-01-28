import unittest
from theatre.new_text import *
from theatre.prosemirror import parse_document, emit_document

doc_dump = {
    "doc": {
        "type": "doc",
        "content": [
            {
                "type": "paragraph",
                "content": [
                    {"type": "text", "text": "Paragraph. "},
                    {"type": "text", "marks": [{"type": "strong"}], "text": "Bold"},
                    {"type": "text", "text": ". "},
                    {"type": "text", "marks": [{"type": "em"}], "text": "Italics"},
                    {"type": "text", "text": ". Wiki link: "},
                    {"type": "wikilinknode", "attrs": {"title": "Node"}},
                    {"type": "text", "text": ". "},
                    {
                        "type": "math_inline",
                        "content": [{"type": "text", "text": "math"}],
                    },
                    {"type": "text", "text": "."},
                ],
            },
            {
                "type": "bullet_list",
                "content": [
                    {
                        "type": "list_item",
                        "content": [
                            {
                                "type": "paragraph",
                                "content": [{"type": "text", "text": "item"}],
                            },
                            {
                                "type": "bullet_list",
                                "content": [
                                    {
                                        "type": "list_item",
                                        "content": [
                                            {
                                                "type": "paragraph",
                                                "content": [
                                                    {"type": "text", "text": "item"}
                                                ],
                                            }
                                        ],
                                    }
                                ],
                            },
                        ],
                    }
                ],
            },
            {
                "type": "ordered_list",
                "attrs": {"order": 1},
                "content": [
                    {
                        "type": "list_item",
                        "content": [
                            {
                                "type": "paragraph",
                                "content": [{"type": "text", "text": "item"}],
                            },
                            {
                                "type": "ordered_list",
                                "attrs": {"order": 1},
                                "content": [
                                    {
                                        "type": "list_item",
                                        "content": [
                                            {
                                                "type": "paragraph",
                                                "content": [
                                                    {"type": "text", "text": "item"}
                                                ],
                                            }
                                        ],
                                    }
                                ],
                            },
                        ],
                    }
                ],
            },
            {"type": "horizontal_rule"},
            {"type": "paragraph", "content": [{"type": "text", "text": "Paragraph"}]},
            {"type": "code_block", "content": [{"type": "text", "text": "code block"}]},
            {"type": "paragraph", "content": [{"type": "text", "text": "Paragraph"}]},
            {"type": "math_display", "content": [{"type": "text", "text": "e=mc^2"}]},
        ],
    }
}


class ProseMirrorTest(unittest.TestCase):
    def test_complete_document(self):
        doc = parse_document(doc_dump)
        self.assertEqual(
            doc,
            CTDocument(
                children=[
                    Paragraph(
                        children=[
                            TextFragment(
                                contents="Paragraph. ",
                                emphasized=False,
                                bold=False,
                                code=False,
                            ),
                            TextFragment(
                                contents="Bold", emphasized=False, bold=True, code=False
                            ),
                            TextFragment(
                                contents=". ", emphasized=False, bold=False, code=False
                            ),
                            TextFragment(
                                contents="Italics",
                                emphasized=True,
                                bold=False,
                                code=False,
                            ),
                            TextFragment(
                                contents=". Wiki link: ",
                                emphasized=False,
                                bold=False,
                                code=False,
                            ),
                            InternalLinkFragment(title="Node"),
                            TextFragment(
                                contents=". ", emphasized=False, bold=False, code=False
                            ),
                            MathFragment(contents="math"),
                            TextFragment(
                                contents=".", emphasized=False, bold=False, code=False
                            ),
                        ]
                    ),
                    UnorderedList(
                        children=[
                            ListItem(
                                children=[
                                    Paragraph(
                                        children=[
                                            TextFragment(
                                                contents="item",
                                                emphasized=False,
                                                bold=False,
                                                code=False,
                                            )
                                        ]
                                    ),
                                    UnorderedList(
                                        children=[
                                            ListItem(
                                                children=[
                                                    Paragraph(
                                                        children=[
                                                            TextFragment(
                                                                contents="item",
                                                                emphasized=False,
                                                                bold=False,
                                                                code=False,
                                                            )
                                                        ]
                                                    )
                                                ]
                                            )
                                        ]
                                    ),
                                ]
                            )
                        ]
                    ),
                    OrderedList(
                        children=[
                            ListItem(
                                children=[
                                    Paragraph(
                                        children=[
                                            TextFragment(
                                                contents="item",
                                                emphasized=False,
                                                bold=False,
                                                code=False,
                                            )
                                        ]
                                    ),
                                    OrderedList(
                                        children=[
                                            ListItem(
                                                children=[
                                                    Paragraph(
                                                        children=[
                                                            TextFragment(
                                                                contents="item",
                                                                emphasized=False,
                                                                bold=False,
                                                                code=False,
                                                            )
                                                        ]
                                                    )
                                                ]
                                            )
                                        ]
                                    ),
                                ]
                            )
                        ]
                    ),
                    HorizontalRule(),
                    Paragraph(
                        children=[
                            TextFragment(
                                contents="Paragraph",
                                emphasized=False,
                                bold=False,
                                code=False,
                            )
                        ]
                    ),
                    CodeBlock(contents="code block"),
                    Paragraph(
                        children=[
                            TextFragment(
                                contents="Paragraph",
                                emphasized=False,
                                bold=False,
                                code=False,
                            )
                        ]
                    ),
                    MathBlock(contents="e=mc^2"),
                ]
            ),
        )
        json = emit_document(doc)
