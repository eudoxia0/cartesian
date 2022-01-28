"""
Code to rename links in a document.
"""
from theatre.error import CTError
from theatre.text import *


def rename_link(doc: CTDocument, old_title: str, new_title: str) -> CTDocument:
    return CTDocument(
        children=[rn_block(elem, old_title, new_title) for elem in doc.children]
    )


def rn_block(block: BlockNode, old_title: str, new_title: str) -> BlockNode:
    if isinstance(block, Paragraph):
        return Paragraph(
            children=[rn_frag(elem, old_title, new_title) for elem in block.children]
        )
    elif isinstance(block, OrderedList):
        return OrderedList(
            children=[rn_item(elem, old_title, new_title) for elem in block.children]
        )
    elif isinstance(block, UnorderedList):
        return UnorderedList(
            children=[rn_item(elem, old_title, new_title) for elem in block.children]
        )
    elif isinstance(block, HorizontalRule):
        return HorizontalRule()
    elif isinstance(block, CodeBlock):
        return CodeBlock(contents=block.contents)
    elif isinstance(block, BlockQuote):
        return BlockQuote(
            children=[rn_block(elem, old_title, new_title) for elem in block.children]
        )
    elif isinstance(block, MathBlock):
        return MathBlock(contents=block.contents)
    else:
        raise CTError("Unknown Block Node", "Unknown block node type.")


def rn_item(item: ListItem, old_title: str, new_title: str) -> ListItem:
    return ListItem(
        children=[rn_block(elem, old_title, new_title) for elem in item.children]
    )


def rn_frag(frag: InlineFragment, old_title: str, new_title: str) -> InlineFragment:
    if isinstance(frag, InternalLinkFragment):
        if frag.title == old_title:
            return InternalLinkFragment(title=new_title)
        else:
            return frag
    else:
        return frag
