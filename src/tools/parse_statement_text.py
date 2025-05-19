from dependencies import get_text_parser_llm
from langchain_core.messages import HumanMessage
from typing import Any
import json

BANK_STATEMENT_SCHEMA = {
    "type": "object",
    "properties": {
        "account_holder": {"type": "string"},
        "account_name": {"type": "string"},
        "start_date": {
            "type": "string",
            "format": "date",
            "pattern": "^\\d{4}-\\d{2}-\\d{2}$"  # YYYY-MM-DD
        },
        "end_date": {
            "type": "string",
            "format": "date",
            "pattern": "^\\d{4}-\\d{2}-\\d{2}$"
        },
        "opening_balance": {"type": "number"},
        "closing_balance": {"type": "number"},
        "credit_limit": {"type": "number"},
        "interest_charged": {"type": "number"},
        "transactions": {
            "type": "array",
            "items": {
                "type": "object",
                "properties": {
                    "transaction_date": {
                        "type": "string",
                        "format": "date",
                        "pattern": "^\\d{4}-\\d{2}-\\d{2}$"
                    },
                    "transaction_details": {"type": "string"},
                    "amount": {"type": "number"}
                },
                "required": [
                    "transaction_date",
                    "transaction_details",
                    "amount"
                ]
            }
        }
    },
    "required": [
        "account_holder",
        "account_name",
        "start_date",
        "end_date",
        "opening_balance",
        "closing_balance",
        "credit_limit",
        "interest_charged",
        "transactions"
    ]
}

def parse_statement_text(text: str) -> dict:
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
    Returns:
        dict: {"parsed_text": "...", "fatal_err": False} or {"fatal_err": True}
    """

    print(f"[parse_statement_text] parsing extracted text...")

    # llm = get_text_parser_llm()
    llm = get_text_parser_llm(model_kwargs={
        "response_format": {
            "type": "json_schema",
            "schema": BANK_STATEMENT_SCHEMA
        }
    })

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

    return {
        "parsed_text": response.content.strip(),
    }