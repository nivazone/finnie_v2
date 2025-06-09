import pdfplumber
from langchain_core.tools import tool
from logger import log
import os
from langchain_core.runnables.config import RunnableConfig
from langchain_core.callbacks.manager import adispatch_custom_event
from memory_store import put_item

def _extract_text(path: str) -> dict:
    """
    Extracts the full textual content and tabular data from a PDF file.

    Args:
        path: path to the bank statement

    Returns:
        dict: {"extracted_text": "...", "fatal_err": False} or {"fatal_err": True}
    """
    
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
async def extract_all_texts(folder_path: str, config: RunnableConfig) -> dict:
    """
    Iterates over all PDF files in a folder and extracts their content using extract_text.

    Args:
        folder_path (str): Path to folder containing PDF files.

    Returns:
        dict: {
            "batch_refs": ["<ref_id1>", "<ref_id2>", ...],
            "fatal_err": False
        }
        or
        {"fatal_err": True} if any fails.
    """

    log.info(f"[extract_all_texts] going through {folder_path}...")

    await adispatch_custom_event("on_extract_all_texts", {"friendly_msg": "Extracting text...\n"}, config=config)

    ref_ids = []
    
    try:
        for filename in sorted(os.listdir(folder_path)):
            if filename.lower().endswith(".pdf"):
                full_path = os.path.join(folder_path, filename)
                result = _extract_text(full_path)
                content = result.get("extracted_text")

                ref_id = put_item(content)
                ref_ids.append(ref_id)

        return {"batch_refs": ref_ids, "fatal_err": False}

    except Exception as e:
        log.error(f"[extract_all_texts_from_folder] Fatal error: {e}")
        return {
            "fatal_err": True,
            "err_details": str(e)
        }
