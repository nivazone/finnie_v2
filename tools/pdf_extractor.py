from langchain.tools import tool
import pdfplumber

@tool
def pdf_extractor(pdf_path: str) -> str:
    """
    Extracts the full textual content and tabular data from a PDF file.

    This tool processes a PDF document and returns a single plain text string 
    containing:
        - all extracted page text (in natural reading order)
        - all detected tables (formatted as plain text with rows and columns)

    Tables are flattened into text using pipe delimiters (" | ") between columns, 
    and page boundaries are clearly marked.

    Args:
        pdf_path (str): The file path to the PDF document to be processed.

    Returns:
        str: A unified plain text output containing both the document text 
             and any table data.
    """

    output = ""
    with pdfplumber.open(pdf_path) as pdf:
        for page in pdf.pages:
            output += f"\n\n--- Page {page.page_number} ---\n\n"
            output += page.extract_text() or ""
            tables = page.extract_tables()
            if tables:
                for table in tables:
                    output += "\n[Table]\n"
                    for row in table:
                        output += " | ".join(str(cell) for cell in row) + "\n"
    return output.strip()