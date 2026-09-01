# Rally v2 for WebMCP

### ChatGPT opens the door. Rally's agents do the work.

Rally gives companies accountable AI teammates that people can email or use from
a signed-in workspace. This derivative adds WebMCP to the real Rally product:
ChatGPT can fill the existing job form, start that exact job after confirmation,
find the resulting run, and open its agents, checks, and deliverables.

There is no separate WebMCP “studio.” The public page offers two read-only tools
for real public Rally runs. The signed-in workspace offers five tools backed by
Rally's existing authenticated APIs.

| Surface | URL |
|---|---|
| Review build | <https://v2-native-review.rally-webmcp.pages.dev/> |
| Intended judge path | <https://rally.agent9.dev/v2/> |
| Repository | <https://github.com/Agent9AI/rally-webmcp> |
| Conservative v1 baseline | `baseline/all-things-agentic-2026` |

## The useful WebMCP flow

1. Ask ChatGPT to prepare a Rally job.
2. Rally opens its real job form with the title and definition of done filled in.
3. Edit anything on the page.
4. Ask ChatGPT to start the visible job.
5. The browser reviews the consequential call, then Rally posts the exact form to
   `POST /v1/workspace/jobs`.
6. Rally returns a real run ID. Its agents begin working through the normal queue.
7. Ask ChatGPT to open that run. The same workspace shows participating agents,
   the checklist, independent checks, progress, and available results.

OpenAI describes site tools as using the page's current interface and signed-in
session. Rally follows that model: WebMCP reuses the same authentication,
validation, idempotency, job intake, and run views as the human controls.

## Implemented tools

### Public page

| Tool | What it does |
|---|---|
| `rally_list_public_runs` | Finds real jobs in Rally's public Cloudflare D1 feed and updates the live console |
| `rally_inspect_public_run` | Opens one public run and shows its workers, checks, progress, and evidence |

Both are read-only. Returned run content is treated as untrusted data.

### Signed-in Rally workspace

| Tool | What it does | Real effect |
|---|---|---|
| `rally_prepare_job` | Opens and fills the existing Rally job form | Page state only |
| `rally_start_visible_job` | Queues the exact visible form | Starts real, potentially billable agent or media work |
| `rally_list_my_jobs` | Searches the authenticated workspace queue | Authenticated read |
| `rally_open_job` | Opens a run with agents, checks, and deliverables | Authenticated read |
| `rally_open_connection` | Takes the person to the real setup for n8n, GitHub, Cloudflare, or another supported service | Navigation and authenticated reads; the person completes provider sign-in |

The start tool does not accept a hidden prompt. It reads the form the person can
see. The existing idempotency key and workspace policy remain attached.

## Ruflo research reserve

Rally now has an optional, visibly armed research profile for unusually heavy
jobs. Open **Research reserve**, review its boundary, then press **Arm Ruflo for
this job**. WebMCP can request the same `research_mode: "ruflo"`, but it must
open and update that real control before the existing start tool can submit it.

Ruflo does not become a fourth Rally worker. Claude, Gemini, and Codex remain
accountable for checklist ownership and cross-family verification. Ruflo is a
run-scoped MCP coordinator with exactly seven facade tools for guidance,
routing, and private run memory. Rally blocks Ruflo's shell, browser, GitHub,
agent-execution, daemon, federation, connector credentials, and cross-run
memory surfaces.

The boundary is enforced three times:

1. the authenticated Worker advertises and accepts the profile only behind its
   producer feature gate;
2. the runner freezes an immutable per-run authority record, verifies Ruflo
   `3.38.20`, and never silently downgrades a rejected research job;
3. `bin/rally-ruflo` filters discovery and rejects every unapproved direct
   `tools/call`, even though Ruflo's native selector does not enforce that by
   itself.

Claude receives the strict combined MCP file. Codex keeps `--ignore-user-config`,
receives only Rally's two invocation-local MCP servers, and enables its native
web search for research runs. Gemini receives a canonical workspace MCP file
restored from the immutable authority immediately before its turn. Model sign-in
still comes from each user's own CLI subscription; an OpenAI Pro account can
authenticate Codex while Ruflo remains the local MCP coordination layer.

## Three real Rally jobs to demonstrate

### Make the WebMCP launch song

A Rally creative agent prepares the brief, Lyria creates the MP3, and a different
Rally agent must check the complete track before it can be called finished.

The existing run `r-20260901-2fb9a4` is honest work-in-progress evidence:
the MP3 exists, but only four of six checks are complete because the independent
full-file listening check remains open. Do not present it as finished.

### Turn a run into an Agent9 Insight

Ask ChatGPT to open the source run first, then fill a new writing job from the
details visible in that run. A different Rally agent checks the important
claims. The resulting article is a Rally deliverable. `source_run_id` records
the relationship, but does not copy the earlier workspace or resume that run.

Creating an unpublished Agent9 draft through n8n is the next integration gate.
Do not claim that step until Rally returns a real content ID, preview URL, and
connector receipt.

### Open a job that needs attention

Use `rally_list_my_jobs` and `rally_open_job` to take the person to the real run.
Second Wind is an existing Rally behavior inside that run: when eligible, it can
hand a blocked step to another agent without replacing the run's checklist.
Starting a new job with `source_run_id` creates a follow-up reference; it does
not resume or inherit the earlier run.

## WebMCP, MCP, and A2A in plain English

- **WebMCP** lets ChatGPT use the Rally page you have open.
- **MCP** gives Rally's workers approved business tools after you connect them.
- **A2A** lets another agent send a job into Rally.

A WebMCP call does not connect an MCP server. Connection setup remains in the
signed-in Rally workspace, and provider credentials never enter a site-tool
result.

## Existing Rally execution path

```text
ChatGPT prepares visible job
  → person reviews or edits
  → browser confirms start
  → Google control plane signs the run's deny-by-default connector grants
  → Cloudflare Worker stores the job in D1
  → Rally runner collects it
  → Gemini + Google ADK coordinate
  → specialist model workers execute
  → a different worker verifies
  → workspace shows the run and verified deliverables
```

The Worker already implements:

- `POST /v1/workspace/jobs` — authenticated, idempotent job intake;
- `GET /v1/workspace/runs` — private workspace queue;
- `GET /v1/workspace/runs/:id` — real run detail;
- `GET /v1/workspace/artifacts/:id/:name` — integrity-checked deliverables.
- `GET /v1/workspace/capabilities` — authenticated producer receipt for the
  optional Ruflo reserve.

The original `rally.agent9.dev/` root still serves the v1 Pages project. The
Worker now reserves `/v2/` for the derivative Pages project while reusing the
same origin, authenticated Rally APIs, D1, and R2.

The `/v2/` sign-in screen uses Rally's existing allowlisted email proof because
Google's embedded button may not run in ChatGPT's browser. The email includes a
ten-minute, one-use key that the person pastes into the same Rally tab. A closed
`return_path` enum keeps v1 links on `/admin/` and WebMCP links on `/v2/admin/`.

## Safety boundaries

- Workspace tools register only after successful Rally sign-in.
- Logging out aborts and removes the workspace tools.
- Every input schema is closed and bounded; handlers repeat validation.
- The start tool clearly declares that it queues real, potentially billable work.
- The browser's execution `AbortSignal` reaches the authenticated POST.
- Run timelines, agent names, and deliverable metadata are returned as untrusted.
- Credentials stay inside the page's existing authentication and connector code.
- Hosted connector grants are signed and bound to the exact run, requester, and
  workspace; the browser and D1 projections never receive credentials.
- Ruflo is off by default, applies to one submitted run, and resets to Standard
  immediately after a successful submission.
- Completed verified artifacts are fetched through the authenticated workspace
  endpoint and exposed as accessible Play/Download controls.
- Closing the page aborts the registration lifecycle.

## Repository map

```text
rally-webmcp/
├── site/
│   ├── index.html             Rally product page + plain WebMCP explanation
│   ├── app.js                 two read-only public tools
│   └── admin/
│       ├── index.html         real signed-in Rally workspace
│       ├── app.js             five authenticated workspace tools
│       └── styles.css         Rally workspace UI
├── src/worker/
│   ├── index.js               D1 job intake, workspace reads, static host routing
│   └── wrangler.jsonc         original and isolated WebMCP custom domains
├── src/                       deterministic Rally runner and media path
├── cloud/                     Google ADK coordinator and connector control plane
├── tests/
│   ├── test_webmcp_runtime.mjs
│   └── test_site.py
└── docs/
    ├── WEBMCP-CHALLENGE-SOURCEBOOK.md
    └── WEBMCP-PRODUCT-FRAME.md
```

## Verify locally

```bash
make test
node --check site/app.js
node --check site/admin/app.js
node --check src/worker/index.js
git diff --check
```

`make test` runs the Rally execution suite, product contracts, Worker routing
checks, and the behavioral contract for the two public tools.

## Honest remaining gates

- Deploy and verify the isolated `rally.agent9.dev/v2/` path.
- Run all five signed-in tools in ChatGPT's built-in browser.
- Complete the song's independent listening check.
- Connect and certify the exact n8n workflow that creates an unpublished Agent9
  draft.
- Add a one-time approval endpoint that returns the real Agent9 content ID and
  preview URL.
- Record the narrated demo and verify the Devpost entry says **Submitted**.

## Official references

- [WebMCP Challenge](https://webmcp.devpost.com/)
- [OpenAI site tools documentation](https://learn.chatgpt.com/docs/webmcp)
- [WebMCP specification](https://webmachinelearning.github.io/webmcp/)
- [Cloudflare Pages](https://developers.cloudflare.com/pages/)
