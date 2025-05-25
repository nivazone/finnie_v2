import pdfplumber
from langchain_core.tools import tool
from logger import log
import os

def _extract_text(path: str) -> dict:
    """
    Extracts the full textual content and tabular data from a PDF file.

    Args:
        path: path to the bank statement

    Returns:
        dict: {"extracted_text": "...", "fatal_err": False} or {"fatal_err": True}
    """

    log.info(f"[extract_text] extracting text from {path}...")
    
    output = ""
    
    with pdfplumber.open(path) as pdf:
        for page in pdf.pages:
            output += f"\n\n--- Page {page.page_number} ---\n\n"
            output += page.extract_text() or ""
            tables = page.extract_tables()
            if tables:
                for table in tables:
                    output += "\n[Table]\n"
                    for row in table:
                        output += " | ".join(str(cell) for cell in row) + "\n"

    return {
        "extracted_text": output.strip(),
    }

@tool
def extract_all_texts(folder_path: str) -> dict:
    """
    Iterates over all PDF files in a folder and extracts their content using extract_text.

    Args:
        folder_path (str): Path to folder containing PDF files.

    Returns:
        dict: {
            "batches": ["text of document 1", "text of document 2", ...],
            "fatal_err": False
        }
        or
        {"fatal_err": True} if any fails.
    """

    log.info(f"[extract_all_texts] going through {folder_path}...")

    batches = []
    
    try:
        for filename in sorted(os.listdir(folder_path)):
            if filename.lower().endswith(".pdf"):
                full_path = os.path.join(folder_path, filename)
                result = _extract_text(full_path)
                content = result.get("extracted_text")
                batches.append(content)

        return {"batches": batches}

    except Exception as e:
        log.error(f"[extract_all_texts_from_folder] Fatal error: {e}")
        return {"fatal_err": True}
