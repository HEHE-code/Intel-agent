"""数据模型 —— 对应设计文档三张表。"""
from __future__ import annotations

from datetime import datetime

from sqlalchemy import JSON, Boolean, DateTime, ForeignKey, String, Text
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column, relationship


class Base(DeclarativeBase):
    pass


def _now() -> datetime:
    return datetime.now()


class AgentConfig(Base):
    """智能体配置。"""

    __tablename__ = "agent_config"

    id: Mapped[str] = mapped_column(String, primary_key=True)
    name: Mapped[str] = mapped_column(String, nullable=False)
    domain: Mapped[str] = mapped_column(String, nullable=False)  # military/finance/...
    intent: Mapped[str] = mapped_column(Text, nullable=False)  # 原始自然语言输入
    tools: Mapped[list] = mapped_column(JSON, default=list)  # 工具集列表
    prompt_template: Mapped[str] = mapped_column(Text, default="")
    created_at: Mapped[datetime] = mapped_column(DateTime, default=_now)

    runs: Mapped[list["RunRecord"]] = relationship(
        back_populates="agent", cascade="all, delete-orphan"
    )


class RunRecord(Base):
    """每次执行记录。"""

    __tablename__ = "run_record"

    id: Mapped[str] = mapped_column(String, primary_key=True)
    agent_id: Mapped[str] = mapped_column(
        ForeignKey("agent_config.id", ondelete="CASCADE"), nullable=False
    )
    status: Mapped[str] = mapped_column(String, default="running")  # running/completed/failed
    steps: Mapped[list] = mapped_column(JSON, default=list)  # 各节点运行日志
    report_md: Mapped[str] = mapped_column(Text, default="")  # 最终 Markdown 报告
    starred: Mapped[bool] = mapped_column(Boolean, default=False)  # 收藏标星
    note: Mapped[str] = mapped_column(Text, default="")  # 用户批注
    created_at: Mapped[datetime] = mapped_column(DateTime, default=_now)

    agent: Mapped[AgentConfig] = relationship(back_populates="runs")


class DomainToolConfig(Base):
    """领域工具配置 —— 运行时可调整开关与 Key。"""

    __tablename__ = "domain_tool_config"

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    domain: Mapped[str] = mapped_column(String, nullable=False)
    tool_name: Mapped[str] = mapped_column(String, nullable=False)
    api_key_env: Mapped[str] = mapped_column(String, default="")  # 对应的环境变量名
    enabled: Mapped[bool] = mapped_column(Boolean, default=True)


class Schedule(Base):
    """定时运行配置 —— 智能体按计划自动跑。

    支持三种类型：
    - once: 单次，到 once_at 时间跑一次后自动失效（cron_expr 留空）
    - daily: 每天，cron_expr 形如 "M H * * *"
    - weekly: 每周，cron_expr 形如 "M H * * W"（W=0..6，0=周日）
    """

    __tablename__ = "schedule"

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    agent_id: Mapped[str] = mapped_column(
        ForeignKey("agent_config.id", ondelete="CASCADE"), nullable=False, unique=True
    )
    run_type: Mapped[str] = mapped_column(String, default="daily")  # once/daily/weekly
    cron_expr: Mapped[str] = mapped_column(String, default="")  # daily/weekly 用
    once_at: Mapped[datetime | None] = mapped_column(DateTime, nullable=True)  # once 用
    enabled: Mapped[bool] = mapped_column(Boolean, default=True)
    last_run_at: Mapped[datetime | None] = mapped_column(DateTime, nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=_now)


class AgentTemplate(Base):
    """智能体模板 —— 常用情报需求存成模板，一键复用。

    与 AgentConfig 字段类似但独立：应用模板生成新 AgentConfig，两者无关联。
    """

    __tablename__ = "agent_template"

    id: Mapped[str] = mapped_column(String, primary_key=True)  # tpl_xxx
    name: Mapped[str] = mapped_column(String, nullable=False)
    domain: Mapped[str] = mapped_column(String, nullable=False)
    intent_template: Mapped[str] = mapped_column(Text, nullable=False)  # 可带占位描述
    tools: Mapped[list] = mapped_column(JSON, default=list)
    prompt_template: Mapped[str] = mapped_column(Text, default="")
    created_at: Mapped[datetime] = mapped_column(DateTime, default=_now)


class CustomDomain(Base):
    """用户自定义情报领域（持久化）。

    预设 5 领域写死在 registry.py；自定义领域存此表。
    生成页领域标签 = 预设 + 此表所有记录。
    """

    __tablename__ = "custom_domain"

    key: Mapped[str] = mapped_column(String, primary_key=True)  # 如 "能源"
    label: Mapped[str] = mapped_column(String, nullable=False)  # 显示名，同 key
    color: Mapped[str] = mapped_column(String, default="#64748B")  # 标签色
    created_at: Mapped[datetime] = mapped_column(DateTime, default=_now)


class AgentMemory(Base):
    """智能体记忆 —— 历次报告的关键结论，供下次运行参考。

    每次运行后由 LLM 提取本次报告 3-5 条关键结论存入。
    分析节点读取最近几条记忆，让报告有连续性。
    """

    __tablename__ = "agent_memory"

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    agent_id: Mapped[str] = mapped_column(
        ForeignKey("agent_config.id", ondelete="CASCADE"), nullable=False
    )
    run_id: Mapped[str] = mapped_column(String, nullable=False)  # 来源运行
    key_points: Mapped[list] = mapped_column(JSON, default=list)  # 3-5 条关键结论
    created_at: Mapped[datetime] = mapped_column(DateTime, default=_now)


class AggregateTask(Base):
    """多智能体协同 —— 组合多个智能体报告做综合研判。

    选 N 个智能体，取各自最新报告，LLM 综合分析产出综合报告。
    """

    __tablename__ = "aggregate_task"

    id: Mapped[str] = mapped_column(String, primary_key=True)  # agg_xxx
    name: Mapped[str] = mapped_column(String, nullable=False)  # 综合主题
    agent_ids: Mapped[list] = mapped_column(JSON, default=list)  # 选中的智能体 id 列表
    theme: Mapped[str] = mapped_column(Text, default="")  # 综合分析主题
    report_md: Mapped[str] = mapped_column(Text, default="")  # 综合报告
    status: Mapped[str] = mapped_column(String, default="running")  # running/completed/failed
    created_at: Mapped[datetime] = mapped_column(DateTime, default=_now)
