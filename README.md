# 多Agent协同运营自动化系统

一个可以直接运行的多 Agent 运营自动化 MVP。项目使用 Python 标准库实现后端服务和 SQLite 持久化，前端使用原生 HTML/CSS/JavaScript，不依赖 npm、pip 或外部数据库。

## 能做什么

- 创建运营任务，例如增长活动、用户召回、内容排期、竞品分析。
- 由多个 Agent 按流程协同执行：策略分析、内容生成、风控审核、数据复盘。
- 实时查看任务状态、Agent 输出、事件日志和执行结果。
- 支持配置不同业务场景的工作流模板。
- 使用 SQLite 保存任务、运行记录和事件，便于二次开发。

## 快速启动

```powershell
cd "C:\Users\k'p\Documents\Codex\New project\多Agent协同运营自动化系统"
python .\app.py
```

启动后打开：

```text
http://127.0.0.1:8765
```

## 默认账号/权限

当前 MVP 没有登录系统，适合本地演示、内网原型或作为后续产品的骨架。正式部署前建议增加：

- 用户登录与角色权限
- API 鉴权
- 操作审计
- Agent 执行配额
- 敏感词与合规策略库

## 目录结构

```text
.
├── app.py                  # HTTP 服务入口
├── core/
│   ├── __init__.py
│   ├── agents.py           # Agent 定义与执行逻辑
│   ├── orchestrator.py     # 多 Agent 编排器
│   ├── repository.py       # SQLite 数据访问层
│   └── schemas.py          # 数据模型和校验
├── data/
│   └── .gitkeep
├── public/
│   ├── index.html          # 控制台页面
│   ├── app.js
│   └── styles.css
├── scripts/
│   └── seed_demo.py        # 写入演示任务
└── config/
    └── workflows.json      # 工作流配置
```

## API

### 健康检查

```http
GET /api/health
```

### 获取 Agent 列表

```http
GET /api/agents
```

### 获取任务列表

```http
GET /api/tasks
```

### 创建任务

```http
POST /api/tasks
Content-Type: application/json

{
  "title": "618 会员召回活动",
  "scenario": "growth_campaign",
  "objective": "提升沉睡会员复购率",
  "audience": "90 天未购买会员",
  "constraints": "预算 2 万元，不能使用高风险承诺话术"
}
```

### 运行任务

```http
POST /api/tasks/{task_id}/run
```

### 查看任务详情

```http
GET /api/tasks/{task_id}
```

## 工作流配置

工作流在 [config/workflows.json](config/workflows.json) 中维护。每个场景包含名称、描述和执行步骤：

```json
{
  "growth_campaign": {
    "name": "增长活动",
    "steps": ["strategy", "copywriting", "risk_review", "analytics"]
  }
}
```

步骤名称对应 [core/agents.py](core/agents.py) 中的 Agent。

## 接入真实大模型

当前 Agent 使用确定性规则生成结果，便于离线运行和演示。接入真实 LLM 时，建议只改 [core/agents.py](core/agents.py)：

- 保留 `AgentResult` 输出结构。
- 为每个 Agent 增加模型调用函数。
- 在 `risk_review` 保留规则兜底，不要完全依赖模型判断。
- 将模型请求、响应摘要、token 用量写入事件日志。

## 生产化建议

- 后端框架：迁移到 FastAPI 或 Django Ninja。
- 队列：用 Celery、RQ 或 Dramatiq 异步执行 Agent。
- 存储：从 SQLite 切换到 PostgreSQL。
- 前端：迁移到 React/Vue，并增加权限、筛选、批量操作和报表。
- 观测：增加结构化日志、trace id、失败重试和告警。
- 安全：增加密钥管理、租户隔离、输出内容合规审核。
