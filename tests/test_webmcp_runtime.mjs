import assert from "node:assert/strict";
import fs from "node:fs";
import vm from "node:vm";

const classList = () => {
  const values = new Set();
  return {
    add: (...names) => names.forEach((name) => values.add(name)),
    contains: (name) => values.has(name),
    remove: (...names) => names.forEach((name) => values.delete(name)),
    toggle: (name, force) => {
      const next = force === undefined ? !values.has(name) : Boolean(force);
      if (next) values.add(name);
      else values.delete(name);
      return next;
    },
  };
};

const node = (tag = "div") => {
  const listeners = new Map();
  return {
    tag,
    children: [],
    className: "",
    classList: classList(),
    dataset: {},
    hidden: false,
    open: false,
    style: {},
    tabIndex: 0,
    textContent: "",
    value: "",
    checked: false,
    showModal() { this.open = true; },
    close() { this.open = false; },
    append(...children) { this.children.push(...children); },
    replaceChildren(...children) { this.children = children; },
    setAttribute(name, value) { this[name] = String(value); },
    removeAttribute(name) { delete this[name]; },
    addEventListener(name, callback) {
      const callbacks = listeners.get(name) || [];
      callbacks.push(callback);
      listeners.set(name, callbacks);
    },
    dispatch(name) {
      (listeners.get(name) || []).forEach((callback) => callback({
        currentTarget: this,
        key: "",
        preventDefault() {},
        target: this,
        type: name,
      }));
    },
    focus() {},
    matches() { return false; },
    querySelector() { return null; },
    scrollIntoView() {},
  };
};

const field = (value = "", dataset = {}) => Object.assign(node("input"), {
  dataset: { ...dataset },
  value,
});

const composite = (children = {}) => Object.assign(node(), {
  querySelector(selector) { return children[selector] || null; },
});

const company = field();
const team = field();
const goal = field();
const systems = field();
const sourceRun = field();
const secondWind = field();
secondWind.checked = true;

const songDirection = field("", { webmcpTrack: "song", webmcpFieldLabel: "song direction" });
const songHook = field("", { webmcpTrack: "song", webmcpFieldLabel: "song hook" });
const songStyle = field("west-coast-storytelling", { webmcpTrack: "song", webmcpFieldLabel: "song style" });
const songDuration = field("72", { webmcpTrack: "song", webmcpFieldLabel: "song length" });
const songBrief = field("", { webmcpTrack: "song", webmcpFieldLabel: "visible song brief" });
songBrief.matches = (selector) => selector === "[data-webmcp-song-brief]";

const insightsAngle = field("", { webmcpTrack: "insights", webmcpFieldLabel: "article angle" });
const insightsAudience = field("builders", { webmcpTrack: "insights", webmcpFieldLabel: "article audience" });
const insightsClosing = field("", { webmcpTrack: "insights", webmcpFieldLabel: "article closing thought" });
const insightsTitle = field("", { webmcpTrack: "insights", webmcpFieldLabel: "article title" });
const insightsDeck = field("", { webmcpTrack: "insights", webmcpFieldLabel: "article deck" });
const insightsBody = field("", { webmcpTrack: "insights", webmcpFieldLabel: "article body" });

const connectorProfile = field("n8n-agent9-insights", { webmcpTrack: "connector", webmcpFieldLabel: "connector profile" });
const connectorAccess = field("read-with-approved-writes", { webmcpTrack: "connector", webmcpFieldLabel: "connector access" });
const connectorPurpose = field("", { webmcpTrack: "connector", webmcpFieldLabel: "connector purpose" });
const connectorPlan = field("", { webmcpTrack: "connector", webmcpFieldLabel: "connector plan" });

const trackedFields = [
  songDirection,
  songHook,
  songStyle,
  songDuration,
  songBrief,
  insightsAngle,
  insightsAudience,
  insightsClosing,
  insightsTitle,
  insightsDeck,
  insightsBody,
  connectorProfile,
  connectorAccess,
  connectorPurpose,
  connectorPlan,
];

const setupLink = { href: "mailto:terry@agent9.dev?subject=Create%20a%20Rally%20teammate" };
const webMcpLabel = node("span");
webMcpLabel.textContent = "WebMCP agent-ready";
const webMcpStatus = composite({ span: webMcpLabel });
const v2StatusTitle = node("b");
const v2StatusNote = node("small");
const webMcpV2Status = composite({ b: v2StatusTitle, small: v2StatusNote });
const taskReceipt = node("section");
taskReceipt.hidden = true;
const taskTitle = node("h3");
const taskState = node("span");
const taskModel = node("b");
const taskArtifact = node("b");
const taskNote = node("p");
const traceList = node("ol");
const studioTitle = node("h3");
const studioState = node("span");
const studioSummary = node("p");
const studioWorkflow = node("b");
const studioDestination = node("b");
const studioChecks = node("ul");
const webMcpDialog = node("dialog");
const workflowTabs = ["song", "insights", "connector"].map((workflow) => {
  const tab = node("button");
  tab.dataset.webmcpWorkflow = workflow;
  return tab;
});
const workflowPanels = ["song", "insights", "connector"].map((workflow) => {
  const panel = node("section");
  panel.dataset.webmcpPanel = workflow;
  return panel;
});

const elements = new Map([
  ['meta[name="rally-console-api"]', { content: "https://public.example.test/v1/console" }],
  ["#demo", node("section")],
  ["#webmcp", node("section")],
  ["[data-managed-setup-link]", setupLink],
  ["[data-job-company]", company],
  ["[data-job-team]", team],
  ["[data-job-goal]", goal],
  ["[data-job-systems]", systems],
  ["[data-job-source-run]", sourceRun],
  ["[data-second-wind]", secondWind],
  ["[data-webmcp-status]", webMcpStatus],
  ["[data-webmcp-v2-status]", webMcpV2Status],
  ["[data-webmcp-task-receipt]", taskReceipt],
  ["[data-webmcp-task-title]", taskTitle],
  ["[data-webmcp-task-state]", taskState],
  ["[data-webmcp-task-model]", taskModel],
  ["[data-webmcp-task-artifact]", taskArtifact],
  ["[data-webmcp-task-note]", taskNote],
  ["[data-webmcp-trace]", traceList],
  ["[data-webmcp-studio-title]", studioTitle],
  ["[data-webmcp-studio-state]", studioState],
  ["[data-webmcp-studio-summary]", studioSummary],
  ["[data-webmcp-studio-workflow]", studioWorkflow],
  ["[data-webmcp-studio-destination]", studioDestination],
  ["[data-webmcp-studio-checks]", studioChecks],
  ["[data-webmcp-dialog]", webMcpDialog],
  ['[data-webmcp-workflow="song"]', workflowTabs[0]],
  ['[data-webmcp-workflow="insights"]', workflowTabs[1]],
  ['[data-webmcp-workflow="connector"]', workflowTabs[2]],
  ["[data-webmcp-song-direction]", songDirection],
  ["[data-webmcp-song-hook]", songHook],
  ["[data-webmcp-song-style]", songStyle],
  ["[data-webmcp-song-duration]", songDuration],
  ["[data-webmcp-song-brief]", songBrief],
  ["[data-webmcp-insights-angle]", insightsAngle],
  ["[data-webmcp-insights-audience]", insightsAudience],
  ["[data-webmcp-insights-closing]", insightsClosing],
  ["[data-webmcp-insights-title]", insightsTitle],
  ["[data-webmcp-insights-deck]", insightsDeck],
  ["[data-webmcp-insights-body]", insightsBody],
  ["[data-webmcp-connector-profile]", connectorProfile],
  ["[data-webmcp-connector-access]", connectorAccess],
  ["[data-webmcp-connector-purpose]", connectorPurpose],
  ["[data-webmcp-connector-plan]", connectorPlan],
]);

const publicRun = {
  run_id: "r-public-1",
  title: "Verify the shared WebMCP launch",
  status: "blocked",
  done_items: 1,
  total_items: 2,
  turn: 3,
  updated_at: "2026-09-01T12:00:00Z",
  progress: { done: 1, total: 2 },
  value_receipt: {
    independently_verified: 1,
    evidence_receipts: 2,
    model_families: 3,
    self_approved: 0,
  },
  checklist: [
    {
      id: "c1",
      description: "Confirm the browser tool contract",
      state: "done",
      owner: "codex",
      verified_by: "agy",
      evidence: "Runtime harness passed",
    },
    {
      id: "c2",
      description: "Capture final in-app browser evidence",
      state: "blocked",
      owner: "claude",
      verified_by: null,
      evidence: "Awaiting the deployed judge URL",
    },
  ],
  timeline: [],
  agents: [],
  provenance: { published_at: "2026-09-01T12:00:00Z" },
};

const fetchCalls = [];
async function fetchMock(url, options = {}) {
  fetchCalls.push({ options, url: String(url) });
  const parsed = new URL(url);
  let payload;
  if (parsed.pathname.endsWith("/runs") && parsed.searchParams.get("limit") === "12") {
    payload = { generated_at: "2026-09-01T12:00:00Z", runs: [publicRun] };
  } else if (parsed.pathname.endsWith(`/runs/${publicRun.run_id}`)) {
    payload = publicRun;
  } else {
    return { ok: false, status: 404, async json() { return {}; } };
  }
  return { ok: true, status: 200, async json() { return payload; } };
}

const tools = new Map();
const registrationOptions = new Map();
const document = {
  documentElement: { dataset: {} },
  visibilityState: "visible",
  modelContext: {
    async registerTool(tool, options = {}) {
      assert(!tools.has(tool.name), `duplicate tool: ${tool.name}`);
      tools.set(tool.name, tool);
      registrationOptions.set(tool.name, options);
    },
  },
  addEventListener() {},
  createDocumentFragment() { return node("#fragment"); },
  createElement(tag) { return node(tag); },
  createElementNS(namespaceURI, tag) {
    return Object.assign(node(tag), { namespaceURI });
  },
  createTextNode(text) { return { textContent: text }; },
  querySelector(selector) { return elements.get(selector) || null; },
  querySelectorAll(selector) {
    if (selector === "[data-webmcp-trace]") return [traceList];
    if (selector === "[data-webmcp-track]") return trackedFields;
    if (selector === "[data-webmcp-workflow]") return workflowTabs;
    if (selector === "[data-webmcp-panel]") return workflowPanels;
    return [];
  },
};

const windowListeners = new Map();
const window = {
  addEventListener(name, callback) {
    const callbacks = windowListeners.get(name) || [];
    callbacks.push(callback);
    windowListeners.set(name, callbacks);
  },
  dispatch(name) { (windowListeners.get(name) || []).forEach((callback) => callback()); },
  requestAnimationFrame(callback) { callback(); },
  scrollY: 0,
};
window.self = window;
window.top = window;

const context = vm.createContext({
  AbortController,
  DOMException,
  URL,
  console,
  document,
  fetch: fetchMock,
  setTimeout,
  window,
});
const app = fs.readFileSync(new URL("../site/app.js", import.meta.url), "utf8");
vm.runInContext(app, context, { filename: "site/app.js" });
await new Promise((resolve) => setTimeout(resolve, 0));

const expectedTools = [
  "rally_draft_job",
  "rally_inspect_public_run",
  "rally_list_public_runs",
  "rally_review_visible_draft",
  "rally_stage_challenge_song",
  "rally_stage_connector_plan",
  "rally_stage_insights_draft",
];
assert.deepEqual([...tools.keys()].sort(), expectedTools);
assert.equal(v2StatusTitle.textContent, "WebMCP connected · 7 tools");
assert.equal(document.documentElement.dataset.webmcp, "ready");

for (const [name, tool] of tools) {
  assert.equal(tool.inputSchema.type, "object", `${name} must use an object schema`);
  assert.equal(tool.inputSchema.additionalProperties, false, `${name} must close its schema`);
  assert(registrationOptions.get(name).signal instanceof AbortSignal, `${name} needs a lifecycle signal`);
  assert.equal(registrationOptions.get(name).signal.aborted, false);
}
assert.equal(tools.get("rally_review_visible_draft").annotations.untrustedContentHint, true);
assert.equal(tools.get("rally_list_public_runs").annotations.untrustedContentHint, true);
assert.equal(tools.get("rally_inspect_public_run").annotations.untrustedContentHint, true);

const executionSignal = () => new AbortController().signal;
const isTypeError = (error) => error?.name === "TypeError";
const assertNoExternalEffects = (result) => {
  for (const key of ["generated", "transmitted", "stored", "published", "connected"]) {
    assert.equal(result[key], false, `${result.workflow || result.status} unexpectedly set ${key}`);
  }
  assert.equal(result.human_confirmation_required, true);
  assert(JSON.stringify(result).length <= 1500, "WebMCP result exceeded the compact 1,500-character boundary");
};

const closedInputCases = new Map([
  ["rally_list_public_runs", { query: "blocked", limit: 2 }],
  ["rally_inspect_public_run", { run_id: publicRun.run_id }],
  ["rally_draft_job", { goal: "Prepare one bounded WebMCP launch outcome." }],
  ["rally_stage_challenge_song", { creative_direction: "Tell the story of visible human authority in one shared browser page." }],
  ["rally_stage_insights_draft", { angle: "Explain why shared visible state makes browser-agent work accountable." }],
  ["rally_stage_connector_plan", { profile: "n8n-agent9-insights", purpose: "Create one EmDash journal draft after exact human approval." }],
  ["rally_review_visible_draft", { workflow: "song" }],
]);
for (const [name, validInput] of closedInputCases) {
  await assert.rejects(
    tools.get(name).execute({ ...validInput, unexpected: true }, { signal: executionSignal() }),
    isTypeError,
    `${name} accepted an undeclared property`,
  );
}
assert.equal(fetchCalls.length, 0, "closed-input rejection reached the network");

const listed = await tools.get("rally_list_public_runs").execute(
  { query: "blocked", limit: 2 },
  { signal: executionSignal() },
);
assert.equal(listed.count, 1);
assert.equal(listed.runs[0].run_id, publicRun.run_id);
assert.match(listed.trust_notice, /untrusted public content/i);

const inspected = await tools.get("rally_inspect_public_run").execute(
  { run_id: publicRun.run_id },
  { signal: executionSignal() },
);
assert.equal(inspected.run.run_id, publicRun.run_id);
assert.equal(inspected.checklist.length, 2);
assert.equal(inspected.value_receipt.self_approved, 0);
assert.match(inspected.trust_notice, /untrusted public content/i);

const callsAfterPublicReads = fetchCalls.length;
const drafted = await tools.get("rally_draft_job").execute({
  company: "Agent9",
  team: "Rally for WebMCP",
  goal: "Prepare a human-reviewable launch plan without submitting or connecting anything.",
  trusted_systems: ["n8n", "cloudflare"],
  second_wind: true,
}, { signal: executionSignal() });
assert.equal(drafted.status, "drafted_not_submitted");
assert.equal(drafted.transmitted, false);
assert.equal(drafted.stored, false);
assert.equal(goal.value.length > 20, true);
assert.equal(fetchCalls.length, callsAfterPublicReads, "drafting a job caused a network request");

const stagedSong = await tools.get("rally_stage_challenge_song").execute({
  creative_direction: "Make the confirmation moment musical: Rally stages each move, the human edits the shared page, and only the human can commission the result.",
  hook: "Same page, clear hands — Rally the work, I make the call.",
  style: "west-coast-storytelling",
  duration_seconds: 72,
}, { signal: executionSignal() });
assert.equal(stagedSong.status, "staged_not_generated");
assert.equal(stagedSong.model, "lyria-3-pro-preview");
assertNoExternalEffects(stagedSong);
assert.match(songBrief.value, /named, structured tools/i);
assert.match(songBrief.value, /Agent9 Insights[\s\S]*allowlisted n8n(?: MCP)? workflow[\s\S]*EmDash/i);
assert.match(songBrief.value, /WebMCP is the shared browser surface[\s\S]*governed MCP[\s\S]*A2A/i);
assert.equal(goal.value, songBrief.value);
assert.equal(webMcpDialog.open, true, "song staging did not reveal the Rally browser-task dialog");
assert.equal(workflowTabs[0]["aria-selected"], "true");
assert.equal(workflowPanels[0].hidden, false);
assert.equal(workflowPanels[1].hidden, true);
assert.equal(fetchCalls.length, callsAfterPublicReads, "song staging caused a network request");

const reviewTool = tools.get("rally_review_visible_draft");
const reviewedDefaultSong = await reviewTool.execute(
  { workflow: "song" },
  { signal: executionSignal() },
);
assert.equal(reviewedDefaultSong.status, "ready_for_human_decision");
assert.equal(reviewedDefaultSong.ready, true);
assertNoExternalEffects(reviewedDefaultSong);

const stagedInsights = await tools.get("rally_stage_insights_draft").execute({
  angle: "Explain why a browser agent should prepare work in the exact page a person can inspect and revise.",
  audience: "builders",
  closing_thought: "Put the agent's controls where the person can see them.",
}, { signal: executionSignal() });
assert.equal(stagedInsights.status, "staged_not_published");
assert.equal(stagedInsights.future_destination, "EmDash journal draft");
assertNoExternalEffects(stagedInsights);
assert.match(insightsBody.value, /allowlisted n8n MCP workflow/i);
assert.match(insightsBody.value, /It does not publish/i);
assert.match(insightsBody.value, /not a general browser recorder/i);
assert.equal(workflowTabs[1]["aria-selected"], "true");
assert.equal(workflowPanels[1].hidden, false);
assert.equal(fetchCalls.length, callsAfterPublicReads, "Insights staging caused a network request");

const stagedConnector = await tools.get("rally_stage_connector_plan").execute({
  profile: "n8n-agent9-insights",
  access_mode: "read-with-approved-writes",
  purpose: "Create one EmDash journal draft for a human-approved Agent9 Insights article.",
}, { signal: executionSignal() });
assert.equal(stagedConnector.status, "staged_not_connected");
assert.equal(stagedConnector.profile, "n8n-agent9-insights");
assertNoExternalEffects(stagedConnector);
assert.match(connectorPlan.value, /never accepts an arbitrary URL/i);
assert.match(connectorPlan.value, /Every write needs explicit human approval/i);
assert.match(connectorPlan.value, /No discovery, authorization, network request, storage, or connection has started/i);
assert.equal(workflowTabs[2]["aria-selected"], "true");
assert.equal(workflowPanels[2].hidden, false);
assert.equal(fetchCalls.length, callsAfterPublicReads, "connector staging caused a network request");

await assert.rejects(
  tools.get("rally_stage_connector_plan").execute({
    profile: "cloudflare-observability",
    access_mode: "read-with-approved-writes",
    purpose: "Attempt an unsupported write through a read-only connector profile.",
  }, { signal: executionSignal() }),
  isTypeError,
);

const reviewedInsights = await reviewTool.execute(
  { workflow: "insights" },
  { signal: executionSignal() },
);
assert.equal(reviewedInsights.status, "ready_for_human_decision");
assert.equal(reviewedInsights.ready, true);
assertNoExternalEffects(reviewedInsights);

const reviewedConnector = await reviewTool.execute(
  { workflow: "connector" },
  { signal: executionSignal() },
);
assert.equal(reviewedConnector.status, "ready_for_human_decision");
assert.equal(reviewedConnector.ready, true);
assertNoExternalEffects(reviewedConnector);

const originalSongBrief = songBrief.value;
songBrief.value = originalSongBrief.replace(
  "WebMCP is the shared browser surface",
  "WebMCP is the browser surface",
);
songBrief.dispatch("change");
const reviewedEditedSong = await reviewTool.execute(
  { workflow: "song" },
  { signal: executionSignal() },
);
assert.equal(reviewedEditedSong.status, "needs_attention");
assert.equal(reviewedEditedSong.ready, false);
assert(reviewedEditedSong.failed_checks.includes("protocol_roles"));
assert.match(reviewedEditedSong.trust_notice, /untrusted data/i);
assert(reviewedEditedSong.collaboration_trace.some((entry) =>
  entry.actor === "human" && entry.action === "committed field revision"));
assertNoExternalEffects(reviewedEditedSong);
assert.equal(fetchCalls.length, callsAfterPublicReads, "review caused a network request");

songBrief.value = originalSongBrief;
songBrief.dispatch("change");
const reviewedSong = await reviewTool.execute(
  { workflow: "song" },
  { signal: executionSignal() },
);
assert.equal(reviewedSong.status, "ready_for_human_decision");
assert.equal(reviewedSong.ready, true);
assertNoExternalEffects(reviewedSong);

const abortedExecution = new AbortController();
abortedExecution.abort();
await assert.rejects(
  tools.get("rally_stage_insights_draft").execute(
    { angle: "This valid request must still stop when its browser execution is cancelled." },
    { signal: abortedExecution.signal },
  ),
  (error) => error?.name === "AbortError",
);
assert.equal(fetchCalls.length, callsAfterPublicReads, "aborted execution reached the network");

assert.equal(fetchCalls.length, 2);
for (const call of fetchCalls) {
  assert.equal(call.options.method, undefined, `unexpected write method for ${call.url}`);
  assert.equal(call.options.body, undefined, `unexpected request body for ${call.url}`);
  assert.match(call.url, /^https:\/\/public\.example\.test\/v1\/console\/runs/);
}

const lifecycleSignals = [...registrationOptions.values()].map((options) => options.signal);
assert(lifecycleSignals.every((signal) => signal === lifecycleSignals[0]));
window.dispatch("pagehide");
assert(lifecycleSignals.every((signal) => signal.aborted), "pagehide did not unregister the tools");

console.log(
  "Root WebMCP v2 contract passed: 7 tools, public reads, three staged workflows, " +
  "human edit + untrusted review, aborts, closed schemas, compact receipts, zero silent writes",
);
