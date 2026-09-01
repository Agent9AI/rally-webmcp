import assert from "node:assert/strict";
import { webcrypto } from "node:crypto";
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
  const attributes = new Map();
  const childrenBySelector = new Map();
  const listeners = new Map();
  return {
    tagName: tag.toUpperCase(),
    children: [],
    classList: classList(),
    dataset: {},
    disabled: false,
    hidden: false,
    open: false,
    required: false,
    style: { setProperty() {} },
    textContent: "",
    value: "",
    checked: false,
    append(...children) { this.children.push(...children); },
    insertBefore(child) { this.children.unshift(child); },
    replaceChildren(...children) { this.children = children; },
    remove() {},
    setAttribute(name, value) {
      attributes.set(name, String(value));
      this[name] = String(value);
    },
    getAttribute(name) { return attributes.get(name) ?? null; },
    removeAttribute(name) {
      attributes.delete(name);
      delete this[name];
    },
    addEventListener(name, callback) {
      const callbacks = listeners.get(name) || [];
      callbacks.push(callback);
      listeners.set(name, callbacks);
    },
    removeEventListener() {},
    async dispatch(name) {
      const event = {
        currentTarget: this,
        key: "",
        preventDefault() {},
        target: this,
        type: name,
      };
      for (const callback of listeners.get(name) || []) await callback(event);
    },
    closest() { return null; },
    focus() { this.focused = true; },
    load() {},
    matches() { return false; },
    play: async () => {},
    querySelector(selector) {
      if (!childrenBySelector.has(selector)) childrenBySelector.set(selector, node());
      return childrenBySelector.get(selector);
    },
    querySelectorAll() { return []; },
    reportValidity() { return true; },
    reset() { this.resetCalled = true; },
    scrollIntoView() {},
    showModal() { this.open = true; },
    close() { this.open = false; },
  };
};

const elements = new Map();
const elementFor = (selector) => {
  if (!elements.has(selector)) elements.set(selector, node());
  return elements.get(selector);
};

const registrations = new Map();
const documentListeners = new Map();
const appendedHeadNodes = [];
const document = {
  activeElement: null,
  documentElement: { dataset: {} },
  head: { append(child) { appendedHeadNodes.push(child); } },
  hidden: false,
  modelContext: {
    async registerTool(tool, options = {}) {
      registrations.set(tool.name, { options, tool });
    },
  },
  addEventListener(name, callback) {
    const callbacks = documentListeners.get(name) || [];
    callbacks.push(callback);
    documentListeners.set(name, callbacks);
  },
  createElement: (tag) => node(tag),
  createTextNode: (text) => ({ textContent: text }),
  querySelector: elementFor,
  querySelectorAll: () => [],
};

const location = {
  hash: "",
  hostname: "rally.agent9.dev",
  href: "https://rally.agent9.dev/v2/admin/",
  origin: "https://rally.agent9.dev",
  pathname: "/v2/admin/",
  search: "",
  assign() { throw new Error("auth runtime must not navigate"); },
  replace() { throw new Error("auth runtime must not replace the page"); },
};
const windowListeners = new Map();
const historyCalls = [];
const window = {
  RALLY_ADMIN_CONFIG: {
    apiBase: "https://rally.agent9.dev/api/control-plane",
    googleClientId: "1000134647783-test.apps.googleusercontent.com",
  },
  addEventListener(name, callback) {
    const callbacks = windowListeners.get(name) || [];
    callbacks.push(callback);
    windowListeners.set(name, callbacks);
  },
  clearTimeout,
  history: { replaceState(...args) { historyCalls.push(args); } },
  location,
  matchMedia: () => ({ matches: false }),
  requestAnimationFrame: (callback) => callback(),
  setInterval: () => 1,
  setTimeout,
};
window.self = window;
window.top = window;

const calls = [];
const validToken = `ml1.${"a".repeat(43)}.1999999999.${"b".repeat(24)}.${"c".repeat(43)}`;
const loginCode = "d".repeat(43);
const sessionToken = "e".repeat(43);

async function fetchMock(input, options = {}) {
  const url = new URL(String(input), location.origin);
  const body = typeof options.body === "string" ? JSON.parse(options.body) : null;
  calls.push({ body, headers: new Headers(options.headers || {}), method: options.method || "GET", url });
  if (url.pathname.endsWith("/v1/auth/magic-link/request")) {
    return Response.json({ accepted: true }, { status: 202 });
  }
  if (url.pathname.endsWith("/v1/auth/magic-link/consume")) {
    if (body?.token !== validToken) {
      return Response.json({ detail: "magic link is invalid or expired" }, { status: 401 });
    }
    return Response.json({ login_code: loginCode });
  }
  if (url.pathname.endsWith("/v1/auth/exchange")) {
    assert.deepEqual(body, { code: loginCode });
    return Response.json({
      account: {
        email: "imterryim@gmail.com",
        hosted_domain: null,
        name: "Terry",
        picture: null,
        uid: "email:test",
        workspace_id: "agent9-rally",
      },
      expires_in: 1800,
      session_token: sessionToken,
    });
  }
  if (url.pathname.endsWith("/v1/auth/logout")) return Response.json({ revoked: true });
  if (url.pathname === "/v1/workspace/capabilities") {
    return Response.json({
      schema_version: 1,
      research_profiles: ["standard", "ruflo"],
      ruflo: { available: true, version: "3.38.20", scope: "run_only" },
    });
  }
  if (url.pathname === "/v1/workspace/jobs" && (options.method || "GET") === "POST") {
    return Response.json({
      run_id: "r-20260901-d3042d73-9378-4516-8e63-5960d47db896",
      status: "accepted",
      accepted_at: "2026-09-01T23:15:00Z",
    }, { status: 202 });
  }
  if (url.pathname === "/v1/workspace/runs") return Response.json({ runs: [] });
  if (url.pathname.startsWith("/v1/workspace/runs/")) {
    return Response.json({
      run_id: url.pathname.split("/").pop(), title: "Deep WebMCP research",
      status: "queued", progress: { done: 0, total: 0 }, checklist: [],
      agents: [], artifacts: [], timeline: [],
    });
  }
  if (url.pathname.endsWith("/v1/email-provider-options")) {
    return Response.json({ pilot_address: "", providers: [], trial_domain: "updates.agent9.dev" });
  }
  if (url.pathname.endsWith("/v1/teammates")) return Response.json({ teammates: [] });
  if (url.pathname.endsWith("/v1/connectors")) return Response.json({ connectors: [] });
  if (url.pathname.endsWith("/v1/connections")) return Response.json({ connections: [] });
  return Response.json({ detail: "not found" }, { status: 404 });
}

const deniedStorage = new Proxy({}, {
  get() { throw new Error("browser storage must not be used for authentication"); },
});
elementFor("[data-dashboard]").hidden = true;
elementFor("[data-magic-key-divider]").hidden = true;
elementFor("[data-magic-key-form]").hidden = true;
const context = vm.createContext({
  AbortController,
  Blob,
  CSS: { escape: (value) => String(value) },
  DOMException,
  Date,
  Error,
  Headers,
  HTMLMediaElement: { HAVE_FUTURE_DATA: 3 },
  Intl,
  JSON,
  Map,
  Math,
  Number,
  Object,
  Promise,
  Response,
  Set,
  String,
  TypeError,
  URL,
  URLSearchParams,
  Uint32Array,
  console,
  crypto: webcrypto,
  document,
  fetch: fetchMock,
  localStorage: deniedStorage,
  sessionStorage: deniedStorage,
  setTimeout,
  window,
});

const app = fs.readFileSync(new URL("../site/admin/app.js", import.meta.url), "utf8");
vm.runInContext(app, context, { filename: "site/admin/app.js" });
await new Promise((resolve) => setTimeout(resolve, 0));

const signedOut = elementFor("[data-signed-out]");
const dashboard = elementFor("[data-dashboard]");
const emailForm = elementFor("[data-magic-link-form]");
const emailInput = elementFor("[data-magic-link-email]");
const keyForm = elementFor("[data-magic-key-form]");
const keyInput = elementFor("[data-magic-key-input]");
const keyStatus = elementFor("[data-magic-key-status]");
const signOut = elementFor("[data-sign-out]");

assert.equal(elementFor("[data-google-button]").hidden, true);
assert.equal(emailForm.hidden, false);
assert.equal(keyForm.hidden, false);
assert.equal(registrations.size, 0, "tools must not register before authentication");
assert.equal(appendedHeadNodes.length, 0, "v2 must not load the blocked Google GIS script");

emailInput.value = "imterryim@gmail.com";
await emailForm.dispatch("submit");
const requestCall = calls.find((call) => call.url.pathname.endsWith("/magic-link/request"));
assert.deepEqual(requestCall.body, {
  email: "imterryim@gmail.com",
  return_path: "/v2/admin/",
});
assert.equal(emailInput.value, "");
assert.equal(keyInput.focused, true);

keyInput.value = "expired-key";
await keyForm.dispatch("submit");
assert.equal(keyInput.value, "", "rejected keys must be cleared before the request finishes");
assert.match(keyStatus.textContent, /expired|already used/i);
assert.equal(dashboard.hidden, true);
assert.equal(registrations.size, 0, "rejected keys must not expose workspace tools");

keyInput.value = validToken;
await keyForm.dispatch("submit");
await new Promise((resolve) => setTimeout(resolve, 0));

assert.equal(keyInput.value, "", "the bearer key must be cleared immediately");
assert.equal(signedOut.hidden, true);
assert.equal(dashboard.hidden, false);
assert.equal(registrations.size, 5, "tools register only after session exchange succeeds");
assert.equal(document.documentElement.dataset.webmcpWorkspace, "ready");
assert.equal(location.pathname, "/v2/admin/");
assert.equal(historyCalls.length, 0);

const consumeCalls = calls.filter((call) => call.url.pathname.endsWith("/magic-link/consume"));
assert.equal(consumeCalls.length, 2);
assert.deepEqual(consumeCalls[1].body, { token: validToken });
for (const call of calls.filter((call) => !call.url.pathname.endsWith("/magic-link/consume"))) {
  assert(!JSON.stringify(call.body).includes(validToken), "key leaked outside the consume request");
  assert(!call.url.href.includes(validToken), "key leaked into a URL");
}

const prepareResearch = registrations.get("rally_prepare_job").tool;
const startVisible = registrations.get("rally_start_visible_job").tool;
const prepared = await prepareResearch.execute({
  title: "Deep WebMCP research",
  goal: "Reconcile primary sources and produce an independently verified competition brief.",
  research_mode: "ruflo",
  second_wind: true,
});
assert.equal(prepared.research_mode, "ruflo");
assert.equal(elementFor("[data-research-reserve]").dataset.state, "armed");
assert.equal(elementFor("[data-research-arm]").getAttribute("aria-pressed"), "true");
assert.match(elementFor("[data-composer-research]").textContent, /Ruflo research/);

const started = await startVisible.execute({});
assert.equal(started.research_mode, "ruflo");
const jobCall = calls.find((call) => call.url.pathname === "/v1/workspace/jobs");
assert.equal(jobCall.body.research_mode, "ruflo");
assert.equal(elementFor("[data-research-reserve]").dataset.state, "sealed");
assert.equal(elementFor("[data-research-arm]").getAttribute("aria-pressed"), "false");
assert.match(elementFor("[data-job-receipt-detail]").textContent, /Ruflo armed for this run/);

await signOut.dispatch("click");
assert.equal(signedOut.hidden, false);
assert.equal(dashboard.hidden, true);
assert.equal(document.documentElement.dataset.webmcpWorkspace, undefined);
for (const { options } of registrations.values()) assert.equal(options.signal.aborted, true);

console.log("Admin auth runtime passed: v2 email request, paste-key exchange, tool gate, and logout");
