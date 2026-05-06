const state = {
  tasks: [],
  selectedTaskId: null,
  workflows: {},
  agents: [],
  events: []
};

const els = {
  health: document.querySelector("#health"),
  refreshBtn: document.querySelector("#refreshBtn"),
  taskForm: document.querySelector("#taskForm"),
  scenarioSelect: document.querySelector("#scenarioSelect"),
  taskList: document.querySelector("#taskList"),
  taskCount: document.querySelector("#taskCount"),
  taskDetails: document.querySelector("#taskDetails"),
  runBtn: document.querySelector("#runBtn"),
  agentGrid: document.querySelector("#agentGrid"),
  agentCount: document.querySelector("#agentCount")
};

async function api(path, options = {}) {
  const response = await fetch(path, {
    headers: { "Content-Type": "application/json" },
    ...options
  });
  const payload = await response.json();
  if (!response.ok) {
    throw new Error(payload.error || "请求失败");
  }
  return payload;
}

async function boot() {
  await checkHealth();
  await loadAgents();
  await loadTasks();
}

async function checkHealth() {
  try {
    await api("/api/health");
    els.health.textContent = "服务正常";
  } catch (error) {
    els.health.textContent = "服务异常";
  }
}

async function loadAgents() {
  const payload = await api("/api/agents");
  state.agents = payload.agents;
  state.workflows = payload.workflows;
  renderScenarioOptions();
  renderAgents();
}

async function loadTasks() {
  const payload = await api("/api/tasks");
  state.tasks = payload.tasks;
  if (!state.selectedTaskId && state.tasks.length) {
    state.selectedTaskId = state.tasks[0].id;
  }
  renderTasks();
  if (state.selectedTaskId) {
    await loadTaskDetails(state.selectedTaskId);
  }
}

async function loadTaskDetails(taskId) {
  const payload = await api(`/api/tasks/${taskId}`);
  state.selectedTaskId = taskId;
  state.events = payload.events;
  renderTasks();
  renderTaskDetails(payload.task, payload.events);
}

function renderScenarioOptions() {
  els.scenarioSelect.innerHTML = Object.entries(state.workflows)
    .map(([key, workflow]) => `<option value="${key}">${workflow.name}</option>`)
    .join("");
}

function renderAgents() {
  els.agentCount.textContent = `${state.agents.length} 个 Agent`;
  els.agentGrid.innerHTML = state.agents
    .map(
      (agent) => `
        <article class="agent-card">
          <strong>${agent.name}</strong>
          <p>${agent.role}</p>
          <span class="badge">${agent.key}</span>
        </article>
      `
    )
    .join("");
}

function renderTasks() {
  els.taskCount.textContent = `${state.tasks.length} 项`;
  if (!state.tasks.length) {
    els.taskList.innerHTML = `<div class="empty">还没有任务</div>`;
    return;
  }
  els.taskList.innerHTML = state.tasks
    .map((task) => {
      const workflow = state.workflows[task.scenario];
      return `
        <article class="task-item ${task.id === state.selectedTaskId ? "active" : ""}" data-task-id="${task.id}">
          <div class="task-title">
            <span>${escapeHtml(task.title)}</span>
            <span class="badge ${task.status}">${statusText(task.status)}</span>
          </div>
          <p>${workflow ? workflow.name : task.scenario} · ${escapeHtml(task.audience)}</p>
          <small>${task.created_at}</small>
        </article>
      `;
    })
    .join("");

  document.querySelectorAll("[data-task-id]").forEach((item) => {
    item.addEventListener("click", () => loadTaskDetails(Number(item.dataset.taskId)));
  });
}

function renderTaskDetails(task, events) {
  els.runBtn.disabled = false;
  els.runBtn.dataset.taskId = task.id;
  const results = task.result?.agents || {};
  const resultCards = Object.values(results)
    .map(
      (result) => `
        <article class="result-card">
          <strong>${result.title}</strong>
          <p>${escapeHtml(result.summary)}</p>
          <span class="badge">评分 ${result.score}</span>
          <pre class="json-box">${escapeHtml(JSON.stringify(result.output, null, 2))}</pre>
        </article>
      `
    )
    .join("");

  els.taskDetails.innerHTML = `
    <div class="task-title">
      <h3>${escapeHtml(task.title)}</h3>
      <span class="badge ${task.status}">${statusText(task.status)}</span>
    </div>
    <p><strong>目标：</strong>${escapeHtml(task.objective)}</p>
    <p><strong>人群：</strong>${escapeHtml(task.audience)}</p>
    <p><strong>约束：</strong>${escapeHtml(task.constraints)}</p>
    ${task.result?.next_actions ? `<p><strong>下一步：</strong>${task.result.next_actions.map(escapeHtml).join(" / ")}</p>` : ""}
    <div class="result-grid">${resultCards || `<div class="empty">尚未运行工作流</div>`}</div>
    <h3>事件日志</h3>
    <div class="event-list">
      ${events
        .map(
          (event) => `
            <div class="event">
              <strong>${event.agent}</strong>
              <span class="muted">${event.event_type} · ${event.created_at}</span>
              <p>${escapeHtml(event.message)}</p>
            </div>
          `
        )
        .join("")}
    </div>
  `;
}

function statusText(status) {
  return {
    pending: "待运行",
    running: "运行中",
    completed: "已完成",
    needs_revision: "需修改",
    failed: "失败"
  }[status] || status;
}

function escapeHtml(value) {
  return String(value)
    .replaceAll("&", "&amp;")
    .replaceAll("<", "&lt;")
    .replaceAll(">", "&gt;")
    .replaceAll('"', "&quot;")
    .replaceAll("'", "&#039;");
}

els.refreshBtn.addEventListener("click", loadTasks);

els.taskForm.addEventListener("submit", async (event) => {
  event.preventDefault();
  const form = new FormData(event.currentTarget);
  const body = Object.fromEntries(form.entries());
  const payload = await api("/api/tasks", {
    method: "POST",
    body: JSON.stringify(body)
  });
  state.selectedTaskId = payload.task.id;
  await loadTasks();
});

els.runBtn.addEventListener("click", async () => {
  const taskId = Number(els.runBtn.dataset.taskId);
  els.runBtn.disabled = true;
  els.runBtn.textContent = "运行中";
  try {
    await api(`/api/tasks/${taskId}/run`, { method: "POST" });
    await loadTasks();
  } finally {
    els.runBtn.disabled = false;
    els.runBtn.textContent = "运行工作流";
  }
});

boot().catch((error) => {
  els.health.textContent = error.message;
});
