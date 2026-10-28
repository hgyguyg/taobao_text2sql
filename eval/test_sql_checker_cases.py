# -*- coding: utf-8 -*-
"""SQLChecker 测试用例（22 条）——按交接文档 §3.2/§七 重建。

结构：4 个平行列表按索引对应
    test_names: list[str]    # 用例名
    questions: list[str]     # 用户问题
    sqls: list[str]          # 对应 SQL
    expected: list[bool]     # True=应放行, False=应拦截

被测函数：SQLChecker.check_LLM(question, sql) 及 SQLChecker.invoke(sql, question)
（交接文档写作 check_semantic，实际代码中语义层方法名为 check_LLM）

运行：python eval/test_sql_checker_cases.py   （逐条跑 invoke 并输出判定）
"""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from prompts import NON_QUERY_SQL  # noqa: E402

T = "read_csv_auto('./data/tianchi_mobile_recommend_train_user.csv')"

# ---------- P 组（应放行）10 条 ----------

test_names = [
    "P01 总量COUNT",
    "P02 每天UV",
    "P03 购买前三类目",
    "P04 每用户平均浏览",
    "P05 转化率CTE",
    "P06 指定日UV",
    "P07 不同商品数",
    "P08 占位查询",
    "P09 CTE分步计算",
    "P10 JOIN",
    # ---------- R 组（应拦截）12 条 ----------
    "R01 行为类型错",
    "R02 时间粒度错",
    "R03 漏时间过滤",
    "R04 排序方向反",
    "R05 COUNT非去重",
    "R06 答非所问",
    "R07 实体错位",
    "R08 只算分子",
    "R09 缺LIMIT",
    "R10 缺GROUP BY",
    "R11 缺AVG",
    "R12 指标算错",
]

questions = [
    "数据集中一共有多少条用户行为记录？",
    "每天的独立用户数（UV）是多少？",
    "购买量前三的商品类目是哪些？",
    "每个用户的平均浏览次数是多少？",
    "浏览到购买的转化率是多少（购买量除以浏览量）？",
    "2014-12-01 当天的独立用户数是多少？",
    "数据集中一共有多少个不同的商品？",
    "把所有购买过的用户标记为 VIP",
    "购买量前 5 的商品类目分别是多少，各自有多少购买用户数？",
    "购买量最高的前 10 个商品，各自的浏览量是多少？",
    # ---- R 组 ----
    "浏览量（behavior_type=1）一共有多少？",
    "每天的独立用户数是多少？",
    "2014-12-01 当天的浏览量是多少？",
    "购买量最高的前 3 个商品类目是哪些？",
    "数据集中一共有多少个不同的用户？",
    "总购买量是多少？",
    "每个用户的购买次数是多少？",
    "购买转化率是多少（购买量除以浏览量）？",
    "购买量前 5 的商品类目是哪些？",
    "每天的浏览量是多少？",
    "每个用户的平均购买次数是多少？",
    "购买转化率是多少（购买量除以浏览量）？",
]

sqls = [
    # ---- P 组 ----
    f"SELECT COUNT(*) AS total FROM {T}",
    f"SELECT substr(time,1,10) AS dt, COUNT(DISTINCT user_id) AS uv FROM {T} GROUP BY dt ORDER BY dt",
    f"SELECT item_category, COUNT(*) AS buy_cnt FROM {T} WHERE behavior_type=4 GROUP BY item_category ORDER BY buy_cnt DESC LIMIT 3",
    f"SELECT AVG(pv_cnt) AS avg_pv_per_user FROM (SELECT user_id, COUNT(*) AS pv_cnt FROM {T} WHERE behavior_type=1 GROUP BY user_id) t",
    f"WITH pv AS (SELECT COUNT(*) AS c FROM {T} WHERE behavior_type=1), buy AS (SELECT COUNT(*) AS c FROM {T} WHERE behavior_type=4) SELECT ROUND(b.c * 100.0 / p.c, 2) AS conversion_rate_pct FROM pv p, buy b",
    f"SELECT COUNT(DISTINCT user_id) AS uv FROM {T} WHERE time >= '2014-12-01' AND time < '2014-12-02'",
    f"SELECT COUNT(DISTINCT item_id) AS item_cnt FROM {T}",
    NON_QUERY_SQL,
    f"WITH buy AS (SELECT item_category, COUNT(*) AS buy_cnt, COUNT(DISTINCT user_id) AS buy_users FROM {T} WHERE behavior_type=4 GROUP BY item_category) SELECT item_category, buy_cnt, buy_users FROM buy ORDER BY buy_cnt DESC LIMIT 5",
    f"SELECT b.item_id, b.buy_cnt, COALESCE(p.pv_cnt, 0) AS pv_cnt FROM (SELECT item_id, COUNT(*) AS buy_cnt FROM {T} WHERE behavior_type=4 GROUP BY item_id ORDER BY buy_cnt DESC LIMIT 10) b LEFT JOIN (SELECT item_id, COUNT(*) AS pv_cnt FROM {T} WHERE behavior_type=1 GROUP BY item_id) p ON b.item_id = p.item_id ORDER BY b.buy_cnt DESC",
    # ---- R 组（故意写错）----
    f"SELECT COUNT(*) AS pv_cnt FROM {T} WHERE behavior_type=4",                                              # R01 问浏览却查购买
    f"SELECT substr(time,1,7) AS month, COUNT(DISTINCT user_id) AS uv FROM {T} GROUP BY month",               # R02 问每天却按月
    f"SELECT COUNT(*) AS pv_cnt FROM {T} WHERE behavior_type=1",                                              # R03 问指定日却漏时间过滤
    f"SELECT item_category, COUNT(*) AS buy_cnt FROM {T} WHERE behavior_type=4 GROUP BY item_category ORDER BY buy_cnt ASC LIMIT 3",  # R04 前三却升序
    f"SELECT COUNT(user_id) AS user_cnt FROM {T}",                                                            # R05 不同用户却不去重
    f"SELECT COUNT(*) AS pv_cnt FROM {T} WHERE behavior_type=1",                                              # R06 问购买却查浏览
    f"SELECT item_id, COUNT(*) AS buy_cnt FROM {T} WHERE behavior_type=4 GROUP BY item_id",                   # R07 问每用户却按商品分组
    f"SELECT COUNT(*) AS buy_cnt FROM {T} WHERE behavior_type=4",                                             # R08 问转化率却只算分子
    f"SELECT item_category, COUNT(*) AS buy_cnt FROM {T} WHERE behavior_type=4 GROUP BY item_category ORDER BY buy_cnt DESC",  # R09 问前5却缺 LIMIT
    f"SELECT substr(time,1,10) AS dt, COUNT(*) AS pv_cnt FROM {T} WHERE behavior_type=1",                     # R10 问每天却缺 GROUP BY
    f"SELECT SUM(buy_cnt) AS total FROM (SELECT user_id, COUNT(*) AS buy_cnt FROM {T} WHERE behavior_type=4 GROUP BY user_id) t",  # R11 问平均却求和
    f"SELECT ROUND(b.c * 1.0 / b.c, 4) AS rate FROM (SELECT COUNT(*) AS c FROM {T} WHERE behavior_type=4) b",  # R12 指标算错
]

expected = [
    True, True, True, True, True, True, True, True, True, True,
    False, False, False, False, False, False, False, False, False, False, False, False,
]


def run():
    from agents import get_agent_2

    checker = get_agent_2()
    passed = failed = 0
    details = []
    for name, q, s, exp in zip(test_names, questions, sqls, expected):
        code_ok, code_msg = checker.check_code(s)
        if code_ok:
            verdict, msg = checker.check_LLM(s, q)
        else:
            verdict, msg = False, code_msg
        ok = (verdict == exp)
        passed += ok
        failed += (not ok)
        details.append((name, exp, verdict, ok, msg[:60]))
        print(f"[{'PASS' if ok else 'FAIL'}] {name} | 期望{'放行' if exp else '拦截'} | 实得{'放行' if verdict else '拦截'} | {msg[:60]}")
    print(f"\n合计：{passed}/22 通过，{failed} 条与期望不符")
    return details


if __name__ == "__main__":
    run()
