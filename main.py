import time

from state import initial_state, AgentState
from utils.overview import build_overview
from utils.graph import build_graph

def _print_result(state: dict, elapsed: float) -> None:
    print("\n" + "=" * 70)
    print("最终回答")
    print("=" * 70)
    print(state.get("final_answer") or "（无输出）")

    print("\n" + "-" * 70)
    print("执行轨迹")
    print("-" * 70)
    for idx, ev in enumerate(state.get("evidence", []), start=1):
        flag = "失败" if ev.get("failed") else "成功"
        print(f"[证据 {idx}] {flag}")
        print(f"  问题：{ev.get('question', '')}")
        print(f"  SQL：{ev.get('sql', '')}")
        result_preview = (ev.get("result") or "").replace("\n", " / ")[:200]
        print(f"  结果：{result_preview}")

    print(f"\n重试次数：{state.get('retry_count', 0)}")
    print(f"补充查询轮数：{state.get('requery_round', 0)}")
    print(f"状态：{state.get('status', 'ok')}")
    print(f"耗时：{elapsed:.1f}s")
    print("=" * 70)

def ask(app, question: str) -> dict:
    overview = build_overview()
    init = initial_state(question, overview, max_retries=3, max_requery=1)

    start = time.time()
    final = app.invoke(init)
    elapsed = time.time() - start

    _print_result(final, elapsed)
    print(f"chart_path: {final.get('chart_path')}")
    print(f"chart_error: {final.get('chart_error')}")
    print(f"chart_spec: {final.get('chart_spec')}")
    return final


def main():
    
    print("正在加载数据并构建数据概览...（首次启动较慢）")
    build_overview()
    app = build_graph()
    
    print("\n淘宝用户行为问数 Agent（输入 q 退出）")
    
    while True:
        try:
            question = input("\n你的问题：").strip()
        except (EOFError, KeyboardInterrupt):
            print("\n再见。")
            break
        if not question:
            continue
        if question.lower() in {"q", "quit", "exit"}:
            print("再见。")
            break
        ask(app, question)



if __name__ == "__main__":
    main()