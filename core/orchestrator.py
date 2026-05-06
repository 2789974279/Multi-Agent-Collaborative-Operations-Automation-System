from __future__ import annotations

import json
from dataclasses import asdict
from pathlib import Path
from typing import Any

from core.agents import AGENTS
from core.repository import Repository


class Orchestrator:
    def __init__(self, repo: Repository, workflow_path: Path):
        self.repo = repo
        self.workflow_path = workflow_path
        self.workflows = self.load_workflows()

    def load_workflows(self) -> dict[str, Any]:
        with self.workflow_path.open("r", encoding="utf-8") as file:
            return json.load(file)

    def list_agents(self) -> list[dict[str, str]]:
        return [
            {"key": key, "name": agent.name, "role": agent.role}
            for key, agent in AGENTS.items()
        ]

    def run_task(self, task_id: int) -> dict[str, Any]:
        task = self.repo.get_task(task_id)
        if not task:
            return {"error": "Task not found"}

        workflow = self.workflows[task["scenario"]]
        context: dict[str, Any] = {}
        self.repo.update_task_status(task_id, "running")
        self.repo.add_event(task_id, "orchestrator", "workflow_started", f"开始执行工作流：{workflow['name']}", workflow)

        try:
            for step in workflow["steps"]:
                agent = AGENTS[step]
                self.repo.add_event(task_id, agent.key, "agent_started", f"{agent.role}开始处理", {})
                result = agent.run(task, context)
                result_dict = asdict(result)
                context[step] = result_dict
                self.repo.add_event(task_id, agent.key, "agent_completed", result.summary, result_dict)

            final_status = self.resolve_status(context)
            final_result = {
                "workflow": workflow["name"],
                "agents": context,
                "launch_ready": final_status == "completed",
                "next_actions": self.next_actions(context),
            }
            self.repo.save_task_result(task_id, final_status, final_result)
            self.repo.add_event(task_id, "orchestrator", "workflow_completed", "工作流执行完成", final_result)
            return {"task": self.repo.get_task(task_id), "events": self.repo.list_events(task_id)}
        except Exception as exc:
            self.repo.save_task_result(task_id, "failed", {"error": str(exc), "agents": context})
            self.repo.add_event(task_id, "orchestrator", "workflow_failed", str(exc), {})
            raise

    def resolve_status(self, context: dict[str, Any]) -> str:
        risk = context.get("risk_review", {}).get("output", {})
        if risk and not risk.get("approved", False):
            return "needs_revision"
        return "completed"

    def next_actions(self, context: dict[str, Any]) -> list[str]:
        risk = context.get("risk_review", {}).get("output", {})
        if risk and not risk.get("approved", False):
            return ["修改风险话术", "重新发起审核", "审核通过后再进入投放"]
        return ["确认预算与排期", "配置渠道触达任务", "上线后每日检查告警指标"]
