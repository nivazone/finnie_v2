def write_statement_to_db(statement_json: str) -> bool:
    """
    Writes structured bank statement data and transactions into database.
    
    Args:
        statement_json: A valid JSON string.

    Returns:
        bool: True or False indicating DB write was successful or not.
    """

    print(f"[write_statement_to_db] saving to database...")

    return True