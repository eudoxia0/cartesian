"""
This module implements the Markdown parser for Cartesian Theatre.
"""

import re
from itertools import chain
from typing import Optional

from mistletoe import Document
from mistletoe.span_token import SpanToken
from mistletoe.html_renderer import BaseRenderer
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
from theatre.error import CTError

#
# Mistletoe setup
#


class WikiLinkToken(SpanToken):
    pattern = re.compile(r"\[\[(.+)\]\]")
    parse_group = 1
    parse_inner = False
    precedence = 5

    title: str

    def __init__(self, match):
        self.title = match.group(1)


class InlineMathToken(SpanToken):
    pattern = re.compile(r"\$(([^\\\$]|\\\\|\\\$)*)\$")
    parse_inner = False
    parse_group = 0

    content: str

    def __init__(self, match):
        self.content = match.group(1).replace(r"\$", "$")


class AstRenderer(BaseRenderer):
    def __init__(self, *extras):
        """
        Args:
            extras (list): allows subclasses to add even more custom tokens.
        """
        super().__init__(*chain([WikiLinkToken, InlineMathToken], extras))

    def render(self, token) -> CTDocument:
        """
        Converts a Markdown AST into a `CTDocument` instance.
        """
        return token_to_json(token)


def token_to_json(token):
    """
    Turns a token into a tree.
    """
    node: dict = {}
    node["type"] = token.__class__.__name__
    node.update(token.__dict__)
    if "header" in node:
        node["header"] = token_to_json(node["header"])
    if "children" in node:
        node["children"] = [token_to_json(child) for child in node["children"]]
    return node


#
# Parsing
#


def parse_doc(json: dict) -> CTDocument:
    assert json["type"] == "Document"
    return CTDocument(children=parse_block_list(json["children"]))


# Block node parsing


def parse_block(json: dict) -> BlockNode:
    parsers: dict = {
        "Paragraph": parse_para,
        "List": parse_list,
        "CodeFence": parse_code_block,
        "ThematicBreak": parse_break,
        "Quote": parse_quote,
        "Heading": parse_heading,
        "BlockCode": lambda _: None,
    }
    type = json["type"]
    if type in parsers:
        return parsers[type](json)
    else:
        raise CTError(
            "Markdown Parse Error",
            f"Unknown block text node with type '{type}'. You may be trying "
            "to use a Markdown feature that is not supported by Cartesian "
            "Theatre's object model.",
        )


def parse_block_list(list) -> List[BlockNode]:
    return [elem for elem in [parse_block(elem) for elem in list] if elem is not None]


def parse_para(json: dict) -> Paragraph:
    return Paragraph(children=[parse_inline(c) for c in json["children"]])


def parse_list(json: dict) -> List:
    start: Option[int] = json["start"]
    children: List[ListItem] = [parse_list_item(item) for item in json["children"]]
    if start is not None:
        # Ordered list
        return OrderedList(children=children)
    else:
        # Unordered list
        return UnorderedList(children=children)


def parse_list_item(json: dict) -> ListItem:
    assert json["type"] == "ListItem"
    return ListItem(children=parse_block_list(json["children"]))


def parse_code_block(json: dict) -> CodeBlock:
    assert len(json["children"]) == 1
    lang: Optional[str] = json["language"]
    if lang == "ct:math":
        return MathBlock(contents=json["children"][0]["content"])
    else:
        return CodeBlock(contents=json["children"][0]["content"])


def parse_break(json: dict) -> Break:
    return Break()


def parse_quote(json: dict) -> ListItem:
    assert json["type"] == "Quote"
    return BlockQuote(children=parse_block_list(json["children"]))


def parse_heading(json: dict) -> Heading:
    assert json["type"] == "Heading"
    return Heading(children=[parse_inline(c) for c in json["children"]])


# Inline node parsing


def parse_inline(json: dict) -> InlineNode:
    parsers: dict = {
        "RawText": parse_text,
        "Strong": parse_bold,
        "Emphasis": parse_italic,
        "InlineCode": parse_inline_code,
        "AutoLink": parse_link,
        "Link": parse_link,
        "WikiLinkToken": parse_internal_link,
        "LineBreak": parse_line_break,
        "InlineMathToken": parse_inline_math,
    }
    type = json["type"]
    if type in parsers:
        return parsers[type](json)
    else:
        raise CTError(
            "Markdown Parsing Error",
            f"Unknown inline text node with type '{type}'. You may be trying to use a Markdown feature that is not supported by Cartesian Theatre's object model.",
        )


def parse_text(json: dict) -> TextNode:
    return TextNode(contents=json["content"])


def parse_bold(json: dict) -> BoldNode:
    children = [parse_inline(c) for c in json["children"]]
    return BoldNode(children=children)


def parse_italic(json: dict) -> ItalicNode:
    children = [parse_inline(c) for c in json["children"]]
    return ItalicNode(children=children)


def parse_inline_code(json: dict) -> InlineCodeNode:
    children = [parse_inline(c) for c in json["children"]]
    return InlineCodeNode(children=children)


def parse_link(json: dict) -> WebLinkNode:
    children = [parse_inline(c) for c in json["children"]]
    return WebLinkNode(url=json["target"], children=children)


def parse_internal_link(json: dict) -> InternalLinkNode:
    return InternalLinkNode(title=json["title"])


def parse_line_break(json: dict) -> TextNode:
    assert json["type"] == "LineBreak"
    return TextNode(contents="\n")


def parse_inline_math(json: dict) -> InlineMathNode:
    assert json["type"] == "InlineMathToken"
    return InlineMathNode(contents=json["content"])


#
# Interface
#


def parse_markdown(text: str) -> CTDocument:
    try:
        with AstRenderer() as renderer:
            rendered = renderer.render(Document(text))
            return parse_doc(rendered)
    except CTError as e:
        raise e
    except:
        raise CTError(
            "Markdown Parsing Error",
            "An unknown internal error occured while parsing Markdown.",
        )
