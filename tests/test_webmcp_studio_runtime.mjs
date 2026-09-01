import assert from "node:assert/strict";
import fs from "node:fs";
import vm from "node:vm";

function fakeClassList() {
  const values = new Set();
  return {
    add: (...names) => names.forEach((name) => values.add(name)),
    contains: (name) => values.has(name),
    toggle(name, force) {
      const next = force === undefined ? !values.has(name) : Boolean(force);
      if (next) values.add(name);
      else values.delete(name);
      return next;
    },
  };
}

function fakeNode(tag = "div", value = "") {
  const listeners = new Map();
  return {
    tag,
    value,
    textContent: "",
    className: "",
    classList: fakeClassList(),
    dataset: {},
    children: [],
    hidden: false,
    disabled: false,
    tabIndex: 0,
    addEventListener(name, callback) {
      const callbacks = listeners.get(name) || [];
      callbacks.push(callback);
      listeners.set(name, callbacks);
    },
    append(...children) { this.children.push(...children); },
    replaceChildren(...children) { this.children = children; },
    setAttribute(name, value) { this[name] = String(value); },
    removeAttribute(name) { delete this[name]; },
    focus() {},
    querySelector(selector) { return this.selectorMap?.get(selector) || null; },
  };
}

function fakeReceipt() {
  const receipt = fakeNode("section");
  receipt.selectorMap = new Map([
    ["[data-receipt-status]", fakeNode("b")],
    ["[data-receipt-summary]", fakeNode("p")],
    [".receipt-status > span", fakeNode("span")],
    ["[data-receipt-checks]", fakeNode("ul")],
  ]);
  return receipt;
}

const songAngle = fakeNode("textarea", "A human and browser agent build one visible WebMCP launch together, with the person retaining the final decision.");
const songHook = fakeNode("input", "Same page, clear hands — Rally the work, I make the call.");
const songDuration = fakeNode("select", "72");
const songBrief = fakeNode("textarea", "Not staged");

const insightsAngle = fakeNode("textarea", "Why shared visible state makes browser-agent collaboration more useful and accountable than pixel guessing.");
const insightsAudience = fakeNode("select", "builders");
const insightsCta = fakeNode("input", "Put the agent's controls where the person can see them.");
const insightsTitle = fakeNode("input", "Not staged");
const insightsDeck = fakeNode("textarea", "Not staged");
const insightsBody = fakeNode("textarea", "Not staged");

const connectorProfile = fakeNode("select", "n8n-agent9-insights");
const connectorMode = fakeNode("select", "read-with-approved-writes");
const connectorPurpose = fakeNode("textarea", "Create one human-approved EmDash journal draft through an exact allowlisted n8n workflow.");
const connectorPlan = fakeNode("textarea", "Not staged");

const trail = fakeNode("ol");
trail.scrollHeight = 100;
trail.scrollTop = 0;
const revision = fakeNode("b");
const runtime = fakeNode("div");
runtime.selectorMap = new Map([["b", fakeNode("b")], ["small", fakeNode("small")]]);

const receipts = {
  song: fakeReceipt(),
  insights: fakeReceipt(),
  connector: fakeReceipt(),
};

const tabs = ["song", "insights", "connector"].map((workflow) => {
  const tab = fakeNode("button");
  tab.dataset.tab = workflow;
  return tab;
});
const panels = ["song", "insights", "connector"].map((workflow) => {
  const panel = fakeNode("section");
  panel.dataset.panel = workflow;
  return panel;
});

const selectorMap = new Map([
  ["[data-song-angle]", songAngle],
  ["[data-song-hook]", songHook],
  ["[data-song-duration]", songDuration],
  ["[data-song-brief]", songBrief],
  ["[data-insights-angle]", insightsAngle],
  ["[data-insights-audience]", insightsAudience],
  ["[data-insights-cta]", insightsCta],
  ["[data-insights-title]", insightsTitle],
  ["[data-insights-deck]", insightsDeck],
  ["[data-insights-body]", insightsBody],
  ["[data-connector-profile]", connectorProfile],
  ["[data-connector-mode]", connectorMode],
  ["[data-connector-purpose]", connectorPurpose],
  ["[data-connector-plan]", connectorPlan],
  ["[data-collaboration-trail]", trail],
  ["[data-revision-count]", revision],
  ["[data-webmcp-status]", runtime],
  ["[data-receipt=\"song\"]", receipts.song],
  ["[data-receipt=\"insights\"]", receipts.insights],
  ["[data-receipt=\"connector\"]", receipts.connector],
]);

const registered = new Map();
const document = {
  documentElement: { dataset: {} },
  modelContext: {
    async registerTool(tool) {
      assert(!registered.has(tool.name), `duplicate tool: ${tool.name}`);
      registered.set(tool.name, tool);
    },
  },
  createElement: (tag) => fakeNode(tag),
  createTextNode: (text) => ({ textContent: text }),
  querySelector: (selector) => selectorMap.get(selector) || null,
  querySelectorAll(selector) {
    if (selector === "[data-tab]") return tabs;
    if (selector === "[data-panel]") return panels;
    return [];
  },
};

const window = {
  addEventListener() {},
  clearTimeout,
  setTimeout,
};
window.top = window;
window.self = window;

const context = vm.createContext({
  AbortController,
  DOMException,
  Object,
  Promise,
  TypeError,
  console,
  document,
  setTimeout,
  window,
});
const source = fs.readFileSync(new URL("../site/webmcp/app.js", import.meta.url), "utf8");
vm.runInContext(source, context, { filename: "site/webmcp/app.js" });
await new Promise((resolve) => setTimeout(resolve, 0));

assert.deepEqual([...registered.keys()].sort(), [
  "rally_webmcp_review_visible_draft",
  "rally_webmcp_stage_connector",
  "rally_webmcp_stage_insights",
  "rally_webmcp_stage_song",
]);
for (const tool of registered.values()) {
  assert.equal(tool.inputSchema.type, "object");
  assert.equal(tool.inputSchema.additionalProperties, false);
  assert.equal(tool.annotations.readOnlyHint, false);
  assert(tool.description.length <= 500, `${tool.name} description is too long`);
}
assert.equal(registered.get("rally_webmcp_review_visible_draft").annotations.untrustedContentHint, true);

const signal = new AbortController().signal;
const stageSong = registered.get("rally_webmcp_stage_song");
const song = await stageSong.execute({
  story_angle: songAngle.value,
  hook: songHook.value,
  duration_seconds: 72,
}, { signal });
assert.equal(song.status, "staged_for_human_review");
assert.equal(song.generated, false);
assert.equal(song.transmitted, false);
assert.match(songBrief.value, /named, structured JavaScript tools/i);
assert.match(songBrief.value, /allowlisted n8n MCP workflow/i);
assert.match(songBrief.value, /A2A handles bounded outside-agent handoffs/i);
assert.doesNotMatch(songBrief.value, /Tupac|Coolio/i);
assert(JSON.stringify(song).length <= 1500);

const review = registered.get("rally_webmcp_review_visible_draft");
const songReview = await review.execute({ workflow: "song" }, { signal });
assert.equal(songReview.status, "ready_for_human_decision");
assert.equal(songReview.ready, true);
assert.equal(songReview.generated, false);

songBrief.value = songBrief.value.replace("server-side MCP gateway", "browser magic");
const editedSong = await review.execute({ workflow: "song" }, { signal });
assert.equal(editedSong.status, "needs_attention");
assert(editedSong.failed_checks.includes("protocol_roles"));

const insights = await registered.get("rally_webmcp_stage_insights").execute({
  angle: insightsAngle.value,
  audience: "builders",
  closing_thought: insightsCta.value,
}, { signal });
assert.equal(insights.published, false);
assert.equal(insights.transmitted, false);
assert.match(insightsBody.value, /allowlisted n8n MCP workflow/i);
assert.match(insightsBody.value, /EmDash.*journal.*Cloudflare Workers \+ D1/is);
assert.doesNotMatch(insightsBody.value, /—/);
const insightsReview = await review.execute({ workflow: "insights" }, { signal });
assert.equal(insightsReview.ready, true);

const connector = await registered.get("rally_webmcp_stage_connector").execute({
  profile: "n8n-agent9-insights",
  access_mode: "read-with-approved-writes",
  purpose: connectorPurpose.value,
}, { signal });
assert.equal(connector.connected, false);
assert.equal(connector.transmitted, false);
assert.match(connectorPlan.value, /never accepts an arbitrary URL/i);
assert.match(connectorPlan.value, /Every write needs explicit human approval/i);
const connectorReview = await review.execute({ workflow: "connector" }, { signal });
assert.equal(connectorReview.ready, true);

await assert.rejects(
  stageSong.execute({ story_angle: songAngle.value, unexpected: true }, { signal }),
  /Unsupported tool input/,
);
const aborted = new AbortController();
aborted.abort();
await assert.rejects(
  stageSong.execute({ story_angle: songAngle.value }, { signal: aborted.signal }),
  (error) => error?.name === "AbortError",
);

assert.equal(typeof context.fetch, "undefined", "studio unexpectedly gained a network primitive");
console.log("Dedicated WebMCP studio passed: song + Insights + connector + untrusted review, zero network writes");
