import operator
from typing import Annotated, Literal, TypedDict


class Evidence(TypedDict):
    """一轮取数产生的证据。"""

    question: str      # 本轮实际查询的问题
    sql: str           # 执行的 SQL
    result: str        # 结果文本（已截断）
    failed: bool       # 是否最终失败


class AgentState(TypedDict, total=False):
    # ---- 问题 ----
    original_question: str              # 用户原始问题，全程只读
    current_question: str               # 本轮要查询的问题

    # ---- 生成与校验 ----
    sql: str                            # 当前生成的 SQL
    error_msg: str                      # 校验失败信息（空字符串表示通过）
    retry_count: int                    # 当前问题的重试次数
    max_retries: int                    # 单问题最大重试次数

    # ---- 执行 ----
    query_result: str                   # 当前 SQL 的结果文本
    query_df: object                    # 当前 SQL 的结果 DataFrame（供绘图复用）

    # ---- 多轮取数 ----
    evidence: Annotated[list[Evidence], operator.add]
    requery_round: int                  # 已发起的补充查询轮数
    max_requery: int                    # 允许的最大补充查询轮数

    # ---- 分析 ----
    overview: str                       # 数据概览，一次性注入
    sufficient: bool                    # 证据是否充分
    requery_question: str               # 需要补充查询时的问题
    analysis: str                       # 完整分析回答

    # ---- 可视化 ----
    chart_spec: dict                    # 图表规格
    chart_path: str                     # 生成图片的路径
    chart_error: str                    # 绘图失败原因

    # ---- 终态 ----
    final_answer: str
    status: Literal["ok", "degraded", "failed"]


def initial_state(
    question: str,
    overview: str,
    max_retries: int = 3,
    max_requery: int = 1,
) -> AgentState:
    return AgentState(
        original_question=question,
        current_question=question,
        sql="",
        error_msg="",
        retry_count=0,
        max_retries=max_retries,
        query_result="",
        query_df=None,
        evidence=[],
        requery_round=0,
        max_requery=max_requery,
        overview=overview,
        sufficient=False,
        requery_question="",
        analysis="",
        chart_spec={},
        chart_path="",
        chart_error="",
        final_answer="",
        status="ok",
    )
