"""
This module contains dataclasses for the representation of text in Cartesian Theatre.
"""
import textwrap
from typing import Union, List
from dataclasses import dataclass

#
# Inline nodes.
#

InlineNode = Union[
    "TextNode",
    "BoldNode",
    "ItalicNode",
    "InlineCodeNode",
    "InlineMathNode",
    "InternalLinkNode",
    "WebLinkNode",
]


@dataclass
class TextNode:
    """
    Represents an inline chunk of text.
    """

    contents: str

    def to_markdown(self) -> str:
        return self.contents


@dataclass
class BoldNode:
    """
    Represents bold text.
    """

    children: List[InlineNode]

    def to_markdown(self) -> str:
        return "**" + "".join([c.to_markdown() for c in self.children]) + "**"


@dataclass
class ItalicNode:
    """
    Represents italicized text.
    """

    children: List[InlineNode]

    def to_markdown(self) -> str:
        return "_" + "".join([c.to_markdown() for c in self.children]) + "_"


@dataclass
class InlineCodeNode:
    """
    Represents inline monospace text.
    """

    children: List[InlineNode]

    def to_markdown(self) -> str:
        return "`" + "".join([c.to_markdown() for c in self.children]) + "`"


@dataclass
class InlineMathNode:
    """
    Represents inline math.
    """

    contents: str

    def to_markdown(self) -> str:
        return "$" + self.contents.replace("$", r"\$") + "$"


@dataclass
class InternalLinkNode:
    """
    Represents a link to another object in Cartesian Theatre.
    """

    title: str

    def to_markdown(self) -> str:
        return "[[" + self.title + "]]"


@dataclass
class WebLinkNode:
    """
    Represents a link to the web.
    """

    url: str
    children: str

    def to_markdown(self) -> str:
        return (
            "["
            + "".join([c.to_markdown() for c in self.children])
            + "]("
            + self.url
            + ")"
        )


#
# Block nodes
#

BlockNode = Union[
    "Paragraph",
    "OrderedList",
    "UnorderedList",
    "Break",
    "Heading",
    "CodeBlock",
    "BlockQuote",
    "MathBlock",
]


@dataclass
class Paragraph:
    """
    Represents a paragraph containing inline text.
    """

    children: List[InlineNode]

    def to_markdown(self) -> str:
        text: str = "".join([c.to_markdown() for c in self.children])
        return fill(text)


@dataclass
class ListItem:
    """
    Represents an item in an ordered or unordered list.
    """

    children: List[BlockNode]

    def to_markdown(self) -> str:
        return "\n\n".join([c.to_markdown() for c in self.children])


@dataclass
class OrderedList:
    children: List[ListItem]

    def to_markdown(self) -> str:
        items = [c.to_markdown() for c in self.children]
        items = ["-" + indent_list_contents(txt) for txt in items]
        return "\n".join(items)


@dataclass
class UnorderedList:
    children: List[ListItem]

    def to_markdown(self) -> str:
        items = [c.to_markdown() for c in self.children]
        items = [
            f"{idx + 1}." + indent_list_contents(txt) for idx, txt in enumerate(items)
        ]
        return "\n".join(items)


@dataclass
class Break:
    """
    Represents a horizontal break.
    """

    def to_markdown(self) -> str:
        return "---"


@dataclass
class Heading:
    """
    Represents a heading.
    """

    children: List[InlineNode]

    def to_markdown(self) -> str:
        return "# " + "".join([c.to_markdown() for c in self.children])


@dataclass
class CodeBlock:
    """
    Represents a code block.
    """

    contents: str

    def to_markdown(self) -> str:
        return "```\n" + self.contents + "```"


@dataclass
class BlockQuote:
    """
    Represents a block quote.
    """

    children: List[BlockNode]

    def to_markdown(self) -> str:
        text: str = "".join([c.to_markdown() for c in self.children])
        return prefix_all_lines(fill(text), ">")


@dataclass
class MathBlock:
    """
    Represents a block of math.
    """

    contents: str

    def to_markdown(self) -> str:
        return "```ct:math\n" + self.contents + "```"


#
# The Document class.
#


@dataclass
class CTDocument:
    """
    Represents a document in Cartesian Theatre.
    """

    children: List[BlockNode]

    def to_markdown(self) -> str:
        return "\n\n".join([c.to_markdown() for c in self.children])


#
# Utils
#


def prefix_all_lines(text: str, prefix: str = "") -> str:
    lines = [prefix + line for line in text.split("\n")]
    return "\n".join(lines)


def fill(text: str) -> str:
    return textwrap.fill(text, width=80)


def indent_list_contents(text: str) -> str:
    lines = text.split("\n")
    if lines:
        first = lines[0]
        rest = lines[1:]

        first = " " + first
        rest = ["   " + line for line in rest]

        return first + "\n" + "\n".join(rest)
    else:
        return ""
