import unittest
import json

from theatre.markdown import parse_markdown
from theatre.text import (
    CTDocument,
    BlockNode,
    InlineNode,
    Break,
    CodeBlock,
    List,
    ListItem,
    OrderedList,
    UnorderedList,
    Paragraph,
    BlockQuote,
    Heading,
    TextNode,
    BoldNode,
    ItalicNode,
    InlineCodeNode,
    InternalLinkNode,
    WebLinkNode,
    MathBlock,
    InlineMathNode,
)


class MarkdownTest(unittest.TestCase):
    def test_complete_document(self):
        text = """
# This is a heading

This is a paragraph. This is **bold text**. This is _italicized text_. This is `inline code`. This is $math\$math$. This is _**italicized strong text**_. This is an autolink: <http://a.com>. This is a link to the web: [B](http://b.com/). This is a reference link [C][clink]. This is a [[Wiki Link]].

>This is a block-quoted paragraph which is very long so as to span multiple
>source lines of text.

- A

    - B

    - Multiple

      paragraphs

- C

1. A

    1. B

    2. C

3. D

```
This is a code block.

There is **bold text** and `inline code` here.

Another line.
```

```ct:math
\sum\limits_a^b = x^2
```

This is a horizontal rule:

---

[clink]: https://www.c.com
        """
        # Parse the document
        doc = parse_markdown(text)
        # It has eight children
        self.assertEqual(len(doc.children), 9)
        # Destructure
        head, para, quote, ulist, olist, cblock, mblock, lp, rule = doc.children
        # Heading
        self.assertIsInstance(head, Heading)
        self.assertEqual(head.children, [TextNode(contents="This is a heading")])
        # First paragraph
        self.assertIsInstance(para, Paragraph)
        self.assertEqual(
            para.children,
            [
                TextNode(contents="This is a paragraph. This is "),
                BoldNode(children=[TextNode(contents="bold text")]),
                TextNode(contents=". This is "),
                ItalicNode(children=[TextNode(contents="italicized text")]),
                TextNode(contents=". This is "),
                InlineCodeNode(children=[TextNode(contents="inline code")]),
                TextNode(contents=". This is "),
                InlineMathNode(contents="math$math"),
                TextNode(contents=". This is "),
                ItalicNode(
                    children=[
                        BoldNode(children=[TextNode(contents="italicized strong text")])
                    ]
                ),
                TextNode(contents=". This is an autolink: "),
                WebLinkNode(
                    url="http://a.com", children=[TextNode(contents="http://a.com")]
                ),
                TextNode(contents=". This is a link to the web: "),
                WebLinkNode(url="http://b.com/", children=[TextNode(contents="B")]),
                TextNode(contents=". This is a reference link "),
                WebLinkNode(url="https://www.c.com", children=[TextNode(contents="C")]),
                TextNode(contents=". This is a "),
                InternalLinkNode(title="Wiki Link"),
                TextNode(contents="."),
            ],
        )
        # Blockquote
        self.assertIsInstance(quote, BlockQuote)
        self.assertEqual(
            quote.children,
            [
                Paragraph(
                    children=[
                        TextNode(
                            contents="This is a block-quoted paragraph which is very long so as to span multiple"
                        ),
                        TextNode(contents="\n"),
                        TextNode(contents="source lines of text."),
                    ]
                )
            ],
        )
        # Unordered list
        self.assertIsInstance(ulist, UnorderedList)
        self.assertEqual(
            ulist.children,
            [
                ListItem(
                    children=[
                        Paragraph(children=[TextNode(contents="A")]),
                        UnorderedList(
                            children=[
                                ListItem(
                                    children=[
                                        Paragraph(children=[TextNode(contents="B")])
                                    ]
                                ),
                                ListItem(
                                    children=[
                                        Paragraph(
                                            children=[TextNode(contents="Multiple")]
                                        ),
                                        Paragraph(
                                            children=[TextNode(contents="paragraphs")]
                                        ),
                                    ]
                                ),
                            ]
                        ),
                    ]
                ),
                ListItem(children=[Paragraph(children=[TextNode(contents="C")])]),
            ],
        )
        # Ordered list
        self.assertIsInstance(olist, OrderedList)
        self.assertEqual(
            olist.children,
            [
                ListItem(
                    children=[
                        Paragraph(children=[TextNode(contents="A")]),
                        OrderedList(
                            children=[
                                ListItem(
                                    children=[
                                        Paragraph(children=[TextNode(contents="B")])
                                    ]
                                ),
                                ListItem(
                                    children=[
                                        Paragraph(children=[TextNode(contents="C")])
                                    ]
                                ),
                            ]
                        ),
                    ]
                ),
                ListItem(children=[Paragraph(children=[TextNode(contents="D")])]),
            ],
        )
        # Code block
        self.assertIsInstance(cblock, CodeBlock)
        self.assertEqual(
            cblock.contents,
            "This is a code block.\n\nThere is **bold text** and `inline code` here.\n\nAnother line.\n",
        )
        # Math block
        self.assertIsInstance(mblock, MathBlock)
        self.assertEqual(
            mblock.contents,
            "\sum\limits_a^b = x^2\n",
        )
        # Last paragraph
        self.assertIsInstance(lp, Paragraph)
        self.assertEqual(
            lp.children,
            [TextNode(contents="This is a horizontal rule:")],
        )
        # Horizontal
        self.assertIsInstance(rule, Break)

        # Test rendering the document
        output: str = doc.to_markdown()
