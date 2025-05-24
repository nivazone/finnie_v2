import pdfplumber
from langchain_core.tools import tool
from logger import log

@tool
def extract_text(path: str) -> dict:
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