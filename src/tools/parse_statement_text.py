def parse_statement_text(text: str) -> str:
    """
    Parses raw bank statement text into structured account and transaction data.

    Extracted fields include:
        - account name: Name or label of the account.
        - start: Statement start date (string format).
        - end: Statement end date (string format).
        - opening_balance: Opening balance at start of period.
        - closing_balance: Closing balance at end of period.
        - transactions: List of transactions, each with:
            - date: Transaction date (string).
            - transaction_details: Merchant or description.
            - amount: Transaction amount (positive or negative).

    Args:
        text: plain text from the bank statement

    Returns:
        str: valid json string
    """

    print(f"[parse_statement_text] parsing extracted text...")

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