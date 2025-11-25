# utils/file_utils.py
import os

def read_documentation_files(filenames: list) -> str:
    combined_text = ""
    for filename in filenames:
        file_path = os.path.join("uploaded_docs", filename)
        if not os.path.exists(file_path):
            raise FileNotFoundError(f"Documentation file '{filename}' not found.")
        with open(file_path, "r", encoding="utf-8") as f:
            combined_text += f.read() + "\n"
    return combined_text

def read_html_files(filenames: list) -> str:
    combined_html = ""
    for filename in filenames:
        file_path = os.path.join("uploaded_html", filename)
        if not os.path.exists(file_path):
            raise FileNotFoundError(f"HTML file '{filename}' not found.")
        with open(file_path, "r", encoding="utf-8") as f:
            combined_html += f.read() + "\n"
    return combined_html


