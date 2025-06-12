from dependencies import get_db_pool
import json
from decimal import Decimal
from psycopg.rows import dict_row
from logger import log
from typing import Optional
from langchain_core.tools import tool
from memory_store import put_item
from langchain_core.runnables import RunnableConfig
from langchain_core.callbacks.manager import adispatch_custom_event

def _to_float(value):
    return float(value) if isinstance(value, Decimal) else value

@tool
async def read_transactions(config: RunnableConfig, start_date: Optional[str] = None, end_date: Optional[str] = None) -> dict:
    """
    Reads transaction data for a given period from the transactions table and stores
    the result in memory. Returns a reference ID to retrieve it later.

    Args:
        start_date: Optional ISO date string (YYYY-MM-DD)
        end_date: Optional ISO date string (YYYY-MM-DD)

    Returns:
        dict:
            {
                "transactions_ref": "<ref_id>",
                "fatal_err": False
            }
            or
            {
                "fatal_err": True
            } on failure.
    """
    
    log.info(f"[read_transactions] Reading transactions from DB...")

    await adispatch_custom_event("on_read_transactions", {"friendly_msg": "Retrieving transactions...\n"}, config=config)

    try:
        pool = get_db_pool()
        async with pool.connection() as conn:
            async with conn.cursor(row_factory=dict_row) as cur:
                sql = """
                    SELECT 
                        id as transaction_id,
                        transaction_date,
                        transaction_details,
                        amount,
                        category,
                        account_id,
                        created_at
                    FROM transactions
                """
                params = []
                if start_date and end_date:
                    sql += " WHERE transaction_date BETWEEN %s AND %s"
                    params = [start_date, end_date]

                sql += " ORDER BY transaction_date ASC"

                await cur.execute(sql, params)
                rows = await cur.fetchall()

                if not rows:
                    ref_id = put_item({"transactions": []})
                    return {"transactions_ref": ref_id, "fatal_err": False}
                
                log.info(f"[read_transactions] read {len(rows)} transactions...")

                transactions = [
                    {
                        "transaction_id": row["transaction_id"],
                        "transaction_date": row["transaction_date"],
                        "description": row["transaction_details"],
                        "amount": _to_float(row["amount"]),
                        "category": row.get("category"),
                        "account_id": row["account_id"],
                        "created_at": row["created_at"].isoformat() if row["created_at"] else None
                    }
                    for row in rows
                ]

                ref_id = put_item({"transactions": transactions})
                return {"transactions_ref": ref_id, "fatal_err": False}

    except Exception as e:
        log.error(f"[read_transactions] Failed to read transactions: {e}")
        return {
            "fatal_err": True,
            "err_details": str(e)
        }