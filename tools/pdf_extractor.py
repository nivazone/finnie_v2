from langchain.tools import tool
import pdfplumber
from shared.agent_state import AgentState

@tool
def pdf_extractor(state: AgentState) -> AgentState:
    """
    Extracts the full textual content and tabular data from a PDF file.

    This tool processes a PDF document and returns a single plain text string 
    containing:
        - all extracted page text (in natural reading order)
        - all detected tables (formatted as plain text with rows and columns)

    Tables are flattened into text using pipe delimiters (" | ") between columns, 
    and page boundaries are clearly marked.

    Args:
        state (AgentState): Graph state containing 'pdf_path'.

    Returns:
        AgentState: Updated state with 'extracted_text' containing both the document text and any table data.
    """

    print(f"[pdf_extractor] path = {state['pdf_path']}")

    output = ""
    with pdfplumber.open(state["pdf_path"]) as pdf:
        for page in pdf.pages:
            output += f"\n\n--- Page {page.page_number} ---\n\n"
            output += page.extract_text() or ""
            tables = page.extract_tables()
            if tables:
                for table in tables:
                    output += "\n[Table]\n"
                    for row in table:
                        output += " | ".join(str(cell) for cell in row) + "\n"
    
    state["extracted_text"] = output.strip()
    return state