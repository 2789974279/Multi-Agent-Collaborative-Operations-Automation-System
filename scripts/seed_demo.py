from __future__ import annotations

import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from core.repository import Repository
from core.schemas import TaskInput


def main() -> None:
    repo = Repository(ROOT / "data" / "operations.db")
    repo.initialize()
    task = repo.create_task(
        TaskInput(
            title="新用户首单转化活动",
            scenario="growth_campaign",
            objective="提升注册后 7 天内首单转化率",
            audience="近 7 天注册但未下单的新用户",
            constraints="预算 1 万元，不使用夸大承诺，优惠券有效期 5 天",
        )
    )
    print(f"Created demo task #{task['id']}: {task['title']}")


if __name__ == "__main__":
    main()
