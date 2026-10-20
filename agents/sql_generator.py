from langchain_core.output_parsers import StrOutputParser
from langchain_core.prompts import ChatPromptTemplate

from agents import model
from prompts import general_sql_prompt

general_sql_model = model

prompt = ChatPromptTemplate(
    messages=[
        ("system", general_sql_prompt),
        ("user", "{question}")
    ]
)

general_sql_chain = prompt | model | StrOutputParser()

# sql = general_sql_chain.invoke({"question": "表中购买量最多的用户是谁"})
# print(sql)