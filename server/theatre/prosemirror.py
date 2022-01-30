"""
This module contains code to map the text model to and from ProseMirror JSON.
"""
from theatre.error import CTError
from theatre.text import *

#
# Parsing from JSON
#

# Parsing documents


def parse_document(doc: dict) -> CTDocument:
    return CTDocument(children=[parse_block_node(elem) for elem in doc["content"]])


# Parsing block nodes


def parse_block_node(json: dict):
    parsers = {
        "paragraph": parse_paragraph,
        "ordered_list": parse_ordered_list,
        "bullet_list": parse_unordered_list,
        "horizontal_rule": parse_horizontal_rule,
        "code_block": parse_code_block,
        "blockquote": parse_block_quote,
        "math_display": parse_math_block,
        "file_embed": parse_file_block,
    }
    return parsers[json["type"]](json)


def parse_paragraph(json: dict) -> Paragraph:
    return Paragraph(
        children=[parse_fragment(elem) for elem in json.get("content", [])]
    )


def parse_unordered_list(json: dict) -> UnorderedList:
    return UnorderedList(children=[parse_list_item(elem) for elem in json["content"]])


def parse_ordered_list(json: dict) -> OrderedList:
    return OrderedList(children=[parse_list_item(elem) for elem in json["content"]])


def parse_list_item(json: dict) -> ListItem:
    return ListItem(children=[parse_block_node(elem) for elem in json["content"]])


def parse_horizontal_rule(json: dict) -> HorizontalRule:
    return HorizontalRule()


def parse_code_block(json: dict) -> CodeBlock:
    return CodeBlock(contents="".join([node["text"] for node in json["content"]]))


def parse_block_quote(json: dict) -> BlockQuote:
    return BlockQuote(children=[parse_block_node(elem) for elem in json["content"]])


def parse_math_block(json: dict) -> MathBlock:
    return MathBlock(contents="".join([node["text"] for node in json["content"]]))


def parse_file_block(json: dict) -> FileBlock:
    attrs: dict = json["attrs"]
    return FileBlock(
        id=attrs["file_id"], filename=attrs["filename"], mime_type=attrs["mime_type"]
    )


# Parsing fragments


def parse_fragment(json: dict):
    parsers = {
        "text": parse_text,
        "wikilinknode": parse_wiki_link,
        "math_inline": parse_inline_math,
        "checkbox": parse_checkbox,
    }
    return parsers[json["type"]](json)


def parse_text(json: dict) -> Union[TextFragment, WebLinkFragment]:
    marks: List[dict] = json.get("marks", [])
    is_link: bool = bool([mark for mark in marks if mark.get("type", "") == "link"])
    if is_link:
        link_mark: dict = [mark for mark in marks if mark.get("type", "") == "link"][0]
        url: str = link_mark["attrs"]["href"]
        return WebLinkFragment(url=url)
    else:
        is_em: bool = bool([mark for mark in marks if mark.get("type", "") == "em"])
        is_bold: bool = bool(
            [mark for mark in marks if mark.get("type", "") == "strong"]
        )
        is_code: bool = bool([mark for mark in marks if mark.get("type", "") == "code"])
        return TextFragment(
            contents=json["text"], emphasized=is_em, bold=is_bold, code=is_code
        )


def parse_wiki_link(json: dict) -> InternalLinkFragment:
    return InternalLinkFragment(title=json["attrs"]["title"])


def parse_inline_math(json: dict) -> MathFragment:
    return MathFragment(contents="".join([node["text"] for node in json["content"]]))


def parse_checkbox(json: dict) -> CheckboxFragment:
    return CheckboxFragment(checked=json["attrs"]["checked"])


#
# Emitting to JSON
#


def emit_document(doc: CTDocument) -> dict:
    return {"type": "doc", "content": [emit_block(elem) for elem in doc.children]}


def emit_block(block: BlockNode) -> dict:
    if isinstance(block, Paragraph):
        return {
            "type": "paragraph",
            "content": [emit_frag(elem) for elem in block.children],
        }
    elif isinstance(block, OrderedList):
        return {
            "type": "ordered_list",
            "content": [emit_list_item(elem) for elem in block.children],
        }
    elif isinstance(block, UnorderedList):
        return {
            "type": "bullet_list",
            "content": [emit_list_item(elem) for elem in block.children],
        }
    elif isinstance(block, HorizontalRule):
        return {
            "type": "horizontal_rule",
        }
    elif isinstance(block, CodeBlock):
        return {
            "type": "code_block",
            "content": [{"type": "text", "text": block.contents}],
        }
    elif isinstance(block, BlockQuote):
        return {
            "type": "blockquote",
            "content": [emit_block(elem) for elem in block.children],
        }
    elif isinstance(block, MathBlock):
        return {
            "type": "math_display",
            "content": [{"type": "text", "text": block.contents}],
        }
    elif isinstance(block, FileBlock):
        return {
            "type": "file_embed",
            "attrs": {
                "file_id": block.id,
                "filename": block.filename,
                "mime_type": block.mime_type,
            },
        }
    else:
        raise CTError("Unknown Block Node", "Unknown block node type.")


def emit_list_item(item: ListItem) -> dict:
    return {
        "type": "list_item",
        "content": [emit_block(elem) for elem in item.children],
    }


def emit_frag(frag: InlineFragment) -> dict:
    if isinstance(frag, TextFragment):
        marks = []
        if frag.emphasized:
            marks.append({"type": "em"})
        if frag.bold:
            marks.append({"type": "strong"})
        if frag.code:
            marks.append({"type": "code"})
        return {"type": "text", "marks": marks, "text": frag.contents}
    elif isinstance(frag, MathFragment):
        return {
            "type": "math_inline",
            "content": [{"type": "text", "text": frag.contents}],
        }
    elif isinstance(frag, InternalLinkFragment):
        return {"type": "wikilinknode", "attrs": {"title": frag.title}}
    elif isinstance(frag, WebLinkFragment):
        return {
            "type": "text",
            "text": frag.url,
            "marks": [{"type": "link", "attrs": {"href": frag.url}}],
        }
    elif isinstance(frag, CheckboxFragment):
        return {
            "type": "checkbox",
            "attrs": {
                "checked": frag.checked,
            },
        }
    else:
        raise CTError("Unknown Inline Fragment", "Unknown inline fragment type.")
