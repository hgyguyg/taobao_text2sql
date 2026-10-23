from config import model

from langchain_core.output_parsers import StrOutputParser
from langchain_core.prompts import ChatPromptTemplate

from prompts import SQL_CHECKER_PROMPT
from utils.check import check_sql

prompt = ChatPromptTemplate(
    messages=[
        ("system", SQL_CHECKER_PROMPT)
    ]
)

sql_checker = prompt | model | StrOutputParser()

class SQLChecker:
    def __init__(self):
        self.chain = sql_checker

    def check_code(self, sql: str):
        """代码检验"""
        return check_sql(sql)

    def check_LLM(self,sql: str,question: str):
        """LLM 语义检验"""
        res = self.chain.invoke({"question": question,"sql": sql})
        res = res.replace("*","").replace(" ","").strip()

        if res.startswith("通过"):
            return True,""
        else:
            return False,res.split("不通过")[1].strip() or "语义不符"

    def invoke(self,sql: str,question: str):
        ok,msg = self.check_code((sql))

        if not ok:
            return False,msg

        return self.check_LLM(sql,question)

agent_2 = None

def get_agent_2():
    global agent_2
    if agent_2 is None:
        agent_2 = SQLChecker()
    return agent_2