import uuid
from pathlib import Path

import matplotlib
import matplotlib.pyplot as plt
from langchain_core.output_parsers import StrOutputParser
from langchain_core.prompts import ChatPromptTemplate
from pydantic import BaseModel,Field

from config import model, CHART_DIR
from prompts import VISUALIZER_PROMPT

matplotlib.use("Agg")

plt.rcParams["font.sans-serif"] = ["Microsoft YaHei", "SimHei", "DejaVu Sans"]
plt.rcParams["axes.unicode_minus"] = False

class VisualizeResult(BaseModel):
    chart_type: str = Field(default="none", description="图表类型")
    title: str = Field(default="查询结果", description="图表标题")
    x_field: str = Field(default="", description="X轴字段")
    y_field: str = Field(default="", description="Y轴字段")
    x_label: str = Field(default="", description="X轴标签")
    y_label: str = Field(default="", description="Y轴标签")
    reason: str = Field(default="图表规格解析失败，跳过绘图")

class Visualizer:
    def __init__(self):
        self.chain = (ChatPromptTemplate(messages=[("system",VISUALIZER_PROMPT)]) |
                      model.with_structured_output(VisualizeResult,include_raw=True)
                      )

    def decide(self,query_result,analysis):
        data = self.chain.invoke({
            "query_result": query_result,
            "analysis": analysis
        })
        parsed = data["parsed"]
        return{
            "chart_type": parsed.chart_type,
            "title": parsed.title,
            "x_field": parsed.x_field,
            "y_field": parsed.y_field,
            "x_label": parsed.x_label,
            "y_label": parsed.y_label,
            "reason": parsed.reason
        }

    def draw(self,spec: dict, df):
        chart_type = spec.get("chart_type", "none")
        if chart_type == "none" or df is None or len(df) == 0:
            return ""

        x_field = spec.get("x_field", "")
        y_field = spec.get("y_field", "")
        if x_field not in df.columns or y_field not in df.columns:
            raise ValueError(
                f"字段不存在：x_field={x_field!r} y_field={y_field!r} "
                f"可用列={list(df.columns)}"
            )

        # 行数过多时只取前 30 行，避免图变成黑块
        plot_df = df.head(30)

        fig, ax = plt.subplots(figsize=(10, 6))

        if chart_type == "bar":
            ax.bar(plot_df[x_field].astype(str), plot_df[y_field])
            ax.set_xlabel(spec.get("x_label") or x_field)
            ax.set_ylabel(spec.get("y_label") or y_field)
            plt.xticks(rotation=45, ha="right")
        elif chart_type == "line":
            ax.plot(plot_df[x_field].astype(str), plot_df[y_field], marker="o")
            ax.set_xlabel(spec.get("x_label") or x_field)
            ax.set_ylabel(spec.get("y_label") or y_field)
            plt.xticks(rotation=45, ha="right")
        elif chart_type == "pie":
            ax.pie(plot_df[y_field], labels=plot_df[x_field].astype(str), autopct="%1.1f%%")
        elif chart_type == "scatter":
            ax.scatter(plot_df[x_field], plot_df[y_field])
            ax.set_xlabel(spec.get("x_label") or x_field)
            ax.set_ylabel(spec.get("y_label") or y_field)
        else:
            plt.close(fig)
            return ""

        ax.set_title(spec.get("title") or "查询结果")
        fig.tight_layout()

        CHART_DIR.mkdir(parents=True, exist_ok=True)
        out_path = CHART_DIR / f"chart_{uuid.uuid4().hex[:8]}.png"
        fig.savefig(out_path, dpi=120, bbox_inches="tight")
        plt.close(fig)
        return str(out_path)

agent_4 = None

def get_agent_4():
    global agent_4
    if agent_4 is None:
        agent_4 = Visualizer()
    return agent_4