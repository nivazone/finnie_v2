from dependencies import get_text_parser_llm
from typing import List
from pydantic import BaseModel, Field
from logger import log
class Transaction(BaseModel):
    """A single transaction in the bank statement."""

    transaction_date: str = Field(description="Transaction date in YYYY-MM-DD format")
    transaction_details: str = Field(description="Details or description of the transaction")
    amount: float = Field(description="Transaction amount")

class BankStatement(BaseModel):
    """Structured bank statement."""

    account_holder: str = Field(description="Name of the account holder")
    account_name: str = Field(description="Name or label of the account")
    start_date: str = Field(description="Statement start date in YYYY-MM-DD format")
    end_date: str = Field(description="Statement end date in YYYY-MM-DD format")
    opening_balance: float = Field(description="Opening balance at the start of the period")
    closing_balance: float = Field(description="Closing balance at the end of the period")
    credit_limit: float = Field(description="Credit limit (if applicable)")
    interest_charged: float = Field(description="Interest charges for the period")
    transactions: List[Transaction] = Field(description="List of transactions")

async def parse_statement_text(text: str) -> dict:
    """
    Parses raw bank statement text into structured account and transaction data.

    Args:
        text: plain text from the bank statement

    Returns:
        dict: {"parsed_text": "...", "fatal_err": False} or {"fatal_err": True}
    """

    log.info(f"[parse_statement_text] parsing extracted text...")

    try:
        llm = get_text_parser_llm().with_structured_output(BankStatement)
        response = await llm.ainvoke("Parse this bank statement text:\n" + text)

        return {
            "parsed_text": response.dict(),
        }
    
    except Exception as e:
        log.error(f"Failed to parse text: {e}")
        return {"fatal_err": True}