"""
Code to extract wiki links from a document.
"""
from typing import Optional, Set

from theatre.error import CTError
from theatre.text import *


def extract_links(doc: CTDocument) -> Set[str]:
    return set.union(*[extract_block_links(elem) for elem in doc.children])


def extract_block_links(block: BlockNode) -> Set[str]:
    if isinstance(block, Paragraph):
        return set(
            [
                elem
                for elem in [extract_frag_links(elem) for elem in block.children]
                if elem is not None
            ]
        )
    elif isinstance(block, OrderedList):
        return set.union(*[extract_item_links(elem) for elem in block.children])
    elif isinstance(block, UnorderedList):
        return set.union(*[extract_item_links(elem) for elem in block.children])
    elif isinstance(block, HorizontalRule):
        return set()
    elif isinstance(block, CodeBlock):
        return set()
    elif isinstance(block, Heading):
        return set(
            [
                elem
                for elem in [extract_frag_links(elem) for elem in block.children]
                if elem is not None
            ]
        )
    elif isinstance(block, BlockQuote):
        return set.union(*[extract_block_links(elem) for elem in block.children])
    elif isinstance(block, MathBlock):
        return set()
    elif isinstance(block, FileBlock):
        return set()
    else:
        raise CTError("Unknown Block Node", "Unknown block node type.")


def extract_item_links(item: ListItem) -> Set[str]:
    return set.union(*[extract_block_links(elem) for elem in item.children])


def extract_frag_links(frag: InlineFragment) -> Optional[str]:
    if isinstance(frag, InternalLinkFragment):
        return frag.title
    else:
        return None
