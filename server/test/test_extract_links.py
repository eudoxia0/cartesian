import unittest
from theatre.text import *
from theatre.extract_links import extract_links, extract_file_links

doc = CTDocument(
    children=[
        Paragraph(
            children=[
                InternalLinkFragment(title="A"),
                InternalLinkFragment(title="B"),
            ]
        ),
        UnorderedList(
            children=[
                ListItem(
                    children=[
                        Paragraph(
                            children=[
                                InternalLinkFragment(title="A"),
                            ]
                        ),
                        OrderedList(
                            children=[
                                ListItem(
                                    children=[
                                        Paragraph(
                                            children=[
                                                InternalLinkFragment(title="C"),
                                            ]
                                        ),
                                        FileBlock(
                                            id=1,
                                            filename="1.jpg",
                                            mime_type="image/jpeg",
                                        ),
                                    ]
                                )
                            ]
                        ),
                        FileBlock(
                            id=2,
                            filename="2.png",
                            mime_type="image/png",
                        ),
                    ]
                )
            ]
        ),
        BlockQuote(
            children=[
                Paragraph(
                    children=[
                        InternalLinkFragment(title="B"),
                        InternalLinkFragment(title="C"),
                        InternalLinkFragment(title="D"),
                    ]
                ),
                FileBlock(
                    id=3,
                    filename="3.tiff",
                    mime_type="image/tiff",
                ),
            ]
        ),
    ]
)


class ExtractLinksTestCase(unittest.TestCase):
    def test_extract_wiki_links(self):
        self.assertEqual(extract_links(doc), {"A", "B", "C", "D"})

    def test_extract_file_links(self):
        self.assertEqual(
            extract_file_links(doc),
            {
                FileBlock(
                    id=1,
                    filename="1.jpg",
                    mime_type="image/jpeg",
                ),
                FileBlock(
                    id=2,
                    filename="2.png",
                    mime_type="image/png",
                ),
                FileBlock(
                    id=3,
                    filename="3.tiff",
                    mime_type="image/tiff",
                ),
            },
        )
