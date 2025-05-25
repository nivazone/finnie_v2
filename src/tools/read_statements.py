from dependencies import get_db_pool
import json
from decimal import Decimal
from psycopg.rows import dict_row
from logger import log
from typing import Optional
from langchain_core.tools import tool

def _to_float(value):
    return float(value) if isinstance(value, Decimal) else value

@tool
async def read_transactions(start_date: Optional[str] = None, end_date: Optional[str] = None) -> dict:
    """
    Reads transaction data for a given period from the transactions table.

    Args:
        start_date: Optional ISO date string (YYYY-MM-DD)
        end_date: Optional ISO date string (YYYY-MM-DD)

    Returns:
        dict: {"transactions_json": "...", "fatal_err": False} or {"fatal_err": True}
    """

    log.info(f"[read_transactions] reading transactions from DB...")

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
                        statement_id,
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
                    return {
                        "transactions_json": json.dumps({"transactions": []}),
                        "fatal_err": False
                    }
                
                log.info(f"[read_transactions] read {len(rows)} transactions...")

                transactions = [
                    {
                        "transaction_id": row["transaction_id"],
                        "transaction_date": row["transaction_date"],
                        "description": row["transaction_details"],
                        "amount": _to_float(row["amount"]),
                        "category": row.get("category"),
                        "statement_id": row["statement_id"],
                        "created_at": row["created_at"].isoformat() if row["created_at"] else None
                    }
                    for row in rows
                ]

                return {
                    "transactions_json": json.dumps({"transactions": transactions}),
                    "fatal_err": False
                }

    except Exception as e:
        log.error(f"[read_transactions] failed to read transactions: {e}")
        return {
            "transactions_json": json.dumps({}),
            "fatal_err": True
        }