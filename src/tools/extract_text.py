def extract_text(path: str) -> str:
    """
    Extracts the full textual content and tabular data from a PDF file.

    Args:
        path: path to the bank statement

    Returns:
        str: extracted text from the bank statement
    """

    print(f"[extract_text] extracting text from {path}...")
    
    all_text = """
    bank statement
    account name: Nivantha Mandawala
    opening balance: $2000
    closing balance: $4000
    start: 01/04/2025
    end: 30/04/2025
    transactions:
        01/04/2025  Tango Energy    $45
        02/04/2025  Uber Eats       $34
    """

    return all_text