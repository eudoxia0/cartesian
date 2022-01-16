import unittest
from theatre.new_text import *
from theatre.extract_links import extract_links


class ExtractLinksTestCase(unittest.TestCase):
    def test_extract_links(self):
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
                                                )
                                            ]
                                        )
                                    ]
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
                    ]
                ),
            ]
        )
        self.assertEqual(extract_links(doc), {"A", "B", "C", "D"})
