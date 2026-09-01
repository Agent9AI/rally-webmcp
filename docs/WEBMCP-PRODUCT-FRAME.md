# Rally for WebMCP — product and release frame

## Decision

**Product:** Rally

**Devpost title:** Rally for WebMCP

**Subtitle:** Accountable browser collaboration
**Repository:** `rally-webmcp`

Rally for WebMCP turns a browser page into a shared, governed launch room. A
person and a browser agent can inspect evidence, prepare an artifact, edit the
same visible plan, review the human's revision, and stage a Cloudflare preview.
The agent never receives a hidden path around the person's final decision.

The challenge deadline is **September 3, 2026 at 1:00 PM Pacific / 4:00 PM
Eastern**. The official rules, not conflicting community timestamps, are the
release clock: <https://webmcp.devpost.com/rules>.

## The demonstration

> Ask Rally's browser tools to create a WebMCP-native launch experience,
> generate its original theme song with Lyria 3 Pro, preserve the human-agent
> revision trail, and stage a real Cloudflare preview. The person edits and
> confirms the consequential steps.

The final sub-three-minute demo should show one continuous workflow:

1. The browser agent inspects a real public Rally run and its verification
   record through structured tools instead of pixel guessing.
2. It stages a WebMCP Challenge song task in the visible Rally interface. The
   brief accurately explains WebMCP, Rally's browser tools, the separate MCP
   connector gateway, and A2A handoffs.
3. The person edits the task. Rally records only the bounded page interaction:
   agent stage, human revision, agent review, and human confirmation.
4. The agent reads the exact visible revision back as untrusted content and
   checks the Lyria model pin, originality boundary, connector accuracy,
   provenance receipt, and cross-family verification rule.
5. After human confirmation, Rally's existing media boundary generates the song
   with `lyria-3-pro-preview`; another model family verifies the complete MP3.
6. The browser agent prepares a fixed-scope Cloudflare Pages preview plan. The
   person reviews the target, branch, asset manifest, and permissions, then
   explicitly launches it through Rally's authenticated deployment executor.
7. Rally returns the public preview URL, asset hashes, deployment ID, and the
   collaboration trail as one receipt.

## Why this is genuinely WebMCP-native

WebMCP lets a page expose named JavaScript tools with structured schemas to a
browser agent. It is valuable here because the human and the agent operate on
the same live interface and reuse Rally's application logic. It is not merely a
remote API renamed for a hackathon.

The workflow contains the turn-taking that ordinary form filling lacks:

```text
agent stages v1 → human edits v2 → agent reads v2 → agent reviews v3
       → human confirms → Rally executes → independent verifier checks
```

Rally uses three adjacent protocols without conflating them:

| Boundary | Responsibility |
|---|---|
| WebMCP | Human-present browser collaboration and visible page state |
| MCP | Background workers use explicitly approved business-system tools |
| A2A | External agent systems exchange bounded tasks and artifacts |
| Rally | Identity, authority, revisions, recovery, evidence, and no self-approval |

## Interaction recording: the honest boundary

WebMCP is **not** a general browser recorder, session-replay system, or license
to collect cross-site activity. The page receives a callback when one of its
own registered tools is executed, so Rally can instrument that callback and its
own form events.

Rally's collaboration trail may record:

- tool name and bounded semantic result;
- page-local revision number;
- whether the change came from a WebMCP handler or a trusted human DOM event;
- generation and deployment receipt identifiers;
- timestamps and content hashes when the trail is exported.

It must not record:

- browsing history, other tabs, cross-origin clicks, screenshots, or keystrokes;
- credentials, cookies, access tokens, private prompts, or raw connector data;
- agent reasoning or unsupported claims about browser-wide observability.

The first implementation is page-local and ephemeral. Persistence is opt-in at
the human-confirmed run or deployment boundary and stores only a bounded,
redacted receipt.

## Repository boundary

`baseline/all-things-agentic-2026` points to commit `cf2e346`, the clean Rally
snapshot before this derivative work. The original `/Users/terry/rally`
worktree and remote remain untouched. This repository's source remote has a
disabled push URL until a new `Agent9AI/rally-webmcp` remote is created.

```text
rally-webmcp/
├── site/
│   ├── app.js                 WebMCP handlers, visible state, trace
│   ├── index.html             launch/song collaboration interface
│   └── styles.css             shared-state and receipt presentation
├── src/
│   ├── media.py               bounded Lyria generation + receipt
│   ├── runner.py              deterministic execution authority
│   └── worker/                Cloudflare ingress, D1, R2 projections
├── cloud/                     authenticated control plane + connector gateway
├── tests/
│   ├── test_webmcp_runtime.mjs handler-level browser contract harness
│   └── test_media.py          WebMCP-specific Lyria routing contract
└── docs/
    ├── WEBMCP.md              public tool contract
    ├── WEBMCP-CHALLENGE.md    submission/demo checklist
    └── WEBMCP-PRODUCT-FRAME.md this decision record
```

## Tool strategy

The public surface stays small and non-overlapping. Current implemented slice:

| Tool | Visible effect | External effect |
|---|---|---|
| `rally_list_public_runs` | Filters and synchronizes the public run console | None; reads public D1 projection |
| `rally_inspect_public_run` | Opens bounded checklist and proof | None; reads public D1 projection |
| `rally_draft_job` | Populates a generic governed commission | None; staged only |
| `rally_stage_challenge_song` | Creates the visible WebMCP-specific Lyria brief and trace v1 | No generation, storage, or transmission |
| `rally_review_visible_song_task` | Reads human edits as untrusted data and updates the review receipt | No generation, storage, or transmission |

Next launch slice:

- `rally_stage_cloudflare_preview`: prepare an allowlisted Pages project,
  preview branch, fixed asset manifest, and expected source revision;
- a human-only **Deploy preview** control outside the tool call;
- an authenticated executor that uses a narrowly scoped Cloudflare credential,
  rejects stale revisions and arbitrary project names, and returns a deployment
  receipt.

The deployment tool must never accept an API token, arbitrary Worker source,
shell command, account ID, or unrestricted target URL from the agent.

## Cloudflare execution boundary

WebMCP is the browser coordination surface; it should not hold Cloudflare
credentials. The safe path is:

```text
WebMCP stages fixed preview plan in visible Rally page
  → human reviews target + manifest and clicks Deploy preview
  → authenticated Rally control plane checks session and expected revision
  → bounded executor deploys only the generated static bundle
  → Pages deployment ID + preview URL + asset hashes return to Rally
```

Use a dedicated preview project or branch. Production promotion is out of scope
for the hackathon demo. Keep the Pages/Workers token out of frontend JavaScript
and repository history. Prefer Wrangler for operator-driven deployment and use
the Pages API only inside the authenticated executor when the browser workflow
requires it.

## Judging map

The challenge evaluates four criteria equally:

| Criterion | Rally proof |
|---|---|
| WebMCP leverage | Typed tools, shared visible state, human edit read-back, bounded trace, abort handling, trust annotations |
| Execution | Working live app, real Lyria MP3, real Cloudflare preview, runtime handler tests, receipts |
| Potential impact | Safer human-agent deployment for teams that need proof and explicit authority |
| Creativity and ambition | The product uses WebMCP to create, audit, soundtrack, and deploy its own WebMCP launch experience |

## Release gates

- [x] Independent `rally-webmcp` clone with full Rally history
- [x] Baseline tag and push-disabled source remote
- [x] WebMCP Lyria staging + human edit read-back
- [x] Page-local bounded collaboration trail
- [x] Handler-level WebMCP runtime test
- [x] WebMCP-specific Lyria routing and connector-accuracy test
- [ ] Visible Cloudflare preview plan with revision fencing
- [ ] Authenticated human-only preview deployment executor
- [ ] Real Lyria generation and independent listening receipt
- [ ] Real Cloudflare preview URL and deployment receipt
- [ ] ChatGPT in-app browser tool discovery and invocation evidence
- [ ] Ordinary browser fallback and responsive QA
- [ ] Public `Agent9AI/rally-webmcp` repository with visible Apache-2.0 license
- [ ] Public YouTube demo under 3:00 with clear audio
- [ ] Devpost project saved no later than September 2
- [ ] Final submission completed by September 3 at 10:00 AM Eastern
- [ ] Freeze repo, live site, and Devpost entry through judging

## Official references

- Challenge: <https://webmcp.devpost.com/>
- Rules: <https://webmcp.devpost.com/rules>
- WebMCP draft: <https://webmachinelearning.github.io/webmcp/>
- Chrome WebMCP guidance: <https://developer.chrome.com/docs/ai/agents>
- Cloudflare Browser Run WebMCP: <https://developers.cloudflare.com/browser-run/features/webmcp/>
- Cloudflare Pages direct upload: <https://developers.cloudflare.com/pages/get-started/direct-upload/>
- Lyria generation: <https://docs.cloud.google.com/gemini-enterprise-agent-platform/models/music/generate-music>
