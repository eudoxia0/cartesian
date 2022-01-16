"""
This module contains classes for representing errors in cartesian theatre.
"""


class CTError(Exception):
    title: str
    message: str

    def __init__(self, title: str, message: str):
        self.title = title
        self.message = message
        super().__init__(self.message)

    def to_json(self) -> dict:
        """
        Render the exception as a JSON object for the API.
        """
        return {
            "title": self.title,
            "message": self.message,
        }

    def __str__(self):
        return f"{self.title}: {self.message}"
