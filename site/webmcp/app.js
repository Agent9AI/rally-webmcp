(() => {
  "use strict";

  const $ = (selector, root = document) => root.querySelector(selector);
  const $$ = (selector, root = document) => [...root.querySelectorAll(selector)];

  const state = {
    revision: 0,
    trail: [],
    activeWorkflow: "song",
    staged: { song: false, insights: false, connector: false },
    suppressFieldEvents: false,
    toastTimer: 0,
  };

  const WORKFLOWS = ["song", "insights", "connector"];
  const AUDIENCES = ["builders", "operators", "security-leaders"];
  const ACCESS_MODES = ["read-only", "read-with-approved-writes"];
  const CONNECTOR_PROFILES = {
    "n8n-agent9-insights": {
      label: "n8n · Agent9 Insights workflow",
      transport: "Allowlisted remote MCP profile; server credentials stay in Rally's control plane",
      tools: "get_workflow_details (read), execute_workflow (one-time human approval)",
      writeBoundary: "Execute one allowlisted workflow that creates an EmDash journal draft; publishing is excluded",
      allowedModes: ["read-only", "read-with-approved-writes"],
    },
    "cloudflare-operator": {
      label: "Cloudflare · observability",
      transport: "Allowlisted Cloudflare Observability MCP profile through Rally's server-side gateway",
      tools: "query_worker_observability, observability_keys, observability_values (read)",
      writeBoundary: "No write tool is enabled; deployment remains a separate operator workflow",
      allowedModes: ["read-only"],
    },
    "github-repository": {
      label: "GitHub · repository reads",
      transport: "Allowlisted GitHub MCP profile through Rally's server-side gateway",
      tools: "Repository, file, issue, pull request, commit, release, tag, and code search reads",
      writeBoundary: "No create, update, merge, release, settings, secret, or destructive tool is enabled",
      allowedModes: ["read-only"],
    },
    "google-workspace": {
      label: "Google Workspace · knowledge gateway",
      transport: "Allowlisted Workspace MCP profile through Rally's server-side gateway",
      tools: "Pinned read-minimal tools for Gmail, Drive, Docs, Sheets, Slides, Calendar, Chat, and People",
      writeBoundary: "No send, share, calendar mutation, or document-write tool is enabled",
      allowedModes: ["read-only"],
    },
  };

  function noExternalEffects() {
    return {
      generated: false,
      transmitted: false,
      stored: false,
      published: false,
      connected: false,
    };
  }

  function checkSignal(signal) {
    if (!signal?.aborted) return;
    throw new DOMException("Tool execution was cancelled", "AbortError");
  }

  function closedInput(input, allowed) {
    if (!input || typeof input !== "object" || Array.isArray(input)) {
      throw new TypeError("Tool input must be an object");
    }
    const extra = Object.keys(input).find((key) => !allowed.includes(key));
    if (extra) throw new TypeError(`Unsupported tool input: ${extra}`);
    return input;
  }

  function boundedText(value, name, minimum, maximum, optional = false) {
    if (value === undefined || value === null) {
      if (optional) return "";
      throw new TypeError(`${name} is required`);
    }
    if (typeof value !== "string") throw new TypeError(`${name} must be a string`);
    const text = value.trim();
    if (!text && optional) return "";
    if (text.length < minimum || text.length > maximum) {
      throw new TypeError(`${name} must be ${minimum}–${maximum} characters`);
    }
    return text;
  }

  function boundedInteger(value, name, minimum, maximum) {
    if (!Number.isInteger(value) || value < minimum || value > maximum) {
      throw new TypeError(`${name} must be an integer from ${minimum} to ${maximum}`);
    }
    return value;
  }

  function enumValue(value, name, allowed) {
    if (typeof value !== "string" || !allowed.includes(value)) {
      throw new TypeError(`${name} must be one of: ${allowed.join(", ")}`);
    }
    return value;
  }

  function setValues(updates) {
    state.suppressFieldEvents = true;
    try {
      Object.entries(updates).forEach(([selector, value]) => {
        const field = $(selector);
        if (field) field.value = String(value);
      });
    } finally {
      state.suppressFieldEvents = false;
    }
  }

  function setActiveWorkflow(workflow) {
    if (!WORKFLOWS.includes(workflow)) return;
    state.activeWorkflow = workflow;
    $$('[data-tab]').forEach((tab) => {
      const active = tab.dataset.tab === workflow;
      tab.classList.toggle("is-active", active);
      tab.setAttribute("aria-selected", String(active));
      tab.tabIndex = active ? 0 : -1;
    });
    $$('[data-panel]').forEach((panel) => {
      panel.hidden = panel.dataset.panel !== workflow;
    });
  }

  function renderTrail() {
    const list = $("[data-collaboration-trail]");
    const counter = $("[data-revision-count]");
    if (counter) counter.textContent = `v${state.revision}`;
    if (!list) return;

    if (!state.trail.length) {
      const item = document.createElement("li");
      item.className = "trail-empty";
      const icon = document.createElement("span");
      icon.setAttribute("aria-hidden", "true");
      icon.textContent = "↔";
      const copy = document.createElement("p");
      const title = document.createElement("b");
      title.textContent = "Ready for a shared turn";
      const detail = document.createElement("small");
      detail.textContent = "Stage a showcase or edit a field.";
      copy.append(title, detail);
      item.append(icon, copy);
      list.replaceChildren(item);
      return;
    }

    const events = state.trail.map((entry) => {
      const item = document.createElement("li");
      item.className = `trail-event is-${entry.actor}`;
      const avatar = document.createElement("span");
      avatar.className = "trail-avatar";
      avatar.setAttribute("aria-hidden", "true");
      avatar.textContent = entry.actor === "agent" ? "A" : entry.actor === "human" ? "H" : "R";
      const copy = document.createElement("p");
      const title = document.createElement("b");
      title.textContent = entry.action;
      const detail = document.createElement("small");
      detail.textContent = entry.summary;
      const revision = document.createElement("span");
      revision.className = "trail-revision";
      revision.textContent = `v${entry.revision}`;
      copy.append(title, detail);
      item.append(avatar, copy, revision);
      return item;
    });
    list.replaceChildren(...events);
    list.scrollTop = list.scrollHeight;
  }

  function recordTurn(actor, action, summary) {
    state.revision += 1;
    state.trail.push({
      revision: state.revision,
      actor,
      action: String(action).slice(0, 72),
      summary: String(summary).slice(0, 180),
    });
    if (state.trail.length > 30) state.trail.shift();
    renderTrail();
  }

  function renderReceipt(workflow, { tone, status, summary, checks = [] }) {
    const receipt = $(`[data-receipt="${workflow}"]`);
    if (!receipt) return;
    receipt.dataset.tone = tone;
    const statusNode = $("[data-receipt-status]", receipt);
    const summaryNode = $("[data-receipt-summary]", receipt);
    const statusIcon = $(".receipt-status > span", receipt);
    const checkList = $("[data-receipt-checks]", receipt);
    if (statusNode) statusNode.textContent = status;
    if (summaryNode) summaryNode.textContent = summary;
    if (statusIcon) statusIcon.textContent = tone === "ready" ? "✓" : tone === "attention" ? "!" : tone === "staged" ? "↔" : "○";
    if (checkList) {
      const items = checks.map((check) => {
        const item = document.createElement("li");
        const icon = document.createElement("span");
        icon.textContent = check.passed ? "✓" : "○";
        item.append(icon, document.createTextNode(check.label));
        return item;
      });
      checkList.replaceChildren(...items);
    }
  }

  function announce(message, error = false) {
    const toast = $("[data-toast]");
    if (!toast) return;
    window.clearTimeout(state.toastTimer);
    toast.textContent = message;
    toast.classList.toggle("is-error", error);
    toast.hidden = false;
    state.toastTimer = window.setTimeout(() => { toast.hidden = true; }, 3600);
  }

  function songBrief({ storyAngle, hook, durationSeconds }) {
    return [
      "RALLY FOR WEBMCP CHALLENGE — ORIGINAL LYRIA COMMISSION",
      "",
      "OUTCOME",
      "Create one fully original song for the Rally for WebMCP demo. Every lyric must explain WebMCP or show how Rally uses it; this is not a generic AI anthem.",
      "",
      "MODEL + FORMAT",
      "- Google Lyria 3 Pro preview (`lyria-3-pro-preview`) through Rally's separately authorized media gateway.",
      `- ${durationSeconds} seconds, clean ending, playable MP3, generation receipt, and full-file independent listening review.`,
      "",
      "MUSICAL DIRECTION",
      "- Smooth West Coast storytelling hip-hop around 88 BPM: laid-back drums, rounded bass, warm electric piano, muted guitar, a subtle high synth, vivid narrative verses, and a soulful original hook.",
      "- Capture the warmth and clarity of classic narrative rap without naming, copying, or imitating any artist, recording, melody, flow, or lyric.",
      `- Story angle: ${storyAngle}`,
      `- Original hook seed: ${hook || "Write a short, memorable hook about one shared page and a human-held decision."}`,
      "",
      "LYRICAL STORY MAP",
      "1. Open with the old problem: a browser agent guessing at pixels and a person chasing opaque actions.",
      "2. Define WebMCP plainly: a website exposes named, structured JavaScript tools so the browser agent can use the page's real functionality.",
      "3. Show this Rally studio staging the Lyria brief, an Agent9 Insights article, and a governed connector plan in visible, human-editable state.",
      "4. Keep the protocol roles exact: WebMCP is the shared page surface; Rally's server-side MCP gateway connects approved systems; A2A handles bounded outside-agent handoffs; Rally keeps authority and proof.",
      "5. Tell the publishing route accurately: after explicit human approval, Rally may use one allowlisted n8n MCP workflow to create an EmDash `journal` draft on agent9.dev's Cloudflare Workers + D1 site. It does not silently publish.",
      "6. Make the boundary the emotional turn: the agent can inspect, stage, and review; the person decides whether anything is generated, transmitted, connected, stored, or published.",
      "",
      "ACCEPTANCE GATE",
      "- Preserve available Lyria provenance, record the exact model ID, duration, MIME type, byte count, SHA-256, and timestamp.",
      "- A worker from a different model family must listen to the complete MP3. The generator cannot approve its own work.",
      "- Do not generate, store, transmit, deliver, or publish until the person explicitly commissions the reviewed brief.",
    ].join("\n");
  }

  function insightsDraft({ angle, audience, closingThought }) {
    const audienceLabel = {
      builders: "AI product builders",
      operators: "business operators",
      "security-leaders": "security and governance leaders",
    }[audience];
    const title = "The page is the protocol: building accountable browser agents with WebMCP";
    const deck = "Rally turns a website into a shared launch room where an agent can prepare structured work and the person can inspect, revise, and approve the same visible state.";
    const body = [
      "WebMCP makes a simple but important change to browser-agent collaboration: the website can expose named, structured JavaScript tools instead of forcing an agent to infer every action from pixels. The page's own functionality becomes a bounded interface, and the person remains seated beside it.",
      "",
      `For ${audienceLabel}, the practical question is this: ${angle}`,
      "",
      "Rally uses WebMCP as a shared page surface. In this studio, a browser agent can stage a fully original Lyria song brief, prepare this Agent9 Insights article, or propose a governed connector admission plan. Each action changes fields the person can see. The person can rewrite those fields, and Rally can review the exact visible revision as untrusted content. The collaboration trail stores only semantic turns on this page, not browsing history, screenshots, other tabs, credentials, or raw keystrokes.",
      "",
      "That page boundary matters because WebMCP is not a remote MCP-server connector. Rally's server-side gateway separately connects approved MCP servers and keeps credentials, transport admission, capability discovery, schema fingerprints, tool allowlists, payload ceilings, and write approvals off the page. A2A serves another boundary: bounded task and artifact handoffs with outside agent systems. Rally holds identity, authority, recovery, evidence, and independent verification across all three.",
      "",
      "The publishing route demonstrates the distinction. First, WebMCP stages this human-editable article locally. Nothing is transmitted. After a person explicitly approves the final revision, Rally may invoke exactly one allowlisted n8n MCP workflow. That workflow sends a bounded payload to EmDash, which creates a `journal` draft for Agent9 Insights on agent9.dev's Cloudflare Workers + D1 site. It does not publish. Publication remains a separate human decision with its own receipt.",
      "",
      "This is what accountable agent speed looks like: fast preparation, visible revision, narrow authority, and proof at the boundary where work can finally leave the page.",
      "",
      closingThought || "Put the agent's controls where the person can see them.",
    ].join("\n");
    return { title, deck, body };
  }

  function connectorPlan({ profileKey, accessMode, purpose }) {
    const profile = CONNECTOR_PROFILES[profileKey];
    return [
      "RALLY MCP CONNECTOR ADMISSION PLAN — REVIEW ONLY",
      "",
      `PROFILE: ${profile.label}`,
      `PURPOSE: ${purpose}`,
      `PROPOSED ACCESS: ${accessMode === "read-only" ? "read only" : "reads plus individually approved writes"}`,
      "",
      "PROTOCOL BOUNDARY",
      "- WebMCP is the shared page surface where a browser agent and a person stage and revise this proposal.",
      "- Rally's server-side gateway connects approved MCP servers. This page never accepts an arbitrary URL, OAuth grant, credential, token, or server response.",
      "- A2A is reserved for bounded outside-agent task and artifact handoffs; it is not the connector transport.",
      "",
      "FIXED PROFILE",
      `- Transport: ${profile.transport}.`,
      `- Candidate tools: ${profile.tools}.`,
      `- Write boundary: ${profile.writeBoundary}.`,
      "",
      "ADMISSION GATES",
      "1. Match an operator-maintained profile; reject arbitrary endpoints and redirects.",
      "2. Require HTTPS, private-network admission checks, and exact OAuth origin binding.",
      "3. Bound capability discovery by time, response size, and tool count.",
      "4. Record a schema fingerprint and require review when any tool schema changes.",
      "5. Apply an exact per-tool allowlist, payload ceiling, timeout, and redaction policy.",
      "6. Keep reads and writes distinct. Every write needs explicit human approval for the visible revision.",
      "7. Return a redacted receipt; never expose credentials, cookies, tokens, or raw private connector data.",
      "",
      "STAGED RESULT",
      "No discovery, authorization, network request, storage, or connection has started. The current state is a human-editable proposal only.",
    ].join("\n");
  }

  async function stageSong(input, options = {}) {
    input = closedInput(input, ["story_angle", "hook", "duration_seconds"]);
    checkSignal(options.signal);
    const storyAngle = boundedText(input.story_angle, "story_angle", 20, 360);
    const hook = boundedText(input.hook, "hook", 0, 180, true);
    const durationSeconds = boundedInteger(input.duration_seconds ?? 72, "duration_seconds", 45, 90);
    await Promise.resolve();
    checkSignal(options.signal);

    const brief = songBrief({ storyAngle, hook, durationSeconds });
    setValues({
      "[data-song-angle]": storyAngle,
      "[data-song-hook]": hook,
      "[data-song-duration]": durationSeconds,
      "[data-song-brief]": brief,
    });
    state.staged.song = true;
    setActiveWorkflow("song");
    recordTurn(
      options.source === "human" ? "human" : "agent",
      options.source === "human" ? "Staged song from page controls" : "Tool · rally_webmcp_stage_song",
      `${durationSeconds}s Lyria brief staged in visible page state; no audio generated`,
    );
    renderReceipt("song", {
      tone: "staged",
      status: "Staged for human review",
      summary: "The complete commission is visible and editable. Lyria has not been called.",
      checks: [
        { passed: true, label: "Originality boundary" },
        { passed: true, label: "Exact Lyria model" },
        { passed: false, label: "Human review pending" },
      ],
    });
    return {
      status: "staged_for_human_review",
      workflow: "song",
      page_revision: state.revision,
      model: "lyria-3-pro-preview",
      human_can_edit: true,
      human_approval_required: true,
      ...noExternalEffects(),
      next_step: "Edit the visible brief, then call rally_webmcp_review_visible_draft with workflow song.",
    };
  }

  async function stageInsights(input, options = {}) {
    input = closedInput(input, ["angle", "audience", "closing_thought"]);
    checkSignal(options.signal);
    const angle = boundedText(input.angle, "angle", 20, 360);
    const audience = enumValue(input.audience ?? "builders", "audience", AUDIENCES);
    const closingThought = boundedText(input.closing_thought, "closing_thought", 0, 180, true);
    await Promise.resolve();
    checkSignal(options.signal);

    const draft = insightsDraft({ angle, audience, closingThought });
    setValues({
      "[data-insights-angle]": angle,
      "[data-insights-audience]": audience,
      "[data-insights-cta]": closingThought,
      "[data-insights-title]": draft.title,
      "[data-insights-deck]": draft.deck,
      "[data-insights-body]": draft.body,
    });
    state.staged.insights = true;
    setActiveWorkflow("insights");
    recordTurn(
      options.source === "human" ? "human" : "agent",
      options.source === "human" ? "Staged article from page controls" : "Tool · rally_webmcp_stage_insights",
      "Agent9 Insights article staged locally; n8n, EmDash, Workers, and D1 were not called",
    );
    renderReceipt("insights", {
      tone: "staged",
      status: "Draft staged on this page",
      summary: "The article is editable. Its approved future route stops at an EmDash journal draft.",
      checks: [
        { passed: true, label: "Route disclosed" },
        { passed: true, label: "Draft-only boundary" },
        { passed: false, label: "Human review pending" },
      ],
    });
    return {
      status: "staged_for_human_review",
      workflow: "insights",
      page_revision: state.revision,
      destination_if_later_approved: "EmDash journal draft",
      human_can_edit: true,
      human_approval_required: true,
      ...noExternalEffects(),
      next_step: "Edit the visible article, then review workflow insights. No publish action exists here.",
    };
  }

  async function stageConnector(input, options = {}) {
    input = closedInput(input, ["profile", "access_mode", "purpose"]);
    checkSignal(options.signal);
    const profileKey = enumValue(input.profile, "profile", Object.keys(CONNECTOR_PROFILES));
    const accessMode = enumValue(input.access_mode ?? "read-only", "access_mode", ACCESS_MODES);
    const purpose = boundedText(input.purpose, "purpose", 20, 280);
    if (!CONNECTOR_PROFILES[profileKey].allowedModes.includes(accessMode)) {
      throw new TypeError(`${profileKey} supports read-only onboarding in Rally's current safe preset`);
    }
    await Promise.resolve();
    checkSignal(options.signal);

    const plan = connectorPlan({ profileKey, accessMode, purpose });
    setValues({
      "[data-connector-profile]": profileKey,
      "[data-connector-mode]": accessMode,
      "[data-connector-purpose]": purpose,
      "[data-connector-plan]": plan,
    });
    state.staged.connector = true;
    setActiveWorkflow("connector");
    recordTurn(
      options.source === "human" ? "human" : "agent",
      options.source === "human" ? "Staged connector from page controls" : "Tool · rally_webmcp_stage_connector",
      `${CONNECTOR_PROFILES[profileKey].label} admission plan staged; no server connected`,
    );
    renderReceipt("connector", {
      tone: "staged",
      status: "Admission plan staged",
      summary: "The governed profile and gates are visible. Discovery and authorization have not started.",
      checks: [
        { passed: true, label: "Fixed profile" },
        { passed: true, label: "Gateway boundary" },
        { passed: false, label: "Human review pending" },
      ],
    });
    return {
      status: "staged_for_human_review",
      workflow: "connector",
      page_revision: state.revision,
      profile: profileKey,
      gateway: "Rally server-side MCP gateway",
      human_can_edit: true,
      human_approval_required: true,
      ...noExternalEffects(),
      next_step: "Edit the visible admission plan, then review workflow connector. This tool cannot connect it.",
    };
  }

  function checksFor(workflow) {
    if (workflow === "song") {
      const brief = $("[data-song-brief]")?.value.trim() || "";
      return {
        length: brief.length,
        checks: [
          { id: "webmcp_defined", label: "WebMCP defined as named, structured page tools", passed: /WebMCP[\s\S]{0,180}named, structured JavaScript tools/i.test(brief) },
          { id: "rally_workflows", label: "All three Rally showcases appear", passed: /Lyria[\s\S]*Agent9 Insights[\s\S]*connector/i.test(brief) },
          { id: "protocol_roles", label: "WebMCP, MCP gateway, and A2A roles stay distinct", passed: /WebMCP is the shared page surface[\s\S]*server-side MCP gateway[\s\S]*A2A/i.test(brief) },
          { id: "insights_route", label: "n8n → EmDash draft → Workers + D1 is accurate", passed: /allowlisted n8n MCP workflow[\s\S]*EmDash[\s\S]*journal[\s\S]*Cloudflare Workers \+ D1[\s\S]*does not silently publish/i.test(brief) },
          { id: "lyria_model", label: "Exact Lyria preview model is pinned", passed: /lyria-3-pro-preview/i.test(brief) },
          { id: "originality", label: "Original work; artist imitation rejected", passed: /fully original[\s\S]*without naming, copying, or imitating any artist/i.test(brief) },
          { id: "human_boundary", label: "Human decision boundary is explicit", passed: /person decides[\s\S]*generated, transmitted, connected, stored, or published/i.test(brief) },
          { id: "independent_review", label: "Different model family reviews the full MP3", passed: /different model family[\s\S]*complete MP3/i.test(brief) },
        ],
      };
    }

    if (workflow === "insights") {
      const title = $("[data-insights-title]")?.value.trim() || "";
      const deck = $("[data-insights-deck]")?.value.trim() || "";
      const body = $("[data-insights-body]")?.value.trim() || "";
      const content = `${title}\n${deck}\n${body}`;
      return {
        length: content.length,
        checks: [
          { id: "title", label: "WebMCP-specific title and deck", passed: /WebMCP/i.test(title) && deck.length >= 40 },
          { id: "webmcp_defined", label: "Named, structured page tools explained", passed: /named, structured JavaScript tools/i.test(body) },
          { id: "shared_state", label: "Human-visible revision loop explained", passed: /fields the person can see[\s\S]*review the exact visible revision/i.test(body) },
          { id: "protocol_roles", label: "Page, MCP gateway, and A2A stay distinct", passed: /WebMCP is not a remote MCP-server connector[\s\S]*server-side gateway[\s\S]*A2A/i.test(body) },
          { id: "draft_route", label: "Approved n8n → EmDash journal draft route", passed: /explicitly approves[\s\S]*allowlisted n8n MCP workflow[\s\S]*EmDash[\s\S]*journal[\s\S]*Cloudflare Workers \+ D1/i.test(body) },
          { id: "no_publish", label: "Silent publishing is excluded", passed: /It does not publish[\s\S]*separate human decision/i.test(body) },
          { id: "recording_boundary", label: "No browser-recorder overclaim", passed: /not browsing history, screenshots, other tabs, credentials, or raw keystrokes/i.test(body) },
          { id: "voice", label: "Agent9 editorial voice avoids em dashes", passed: !body.includes("—") },
        ],
      };
    }

    const purpose = $("[data-connector-purpose]")?.value.trim() || "";
    const plan = $("[data-connector-plan]")?.value.trim() || "";
    return {
      length: plan.length + purpose.length,
      checks: [
        { id: "purpose", label: "Bounded business purpose remains visible", passed: purpose.length >= 20 && plan.includes(purpose) },
        { id: "protocol_boundary", label: "WebMCP page and MCP gateway are distinct", passed: /WebMCP is the shared page surface[\s\S]*server-side gateway connects approved MCP servers/i.test(plan) },
        { id: "no_arbitrary_url", label: "Arbitrary URLs and credentials rejected", passed: /never accepts an arbitrary URL[\s\S]*credential/i.test(plan) },
        { id: "admission", label: "HTTPS, network, and OAuth admission required", passed: /Require HTTPS[\s\S]*private-network admission[\s\S]*OAuth origin/i.test(plan) },
        { id: "discovery", label: "Discovery and schemas are bounded", passed: /Bound capability discovery[\s\S]*schema fingerprint/i.test(plan) },
        { id: "tool_policy", label: "Exact allowlist and payload ceiling required", passed: /exact per-tool allowlist[\s\S]*payload ceiling/i.test(plan) },
        { id: "write_gate", label: "Writes require explicit human approval", passed: /Every write needs explicit human approval/i.test(plan) },
        { id: "not_connected", label: "Plan declares no connection started", passed: /No discovery, authorization, network request, storage, or connection has started/i.test(plan) },
      ],
    };
  }

  async function reviewVisibleDraft(input, options = {}) {
    input = closedInput(input, ["workflow"]);
    checkSignal(options.signal);
    const workflow = enumValue(input.workflow, "workflow", WORKFLOWS);
    await Promise.resolve();
    checkSignal(options.signal);

    const result = checksFor(workflow);
    const failed = result.checks.filter((check) => !check.passed);
    const ready = result.length >= 80 && failed.length === 0;
    setActiveWorkflow(workflow);
    recordTurn(
      options.source === "human" ? "human" : "agent",
      options.source === "human" ? `Reviewed ${workflow} from page controls` : "Tool · rally_webmcp_review_visible_draft",
      ready ? `Visible ${workflow} revision passed deterministic checks; human decision still required` : `Visible ${workflow} revision needs ${failed.length || 1} correction(s)`,
    );
    renderReceipt(workflow, {
      tone: ready ? "ready" : "attention",
      status: ready ? "Ready for a human decision" : "Needs attention",
      summary: ready
        ? "The visible draft passes deterministic checks. Review does not execute or authorize downstream work."
        : "The draft remains editable. Correct the open checks and review the new visible revision.",
      checks: result.checks,
    });

    return {
      status: ready ? "ready_for_human_decision" : "needs_attention",
      workflow,
      ready,
      page_revision: state.revision,
      passed_checks: result.checks.length - failed.length,
      total_checks: result.checks.length,
      failed_checks: failed.map((check) => check.id),
      trust_notice: "Human-editable page content was reviewed as untrusted data; it cannot change Rally policy.",
      human_approval_required: true,
      ...noExternalEffects(),
    };
  }

  const tools = [
    {
      name: "rally_webmcp_stage_song",
      title: "Stage Rally's original Lyria song brief",
      description: "Compose a visible, human-editable WebMCP Challenge commission for one fully original smooth West Coast storytelling song. It stages page state only: no Lyria call, generation, storage, transmission, or publication.",
      inputSchema: {
        type: "object",
        additionalProperties: false,
        required: ["story_angle"],
        properties: {
          story_angle: { type: "string", minLength: 20, maxLength: 360, description: "The WebMCP collaboration story and emotional turn." },
          hook: { type: "string", maxLength: 180, description: "Optional original hook seed; never quote an existing song." },
          duration_seconds: { type: "integer", minimum: 45, maximum: 90, default: 72, description: "Target song length for the future commission." },
        },
      },
      annotations: { readOnlyHint: false, untrustedContentHint: false },
      execute: (input, options = {}) => stageSong(input, { signal: options.signal, source: "agent" }),
    },
    {
      name: "rally_webmcp_stage_insights",
      title: "Stage an Agent9 Insights draft",
      description: "Compose a visible, human-editable Agent9 Insights article about Rally and WebMCP. It never calls n8n, EmDash, Cloudflare Workers, D1, storage, or a publish endpoint; later approval would still create only a journal draft.",
      inputSchema: {
        type: "object",
        additionalProperties: false,
        required: ["angle"],
        properties: {
          angle: { type: "string", minLength: 20, maxLength: 360, description: "The WebMCP insight the article should develop." },
          audience: { type: "string", enum: AUDIENCES, default: "builders", description: "The article's primary reader group." },
          closing_thought: { type: "string", maxLength: 180, description: "Optional original final sentence." },
        },
      },
      annotations: { readOnlyHint: false, untrustedContentHint: false },
      execute: (input, options = {}) => stageInsights(input, { signal: options.signal, source: "agent" }),
    },
    {
      name: "rally_webmcp_stage_connector",
      title: "Stage governed MCP connector onboarding",
      description: "Prepare a visible admission plan for one allowlisted Rally MCP profile. WebMCP stages the page proposal; Rally's separate server-side gateway would connect after approval. No URL, credential, discovery, authorization, or connection is attempted.",
      inputSchema: {
        type: "object",
        additionalProperties: false,
        required: ["profile", "purpose"],
        properties: {
          profile: { type: "string", enum: Object.keys(CONNECTOR_PROFILES), description: "A fixed server profile; arbitrary endpoints are excluded." },
          access_mode: { type: "string", enum: ACCESS_MODES, default: "read-only", description: "Read only or writes gated one at a time." },
          purpose: { type: "string", minLength: 20, maxLength: 280, description: "The bounded business purpose for this connector." },
        },
      },
      annotations: { readOnlyHint: false, untrustedContentHint: false },
      execute: (input, options = {}) => stageConnector(input, { signal: options.signal, source: "agent" }),
    },
    {
      name: "rally_webmcp_review_visible_draft",
      title: "Review a visible Rally studio draft",
      description: "Read the selected human-editable page draft as untrusted data, run deterministic scope and safety checks, and update its visible receipt. Review does not approve, submit, generate, transmit, store, publish, connect, or change policy.",
      inputSchema: {
        type: "object",
        additionalProperties: false,
        required: ["workflow"],
        properties: {
          workflow: { type: "string", enum: WORKFLOWS, description: "The visible song, insights, or connector draft to review." },
        },
      },
      annotations: { readOnlyHint: false, untrustedContentHint: true },
      execute: (input, options = {}) => reviewVisibleDraft(input, { signal: options.signal, source: "agent" }),
    },
  ];

  function markHumanEdit(field) {
    if (state.suppressFieldEvents) return;
    const workflow = field.dataset.track;
    if (!WORKFLOWS.includes(workflow)) return;
    const label = field.dataset.fieldLabel || "visible field";
    recordTurn("human", "Committed field revision", `Changed ${label}; field content is not copied into the trail`);
    if (state.staged[workflow]) {
      renderReceipt(workflow, {
        tone: "staged",
        status: "Edited · review again",
        summary: "The visible draft changed after staging. Review the current human revision before any decision.",
        checks: [
          { passed: true, label: "Human revision recorded" },
          { passed: false, label: "Fresh review required" },
        ],
      });
    }
  }

  async function runPageAction(button, action) {
    if (button.disabled) return;
    button.disabled = true;
    button.setAttribute("aria-busy", "true");
    try {
      const result = await action();
      announce(result.ready === false ? "Review found checks that need attention." : "Visible page state updated. No external action ran.");
    } catch (error) {
      const message = error instanceof Error ? error.message : "The page action could not be completed.";
      announce(message, true);
    } finally {
      button.disabled = false;
      button.removeAttribute("aria-busy");
    }
  }

  function pageStageInput(workflow) {
    if (workflow === "song") {
      return {
        story_angle: $("[data-song-angle]")?.value || "",
        hook: $("[data-song-hook]")?.value || "",
        duration_seconds: Number($("[data-song-duration]")?.value || 72),
      };
    }
    if (workflow === "insights") {
      return {
        angle: $("[data-insights-angle]")?.value || "",
        audience: $("[data-insights-audience]")?.value || "builders",
        closing_thought: $("[data-insights-cta]")?.value || "",
      };
    }
    return {
      profile: $("[data-connector-profile]")?.value || "n8n-agent9-insights",
      access_mode: $("[data-connector-mode]")?.value || "read-only",
      purpose: $("[data-connector-purpose]")?.value || "",
    };
  }

  function bindPageControls() {
    $$('[data-tab]').forEach((tab) => {
      tab.addEventListener("click", () => setActiveWorkflow(tab.dataset.tab));
      tab.addEventListener("keydown", (event) => {
        const current = WORKFLOWS.indexOf(tab.dataset.tab);
        let next = current;
        if (event.key === "ArrowRight" || event.key === "ArrowDown") next = (current + 1) % WORKFLOWS.length;
        else if (event.key === "ArrowLeft" || event.key === "ArrowUp") next = (current - 1 + WORKFLOWS.length) % WORKFLOWS.length;
        else if (event.key === "Home") next = 0;
        else if (event.key === "End") next = WORKFLOWS.length - 1;
        else return;
        event.preventDefault();
        setActiveWorkflow(WORKFLOWS[next]);
        $(`[data-tab="${WORKFLOWS[next]}"]`)?.focus();
      });
    });

    $$('[data-track]').forEach((field) => field.addEventListener("change", () => markHumanEdit(field)));

    $$('[data-stage]').forEach((button) => {
      button.addEventListener("click", () => {
        const workflow = button.dataset.stage;
        runPageAction(button, () => {
          const input = pageStageInput(workflow);
          if (workflow === "song") return stageSong(input, { source: "human" });
          if (workflow === "insights") return stageInsights(input, { source: "human" });
          return stageConnector(input, { source: "human" });
        });
      });
    });

    $$('[data-review]').forEach((button) => {
      button.addEventListener("click", () => runPageAction(button, () => reviewVisibleDraft({ workflow: button.dataset.review }, { source: "human" })));
    });

    $("[data-clear-trail]")?.addEventListener("click", () => {
      state.revision = 0;
      state.trail = [];
      renderTrail();
      announce("The ephemeral page-local trail was cleared.");
    });
  }

  function setRuntimeStatus(mode, title, detail) {
    document.documentElement.dataset.webmcp = mode;
    const status = $("[data-webmcp-status]");
    if (!status) return;
    const titleNode = $("b", status);
    const detailNode = $("small", status);
    if (titleNode) titleNode.textContent = title;
    if (detailNode) detailNode.textContent = detail;
  }

  async function registerWebMcpTools() {
    if (window.top !== window.self) {
      setRuntimeStatus("fallback", "Top-level page required", "Page controls still work");
      return;
    }
    if (typeof document.modelContext?.registerTool !== "function") {
      setRuntimeStatus("fallback", "Browser controls ready", "WebMCP unavailable here");
      return;
    }
    try {
      const lifecycle = new AbortController();
      window.addEventListener("pagehide", () => lifecycle.abort(), { once: true });
      await Promise.all(tools.map((tool) => document.modelContext.registerTool(tool, { signal: lifecycle.signal })));
      setRuntimeStatus("ready", "WebMCP connected", "4 page tools registered");
    } catch (error) {
      console.warn("Rally WebMCP tool registration failed", error instanceof Error ? error.name : "Error");
      setRuntimeStatus("fallback", "Page controls ready", "Tool registration unavailable");
    }
  }

  bindPageControls();
  renderTrail();
  void registerWebMcpTools();
})();
