from dependencies import get_db_connection
from langchain_core.tools import tool
import json

@tool
def write_statement_to_db(json_str: str) -> dict:
    """
    Writes structured bank statement data and transactions into database.
    
    Args:
        json_str: A valid JSON string containing parsed bank statement data
    
    Returns:
        dict: Update to the AgentState. Sets 'fatal_err' = True if anything fails.
    """

    print(f"[write_statement_to_db] saving to database...")

    try:
        parsed_data = json.loads(json_str)
        conn = get_db_connection()
        
        with conn:
            with conn.cursor() as cur:
                try:
                    cur.execute("""
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
                        RETURNING 
                            id;
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
                    
                    statement_id = cur.fetchone()[0]

                    for tx in parsed_data["transactions"]:
                        cur.execute("""
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
                    conn.commit()
                    return {"fatal_err": False}
                
                except Exception as e:
                    print(f"--- [ERROR] Database operation failed: {e}")
                    conn.rollback()
                    return {"fatal_err": True}
    
    except Exception as e:
        print(f"--- [ERROR] Unknown error: {e}")
        return {"fatal_err": True}