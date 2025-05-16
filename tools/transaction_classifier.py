from shared.dependencies import get_llm, get_db_connection
from langchain_core.messages import HumanMessage
from datetime import datetime
from shared.agent_state import AgentState
import json

def transaction_classifier(state: AgentState) -> AgentState:
    """
    Classifies individual transactions into spending categories and updates the database.
    This tool queries the transactions table for a specific bank statement, 
    uses an LLM to assign each transaction to a category, and updates 
    the `transactions.category` field accordingly.

    The LLM is instructed to return a structured JSON object for each classification, 
    including:
        - category: The assigned spending category (must be one of allowed categories)
        - search_results: Any merchant lookup results (or blank if not applicable)
        - reason: Explanation of why the category was assigned

    Args:
        state (AgentState): The LangGraph state

    Returns:
        AgentState: The unchanged state after transaction classification completes.

    Example of expected LLM output per transaction:
        {
            "category": "Groceries",
            "search_results": "Coles Supermarket Australia",
            "reason": "Merchant name matches known grocery retailer"
        }

    Notes:
        This is typically called downstream of `postgres_writer`.
        It is a fully autonomous agent step within the LangGraph pipeline.
    """

    print("[transaction_classifier] classifying transactions...")

    allowed_categories = [
        "Groceries", 
        "Transport", 
        "Utilities", 
        "Insurance",
        "Entertainment", 
        "Subscriptions",
        "Healthcare",
        "Dining",
        "Vet",
        "Unknown"
    ]
    categories_str = ", ".join(allowed_categories)

    llm = get_llm()
    conn = get_db_connection()

    prompt_template = f"""
        You are a financial transaction classification agent.
        If you do not have enough data to confidently decide what the category is, do a web search to gather additional data.
        You must classify each transaction into ONE of the following categories:
        {categories_str}

        Instructions:
            - Your JSON must have these fields:
                - "category": the final classification (must match one of the categories list)
                - "search_results": any information found about the merchant (or leave as "" if not applicable)
                - "reason": a short explanation of why you classified this way
            - Important:
                - Return a valid **raw JSON object**, not inside a markdown block.
                - Do not format the output as a code block. Do not use ```json or ``` markers.
                - Only output the pure JSON object without any extra text.

        Example:
        {{
            "category": "Groceries",
            "search_results": "Coles Supermarket Australia",
            "reason": "Merchant name matches known grocery retailer"
        }}

        Here is the transaction you must classify:
    """

    with conn:
        with conn.cursor() as cur:
            cur.execute("""SELECT id FROM statements""")
            result = cur.fetchone()

            if not result:
                raise Exception(f"Statements not found")

            statement_id = result[0]

            cur.execute("""
                SELECT id, transaction_details FROM transactions
                WHERE statement_id = %s
            """, (statement_id,))
            transactions = cur.fetchall()

            for tx_id, details in transactions:
                full_prompt = f"{prompt_template}\n\nTransaction: \"{details}\""
                response = llm.invoke([HumanMessage(content=full_prompt)])

                try:
                    result_json = json.loads(response.content.strip())
                    category = result_json["category"]
                    search_results = result_json["search_results"]
                    reason = result_json["reason"]

                    print(f"[LLM Classification] {category=}, {search_results=}, {reason=}")

                except Exception as e:
                    print("[ERROR] Failed to parse LLM response as JSON:", e)
                    print("[Full prompt]", full_prompt)
                    print("[Response content]:", response)
                    category = "Unknown"

                cur.execute("""
                    UPDATE transactions 
                    SET category = %s 
                    WHERE id = %s
                """, (category.strip(), tx_id))

        conn.commit()

    return state
