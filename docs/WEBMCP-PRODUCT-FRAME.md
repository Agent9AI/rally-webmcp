# Rally v2 — WebMCP product frame

## Decision

**Product:** Rally v2

**Devpost title:** Rally for WebMCP

**Promise:** ChatGPT opens the door. Rally's agents do the work.

**Repository:** `rally-webmcp`
**Judge path:** `https://rally.agent9.dev/v2/` after deployment verification

## Product test

A WebMCP feature belongs in the main demo only if it does one of these things in
the real Rally product:

1. prepares the existing visible job form;
2. starts that exact job through the authenticated queue;
3. opens a real run, agent turn, check, or deliverable; or
4. takes the person to an existing connection they can safely complete.

A page-only text generator does not pass this test.

## Primary flow

```text
person asks ChatGPT for an outcome
  → ChatGPT fills Rally's real job form
  → person edits or reviews the request
  → browser confirms “start”
  → Rally returns a real run ID
  → Rally agents divide and perform the work
  → another agent checks it
  → ChatGPT opens the same run and result
```

This is useful WebMCP because the person and ChatGPT share the live Rally
workspace and signed-in session. The tool calls reuse operations the product
already supports.

## Main demo job

Use one coherent launch job:

> Make our WebMCP launch package: an original song and an Agent9 Insights
> article based on Rally's real run evidence.

The short demo should show:

1. `rally_prepare_job` opens the real form.
2. The person edits one line or chorus idea.
3. `rally_start_visible_job` receives browser review and submits the visible
   form.
4. Rally returns a real run ID.
5. After a time cut, `rally_open_job` shows participating agents, checks, and
   available results.
6. If n8n is genuinely connected by then, the run may expose one exact pending
   “Create Agent9 draft” action. Do not show that state until it returns a real
   content ID and preview URL.

## Tool strategy

### Public page

| Tool | Role |
|---|---|
| `rally_list_public_runs` | Search real public Rally work |
| `rally_inspect_public_run` | Open one public run and its checks |

### Signed-in workspace

| Tool | Role | Side effect |
|---|---|---|
| `rally_prepare_job` | Fill the visible form | Page only |
| `rally_start_visible_job` | Queue the visible form | Starts real agent/media work |
| `rally_list_my_jobs` | Search private runs | Authenticated GET |
| `rally_open_job` | Open agents, checks, and results | Authenticated GET |
| `rally_open_connection` | Open existing service setup | Navigation + authenticated GET |

The registry stays small. Song, article, and recovery are job examples—not
separate tools—because Rally should remain general.

## Plain-language protocol map

| Name | What it means here |
|---|---|
| WebMCP | ChatGPT can use the Rally page the person has open |
| MCP | Rally workers can use a connected business service |
| A2A | Another agent can send a job into Rally |
| Rally | Runs the team, preserves evidence, and prevents self-approval |

Keep this map in documentation or one disclosure. Do not lead the product with
protocol terminology.

## User-visible states

### Prepare

- Job form opens.
- Title and finished result are visible.
- Nothing is running yet.
- Person may edit any field.

### Start

- Tool description says real, potentially billable agents or media may run.
- Browser applies its normal safety review.
- Rally uses the page's signed-in identity.
- The response contains a real run ID and acceptance time.

### Running

- Workspace queue shows the job.
- Run detail shows the actual workers and checklist.
- Refresh uses the existing 13-second workspace poll.

### Complete

- A different worker has approved every required check.
- Verified deliverables can be opened or downloaded through the existing
  authenticated artifact endpoint.

### Failure

- Form input remains available when the POST fails.
- The existing idempotency key is reused on a safe retry.
- The error says nothing was queued when acceptance did not complete.

## Song truth

The real run `r-20260901-2fb9a4` produced a 63.7-second Lyria MP3. It is not a
finished success: four of six checks are complete and the required independent
full-file listening check is still open.

The final demo may call it “audio created” but not “verified” or “complete” until
a different Rally worker listens to the full artifact and closes the remaining
checks.

## Agent9 Insight truth

Rally can commission a writer and independent checker now. The repository also
contains an n8n connector adapter. It does not yet contain proof of a connected
tenant workflow creating a real Agent9 draft.

The main UI must not claim publication or draft creation until a real execution
returns:

- connector and tool name;
- approved payload digest;
- one-time approval ID;
- resulting Agent9 content ID;
- preview URL; and
- redacted execution receipt.

## Deployment frame

The Worker chooses its static Pages project by path:

```text
rally.agent9.dev/
  → agent9-rally.pages.dev

rally.agent9.dev/v2/
  → rally-webmcp.pages.dev
```

Both paths reuse Rally's authenticated Worker endpoints. This leaves the v1
static project untouched while giving the derivative a same-origin workspace.
The v2 screen uses Rally's allowlisted, one-use email proof because Google's
embedded button may not run in ChatGPT's browser. The user pastes the emailed
key into the same Rally tab; an exact return-path enum keeps v1 and v2 links on
their respective admin routes.

Before release:

- deploy the derivative Pages project to its production alias;
- deploy the Worker route and verify both hosts;
- test login, job POST, run reads, artifact reads, and logout under the `/v2/` path.

## Demo outline under three minutes

1. **0:00–0:20 — Value.** “ChatGPT can use Rally with me; Rally's agents still
   do and check the work.”
2. **0:20–0:45 — Prepare.** Ask for the launch package; show the visible form.
3. **0:45–1:00 — Edit.** Change one line.
4. **1:00–1:20 — Start.** Confirm the consequential tool call; show real run ID.
5. **1:20–2:15 — Result.** Time cut; open the same run, agents, checks, and MP3
   or article deliverable.
6. **2:15–2:35 — Connection.** Ask ChatGPT to open n8n setup. Explain only that
   Rally workers use connected services; do not claim draft creation unless live.
7. **2:35–2:50 — Proof.** Show tool list and green CI.
8. **2:50–3:00 — Close.** “ChatGPT opens the door. Rally's agents do the work.”

## Release gates

- [x] Original Rally product identity preserved
- [x] Page-only song/article/connector studio removed
- [x] Two read-only public tools
- [x] Five authenticated workspace tools
- [x] Real job POST reused by human and WebMCP paths
- [x] Real run and connection views reused
- [x] Closed schemas, handler validation, abort propagation, lifecycle cleanup
- [x] Original and derivative static origins separated by path
- [ ] Deploy and verify `rally.agent9.dev/v2/`
- [ ] Invoke all five workspace tools in ChatGPT's browser
- [ ] Finish independent song listening check
- [ ] Connect and certify the Agent9 n8n workflow
- [ ] Return a real Agent9 draft ID and preview URL
- [ ] Record public narrated demo
- [ ] Confirm Devpost says **Submitted**
