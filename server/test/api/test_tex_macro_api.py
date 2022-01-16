import unittest

from test.api.helpers import DatabaseMixin


class TexMacroApiTestCase(DatabaseMixin, unittest.TestCase):
    """
    Tests of the Tex macro API.
    """

    def test_set_and_retrieve(self):
        """
        Test the /api/tex-macros endpoint.
        """
        # Request
        response = self.client.get("/api/tex-macros")
        # Assertions
        self.assertEqual(response.status_code, 200)
        self.assertEqual(
            response.json,
            {
                "data": "",
                "error": None,
            },
        )
        # Request
        response = self.client.post("/api/tex-macros", json={"macros": "test"})
        # Assertions
        self.assertEqual(response.status_code, 200)
        self.assertEqual(
            response.json,
            {
                "data": None,
                "error": None,
            },
        )
        # Request
        response = self.client.get("/api/tex-macros")
        # Assertions
        self.assertEqual(response.status_code, 200)
        self.assertEqual(
            response.json,
            {
                "data": "test",
                "error": None,
            },
        )
