from dependencies import get_db_pool
from langchain_core.tools import tool
import json
from logger import log
from psycopg import AsyncConnection, AsyncCursor


async def _write_statement(json_str: str, conn: AsyncConnection, cur: AsyncCursor) -> None:
    """
    Writes structured bank statement into database.
    
    Args:
        json_str: A valid JSON string containing parsed bank statement data
    
    Raises exception on failure.
    """

    log.info(f"[_write_statement] saving to database...")

    parsed_data = json.loads(json_str)

    await cur.execute("""
        INSERT INTO statements 
            (
                account_holder, 
                account_name, 
                start_date, 
                end_date, 
                opening_balance, 
                closing_balance, 
                credit_limit, 
                interest_charged
            )
        VALUES 
            (%s, %s, %s, %s, %s, %s, %s, %s)
        RETURNING id;
    """, (
        parsed_data["account_holder"],
        parsed_data["account_name"],
        parsed_data["start_date"],
        parsed_data["end_date"],
        parsed_data["opening_balance"],
        parsed_data["closing_balance"],
        parsed_data["credit_limit"],
        parsed_data["interest_charged"]
    ))

    row = await cur.fetchone()

    if row is None:
        raise Exception("Failed to insert statement: no ID returned from database.")

    statement_id = row[0]

    for tx in parsed_data["transactions"]:
        await cur.execute("""
            INSERT INTO transactions 
                (
                    statement_id, 
                    transaction_date, 
                    transaction_details, 
                    amount
                )
            VALUES 
                (%s, %s, %s, %s);
        """, (
            statement_id,
            tx['transaction_date'],
            tx['transaction_details'],
            tx['amount']
        ))

@tool
async def write_all_statements(json_strs: list[str]) -> dict:
    """
    Writes a batch of structured bank statement data to the database.

    Args:
        json_strs: List of valid JSON strings representing parsed bank statements.

    Returns:
        dict: Update to the AgentState. Sets 'fatal_err' = True if anything fails.
    """

    log.info(f"[write_all_statements] saving {len(json_strs)} statements to database...")

    try:
        pool = get_db_pool()

        async with pool.connection() as conn:
            async with conn.cursor() as cur:
                for i, json_str in enumerate(json_strs):
                    log.info(f"[write_all_statements] Inserting statement {i + 1}...")
                    try:
                        await _write_statement(json_str, conn, cur)
                    except Exception as e:
                        log.error(f"--- [write_all_statements] Failed on index {i}: {e}")
                        await conn.rollback()
                        return {"fatal_err": True}

                await conn.commit()
                return {"fatal_err": False}

    except Exception as e:
        log.error(f"[write_all_statements] DB connection error or unknown failure: {e}")
        return {"fatal_err": True}