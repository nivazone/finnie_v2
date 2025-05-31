from dependencies import get_db_pool
from langchain_core.tools import tool
import json
from logger import log
from psycopg import AsyncConnection, AsyncCursor
from memory_store import get_item

async def _write_statement(json_str: str, conn: AsyncConnection, cur: AsyncCursor) -> None:
    """
    Writes structured bank statement into database.
    
    Args:
        json_str: A valid JSON string containing parsed bank statement data
    
    Raises exception on failure.
    """

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
async def write_all_statements(parsed_refs: list[str]) -> dict:
    """
    Writes a batch of structured bank statement data to the database using references
    to parsed statement objects.

    Each parsed_ref should point to a dictionary like:
        {"parsed_text": <BankStatement schema-compatible dict>}

    Args:
        parsed_refs (List[str]): List of reference keys in memory store

    Returns:
        dict:
            {
                "fatal_err": False
            }
            or
            {
                "fatal_err": True
            } if any statement fails.
    """

    log.info(f"[write_all_statements] saving {len(parsed_refs)} statements to database...")

    try:
        pool = get_db_pool()

        async with pool.connection() as conn:
            async with conn.cursor() as cur:
                for i, ref_id in enumerate(parsed_refs):
                    log.info(f"[write_all_statements] inserting statement {i + 1} from ref {ref_id}...")

                    try:
                        entry = get_item(ref_id)
                        json_str = json.dumps(entry["parsed_text"].dict())

                        await _write_statement(json_str, conn, cur)

                    except Exception as e:
                        log.error(f"[write_all_statements] failed on index {i} (ref {ref_id}): {e}")
                        await conn.rollback()
                        return {"fatal_err": True}

                await conn.commit()
                return {"fatal_err": False}

    except Exception as e:
        log.error(f"[write_all_statements] unknown failure: {e}")
        return {"fatal_err": True}