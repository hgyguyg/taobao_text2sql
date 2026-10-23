import os

import duckdb
from dotenv import load_dotenv

load_dotenv()

path = os.getenv("DATA_PATH")

def general_connection():
    return duckdb.connect()

def run_sql(sql:str,max_rows: int = 100):
    con = general_connection()
    df = con.execute(sql).fetch_df()

    if len(df) > max_rows:
        df = df.head(max_rows)

    return df.to_string()

def db_check_sql(sql:str):
    con = general_connection()
    try:
        con.execute(f"EXPLAIN {sql}")
        return True,""
    except Exception as e:
        return False,f"{e}"