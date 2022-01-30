"""
This module contains dataclasses for the representation of text in Cartesian Theatre.
"""
from dataclasses import dataclass
from typing import List, Union

#
# Inline fragments
#

InlineFragment = Union[
    "TextFragment",
    "MathFragment",
    "InternalLinkFragment",
    "WebLinkFragment",
    "CheckboxFragment",
]


@dataclass
class TextFragment:
    """
    Represents an inline chunk of text.
    """

    contents: str
    emphasized: bool
    bold: bool
    code: bool


@dataclass
class MathFragment:
    """
    Represents inline math.
    """

    contents: str


@dataclass
class InternalLinkFragment:
    """
    Represents a link to another object in Cartesian Theatre.
    """

    title: str


@dataclass
class WebLinkFragment:
    """
    Represents a link to the web.
    """

    url: str


@dataclass
class CheckboxFragment:
    """
    Represents a checkbox.
    """

    checked: bool


#
# Block nodes
#

BlockNode = Union[
    "Paragraph",
    "OrderedList",
    "UnorderedList",
    "HorizontalRule",
    "Heading",
    "CodeBlock",
    "BlockQuote",
    "MathBlock",
    "FileBlock",
]


@dataclass
class Paragraph:
    """
    Represents a paragraph containing inline text.
    """

    children: List[InlineFragment]


@dataclass
class ListItem:
    """
    Represents an item in an ordered or unordered list.
    """

    children: List[BlockNode]


@dataclass
class OrderedList:
    children: List[ListItem]


@dataclass
class UnorderedList:
    children: List[ListItem]


@dataclass
class HorizontalRule:
    """
    Represents a horizontal break.
    """


@dataclass
class Heading:
    """
    Represents a heading.
    """

    children: List[InlineFragment]


@dataclass
class CodeBlock:
    """
    Represents a code block.
    """

    contents: str


@dataclass
class BlockQuote:
    """
    Represents a block quote.
    """

    children: List[BlockNode]


@dataclass
class MathBlock:
    """
    Represents a block of math.
    """

    contents: str

@dataclass
class FileBlock:
    """
    Represents an embedded file block.
    """

    id: int
    filename: str
    mime_type: str


#
# The Document class.
#


@dataclass
class CTDocument:
    """
    Represents a document in Cartesian Theatre.
    """

    children: List[BlockNode]
