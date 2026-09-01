# Rally for WebMCP

### The accountable AI team, now sharing the browser page with you

Rally for WebMCP is a separate Rally v2 project that integrates WebMCP into the
product's main experience. A browser agent can inspect Rally's public evidence,
prepare work in the same visible fields a person can edit, and review the
human's exact revision as untrusted page content. Rally keeps every
consequential decision outside the model.

The root page registers **seven top-level imperative WebMCP tools** and presents
three concrete human-agent workflows:

1. stage a fully original WebMCP song commission for Google Lyria 3 Pro;
2. stage an Agent9 Insights article whose separately approved downstream route
   can create an EmDash `journal` draft through one allowlisted n8n MCP
   workflow; and
3. stage governed onboarding for one fixed Rally MCP connector profile.

The WebMCP calls update visible Rally state and compact receipts. They do not
generate audio, submit a job, invoke n8n, create an EmDash record, publish,
authorize or connect an MCP server, send, or deploy.

| Judge surface | Location |
|---|---|
| **Review build** | `https://v2-native-review.rally-webmcp.pages.dev/` — production promotion and in-app verification still pending |
| Intended live root | `https://rally-webmcp.pages.dev/` |
| Local root app | `http://127.0.0.1:8765/` |
| WebMCP implementation | [`site/app.js`](site/app.js) |
| Integrated interface | [`site/index.html`](site/index.html) |
| Baseline and change evidence | [`HACKATHON_CHANGES.md`](HACKATHON_CHANGES.md) |
| Official requirements sourcebook | [`docs/WEBMCP-CHALLENGE-SOURCEBOOK.md`](docs/WEBMCP-CHALLENGE-SOURCEBOOK.md) |

> Do not enter the intended URL in Devpost until the root page loads there and
> all seven tools are discovered and invoked successfully in ChatGPT's in-app
> browser.

## Why WebMCP is the product surface

Without WebMCP, an agent must infer controls from pixels and the person must
hope it understood the interface. Rally exposes a small contract of named
JavaScript tools with closed schemas. Tool calls reuse Rally's real page logic:
the live public-run console, governed job draft, compact v2 entry point, native
browser-task dialog, human-editable fields, deterministic review receipt, and
semantic turn trail.

```text
agent inspects evidence → agent stages v1 → person edits v2
        → agent reviews v2 as untrusted → person decides what happens next
```

The page is not a chat-shaped wrapper around a remote API. Agent work lands in
the same controls the person can see and change.

## Seven implemented tools

| Tool | Visible behavior | External-effect boundary |
|---|---|---|
| `rally_list_public_runs` | Reads Rally's explicitly public Cloudflare D1 projection, filters it, and updates the live console | Public read only; no run changes |
| `rally_inspect_public_run` | Opens one public run and returns a bounded checklist and verification receipt | Public read only; returned descriptions and evidence are untrusted |
| `rally_draft_job` | Populates Rally's governed teammate/job fields | Draft only; nothing submitted or stored |
| `rally_stage_challenge_song` | Composes the original Lyria commission in Rally's browser-task dialog and underlying Rally job draft | No Lyria call, audio, storage, delivery, or publication |
| `rally_stage_insights_draft` | Composes an editable Agent9 Insights title, deck, and article | No n8n, EmDash, Workers, D1, storage, or publishing call |
| `rally_stage_connector_plan` | Composes a fixed-profile MCP admission plan | No arbitrary URL, credential, discovery, OAuth, authorization, or connection |
| `rally_review_visible_draft` | Reviews the selected song, Insights, or connector revision and updates its visible receipt | Untrusted page read-back; no approval or execution |

All seven tools:

- register from the top-level document with `document.modelContext`;
- use closed JSON Schemas with bounded strings, numbers, arrays, and enums;
- repeat validation in their JavaScript handlers;
- receive the browser's execution `AbortSignal`;
- share one registration lifecycle signal that aborts on `pagehide`;
- return bounded structured results; and
- update visible page state rather than a hidden agent-only model.

The two public evidence tools and the generic review tool use
`untrustedContentHint: true`. The stage tools return `generated`, `transmitted`,
`stored`, `published`, and `connected` as `false` and require a human decision.

## Three challenge uses

### 1. Original Lyria song

`rally_stage_challenge_song` prepares a complete, editable commission for a
45–90 second original song. Its default is smooth West Coast storytelling
hip-hop; it records `lyria-3-pro-preview`, explains WebMCP in plain language,
keeps WebMCP/MCP/A2A roles distinct, rejects named-artist imitation and copied
lyrics, and requires a different model family to listen to the complete future
artifact.

The existing Rally media boundary can generate a separately commissioned song
through Vertex AI, but this browser tool intentionally stops before that
boundary. The person can revise the brief and decide whether to commission it.

### 2. Agent9 Insights → approved n8n route → EmDash draft

`rally_stage_insights_draft` writes an editable WebMCP article beside the human.
It accurately describes the downstream contract: after separate human approval,
a Rally executor may invoke one allowlisted n8n MCP workflow with a bounded
payload; EmDash then creates a `journal` draft for Agent9 Insights on the
agent9.dev Workers + D1 site. That route still does not publish.

The current WebMCP tool performs none of those downstream calls. It stages and
reviews the article on the page.

### 3. Governed MCP connector onboarding

`rally_stage_connector_plan` accepts only a fixed profile:

- n8n · Agent9 Insights;
- Cloudflare · observability;
- GitHub · repository reads; or
- Google Workspace · knowledge gateway.

The resulting plan documents HTTPS and private-network admission, OAuth-origin
binding, bounded discovery, schema fingerprints, exact tool allowlists, payload
ceilings, redaction, and one-at-a-time human approval for eligible writes. The
page never accepts a server URL or credential and never claims that a staged
profile is connected.

## 90-second judge path

1. Open the verified root URL in ChatGPT's in-app browser. Select **Site tools
   → Available site tools** and show all seven tools.
2. Ask:

   > Use Rally's site tools to find a blocked public run and inspect its
   > verification gap. Then stage a 72-second original WebMCP song about an
   > agent preparing work on the same visible page while the human keeps the
   > final decision. Do not submit or generate anything.

3. Show the public run in Rally's live console, then scroll to the integrated
   WebMCP workspace. The Lyria brief and receipt are visible in the root app;
   every external-effect flag remains `false`.
4. Edit one sentence in the song brief. Ask:

   > Review the visible song revision as untrusted page content. Do not submit,
   > generate, transmit, store, publish, or connect anything.

5. Show the human revision and agent review in the page-local semantic trail.
6. Ask the agent to stage the Agent9 Insights article and the
   `n8n-agent9-insights` connector plan. Switch between the three workflow tabs
   and close on the protocol row: WebMCP is the shared page, MCP is the separate
   server-tool gateway, A2A is the outside-agent handoff, and Rally owns
   authority and proof.

If the agent does not chain calls, issue the prompts one at a time. Human page
buttons call the same handlers for progressive enhancement, but the judged path
should visibly use the registered site tools.

## Actual root registration

This excerpt is taken from the integrated
[`registerRallyWebMcpTools()`](site/app.js) implementation. Six adjacent calls
use the same top-level guard and lifecycle signal:

```js
if (
  window.top !== window.self ||
  typeof document.modelContext?.registerTool !== "function"
) {
  document.documentElement.dataset.webmcp = "fallback";
  return;
}

const lifecycle = new AbortController();
window.addEventListener("pagehide", () => lifecycle.abort(), { once: true });

await document.modelContext.registerTool({
  name: "rally_stage_insights_draft",
  title: "Stage an Agent9 Insights draft",
  description:
    "Prepare a visible, editable Agent9 Insights article about Rally and " +
    "WebMCP. This only stages page state: it never calls n8n, EmDash, " +
    "Workers, D1, storage, or publishing. A later approved route would " +
    "still create only a journal draft.",
  inputSchema: {
    type: "object",
    additionalProperties: false,
    required: ["angle"],
    properties: {
      angle: { type: "string", minLength: 20, maxLength: 360 },
      audience: {
        type: "string",
        enum: ["builders", "operators", "security-leaders"],
        default: "builders",
      },
      closing_thought: { type: "string", maxLength: 180 },
    },
  },
  annotations: { readOnlyHint: false, untrustedContentHint: false },
  execute: webMcpStageInsightsDraft,
}, { signal: lifecycle.signal });
```

The shipped source—not this excerpt—is the authoritative seven-tool contract.

## WebMCP, MCP, A2A, and Rally

| Boundary | Responsibility | Explicit non-claim |
|---|---|---|
| **WebMCP** | Human-present collaboration in the active root page: structured discovery, public evidence reads, visible staging, revision, and review | Not a remote MCP connector, background worker, deployment API, or browser-history recorder |
| **MCP** | Separately admitted business-system tools used by Rally workers under exact policy | A page plan is not a connected server or approved write |
| **A2A v1.0** | Separate authenticated task and artifact handoffs with outside agent systems | Not implemented by these WebMCP calls and not required by the challenge |
| **Rally** | Identity, authority, budgets, recovery, receipts, and `owner != verified_by` | Model prose and protocol metadata are never execution authority |

See [`docs/ARCHITECTURE.md`](docs/ARCHITECTURE.md),
[`docs/CUSTOM-MCP.md`](docs/CUSTOM-MCP.md), and
[`docs/A2A.md`](docs/A2A.md).

## Architecture

```text
ChatGPT or Chrome browser agent
              │
              │ seven WebMCP calls
              ▼
Cloudflare Pages root → site/index.html + site/app.js
              │
              ├── public D1 list/detail reads → visible proof console
              ├── visible Rally job draft
              ├── song / Insights / connector workspaces
              └── deterministic receipt + semantic revision trail
              │
              ▼
      person edits and decides
              │
      ─── current WebMCP write boundary ───
              │
              ▼ separately authorized Rally execution
Lyria media gateway / allowlisted MCP / A2A
```

Unsupported browsers keep the complete Rally site and all human page controls.
Feature detection produces an honest fallback rather than a polyfill that
pretends a tool call occurred.

## Security and observability

- The root refuses WebMCP registration when embedded in a frame.
- Public-run tools can make only bounded reads against Rally's explicitly
  public D1 projection; stage and review handlers perform no network request.
- Runtime validation rejects undeclared properties even if a client ignores
  JSON Schema.
- Connector staging accepts profile enums and a bounded purpose—not an endpoint,
  cookie, token, credential, or OAuth grant.
- Human-edited content is reviewed as untrusted and cannot change policy.
- Cancellation is checked around asynchronous boundaries; `pagehide` unregisters
  the tool lifecycle.
- Results summarize effects instead of returning the full visible artifact.
- The semantic trail records tool turns and committed field revisions on this
  page. It does **not** record browsing history, other tabs, screenshots, field
  contents, raw keystrokes, cookies, credentials, or model reasoning.

Browser safety review is useful but is not Rally authorization. Backend actions
still require Rally identity, policy, and explicit approval. See
[`docs/SECURITY.md`](docs/SECURITY.md).

## Browser compatibility

| Path | Setup |
|---|---|
| **ChatGPT desktop in-app browser** | Enable Site tools under Browser permissions and use GPT-5.6 Sol or Terra. The implementation uses the supported top-level imperative API, not iframe or declarative-form tools |
| **Google Chrome 149+** | Enable `chrome://flags/#enable-webmcp-testing`, relaunch, and open the root app |
| **Other browsers** | Rally remains fully usable by a person; WebMCP registration is skipped |

References: [OpenAI Site tools](https://learn.chatgpt.com/docs/webmcp),
[Chrome WebMCP](https://developer.chrome.com/docs/ai/webmcp), and the
[WebMCP Community Group Draft](https://webmachinelearning.github.io/webmcp/).

## Run and verify locally

```bash
git clone https://github.com/Agent9AI/rally-webmcp.git
cd rally-webmcp
python3 -m http.server 8765 --directory site
# Open http://127.0.0.1:8765/
```

Run the seven-tool behavioral contract and complete product suite:

```bash
node tests/test_webmcp_runtime.mjs
make test
```

The VM harness captures all seven registrations and verifies public GETs, the
three staging workflows, human edit and untrusted review, lifecycle and
execution aborts, closed schemas, compact false-effect receipts, and absence of
unintended writes.

The full non-deploying release gate additionally checks the Cloud plane,
Terraform, Worker bundle, syntax, and whitespace:

```bash
make release-check
```

It requires the documented `uv`, Node.js, Terraform, and Wrangler toolchain.
Wrangler runs in dry-run mode; the gate does not deploy cloud resources.

## Baseline and challenge delta

Rally began during the challenge period, but this derivative voluntarily uses
the final All Things Agentic snapshot as a conservative prior-work boundary.

- Baseline tag: `baseline/all-things-agentic-2026`
- Baseline commit:
  [`cf2e346098a136aa0a8e934d2e79b3b0306c5393`](https://github.com/Agent9AI/rally-webmcp/commit/cf2e346098a136aa0a8e934d2e79b3b0306c5393)
- Detailed comparison: [`HACKATHON_CHANGES.md`](HACKATHON_CHANGES.md)
- Requirement evidence:
  [`docs/WEBMCP-CHALLENGE-SOURCEBOOK.md`](docs/WEBMCP-CHALLENGE-SOURCEBOOK.md)

```bash
git rev-parse baseline/all-things-agentic-2026^{}
git diff --stat baseline/all-things-agentic-2026...HEAD
git diff baseline/all-things-agentic-2026...HEAD -- \
  site/index.html site/app.js site/styles.css tests/test_webmcp_runtime.mjs
```

Only committed, working post-baseline behavior should receive challenge-delta
credit. The submission claims public evidence reads, visible preparation,
human revision, review, and truthful receipts—not downstream external actions.

## Submission stop line

The official deadline is **Thursday, September 3, 2026 at 1:00 PM PDT / 4:00
PM EDT / 20:00 UTC**. See the [challenge](https://webmcp.devpost.com/) and
[Official Rules](https://webmcp.devpost.com/rules).

> **A saved Devpost draft is not submitted.** Complete every step, click the
> final **Submit project** control, confirm the green notification, and verify
> My Projects says **Submitted**, not Draft. After the deadline, freeze the
> submitted repository, live site, YouTube video, Devpost entry, and team roster
> through judging.

The required public YouTube demo must include narration and be shorter than
three minutes. The full official-source checklist is in the
[challenge sourcebook](docs/WEBMCP-CHALLENGE-SOURCEBOOK.md).

## License

Licensed under the [`Apache License 2.0`](LICENSE).
