# Rally for WebMCP — product and release frame

## Decision

**Product:** Rally v2

**Devpost title:** Rally for WebMCP

**Subtitle:** Accountable browser collaboration

**Repository:** `rally-webmcp`

**Judge URL:** root of the separate Cloudflare Pages project, intended as
`https://rally-webmcp.pages.dev/` after deployment and in-app verification

Rally for WebMCP is not a separate tool lab. The root Rally product now exposes
seven bounded WebMCP tools inside the same application that explains the
accountable team, shows public run evidence, drafts work, and presents Rally's
MCP and A2A boundaries.

A person and a browser agent can inspect evidence, prepare a song brief, stage
an article, stage connector onboarding, edit the same visible fields, and ask
Rally to review the exact human revision. The agent never receives a hidden
path around the person's final decision.

The challenge deadline is **September 3, 2026 at 1:00 PM Pacific / 4:00 PM
Eastern**. The [Official Rules](https://webmcp.devpost.com/rules) are the
release clock.

## Product promise

> Rally lets the browser agent prepare the work where the person can see it,
> then makes authority stop exactly where the page says it stops.

The integrated product demonstrates three challenge uses:

1. **Original WebMCP song:** stage a fully original Lyria 3 Pro commission with
   an exact model pin, WebMCP-specific story, no-imitation boundary, provenance
   requirements, and independent full-file review.
2. **Agent9 Insights:** stage a human-editable article and disclose the future
   bounded route—separate human approval, one allowlisted n8n MCP workflow,
   then an EmDash `journal` draft on Workers + D1. The page does not invoke the
   route or publish.
3. **Governed MCP onboarding:** stage an admission plan for one fixed n8n,
   Cloudflare Observability, GitHub-read, or Google Workspace profile. No
   arbitrary endpoint, credential, discovery request, OAuth flow, or connection
   enters through WebMCP.

These are surrounded by Rally's existing public-run search, verification
inspection, and governed job-draft tools, producing the final seven-tool root
surface.

## Demonstration sequence

The final sub-three-minute video should show one uninterrupted root-page flow:

1. Open ChatGPT's **Available site tools** and show seven top-level imperative
   registrations.
2. Ask Rally to find a blocked public run and inspect its verification gap.
   The same record opens in the visible D1-backed console.
3. Ask Rally to stage a 72-second original WebMCP Challenge song. Rally opens
   the native browser-task dialog and synchronizes the governed Rally draft.
4. Edit the brief manually. Rally records a page-local semantic revision label,
   not the field contents or raw keystrokes.
5. Ask the browser agent to review the visible song revision as untrusted. Show
   the deterministic receipt and retained human decision.
6. Stage the Agent9 Insights article. Show the disclosed n8n → EmDash journal
   draft route and the `published: false` boundary.
7. Stage the n8n connector profile. Show exact admission gates and
   `connected: false`.
8. End on the compact v2 boundary: WebMCP is the shared page; Rally owns
   authority; MCP is the separate business-tool gateway; A2A is the
   outside-agent handoff.

## Why this is genuinely WebMCP-native

WebMCP is valuable because both actors share Rally's live interface and page
state. The model sees named tools and structured schemas; the person sees every
result in familiar controls.

```text
agent inspects → agent stages v1 → human edits v2
       → agent reviews v2 as untrusted → human decides
```

This is not a remote endpoint renamed as WebMCP. The handlers reuse Rally's
public console and onboarding draft, then open one product-native task dialog
for the editors, receipt, tabs, and collaboration trail.

## Final seven-tool strategy

| Tool | Role | Side effects |
|---|---|---|
| `rally_list_public_runs` | Search and display explicitly public Rally evidence | Bounded public GET; visible console update |
| `rally_inspect_public_run` | Open and summarize one public verification record | Bounded public GET; visible console update |
| `rally_draft_job` | Populate a governed Rally job draft | Page state only |
| `rally_stage_challenge_song` | Compose the Lyria commission and synchronize Rally's job draft | Page state only |
| `rally_stage_insights_draft` | Compose an Agent9 Insights article | Page state only |
| `rally_stage_connector_plan` | Compose a fixed-profile MCP admission plan | Page state only |
| `rally_review_visible_draft` | Review a human-edited song, article, or connector plan as untrusted | Page state and receipt only |

The final registry deliberately remains small and non-overlapping. Closed
schemas, handler validation, bounded outputs, abort propagation, trust hints,
and an unregistration lifecycle are part of the shipped contract.

## Protocol map

| Boundary | Responsibility |
|---|---|
| WebMCP | Human-present evidence inspection, staging, visible revision, and review in the root browser page |
| MCP | Separately admitted server-side business tools used by Rally workers |
| A2A | Authenticated outside-agent task and artifact handoffs |
| Rally | Identity, authority, budgets, revisions, recovery, evidence, and no self-approval |

WebMCP does not connect remote MCP servers. A staged connector plan is not a
connection. A2A is supported by a separate Rally boundary, not by these browser
calls, and is not a challenge requirement.

## Interaction recording: the honest boundary

WebMCP is **not** a browser recorder or session-replay permission. Rally can
observe its own handlers and its own page fields.

The integrated semantic trail records only:

- the bounded tool action label;
- whether the turn came from a browser agent or human control;
- a page-local revision number; and
- a short effect summary.

It does not record browsing history, other tabs, cross-origin activity,
screenshots, field contents, raw keystrokes, credentials, cookies, tokens,
private prompts, connector data, or model reasoning. The trail is page-local
and ephemeral.

## Root repository boundary

`baseline/all-things-agentic-2026` points to commit `cf2e346`, the clean Rally
snapshot before the conservative challenge delta. The original Rally worktree
and remote remain protected; this derivative publishes independently.

```text
rally-webmcp/
├── site/
│   ├── index.html             Rally v1 product + compact v2 dialog
│   ├── app.js                 seven tool definitions and handlers
│   └── styles.css             original product + responsive task dialog
├── src/
│   ├── media.py               bounded Lyria generation boundary
│   ├── runner.py              deterministic execution authority
│   └── worker/                Cloudflare ingress, D1, and R2 projections
├── cloud/                     authenticated control plane + connector gateway
├── tests/
│   ├── test_webmcp_runtime.mjs seven-tool root VM contract
│   ├── test_site.py           integrated site and static contracts
│   └── test_media.py          WebMCP-specific Lyria routing contract
└── docs/
    ├── WEBMCP-CHALLENGE-SOURCEBOOK.md official requirement evidence
    └── WEBMCP-PRODUCT-FRAME.md        this decision record
```

## Downstream execution boundary

The root WebMCP app contains public reads and page-state preparation, not
provider credentials or external writes.

```text
WebMCP prepares visible work
  → human reviews the exact revision
  → current browser-tool authority stops
  → separately authenticated Rally executor checks identity, policy, and digest
  → bounded Lyria or allowlisted MCP action runs
  → independent verifier checks the resulting receipt
```

The downstream path is evidence only when committed, tested, and demonstrated.
The root stage/review tools currently and explicitly return false for generation,
transmission, storage, publication, and connection.

## Judging map

| Criterion | Rally proof |
|---|---|
| WebMCP leverage | Seven typed root tools, live evidence reads, shared visible state, human edit read-back, trust annotations, lifecycle and execution aborts |
| Execution | One coherent root product, three usable workflows, progressive enhancement, deterministic behavioral harness |
| Potential impact | Safer preparation for creative work, editorial work, and business-system onboarding without hidden authority |
| Creativity and ambition | WebMCP coordinates a person and agent across evidence, creation, publishing design, and protocol governance in one Rally interface |

## Release gates

- [x] Independent `rally-webmcp` clone and conservative baseline tag
- [x] Integrated root Rally v2 product experience
- [x] Seven top-level imperative `document.modelContext` tools
- [x] Public evidence search and bounded verification inspection
- [x] Original-song, Agent9 Insights, and connector-onboarding staging
- [x] Human revision and untrusted generic review
- [x] Page-local semantic trail with an explicit non-recording boundary
- [x] Closed schemas, runtime validation, compact false-effect receipts
- [x] Execution cancellation and lifecycle cleanup
- [x] Seven-tool VM harness with mocked public reads and no-write ledger
- [ ] Deploy and verify `https://rally-webmcp.pages.dev/`
- [ ] Capture ChatGPT in-app browser discovery and invocation evidence
- [ ] Complete ordinary-browser, responsive, and accessibility QA
- [ ] Record a public narrated YouTube demo under 3:00
- [ ] Finish the Devpost project and confirm **Submitted**, not Draft
- [ ] Freeze repository, live site, video, entry, and roster through judging

Real Lyria generation, a real n8n → EmDash draft receipt, and an authenticated
connector execution receipt may strengthen the demonstration only if completed
and verified before release. They are not claimed by the current browser tools.

## Official references

- Challenge: <https://webmcp.devpost.com/>
- Rules: <https://webmcp.devpost.com/rules>
- OpenAI Site tools: <https://learn.chatgpt.com/docs/webmcp>
- WebMCP draft: <https://webmachinelearning.github.io/webmcp/>
- Chrome WebMCP guidance: <https://developer.chrome.com/docs/ai/webmcp>
- Cloudflare Pages direct upload: <https://developers.cloudflare.com/pages/get-started/direct-upload/>
- Lyria generation: <https://docs.cloud.google.com/gemini-enterprise-agent-platform/models/music/generate-music>
