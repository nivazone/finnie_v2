def read_statement_from_db() -> str:
    """
    Reads statement from database

    Returns:
        str: JSON data of the bank statement
    """

    print(f"[read_statement_from_db] reading from database...")

    statement_json = """
    {
        "bank_statement": {
            "account_name": "Nivantha Mandawala",
            "opening_balance": 2000,
            "closing_balance": 4000,
            "start_date": "2025-04-01",
            "end_date": "2025-04-30",
            "transactions": [
            {
                "date": "2025-04-01",
                "description": "Tango Energy",
                "amount": 45
            },
            {
                "date": "2025-04-02",
                "description": "Uber Eats",
                "amount": 34
            }
            ]
        }
    }
    """

    return statement_json