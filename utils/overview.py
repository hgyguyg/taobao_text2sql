from config import TABLE
from utils.DuckDB import scalar, run_sql

OVERVIEW_CACHE = None

def _fmt(value, default: str = "未知") -> str:
    if value is None:
        return default
    if isinstance(value, float):
        return f"{value:,.2f}"
    if isinstance(value, int):
        return f"{value:,}"      # 将整数按照千分位分隔（例：123,612,123）
    return str(value)

def build_overview():
    """构建数据概览文本。结果缓存在进程内，避免每次提问重算。"""
    global OVERVIEW_CACHE
    if OVERVIEW_CACHE is not None:
        return OVERVIEW_CACHE
    overview = []

    # 数据规模 （用户数量，种类数量，商品数量，开始时间，结束时间，总共的记录数量）
    row_cnt = scalar(f"select count(*) from {TABLE}")
    user_cnt = scalar(f"select count(distinct user_id) from {TABLE}")
    item_cnt = scalar(f"select count(distinct item_id) from {TABLE}")
    cat_cnt = scalar(f"select count(distinct item_category) from {TABLE}")
    start_time = scalar(f"select min(time) from {TABLE}")
    end_time = scalar(f"select max(time) from {TABLE}")

    overview.append("【数据规模】")
    overview.append(f" - 总行数：{_fmt(row_cnt)}")
    overview.append(f" - 用户数量：{_fmt(user_cnt)}")
    overview.append(f" - 商品数量：{_fmt(item_cnt)}")
    overview.append(f" - 类别数量：{_fmt(cat_cnt)}")
    overview.append(f" - 时间范围：{_fmt(start_time)} 至 {_fmt(end_time)}")

    # 各行为类型总量与占比
    try:
        df = run_sql(
            f"""select behavior_type,
                        count(*) as cnt,
                        round(count(*) * 100.0 / {int(row_cnt)}, 2) as pct
                from {TABLE}
                group by behavior_type
                """
        )
        overview.append("")
        overview.append("【各行为类型总量与占比】")
        overview.append("1=pv(浏览) / 2=cart(加购) / 3=fav(收藏) / 4=buy(购买)")
        overview.append("cnt 表示该行为类型的数量，pct 表示该行为类型的占比")
        overview.append(df.to_string())

    except Exception as e:
        print(f"行为类型统计失败：{e}")

    # 支付用户数
    try:
        buyer_cnt = scalar(f"select count(distinct user_id) from {TABLE} where behavior_type = 4")
        avg_buy_per_buyer = scalar(f"select round(count(*) / count(distinct user_id),0) from {TABLE} where behavior_type = 4")
        overview.append("")
        overview.append("【支付用户人数统计】")
        overview.append(f" - 支付用户数：{_fmt(buyer_cnt)}")
        overview.append(f" - 每支付用户平均购买数：{_fmt(avg_buy_per_buyer)}")

    except Exception as e:
        print(f"支付用户数统计失败：{e}")

    # 每日用户活跃数
    try:
        df = run_sql(
            f"""select substr(time,1,10) as dt,
                        count(distinct user_id) uv,
                        count(*) pv
                from {TABLE}
                group by dt
                """
        )
        overview.append("")
        overview.append("【每日用户活跃数】")
        overview.append(f" - 日均活跃人数：{_fmt(df['uv'].mean())}，最低：{_fmt(df['uv'].min())}，最高：{_fmt(df['uv'].max())}")
        overview.append(f" - 日均行为条数：{_fmt(df['pv'].mean())}，最低：{_fmt(df['pv'].min())}，最高：{_fmt(df['pv'].max())}")

    except Exception as e:
        print(f"每日用户活跃数统计失败：{e}")

    overview.append("")
    overview.append("说明：以上为全量数据背景。分析具体查询结果时，应与之对比来判断")
    overview.append("该数值处于什么水位（偏高/偏低/异常），而不是孤立地复述数字。")

    OVERVIEW_CACHE = ('\n'.join(overview))

    return OVERVIEW_CACHE