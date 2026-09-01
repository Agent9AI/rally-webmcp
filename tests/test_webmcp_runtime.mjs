import assert from "node:assert/strict";
import fs from "node:fs";
import vm from "node:vm";

const classList = () => {
  const values = new Set();
  return {
    add: (...names) => names.forEach((name) => values.add(name)),
    contains: (name) => values.has(name),
    toggle: (name, force) => {
      const next = force === undefined ? !values.has(name) : Boolean(force);
      if (next) values.add(name);
      else values.delete(name);
      return next;
    },
  };
};

const field = (value = "") => {
  const listeners = new Map();
  return {
    value,
    checked: false,
    addEventListener(name, callback) {
      const callbacks = listeners.get(name) || [];
      callbacks.push(callback);
      listeners.set(name, callbacks);
    },
    dispatch(name) { (listeners.get(name) || []).forEach((callback) => callback({ type: name })); },
    focus() {},
  };
};

const node = (tag = "div") => ({
  tag,
  children: [],
  className: "",
  textContent: "",
  append(...children) { this.children.push(...children); },
  replaceChildren(...children) { this.children = children; },
});

const company = field();
const team = field();
const goal = field();
const systems = field();
const sourceRun = field();
const secondWind = field();
secondWind.checked = true;

const setupLink = { href: "mailto:terry@agent9.dev?subject=Create%20a%20Rally%20teammate" };
const webMcpLabel = { textContent: "WebMCP agent-ready" };
const webMcpStatus = { classList: classList(), querySelector: () => webMcpLabel };
const taskReceipt = { hidden: true };
const taskTitle = { textContent: "" };
const taskState = { textContent: "", classList: classList() };
const taskModel = { textContent: "" };
const taskArtifact = { textContent: "" };
const taskNote = { textContent: "" };
const traceList = node("ol");

const elements = new Map([
  ["[data-managed-setup-link]", setupLink],
  ["[data-job-company]", company],
  ["[data-job-team]", team],
  ["[data-job-goal]", goal],
  ["[data-job-systems]", systems],
  ["[data-job-source-run]", sourceRun],
  ["[data-second-wind]", secondWind],
  ["[data-webmcp-status]", webMcpStatus],
  ["[data-webmcp-task-receipt]", taskReceipt],
  ["[data-webmcp-task-title]", taskTitle],
  ["[data-webmcp-task-state]", taskState],
  ["[data-webmcp-task-model]", taskModel],
  ["[data-webmcp-task-artifact]", taskArtifact],
  ["[data-webmcp-task-note]", taskNote],
  ["[data-webmcp-trace]", traceList],
]);

const tools = new Map();
const document = {
  documentElement: { dataset: {} },
  visibilityState: "visible",
  modelContext: {
    async registerTool(tool) {
      assert(!tools.has(tool.name), `duplicate tool: ${tool.name}`);
      tools.set(tool.name, tool);
    },
  },
  addEventListener() {},
  createElement(tag) { return node(tag); },
  createTextNode(text) { return { textContent: text }; },
  querySelector(selector) { return elements.get(selector) || null; },
  querySelectorAll() { return []; },
};

const window = {
  addEventListener() {},
  requestAnimationFrame(callback) { callback(); },
  scrollY: 0,
};

const context = vm.createContext({
  AbortController,
  DOMException,
  URL,
  console,
  document,
  setTimeout,
  window,
});
const app = fs.readFileSync(new URL("../site/app.js", import.meta.url), "utf8");
vm.runInContext(app, context, { filename: "site/app.js" });
await new Promise((resolve) => setTimeout(resolve, 0));

assert.deepEqual([...tools.keys()].sort(), [
  "rally_draft_job",
  "rally_inspect_public_run",
  "rally_list_public_runs",
  "rally_review_visible_song_task",
  "rally_stage_challenge_song",
]);

const stage = tools.get("rally_stage_challenge_song");
assert.equal(stage.annotations.readOnlyHint, false);
assert.equal(stage.inputSchema.additionalProperties, false);
const staged = await stage.execute({
  creative_direction: "Make the confirmation moment musical: the agent pauses, the human says confirm, and only then does the chorus open.",
  hook: "Same page, shared light — tools can help, approval stays with me.",
  style: "electro-soul",
  duration_seconds: 68,
}, { signal: new AbortController().signal });

assert.equal(staged.status, "staged_not_generated");
assert.equal(staged.model, "lyria-3-pro-preview");
assert.equal(staged.generation_started, false);
assert.equal(staged.transmitted, false);
assert.equal(staged.human_confirmation_required, true);
assert.equal(taskReceipt.hidden, false);
assert.equal(company.value, "Agent9");
assert.equal(team.value, "Rally for WebMCP");
assert.match(goal.value, /website exposes named, structured tools/i);
assert.match(goal.value, /search public runs[\s\S]*inspect a verification gap/i);
assert.match(goal.value, /Google Workspace[\s\S]*Slack[\s\S]*GitHub[\s\S]*Cloudflare[\s\S]*BigQuery/i);
assert.match(goal.value, /Agent9 Insights[\s\S]*allowlisted n8n workflow[\s\S]*EmDash/i);
assert.match(goal.value, /A2A v1\.0 is supported[\s\S]*Agent Card[\s\S]*JSON-RPC\/HTTP\+JSON/i);
assert.match(goal.value, /WebMCP is the shared browser surface[\s\S]*governed MCP[\s\S]*A2A/i);
assert.match(goal.value, /different model family/i);
assert(goal.value.length <= 4000, `composed song task exceeded visible boundary: ${goal.value.length}`);
assert.equal(staged.collaboration_trace.at(-1).action, "staged_song_task");
assert.equal(traceList.children.length, 1);

const review = tools.get("rally_review_visible_song_task");
assert.equal(review.annotations.readOnlyHint, false);
assert.equal(review.annotations.untrustedContentHint, true);
const reviewed = await review.execute({}, { signal: new AbortController().signal });
assert.equal(reviewed.status, "ready_for_human_decision");
assert.equal(reviewed.ready, true);
assert.equal(reviewed.transmitted, false);
assert.equal(reviewed.human_confirmation_required, true);
assert.equal(taskState.classList.contains("is-ready"), true);

goal.value = goal.value.replace("A2A", "outside-agent protocol");
goal.dispatch("change");
const edited = await review.execute({}, { signal: new AbortController().signal });
assert.equal(edited.status, "needs_attention");
assert.equal(edited.ready, false);
assert(edited.failed_checks.includes("protocol_roles"));
assert.equal(taskState.classList.contains("needs-attention"), true);
assert(edited.collaboration_trace.some((entry) => entry.actor === "human" && entry.action === "edited_visible_task"));
assert.equal(edited.collaboration_trace.at(-1).action, "reviewed_visible_song_task");

console.log("WebMCP runtime contract passed: stage → human edit → untrusted read-back → review");
