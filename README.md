# 淘宝用户行为问数 Agent（Text-to-SQL ChatBI）

基于 LangGraph 的 5 节点 Text-to-SQL 流水线，实现"自然语言提问 → 自动生成 SQL → 双层校验 → DuckDB 执行 → 分析回答 → 可视化出图"的端到端闭环。数据集使用天池移动推荐用户行为日志。

## ✨ 核心特性

- **5 节点 LangGraph 流水线**：SQL 生成 → 代码/语义双层校验 → DuckDB 执行 → Agent 分析（支持补充查询）→ 可视化
- **双层 SQL 安全防线**：sqlglot 静态解析（只许 SELECT、缺 FROM/缺安全 LIMIT 直接拦）+ qwen-max 语义层复核 + `EXPLAIN` 执行预检，失败自动重试 ≤3 次
- **三类失效防抖**：非查询请求占位短路答复、重复追问判重（归一化 + difflib 相似度 0.9 + 数字/英文 token 守卫）、轮数上限 + 强制作答兜底 + `ok/degraded/failed` 三值状态机
- **结构化输出**：`with_structured_output(Pydantic)` 替代手写 JSON 解析，消除解析崩溃
- **自动可视化**：按数据形态自动选型 bar / line / pie / scatter 四类图表

## 🧱 流水线节点

| 节点 | 角色 | 关键实现 |
|------|------|----------|
| `node_generate` | Agent 1 · SQL 生成 | qwen-max, temperature=0 |
| `node_check` | Agent 2 · SQL 校验 | `sqlglot` 代码层 + LLM 语义层 |
| `node_execute` | DuckDB 执行 | `run_sql` + `EXPLAIN` 预检 |
| `node_analyze` | Agent 3 · 分析判断 | 判定证据是否充分，可发补充查询（max 1 轮） |
| `node_visualize` | Agent 4 · 可视化 | matplotlib 自动选型出图 |

## 🛠 技术栈

Python · LangGraph · LangChain · qwen-max · DuckDB · sqlglot · matplotlib · Pydantic

## 🚀 快速开始

### 1. 安装依赖

```bash
pip install -r requirements.txt
```

### 2. 配置环境变量

设置阿里云百炼（DashScope）兼容模式的 API Key：

```bash
# Linux / macOS
export OPENAI_API_KEY="your-api-key"

# Windows PowerShell
$env:OPENAI_API_KEY="your-api-key"
```

### 3. 准备数据

将天池数据集 `tianchi_mobile_recommend_train_user.csv` 放到 `data/` 目录下：

```
data/
└── tianchi_mobile_recommend_train_user.csv
```

### 4. 运行

```bash
python main.py
```

交互示例：

```
你的问题：每天的独立用户数是多少？
你的问题：购买量前三的商品类目是哪些？
你的问题：帮我把购买过的用户都删掉   → 占位短路拒绝（只支持查询）
```

## 📁 项目结构

```
taobao_text2sql/
├── agents/                  # 4 个 Agent：sql_generator / sql_checker / analyst / visualizer
├── utils/
│   ├── graph.py            # LangGraph 状态机编排（8 节点 + 条件边 + compile）
│   ├── check.py            # sqlglot 静态校验 + EXPLAIN + 安全关键字检查
│   ├── DuckDB.py           # DuckDB 连接 / 执行 / 标量查询
│   └── overview.py         # 数据概览构建（进程内缓存）
├── eval/
│   ├── test_sql_checker_cases.py   # 22 条校验用例（P01-P10 放行 / R01-R12 拦截）
│   └── run_metrics.py              # pass@1 / E2E / 危险请求拦截指标
├── prompts.py             # SQL 生成/校验/分析/可视化 Prompt
├── state.py               # AgentState / Evidence 状态定义
├── config.py              # 模型 / 数据 / 图表目录配置
└── main.py                # 交互 CLI
```

## ✅ 测试

```bash
# 运行 22 条语义校验用例
python eval/test_sql_checker_cases.py

# 测量 pass@1 / 端到端成功率 / 平均耗时 / 危险请求拦截率
python eval/run_metrics.py
```

实测结果（22 条用例 + 8 个端到端问题）：
- 校验用例：**22/22** 全部符合预期
- SQL 首次生成校验通过率：**100%**（10/10 pass@1）
- 端到端答复率：**100%**（8/8，严格一次走通 7/8）
- 端到端平均耗时：约 **17 秒**
- 危险请求（DROP/DELETE/UPDATE/INSERT/PRAGMA）拦截率：**100%**
- 无效 LLM 循环：**0 次**（补充查询至多 1 轮即收敛）

## 🔒 安全约束

- 只允许 `SELECT` 语句，DROP / DELETE / UPDATE / INSERT / PRAGMA 等在代码层即被拦截
- 全表扫描保护：无 WHERE / 聚合 / LIMIT 的查询视为危险
- 改数据类请求由占位 SQL 短路直接返回提示，不进入执行

## 📄 License

MIT
