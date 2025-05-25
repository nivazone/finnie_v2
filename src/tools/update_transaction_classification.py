from dependencies import get_db_pool
from langchain_core.tools import tool
from logger import log
from memory_store import get_item

@tool
async def update_transaction_classification(classifications_ref: str) -> dict:
    """
    Updates multiple transaction categories in the database using a memory store reference
    that points to a list of classification results.

    Args:
        classifications_ref (str): Ref ID pointing to {"results": [ {transaction_id, classification}, ... ] }

    Returns:
        dict:
            {"fatal_err": False} on success,
            {"fatal_err": True} on failure
    """
    try:
        data = get_item(classifications_ref)
        results = data.get("results", [])

        log.info(f"[update_transaction_classification] results: {results}")

        if not results:
            log.warning("[update_transaction_classification] no classifications to update.")
            return {"fatal_err": False}

        pool = get_db_pool()
        async with pool.connection() as conn:
            async with conn.cursor() as cur:
                for i, item in enumerate(results):
                    try:
                        tx_id = item["transaction_id"]
                        category = item["classification"]

                        await cur.execute(
                            """
                            UPDATE transactions
                            SET category = %s
                            WHERE id = %s;
                            """,
                            (category, tx_id)
                        )
                    except Exception as e:
                        log.error(f"[update_transaction_classification] failed on item {i}: {e}")
                        await conn.rollback()
                        return {"fatal_err": True}

                await conn.commit()
                return {"fatal_err": False}

    except Exception as e:
        log.error(f"[update_transaction_classification] unknown error: {e}")
        return {"fatal_err": True}
