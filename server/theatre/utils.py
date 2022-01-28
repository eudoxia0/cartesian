"""
Utility module.
"""
import subprocess
import tempfile
from datetime import datetime


def now_millis() -> int:
    return datetime_to_millis(datetime.now())


def datetime_to_millis(stamp: datetime) -> int:
    """
    Convert a datetime to Unix time in milliseconds.
    """
    return int(stamp.timestamp() * 1000)


def millis_to_datetime(millis: int) -> datetime:
    """
    Convert a Unix time in milliseconds to a datetime.
    """
    return datetime.fromtimestamp(float(millis) / 1000)


def determine_mime_type(blob: bytes) -> str:
    """
    Determine the MIME-type of a byte stream.
    """
    # Write the contents to a temporary file
    stream = tempfile.NamedTemporaryFile()
    stream.write(blob)
    stream.flush()
    # Shell out to the `file` tool to extract the MIME type.
    mime_type: str = (
        subprocess.check_output(["file", "-b", "--mime-type", stream.name])
        .decode("utf-8")
        .strip()
    )
    # Close the stream, deleting the file.
    stream.close()
    return mime_type
