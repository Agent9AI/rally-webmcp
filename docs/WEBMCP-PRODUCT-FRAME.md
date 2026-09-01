# Rally for WebMCP — product and release frame

## Decision

**Product:** Rally

**Devpost title:** Rally for WebMCP

**Subtitle:** Accountable browser collaboration

**Repository:** `rally-webmcp`

Rally for WebMCP turns a browser page into a shared, governed launch room. A
person and a browser agent can prepare an artifact, edit the same visible plan,
review the human's revision, and stage governed downstream work.
The agent never receives a hidden path around the person's final decision.

The challenge deadline is **September 3, 2026 at 1:00 PM Pacific / 4:00 PM
Eastern**. The official rules, not conflicting community timestamps, are the
release clock: <https://webmcp.devpost.com/rules>.

## The demonstration

> Ask Rally's browser tools to stage an original WebMCP song, an Agent9
> Insights article, and a governed MCP connector plan in one visible studio.
> The person edits the page and asks the agent to review that exact revision.

The final sub-three-minute demo should show one continuous workflow:

1. Show ChatGPT's **Available site tools** and the four top-level imperative
   `rally_webmcp_*` registrations.
2. The agent stages a WebMCP Challenge song task in the visible Rally interface. The
   brief accurately explains WebMCP, Rally's browser tools, the separate MCP
   connector gateway, and A2A handoffs.
3. The person edits the task. Rally records only the bounded page interaction:
   agent stage, human revision, agent review, and human confirmation.
4. The agent reads the exact visible revision back as untrusted content and
   checks the Lyria model pin, originality boundary, connector accuracy,
   provenance receipt, and cross-family verification rule.
5. It stages the Agent9 Insights draft and shows the truthful future route:
   human approval, one allowlisted n8n MCP workflow, and an EmDash `journal`
   draft on Cloudflare Workers + D1. The page does not execute that route.
6. It stages a fixed-profile MCP admission plan and makes the boundary explicit:
   WebMCP is the page surface; Rally's server-side gateway connects MCP servers.
7. End on the page-local semantic trail and effect flags: generated,
   transmitted, stored, published, and connected all remain `false`.

## Why this is genuinely WebMCP-native

WebMCP lets a page expose named JavaScript tools with structured schemas to a
browser agent. It is valuable here because the human and the agent operate on
the same live interface and reuse Rally's application logic. It is not merely a
remote API renamed for a hackathon.

The workflow contains the turn-taking that ordinary form filling lacks:

```text
agent stages v1 → human edits v2 → agent reads v2 → agent reviews v3
       → human retains the downstream decision
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
worktree and remote remain untouched. This repository now publishes to
<https://github.com/Agent9AI/rally-webmcp>; its `rally-source` push URL remains
disabled so the derivative cannot overwrite the original Rally repository.

```text
rally-webmcp/
├── site/
│   ├── webmcp/                dedicated four-tool judge studio
│   └── app.js                 disclosed baseline Rally page tools
├── src/
│   ├── media.py               bounded Lyria generation + receipt
│   ├── runner.py              deterministic execution authority
│   └── worker/                Cloudflare ingress, D1, R2 projections
├── cloud/                     authenticated control plane + connector gateway
├── tests/
│   ├── test_webmcp_runtime.mjs handler-level browser contract harness
│   ├── test_webmcp_studio_runtime.mjs three-showcase runtime harness
│   └── test_media.py          WebMCP-specific Lyria routing contract
└── docs/
    ├── WEBMCP.md              public tool contract
    ├── WEBMCP-CHALLENGE.md    submission/demo checklist
    └── WEBMCP-PRODUCT-FRAME.md this decision record
```

## Tool strategy

The dedicated judge surface stays small and non-overlapping:

| Tool | Visible effect | External effect |
|---|---|---|
| `rally_webmcp_stage_song` | Stages an original Lyria commission | No generation, storage, or transmission |
| `rally_webmcp_stage_insights` | Stages an Agent9 Insights article | No n8n/EmDash call, storage, or publication |
| `rally_webmcp_stage_connector` | Stages one fixed-profile MCP admission plan | No URL, credential, discovery, authorization, or connection |
| `rally_webmcp_review_visible_draft` | Reviews current human-editable page state and updates its receipt | No approval or downstream action |

The original page's three pre-existing tools and two early song tools are
disclosed in `HACKATHON_CHANGES.md`; the Devpost URL targets `/webmcp/`.

## Downstream execution boundary

WebMCP is the browser coordination surface; it does not hold provider or MCP
credentials. A future external action must follow this path:

```text
WebMCP stages visible work
  → human reviews the exact revision
  → authenticated Rally control plane checks authority + argument digest
  → bounded Lyria or allowlisted MCP executor runs
  → different model family or human verifies the receipt
```

The studio itself is deployed to Cloudflare Pages at
<https://rally.agent9.dev/webmcp/>. Its JavaScript intentionally contains no
network or persistence primitive. Lyria generation, n8n execution, EmDash draft
creation, and MCP connection remain separate work until each is implemented,
tested, and truthfully demonstrated.

## Judging map

The challenge evaluates four criteria equally:

| Criterion | Rally proof |
|---|---|
| WebMCP leverage | Typed tools, shared visible state, human edit read-back, bounded trace, abort handling, trust annotations |
| Execution | Working live Cloudflare app, four real tools, two runtime harnesses, green public CI |
| Potential impact | Safer human-agent preparation for creative work, publishing, and connector onboarding |
| Creativity and ambition | One page demonstrates creation, editorial work, and governance without conflating WebMCP with MCP or A2A |

## Release gates

- [x] Independent `rally-webmcp` clone with full Rally history
- [x] Baseline tag and push-disabled original-Rally remote
- [x] WebMCP Lyria staging + human edit read-back
- [x] Page-local bounded collaboration trail
- [x] Handler-level WebMCP runtime test
- [x] WebMCP-specific Lyria routing and connector-accuracy test
- [x] Dedicated three-showcase `/webmcp/` studio
- [x] Production Cloudflare Pages URL and hardened WebMCP headers
- [x] Public GitHub repository, detected Apache-2.0 license, baseline tag, and green CI
- [ ] Real Lyria generation and independent listening receipt
- [ ] Real human-approved n8n → EmDash draft receipt
- [ ] Authenticated connector execution receipt
- [ ] ChatGPT in-app browser tool discovery and invocation evidence
- [ ] Ordinary browser fallback and responsive QA
- [ ] Public YouTube demo under 3:00 with clear audio
- [ ] Devpost project fully **submitted**, not merely saved, no later than September 2
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
