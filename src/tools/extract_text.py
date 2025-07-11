import pdfplumber
from langchain_core.tools import tool
from logger import log
import os
import csv
from typing import List
from langchain_core.runnables.config import RunnableConfig
from langchain_core.callbacks.manager import adispatch_custom_event
from memory_store import put_item

def _extract_pdf_text(path: str) -> dict:
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
async def extract_all_pdf_texts(folder_path: str, config: RunnableConfig) -> dict:
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

    log.info(f"[extract_all_pdf_texts] going through {folder_path}...")

    await adispatch_custom_event("on_extract_all_pdf_texts", {"friendly_msg": "Extracting PDF text...\n"}, config=config)

    ref_ids = []
    
    try:
        for filename in sorted(os.listdir(folder_path)):
            if filename.lower().endswith(".pdf"):
                full_path = os.path.join(folder_path, filename)
                result = _extract_pdf_text(full_path)
                content = result.get("extracted_text")

                ref_id = put_item(content)
                ref_ids.append(ref_id)

        return {"batch_refs": ref_ids, "fatal_err": False}

    except Exception as e:
        log.error(f"[extract_all_pdf_texts] Fatal error: {e}")
        return {
            "fatal_err": True,
            "err_details": str(e)
        }
    
@tool
async def extract_all_csv_texts(folder_path: str, config: RunnableConfig) -> dict:
    """
    Iterates over all CSV files in a folder, extracts their content, and groups them into batches of 100 rows.

    Args:
        folder_path (str): Path to folder containing CSV files.

    Returns:
        dict: {
            "batch_refs": ["<ref_id1>", "<ref_id2>", ...],
            "fatal_err": False
        }
        or
        {"fatal_err": True, "err_details": "..."}
    """
    log.info(f"[extract_all_csv_texts] going through {folder_path}...")

    await adispatch_custom_event("on_extract_all_csv_texts", {"friendly_msg": "Extracting CSV text...\n"}, config=config)

    batch_size = 100
    batch_refs: List[str] = []

    try:
        for filename in sorted(os.listdir(folder_path)):
            if filename.lower().endswith(".csv"):
                full_path = os.path.join(folder_path, filename)

                with open(full_path, newline='', encoding='utf-8') as f:
                    reader = csv.reader(f)
                    headers = next(reader, [])

                    current_batch = []
                    for i, row in enumerate(reader, 1):
                        line = " | ".join(row)
                        current_batch.append(line)

                        if len(current_batch) == batch_size:
                            content = f"[CSV File: {filename}]\nHeaders: {' | '.join(headers)}\n\n" + "\n".join(current_batch)
                            ref_id = put_item(content)
                            batch_refs.append(ref_id)
                            current_batch = []

                    # Add remaining rows (final batch)
                    if current_batch:
                        content = f"[CSV File: {filename}]\nHeaders: {' | '.join(headers)}\n\n" + "\n".join(current_batch)
                        ref_id = put_item(content)
                        batch_refs.append(ref_id)

        return {"batch_refs": batch_refs, "fatal_err": False}

    except Exception as e:
        log.error(f"[extract_all_csv_texts] Fatal error: {e}")
        return {
            "fatal_err": True,
            "err_details": str(e)
        }
