from langchain_core.output_parsers import StrOutputParser
from langchain_core.prompts import ChatPromptTemplate
from pydantic import BaseModel,Field

from config import model
from prompts import ANALYST_PROMPT


class AnalystResult(BaseModel):
    sufficient: bool
    requery_question: str = Field(default="")
    answer: str = Field(default="")

class Analyst():
    def __init__(self):
        self.chain = (ChatPromptTemplate(messages=[("system",ANALYST_PROMPT)]) |
                      model.with_structured_output(AnalystResult,include_raw=True)
)
    def invoke(self,original_question,evidence,overview):
        out = self.chain.invoke({
            "original_question": original_question,
            "evidence": evidence,
            "overview": overview
        })
        parsed,raw = out["parsed"],out["raw"]
        if parsed is None:
            return {
                "sufficient": True,
                "requery_question": "",
                "answer": raw.content if raw is not None else ""
            }
        return {
            "sufficient": parsed.sufficient,
            "requery_question": parsed.requery_question,
            "answer": parsed.answer
        }

agent_3 = None

def get_agent_3():
    global agent_3
    if agent_3 is None:
        agent_3 = Analyst()
    return agent_3