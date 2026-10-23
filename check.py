import re

import sqlglot
import sqlglot.expressions as exp

from DuckDB import db_check_sql

# 只允许 SELECT 语句
def check_permission(sql):
    if not sql or not sql.strip():
        return False, "SQL 为空"
    try:
        statements = sqlglot.parse(sql, read="duckdb")
    except Exception as e:
        return False, f"sqlglot 解析失败：{e}"
    if not statements:
        return False, "SQL 解析后为空"
    for stmt in statements:
        if stmt is None:
            return False, "SQL 中包含无法解析的语句"
        # 只允许 SELECT（含 WITH ... SELECT）
        if not isinstance(stmt, exp.Select):
            return False, f"只允许 SELECT 语句，检测到：{type(stmt).__name__}"
        # 防御：SELECT ... INTO OUTFILE 写法
        if stmt.args.get("into") is not None:
            return False, "禁止 SELECT INTO 语法"
    return True, ""

# 检查 SQL 语法
def check_syntax(sql: str):
    if not sql or not sql.strip():
        return False, "SQL 为空"

    return db_check_sql(sql)

# 检查 SQL 安全性
DANGEROUS_FUNCTIONS = {
    "load_extension",   # 加载扩展（可执行任意代码）
    "attach", "detach",  # 附加/分离数据库
    "copy",              # 导出数据到文件
    "read_text", "read_blob",  # 读取任意文件
    "glob",              # 列目录
    "secret", "current_setting", "set_config",  # 配置/密钥
    "sleep", "pg_sleep",  # 延时 DoS
}

DANGEROUS_KEYWORDS = {
    "ATTACH", "DETACH", "COPY", "INSTALL", "LOAD", "PRAGMA",
    "SET", "RESET", "EXPORT", "IMPORT", "CREATE", "DROP",
    "ALTER", "INSERT", "UPDATE", "DELETE", "TRUNCATE",
}

def check_security(sql):
    if not sql or not sql.strip():
        return False, "SQL 为空"

    # 第一道：危险关键字粗筛（单词边界，避免误伤列名）
    upper = sql.upper()
    for kw in DANGEROUS_KEYWORDS:
        if re.search(rf"\b{kw}\b", upper):
            return False, f"检测到危险关键字：{kw}"

    # 第二道：危险函数精确匹配（AST 遍历函数节点）
    try:
        stmts = sqlglot.parse(sql, read="duckdb")
        stmts = [ s for s in stmts if s is not None]
    except Exception as e:
        return False, f"安全校验解析失败：{e}"

    for stmt in stmts:
        for f in stmt.find_all(exp.Func):
            name = f.name if isinstance(f, exp.Anonymous) else f.sql_name()
            if name.lower() in DANGEROUS_FUNCTIONS:
                return False, f"检测到危险函数：{name}"

    # 第三道：无 LIMIT 全表扫描检测
    has_limit = False
    has_where = False
    is_aggregate = False
    for stmt in stmts:
        if stmt is None or not isinstance(stmt, exp.Select):
            continue
        if stmt.args.get("limit") is not None:
            has_limit = True
        if stmt.args.get("where") is not None:
            has_where = True
        if stmt.args.get("group") is not None:
            is_aggregate = True
        if any(True for _ in stmt.find_all(exp.AggFunc)):
            is_aggregate = True

    if not has_limit and not has_where and not is_aggregate:
        return False, "检测到无 WHERE 且无 LIMIT 的全表扫描，请添加 LIMIT 或 WHERE 条件"

    return True, ""

def check_sql(sql:str):
    # 1) 权限
    ok, msg = check_permission(sql)
    if not ok:
        return False, msg
    # 2) 语法
    ok, msg = check_syntax(sql)
    if not ok:
        return False, msg
    # 3) 安全
    ok, msg = check_security(sql)
    if not ok:
        return False, msg
    return True,""
