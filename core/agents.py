from __future__ import annotations

from typing import Any

from core.schemas import AgentResult


class BaseAgent:
    key = "base"
    name = "Base Agent"
    role = "基础 Agent"

    def run(self, task: dict[str, Any], context: dict[str, Any]) -> AgentResult:
        raise NotImplementedError


class StrategyAgent(BaseAgent):
    key = "strategy"
    name = "Strategy Agent"
    role = "运营策略分析"

    def run(self, task: dict[str, Any], context: dict[str, Any]) -> AgentResult:
        channels = ["站内信", "短信", "企微", "App Push"]
        if "内容" in task["scenario"]:
            channels = ["公众号", "视频号", "小红书", "社群"]
        plan = {
            "target": task["audience"],
            "core_objective": task["objective"],
            "channels": channels,
            "segments": ["高价值用户", "价格敏感用户", "低活跃用户"],
            "cadence": "3 天预热，5 天集中触达，7 天复盘",
            "success_metrics": ["转化率", "触达率", "退订率", "ROI"],
        }
        return AgentResult(
            agent=self.key,
            title="策略方案",
            summary=f"围绕「{task['objective']}」制定分层触达策略。",
            output=plan,
            score=86,
        )


class CopywritingAgent(BaseAgent):
    key = "copywriting"
    name = "Copywriting Agent"
    role = "内容与话术生成"

    def run(self, task: dict[str, Any], context: dict[str, Any]) -> AgentResult:
        strategy = context.get("strategy", {}).get("output", {})
        channels = strategy.get("channels", ["站内信", "短信"])
        copy = {
            "theme": f"{task['title']} - 限时运营方案",
            "messages": [
                {
                    "channel": channel,
                    "headline": f"{task['audience']}专属提醒",
                    "body": f"我们为你准备了围绕「{task['objective']}」的专属权益，活动期间完成指定动作即可领取。",
                }
                for channel in channels
            ],
            "cta": "立即参与",
            "tone": "清晰、克制、强调权益和行动路径",
        }
        return AgentResult(
            agent=self.key,
            title="内容资产",
            summary=f"已生成 {len(channels)} 个渠道的触达文案。",
            output=copy,
            score=82,
        )


class RiskReviewAgent(BaseAgent):
    key = "risk_review"
    name = "Risk Review Agent"
    role = "合规与风险审核"

    risky_terms = ["稳赚", "绝对", "最高收益", "保本", "唯一", "100%"]

    def run(self, task: dict[str, Any], context: dict[str, Any]) -> AgentResult:
        text = " ".join(
            [
                task["title"],
                task["objective"],
                task["constraints"],
                str(context.get("copywriting", {}).get("output", {})),
            ]
        )
        hits = [term for term in self.risky_terms if term in text]
        approved = not hits
        output = {
            "approved": approved,
            "risk_terms": hits,
            "required_changes": [] if approved else [f"移除或替换高风险词：{term}" for term in hits],
            "policy_notes": ["避免承诺收益", "活动规则需清晰展示", "保留退订和隐私说明"],
        }
        return AgentResult(
            agent=self.key,
            title="风险审核",
            summary="审核通过，可以进入执行准备。" if approved else "存在高风险表达，需要修改后再执行。",
            output=output,
            score=94 if approved else 45,
        )


class AnalyticsAgent(BaseAgent):
    key = "analytics"
    name = "Analytics Agent"
    role = "数据复盘设计"

    def run(self, task: dict[str, Any], context: dict[str, Any]) -> AgentResult:
        risk = context.get("risk_review", {}).get("output", {})
        output = {
            "dashboard": ["曝光人数", "点击人数", "转化人数", "收入", "成本", "ROI"],
            "experiment": "建议按用户活跃度做 A/B 分组，保留 10% 对照组。",
            "alerts": ["退订率 > 1.5%", "投诉量 > 20", "ROI 连续 2 天低于 1"],
            "launch_ready": bool(risk.get("approved", True)),
        }
        return AgentResult(
            agent=self.key,
            title="复盘指标",
            summary="已生成指标看板、实验方案和告警阈值。",
            output=output,
            score=88,
        )


AGENTS: dict[str, BaseAgent] = {
    agent.key: agent
    for agent in [
        StrategyAgent(),
        CopywritingAgent(),
        RiskReviewAgent(),
        AnalyticsAgent(),
    ]
}
