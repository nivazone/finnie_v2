from dependencies import get_text_parser_llm
from typing import List
from pydantic import BaseModel, Field
from logger import log
from langchain_core.tools import tool
import asyncio

DELAY_BETWEEN_BATCHES = 1.0

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

async def _parse_statement_text(text: str) -> dict:
    """
    Parses raw bank statement text into structured account and transaction data.

    Args:
        text: plain text from the bank statement

    Returns:
        dict: {
            "parsed_text": "...", 
            "fatal_err": False} or {"fatal_err": True}
    """

    
    llm = get_text_parser_llm().with_structured_output(BankStatement)
    response = await llm.ainvoke("Parse this bank statement text:\n" + text)

    return {
        "parsed_text": response,
    }
    
@tool
async def parse_all_statements(batch: List[str]) -> dict:
    """
    Parses a raw batch of bank statement texts into structured data including transactions.

    Args:
        batch: A list of plain-text bank statements (as strings)

    Returns:
        dict:
            {
                "parsed_texts": [
                    {"parsed_text": {...}},
                    ...
                ],
                "fatal_err": False
            }
            or
            {"fatal_err": True} if any statement fails.
        }
    """

    log.info(f"[parse_all_statements] parsing extracted texts...")

    parsed_texts = []

    for i, text in enumerate(batch):
        log.info(f"[parse_all_statements] Parsing statement {i + 1}/{len(batch)}")

        try:
            result = await _parse_statement_text(text)
            
            if result.get("fatal_err"):
                log.error(f"[parse_all_statements] Fatal error during parsing at index {i}")
                return {"fatal_err": True}

            parsed_texts.append({"parsed_text": result["parsed_text"]})

            log.info(f"parsed {i+1} statement(s) in this batch. Waiting {DELAY_BETWEEN_BATCHES} to avoid rate limits.")
            await asyncio.sleep(DELAY_BETWEEN_BATCHES)

        except Exception as e:
            log.error(f"[parse_all_statements] Exception at index {i}: {e}")
            return {"fatal_err": True}

    return {
        "parsed_texts": parsed_texts,
        "fatal_err": False
    }

    