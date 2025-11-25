import os
import logging
from typing import List

logger = logging.getLogger(__name__)

def read_documentation_files(filenames: List[str], base_dir: str = "uploaded_docs") -> str:
    """
    Reads and concatenates multiple documentation text files from the given directory.
    """
    combined_text = ""
    for filename in filenames:
        file_path = os.path.join(base_dir, filename)
        if not os.path.exists(file_path):
            logger.warning(f"Documentation file '{filename}' not found at {file_path}. Skipping.")
            continue
        try:
            with open(file_path, "r", encoding="utf-8") as f:
                combined_text += f.read() + "\n"
        except Exception as e:
            logger.error(f"Failed reading doc file '{filename}': {e}")
    return combined_text

def read_html_files(filenames: List[str], base_dir: str = "uploaded_html") -> str:
    """
    Reads and concatenates multiple HTML files from the given directory.
    """
    combined_html = ""
    for filename in filenames:
        file_path = os.path.join(base_dir, filename)
        if not os.path.exists(file_path):
            logger.warning(f"HTML file '{filename}' not found at {file_path}. Skipping.")
            continue
        try:
            with open(file_path, "r", encoding="utf-8") as f:
                combined_html += f.read() + "\n"
        except Exception as e:
            logger.error(f"Failed reading HTML file '{filename}': {e}")
    return combined_html
