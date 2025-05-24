from langchain_core.tools import tool
from pydantic import BaseModel, Field
from typing import List
from dependencies import get_transaction_classifier_llm, get_search_client
import asyncio
from logger import log

BATCH_SIZE = 10

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


class TransactionClassifications(BaseModel):
    """Container for a list of transaction classifications."""
    results: List[TransactionClassification]

@tool
async def classify_transactions(input: Transactions) -> dict:
    """
    Classifies a list of bank transactions into categories using web context and an LLM.

    Args:
        input (Transactions): Contains a list of transactions with id and description.

    Returns:
        dict: {"classifications": ..., "fatal_err": False} on success,
              {"fatal_err": True} on failure.
    """
    log.info(f"[classify_transactions] classifying {len(input.transactions)} transactions...")

    try:
        llm = get_transaction_classifier_llm().with_structured_output(TransactionClassifications)
        search_client = get_search_client()

        batches = [input.transactions[i:i + BATCH_SIZE] for i in range(0, len(input.transactions), BATCH_SIZE)]
        all_results = []

        for batch in batches:
            async def fetch_context(tx: Transaction):
                results = await search_client.ainvoke({"query": tx.description})
                web_context = "\n".join(f"- {r.get('title', '')}: {r.get('content', '')}" for r in results.get("results", []))
                return {
                    "transaction_id": tx.transaction_id,
                    "description": tx.description,
                    "web_context": web_context
                }

            enriched = await asyncio.gather(*[fetch_context(tx) for tx in batch])

            prompt = """
                Classify each transaction into one of the following categories:
                - Groceries, Transport, Utilities, Insurance, Entertainment, Subscriptions, Healthcare, Dining, Vet, Unknown

                For each transaction, respond with: transaction_id and classification.
                """

            for entry in enriched:
                prompt += f"""
                    ---
                    Transaction id: {entry["transaction_id"]}
                    Description: {entry["description"]}
                    Web context: {entry["web_context"]}
                """

            result = await llm.ainvoke(prompt)
            

            if isinstance(result, dict):
                batch_results = result.get("results", [])
            else:
                batch_results = result.results
            
            all_results.extend(batch_results)

        return {
            "classifications": TransactionClassifications(results=all_results).dict(),
            "fatal_err": False
        }

    except Exception as e:
        log.error(f"Failed to classify transactions: {e}")
        return {"fatal_err": True}
