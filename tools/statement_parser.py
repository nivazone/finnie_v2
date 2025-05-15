from langchain.tools import tool
from langchain_core.messages import HumanMessage
from shared.dependencies import get_llm
import json

@tool
def statement_parser(text: str) -> dict:
    """
    Parses raw bank statement text into structured account and transaction data.

    This tool uses an LLM to extract structured financial details from 
    unstructured bank statement text. It returns a clean JSON object 
    containing high-level account metadata and individual transaction records.

    Extracted fields include:
        - account_holder: Name of the account owner.
        - account_name: Name or label of the account.
        - start: Statement start date (string format).
        - end: Statement end date (string format).
        - opening_balance: Opening balance at start of period.
        - closing_balance: Closing balance at end of period.
        - credit_limit: Credit limit (if applicable).
        - interest_charged: Interest charges for the period.
        - transactions: List of transactions, each with:
            - date: Transaction date (string).
            - transaction_details: Merchant or description.
            - amount: Transaction amount (positive or negative).

    Args:
        text (str): The full text content of the bank statement, 
                    including any transaction data and summaries.

    Returns:
        dict: A dictionary containing structured account data and 
              transaction details as extracted by the LLM.
    """

    llm = get_llm()
    prompt = f"""
        You are a bank statement parser.
        Output ONLY raw JSON.
        Extract the following fields:
            account_holder: name of the account owner,
            account_name: name of the account,
            start: statement start date,
            end: statement end date,
            opening_balance: numeric opening balance,
            closing_balance: numeric closing balance,
            credit_limit: numeric credit limit,
            interest_charged: numeric interest charged,
            transactions: list of date, transaction_details, amount.

        Text:
        {text}
        """
    response = llm.invoke([HumanMessage(content=prompt)])
    return json.loads(response.content.strip())