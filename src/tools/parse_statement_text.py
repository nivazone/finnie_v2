from dependencies import get_llm
from langchain_core.messages import HumanMessage
from typing import Any
import json

def parse_statement_text(text: str) -> str:
    """
    Parses raw bank statement text into structured account and transaction data.

    Extracted fields include:
        - account_holder: Name of the account owner.
        - account_name: Name or label of the account.
        - start_date: Statement start date (string format).
        - end_date: Statement end date (string format).
        - opening_balance: Opening balance at start of period.
        - closing_balance: Closing balance at end of period.
        - credit_limit: Credit limit (if applicable).
        - interest_charged: Interest charges for the period.
        - transactions: List of transactions, each with:
            - transaction_date: Transaction date (string).
            - transaction_details: Merchant or description.
            - amount: Transaction amount (positive or negative).

    Args:
        text: plain text from the bank statement

    Returns:
        str: A valid JSON string containing parsed bank statement data
    """

    print(f"[parse_statement_text] parsing extracted text...")

    llm = get_llm()
    prompt = f"""
        You are a bank statement parser.
        
        Important:
        - Return a valid **raw JSON object**, not inside a markdown block.
        - Do not format the output as a code block. Do not use ```json or ``` markers.
        - Only output the pure JSON object without any extra text.
        
        Parse the following fields:
            account_holder: name of the account owner,
            account_name: name of the account,
            start_date: statement start date,
            end_date: statement end date,
            opening_balance: numeric opening balance,
            closing_balance: numeric closing balance,
            credit_limit: numeric credit limit,
            interest_charged: numeric interest charged,
            transactions: list of transaction_date, transaction_details, amount.

        Raw text to parse:
        {text}
        """
    response = llm.invoke([HumanMessage(content=prompt)])

    return response.content.strip()