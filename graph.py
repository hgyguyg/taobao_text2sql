from difflib import SequenceMatcher

from langgraph.graph import StateGraph

from agents import get_agent_1, get_agent_2, get_agent_3, get_agent_4
from prompts import NON_QUERY_SQL
from state import AgentState, Evidence
from utils.DuckDB import run_sql

def _normalize_question(q: str) -> str:
    """问题归一化，用于重复检测。"""
    return "".join(ch for ch in q.strip() if ch not in " \t\r\n，。？！,.?!；;")

def _lex_dup(a,b):
    return SequenceMatcher(None, a, b).ratio() >= 0.9

def node_generate(state:AgentState):
    """Agent 1：生成 SQL。"""

    question = state.current_question or state.original_question
    error_hint = state.get("error_msg","")
    history = state.get("evidence",[]) if state.get('requery_round',0) > 0 else None

    try:
        sql = get_agent_1().invoke(question, error_hint, history)
    except Exception as e:
        return {
            "sql": "",
            "error_msg": "",
            "final_answer": str(e),
            "status": "failed"
        }
    return {
        "sql": sql,
        "error_msg": ""
    }

def node_check(state: AgentState):
    """Agent 2: 代码层 + 语义层检验"""
    sql = state.get("sql")
    question = state.current_question or state.original_question

    if state.get('status') == "failed":
        return {}

    try:
        ok,msg = get_agent_2().invoke(sql,question)
    except Exception as e:
        return {
            "error_msg": f"校验器异常：{e}"
        }

    if ok:
        return {
            "error_msg": ""
        }
    return {
        "error_msg": msg,"retry_count": state.get('retry_count',0)+1
    }

def node_execute(state: AgentState):
    """执行 SQL 语句，同时保留 String（给agent） 和 Dataframe（用于后续画图）"""
    sql = state.get("sql","")
    question = state.get("current_question") or state.get("original_question")

    try:
        df = run_sql(sql)
        result_text = df.to_string()
        return {
            "query_result": result_text,
            "query_df": df,
            "evidence": [Evidence(
                sql=sql,
                question=question,
                result=result_text,
                failed=False
            )],
        }
    except Exception as e:
        failed_text = f"执行失败：{e}"
        return {
            "query_result": failed_text,
            "query_df": None,
            "evidence": Evidence(
                sql=sql,
                question=question,
                result=failed_text,
                failed=True
            )
        }

def node_analyze(state: AgentState):
    """Agent 3：分析 + 判断证据是否充分。"""
    evidence = state.get("evidence", [])
    overview = state.get("overview", "")
    original = state["original_question"]
    requery_round = state.get("requery_round", 0)
    max_requery = state.get("max_requery", 1)

    force_answer = requery_round >= max_requery

    if evidence and not evidence[-1].get("failed") and NON_QUERY_SQL.split("'")[1] in evidence[-1].get("sql",""):
        return {
            "sufficient": True,
            "analysis": str(evidence[-1].get("result") or "").strip() or NON_QUERY_SQL
        }

    try:
        out = get_agent_3().invoke(original,evidence, overview)
    except Exception as e:
        return {
            "sufficient": False,
            "analysis": f"分析阶段异常：{e}",
            "status": "degraded"
        }

    sufficient = out.get("sufficient",True)
    requery_question = str(out.get("requery_question") or "").strip()
    answer = str(out.get("answer") or "").strip()

    if force_answer and not sufficient:
        if answer.strip():
            return {
                "sufficient": True,
                "analysis": answer,
                "status": "degraded"
            }
        ok_evidence = [e for e in evidence if e.get("failed") is False]
        if not ok_evidence:
            return {
                "sufficient": True,
                "analysis": f"执行失败,未能获取到关于{original}的有用证据",
                "status": "degraded"
            }
        last = ok_evidence[-1]
        return {
            "sufficient": True,
            "analysis": f"关于{original}\n,查询结果：{str(last.get('result') or '').strip()}\n补充额度已经用尽，无法继续查询",
            "status": "degraded"
        }

    if not sufficient and requery_question:
        if _lex_dup(_normalize_question(requery_question), _normalize_question(original)):
            return {
                "sufficient": True,
                "analysis": answer or "补充查询与已执行查询重复，改用已有证据回答",
                "status": "degraded"
            }

    if sufficient or not requery_question:
        return {
            "sufficient": True,
            "analysis": answer or "无法获取充分证据",
        }

    return {
        "sufficient": False,
        "analysis": "",
        "requery_question": requery_question,
    }

def node_visualize(state: AgentState) -> dict:
    """Agent 4：决定图表规格并绘图。绘图失败不影响回答。"""
    query_result = state.get("query_result", "")
    analysis = state.get("analysis", "")

    try:
        spec = get_agent_4().decide(query_result=query_result, analysis=analysis)
    except Exception as exc:  # noqa: BLE001
        return {"chart_spec": {}, "chart_error": f"图表决策失败：{exc}"}

    try:
        path = get_agent_4().draw(spec, state.get("query_df"))
        return {"chart_spec": spec, "chart_path": path, "chart_error": ""}
    except Exception as exc:
        return {"chart_spec": spec, "chart_path": "", "chart_error": str(exc)}

def build_graph():
    graph = StateGraph(AgentState)

    graph.add_node("generate",node_generate)
    graph.add_node("check",node_check)
    graph.add_node("execute",node_execute)
    graph.add_node("analyze",node_analyze)
    graph.add_node("visualize",node_visualize)

    graph.set_entry_point("generate")

    graph.add_edge("generate","check")



