from langchain_core.tools import tool
from pydantic import BaseModel, Field
from typing import List
from dependencies import get_transaction_classifier_llm, get_search_client
import asyncio
from decimal import Decimal
from logger import log
from memory_store import get_item, put_item
from langchain_core.runnables import RunnableConfig
from langchain_core.callbacks.manager import adispatch_custom_event

BATCH_SIZE = 50
DELAY_BETWEEN_BATCHES = 1.0
ENRICH_WITH_WEB_CONTEXT = False
PROMPT = """
    1. Classify each transaction into one of the following categories:
        - Groceries
        - Transport
        - Household Bills
        - Entertainment
        - Subscriptions
        - Healthcare
        - Dining
        - Vet & Pet Care
        - Shopping
        - Travel
        - Unknown
        - Credit Card Payments

    2. Transactions with "ONLINE PAYMENT SYDNEY NS" must be classified as "Credit Card Payments".

    3. Decide each transaction is tax deductible or not. Follow Australian Tax Office rules.
        ### Key Rules
        - Work-related expenses are deductible (portion depends on usage).
        - Donations to charities are fully deductible.
        - Meals, groceries, children, pets are *not* deductible.
        - Mobile/Internet plans are 50 % deductible unless otherwise stated.
        - If unsure, set is_tax_deductible=false and deductible_portion=0.0.

    4. For each transaction, respond with: 
        - transaction_id 
        - classification
        - is_tax_deductible
        - deductible_portion
    """

class Transaction(BaseModel):
    """Input model for a single transaction to classify."""
    transaction_id: int = Field(description="Transaction ID")
    description: str = Field(description="Transaction description text")


class Transactions(BaseModel):
    """Model for all transactions to classify."""
    transactions: List[Transaction]


class TransactionClassification(BaseModel):
    """A single classified transaction result."""
    transaction_id: int = Field(description="Transaction ID")
    classification: str = Field(description="Classification of the transaction")
    is_tax_deductible: bool = Field(description="True if the transaction is tax deductible")
    deductible_portion: Decimal = Field(ge=0, le=1, decimal_places=2, description="Portion of the transaction amount that is tax deductible (0.0 to 1.0)")


class TransactionClassifications(BaseModel):
    """Container for a list of transaction classifications."""
    results: List[TransactionClassification]

@tool
async def classify_transactions(transactions_ref: str, config: RunnableConfig) -> dict:
    """
    Classifies a list of bank transactions into categories and tax deductibility using web context and an LLM.
    Transactions are read from memory using a provided reference ID.

    Args:
        transactions_ref (str): UUID key referencing a list of transaction dicts stored in memory.
            Each transaction must have: transaction_id, description.

    Returns:
        dict:
            {
                "classifications_ref": "<ref_id>",
                "fatal_err": False
            }
            or
            {
                "fatal_err": True,
                "err_details": str
            } on failure.
    """

    try:
        transactions_data = get_item(transactions_ref)
        transactions = transactions_data.get("transactions", [])

        log.info(f"[classify_transactions] classifying {len(transactions)} transactions...")

        await adispatch_custom_event("on_classify_transactions", {"friendly_msg": "Classifying transactions...\n"}, config=config)

        if not transactions:
            return {"classifications_ref": put_item({"results": []}), "fatal_err": False}

        llm = get_transaction_classifier_llm().with_structured_output(TransactionClassifications)
        search_client = get_search_client()

        batches = [transactions[i:i + BATCH_SIZE] for i in range(0, len(transactions), BATCH_SIZE)]
        all_results = []

        for batch in batches:
            async def fetch_context(tx: dict):
                web_context = ""
                
                if ENRICH_WITH_WEB_CONTEXT:
                    results = await search_client.ainvoke({"query": tx["description"]})
                    web_context = "\n".join(f"- {r.get('title', '')}: {r.get('content', '')}" for r in results.get("results", []))

                return {
                    "transaction_id": tx["transaction_id"],
                    "description": tx["description"],
                    "web_context": web_context
                }

            enriched = await asyncio.gather(*[fetch_context(tx) for tx in batch])
            prompt = PROMPT

            for entry in enriched:
                prompt += f"""
                    ---
                    Transaction id: {entry["transaction_id"]}
                    Description: {entry["description"]}
                    Web context: {entry["web_context"]}
                """

            result = await llm.ainvoke(prompt)

            batch_results = result.get("results") if isinstance(result, dict) else result.results
            
            if batch_results is None:
                batch_results = []
            
            all_results.extend(batch_results)

            log.info(f"[classify_transactions] Classified {len(batch_results)} transactions. Sleeping {DELAY_BETWEEN_BATCHES}s.")
            await asyncio.sleep(DELAY_BETWEEN_BATCHES)

        classifications_ref = put_item(TransactionClassifications(results=all_results).dict())
        return {"classifications_ref": classifications_ref, "fatal_err": False}

    except Exception as e:
        log.error(f"[classify_transactions] Failed to classify transactions: {e}")
        return {
            "fatal_err": True,
            "err_details": str(e)
        }