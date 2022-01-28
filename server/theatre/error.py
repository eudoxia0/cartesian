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


def file_not_found(file_id: int) -> CTError:
    return CTError(
        "File Not Found",
        f"The file with the ID '{file_id}' was not found in the database.",
    )


def directory_not_found(dir_id: int) -> CTError:
    return CTError(
        "Directory Not Found",
        f"The directory with the ID '{dir_id}' was not found in the database.",
    )


def class_not_found(cls_id: int) -> CTError:
    return CTError(
        "Class Not Found",
        f"The class with the ID '{cls_id}' was not found in the database.",
    )


def class_prop_not_found(cls_prop_id: int) -> CTError:
    return CTError(
        "Class Property Not Found",
        f"The class property with the ID '{cls_prop_id}' was not found in the database.",
    )


def object_not_found(title: str) -> CTError:
    return CTError(
        "Object Not Found",
        f"The object with the title '{title}' was not found in the database.",
    )
