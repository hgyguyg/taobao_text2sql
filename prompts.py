import os

from dotenv import load_dotenv

load_dotenv()

path = os.getenv("PATH")

example_sql = f"""
    with category_status as (
        select item_category,count(case when behavior_type == 1 then 1 end) as pv_cnt,count(case when behavior_type == 4 then 1 end) as buy_cnt
        from read_csv_auto('{path}')
        group by item_category
    )
    select
        item_category,
        pv_cnt,
        buy_cnt,
        round(buy_cnt * 1.0 / nullif(pv_cnt, 0), 2) as conversion_rate
    from category_status
    where pv_cnt > 100
    order by conversion_rate desc
    limit 5
"""

general_sql_prompt = f"""你是一个 SQL 生成助手。DuckDB 数据库有一张表，字段如下：
- user_id: INTEGER，用户ID
- item_id: INTEGER，商品ID
- user_geohash: VARCHAR，用户地理位置（可能为空）
- item_category: INTEGER，商品类目ID
- behavior_type: INTEGER，行为类型，取值为 1 -- pv(浏览) / 2 -- cart(加购) / 3 -- fav(收藏) / 4 -- buy(购买) 
- time: VARCHAR，时间，格式为 'YYYY-MM-DD HH'

参考SQL：{example_sql}
其中使用 from 来查询表时，必须要使用 read_csv_auto 函数来读取数据，格式如下：read_csv_auto('{path}')，其中 path 已经进行初始化了。

用户会用自然语言提问，你只需要输出一条 SQL 语句，不要任何解释、不要 markdown 代码块、不要前后缀文字。
直接输出 SQL，以 SELECT 开头。"""

