from langchain_core.tools import tool
from pydantic import BaseModel, Field
from typing import List
from dependencies import get_transaction_classifier_llm, get_search_client

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


# ========== Tool Function ==========

@tool
def classify_transactions(input: Transactions) -> dict:
    """
    Classifies a list of bank transactions into categories using web context and an LLM.

    Args:
        input (Transactions): Contains a list of transactions with id and description.

    Returns:
        dict: {"parsed_text": ..., "fatal_err": False} on success,
              {"fatal_err": True} on failure.
    """
    print(f"[classify_transactions] classifying {len(input.transactions)} transactions...")

    try:
        llm = get_transaction_classifier_llm().with_structured_output(TransactionClassifications)
        search_client = get_search_client()

        # Step 1: Perform all web searches
        enriched_inputs = []

        for tx in input.transactions:
            results = search_client.invoke({"query": tx.description}).get("results", [])
            web_context = "\n".join(f"- {r.get('title', '')}: {r.get('content', '')}" for r in results)
            enriched_inputs.append({
                "transaction_id": tx.transaction_id,
                "description": tx.description,
                "web_context": web_context
            })

        # Step 2: Build LLM prompt
        prompt = """
            Classify each transaction into one of the following categories:
            - Groceries, Transport, Utilities, Insurance, Entertainment, Subscriptions, Healthcare, Dining, Vet, Unknown

            For each transaction, respond with: transaction_id and classification.
            """

        for entry in enriched_inputs:
            prompt += f"""
                ---
                Transaction id: {entry["transaction_id"]}
                Description: {entry["description"]}
                Web context: {entry["web_context"]}
                """

        # Step 3: Invoke LLM and return response
        response = llm.invoke(prompt)

        return {
            "parsed_text": response.dict(),
            "fatal_err": False
        }

    except Exception as e:
        print(f"[ERROR] Failed to classify transactions: {e}")
        return {"fatal_err": True}
