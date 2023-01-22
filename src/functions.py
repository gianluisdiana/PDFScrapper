import re
import os

def formatText(text: str) -> str:
    """Formats the text to be a title without spaces.

    Args:
        text (str): The text to format.

    Returns:
        The formatted text."""
    text_formatted = " ".join(re.findall(r'\w+', text)) \
        .title() \
        .replace(" ", "")
    return text_formatted

def getNewestFile(folder: str) -> str:
    """Gets the newest file in a folder.

    Args:
        folder (str): The folder to search.

    Returns:
        The name of the newest file.
    """
    files = [os.path.join(folder, file) for file in os.listdir(folder)]
    return max(files, key=os.path.getctime)