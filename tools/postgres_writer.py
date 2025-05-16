from langchain.tools import tool
from shared.dependencies import get_db_connection
from datetime import datetime
from shared.agent_state import AgentState

@tool
def postgres_writer(state: AgentState) -> AgentState:
    """
    Writes structured bank statement data and transactions into a PostgreSQL database.

    This tool inserts account metadata and associated transaction records into 
    relational database tables (`statements`, `transactions`). It expects data 
    to be pre-validated and structured by an upstream document parsing agent.

    The function performs two main actions:
        1. Inserts account-level statement metadata into the `statements` table.
        2. Inserts all associated transactions into the `transactions` table 
           linked by a foreign key (`statement_id`).

    Args:
        state (AgentState): Graph state containing 'parsed_data'.
            Expected keys:
                - account_holder (str)
                - account_name (str)
                - start (str): Statement start date in DD/MM/YY format.
                - end (str): Statement end date in DD/MM/YY format.
                - opening_balance (float)
                - closing_balance (float)
                - credit_limit (float)
                - interest_charged (float)
                - transactions (list of dicts):
                    Each transaction dict must contain:
                        - date (str, optional): Date of transaction (e.g., "Apr 5").
                        - transaction_details (str): Description or merchant.
                        - amount (float): Transaction amount.

    Returns:
        AgentState: State (unchanged).
    """

    print(f"[postgres_writer] writing to database...")

    parsed_data = state["parsed_data"]
    conn = get_db_connection()
    
    with conn:
        with conn.cursor() as cur:
            cur.execute("""
                INSERT INTO statements (account_holder, account_name, start_date, end_date, opening_balance, closing_balance, credit_limit, interest_charged)
                VALUES (%s, %s, %s, %s, %s, %s, %s, %s) RETURNING id;
                """, (
                    parsed_data["account_holder"],
                    parsed_data["account_name"],
                    datetime.strptime(parsed_data["start"], "%d/%m/%y"),
                    datetime.strptime(parsed_data["end"], "%d/%m/%y"),
                    parsed_data["opening_balance"],
                    parsed_data["closing_balance"],
                    parsed_data["credit_limit"],
                    parsed_data["interest_charged"]
                ))
            statement_id = cur.fetchone()[0]
            for tx in parsed_data["transactions"]:
                cur.execute("""
                    INSERT INTO transactions (statement_id, transaction_date, transaction_details, amount)
                    VALUES (%s, %s, %s, %s);
                    """, (
                        statement_id,
                        datetime.strptime(f"{tx['date']} {parsed_data['start'].split('/')[-1]}", "%b %d %y") if tx.get('date') else None,
                        tx['transaction_details'],
                        tx['amount']
                    ))
        conn.commit()
    
    return f"Statement written with ID {statement_id}"
