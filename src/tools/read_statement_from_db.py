from dependencies import get_db_connection
import json
from decimal import Decimal
from psycopg.rows import dict_row

def _to_float(value):
    return float(value) if isinstance(value, Decimal) else value

def read_statement_from_db() -> dict:
    """
    Reads statement from database

    Returns:
        dict: {"statement_json": "...", "fatal_err": False} or {"fatal_err": True}
    """

    print(f"[read_statement_from_db] reading from database...")

    try:
        conn = get_db_connection()

        with conn:
            with conn.cursor(row_factory=dict_row) as cur:
                # Get statement and transactions in a single query
                cur.execute("""
                    SELECT 
                        s.id as statement_id,
                        s.account_holder,
                        s.account_name,
                        s.start_date,
                        s.end_date,
                        s.opening_balance,
                        s.closing_balance,
                        s.credit_limit,
                        s.interest_charged,
                        t.id as transaction_id,
                        t.transaction_date,
                        t.transaction_details,
                        t.amount
                    FROM statements s
                    LEFT JOIN transactions t ON t.statement_id = s.id
                    WHERE s.id = (
                        SELECT id
                        FROM statements 
                        ORDER BY end_date DESC 
                        LIMIT 1
                    )
                """)
                
                rows = cur.fetchall()

                if not rows:
                    return json.dumps({})

                # First row contains statement data
                statement = rows[0]
                
                # Format dates as strings
                statement_data = {
                    "bank_statement": {
                        "statement_id": statement["statement_id"],
                        "account_name": statement["account_name"],
                        "opening_balance": _to_float(statement["opening_balance"]),
                        "closing_balance": _to_float(statement["closing_balance"]),
                        "start_date": statement["start_date"],
                        "end_date": statement["end_date"],
                        "transactions": [
                            {
                                "transaction_id": row["transaction_id"],
                                "transaction_date": row["transaction_date"],
                                "description": row["transaction_details"],
                                "amount": _to_float(row["amount"])
                            }
                            for row in rows
                        ]
                    }
                }

                return {
                    "statement_json": json.dumps(statement_data),
                }

    except Exception as e:
        print(f"[ERROR] Failed to read from database: {str(e)}")
        return {
            "statement_json": json.dumps({}),
            "fatal_err": True
        }