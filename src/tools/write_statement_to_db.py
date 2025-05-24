from dependencies import get_db_pool
from langchain_core.tools import tool
import json
from logger import log

@tool
async def write_statement_to_db(json_str: str) -> dict:
    """
    Writes structured bank statement data and transactions into database.
    
    Args:
        json_str: A valid JSON string containing parsed bank statement data
    
    Returns:
        dict: Update to the AgentState. Sets 'fatal_err' = True if anything fails.
    """

    log.info(f"[write_statement_to_db] saving to database...")

    try:
        parsed_data = json.loads(json_str)
        pool = get_db_pool()

        async with pool.connection() as conn:
            async with conn.cursor() as cur:
                try:
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

                    await conn.commit()
                    return {"fatal_err": False}

                except Exception as e:
                    log.error(f"Database operation failed: {e}")
                    await conn.rollback()
                    return {"fatal_err": True}

    except Exception as e:
        log.error(f"Unknown error: {e}, json_str={json_str}")
        return {"fatal_err": True}