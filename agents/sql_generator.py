import re

from langchain_core.output_parsers import StrOutputParser
from langchain_core.prompts import ChatPromptTemplate

from config import model
from prompts import SQL_GENERATOR_PROMPT,NON_QUERY_SQL

general_sql_model = model

prompt = ChatPromptTemplate(
    messages=[
        ("system", SQL_GENERATOR_PROMPT),
    ]
)

general_sql_chain = prompt | model | StrOutputParser()

def extract_sql(raw: str):
    """从 agent 的回答中提取 SQL"""
    text = raw.strip()

    # 找到文本中第一个 select 或者 with
    match = re.search(r"\b(SELECT|WITH)\b", text, re.IGNORECASE)
    if match is None:
        return NON_QUERY_SQL
    text = text[match.start():]
    # 找到后再去除第一个分号后面的文本
    text = text.split(";")[0].strip()

    if not re.search(r"\b(SELECT|WITH)\b", text, re.IGNORECASE):
        return NON_QUERY_SQL

    return text


class SQLGenerator:
    def __init__(self):
        self.chain = general_sql_chain

    def invoke(self, question, error_hint, history):
        error_block = ""
        if error_hint:
            error_block += "\n上一次生成的 SQL 语句未通过校验\n"
            error_block += f"错误原因：{error_hint}"
            error_block += f"请根据错误原因重新生成，不能犯同样的错误\n"

        history_block = "\n"
        if history:
            for id,evidence in enumerate(history,start=1):
                history_block += f"已有结果：{id}\n"
                history_block += f"查询问题：{evidence.get('question', '')}\n"
                if evidence.get("failed"):
                    history_block += "执行失败"
                else:
                    result = str(evidence.get("result", ""))
                    if len(result) > 1000:
                        result = result[:1000]
                        history_block += result
                        history_block += "\n\n查询结果过长，已经进行截断"
                    else:
                        history_block += result
                    history_block += ""
            history_block += "1. 补充查询是在已有结果基础上做对比或取比例，\n"
            history_block += "**不要重复查询已经拿到的同一批数据**\n"
            history_block +=  "2. 分清「分子范围」和「分母范围」：\n"
            history_block += "占比类查询的分母必须是**全部数据**的汇总值（如全部类目的总浏览量），\n"
            history_block += "不能只用原问题涉及的那几行做分母；\n"
            history_block += "而最终 SELECT 输出的行数要控制在原问题的范围（原问题问前5个，就只输出这5行）\n"
            history_block += "3. 输出行数要少且可读：明细查询必须加 LIMIT，\n"
            history_block += "不要把全部类目/全部商品的明细都返回回来\n"

        raw = self.chain.invoke(
            {"question": question, "error_block": error_block, "history_block": history_block}
        )

        return extract_sql(raw)

agent_1 = None

def get_agent_1():
    global agent_1
    if agent_1 is None:
        agent_1 = SQLGenerator()
    return agent_1
