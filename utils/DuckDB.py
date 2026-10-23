import duckdb

from config import TABLE


def general_connection():
    return duckdb.connect()

def run_sql(sql:str,max_rows: int = 100):
    con = general_connection()
    df = con.execute(sql).fetch_df()

    if len(df) > max_rows:
        df = df.head(max_rows)

    return df

def db_check_sql(sql:str):
    con = general_connection()
    try:
        con.execute(f"EXPLAIN {sql}")
        return True,""
    except Exception as e:
        return False,f"{e}"

def scalar(sql: str):
    try:
        res = general_connection().execute(sql).fetchone()
        return res[0] if res else None
    except Exception as e:
        return None
