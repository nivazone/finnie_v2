from dependencies import get_db_pool
from langchain_core.tools import tool

@tool
async def update_transaction_classification(transaction_id: int, category: str) -> dict:
    """
    Updates the category of a transaction for a given transaction id.

    Args:
        transaction_id: Id of the transaction to be updated
        category: Category of the transaction in plain text

    Returns:
        dict: {"fatal_err": False} on success, {"fatal_err": True} on failure
    """

    print(f"[update_transaction_classification] setting category to '{category}'")

    try:
        pool = get_db_pool()
        async with pool.connection() as conn:
            async with conn.cursor() as cur:
                await cur.execute("""
                    UPDATE transactions
                    SET category = %s
                    WHERE id = %s;
                """, (category, transaction_id))

                # Commit is still required for write ops in psycopg3
                await conn.commit()

        return {"fatal_err": False}

    except Exception as e:
        print(f"[ERROR] Failed to update transaction category: {e}")
        return {"fatal_err": True}
