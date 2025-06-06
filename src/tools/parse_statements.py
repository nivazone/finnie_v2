from dependencies import get_text_parser_llm
from typing import List
from pydantic import BaseModel, Field
from logger import log
from langchain_core.tools import tool
import asyncio
from decimal import Decimal
from memory_store import get_item, put_item

DELAY_BETWEEN_BATCHES = 1.0
PARSING_RULES_PROMPT = """
You are parsing Australian bank statements into JSON that matches the BankStatement schema EXACTLY.

Sign convention:
- For all accounts:
    - money **IN**  (deposits, refunds, salary) -> POSITIVE amount
    - money **OUT** (purchases, fees, transfers) -> NEGATIVE amount
    - purchases / interest -> NEGATIVE
    - payments / refunds -> POSITIVE

- Do NOT include "CR"/"DR" text—use the sign only.
- Use YYYY-MM-DD dates and include every transaction in order.
"""

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
    Parses raw bank-statement text into structured data.

    Returns:
        dict: { "parsed_text": BankStatement }
    """

    llm = get_text_parser_llm().with_structured_output(BankStatement)
    response: BankStatement = await llm.ainvoke(PARSING_RULES_PROMPT + "\n\n---\n\n" + text)

    return {"parsed_text": response}


# ─────────────────────────────── batch tool ──────────────────────────────
@tool
async def parse_all_statements(ref_ids: List[str]) -> dict:
    """
    Parses multiple plain-text statements (referenced via memory keys) into
    structured JSON, returning new memory keys of parsed results.
    """
    log.info(f"[parse_all_statements] parsing {len(ref_ids)} statement(s)…")
    parsed_refs = []

    for i, ref_id in enumerate(ref_ids):
        try:
            log.info(f"[parse_all_statements] parsing {ref_id} ({i+1}/{len(ref_ids)})")
            raw_text = get_item(ref_id)
            result = await _parse_statement_text(raw_text)
            parsed_ref = put_item({"parsed_text": result["parsed_text"]})
            parsed_refs.append(parsed_ref)

            log.info(f"[parse_all_statements] parsed {i+1}/{len(ref_ids)} → sleep {DELAY_BETWEEN_BATCHES}s")
            await asyncio.sleep(DELAY_BETWEEN_BATCHES)

        except Exception as e:
            log.error(f"[parse_all_statements] exception at index {i}: {e}")
            return {"fatal_err": True, "err_details": str(e)}

    return {"parsed_refs": parsed_refs, "fatal_err": False}
