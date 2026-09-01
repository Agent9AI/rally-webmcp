# WebMCP Challenge change record

This file separates the Rally snapshot prepared for All Things Agentic from the
work added for the WebMCP Challenge.

## Conservative baseline

| Evidence | Timestamp (UTC-04:00) | Meaning |
|---|---:|---|
| First repository commit `3d4fa99` | 2026-08-28 12:25:35 | Rally history begins |
| Baseline commit `cf2e346098a136aa0a8e934d2e79b3b0306c5393` | 2026-08-31 19:51:31 | Final All Things Agentic source snapshot |
| Tag `baseline/all-things-agentic-2026` | 2026-08-31 22:21:36 | Immutable label for that snapshot |

The baseline already contained Rally's runner, agent handoffs, independent
verification, media generation, Cloudflare Worker/D1 queue, signed-in workspace,
connector architecture, A2A endpoint, and three early public-page WebMCP tools.
Judges may treat everything at or before the tag as prior work.

## Post-baseline WebMCP work

### Product correction

The first Challenge iteration added a separate page-only song, article, and
connector drafting dialog. Those examples did not start Rally agents. They were
removed after product review.

The current design preserves Rally's original product and puts useful WebMCP
operations in the authenticated Work dashboard:

- ChatGPT prepares the existing visible job form;
- a confirmed tool call submits that exact form through Rally's real job endpoint;
- ChatGPT can list and open real private workspace runs;
- the run view shows actual agents, checks, progress, and deliverables;
- ChatGPT can open the existing Connections UI without handling credentials.

### Public tools

The marketing page now exposes only:

| Tool | Behavior |
|---|---|
| `rally_list_public_runs` | Read and display Rally's real public D1 feed |
| `rally_inspect_public_run` | Open one public run and show its checks |

### Signed-in workspace tools

| Tool | Behavior |
|---|---|
| `rally_prepare_job` | Fill the real Rally form for human review |
| `rally_start_visible_job` | POST the visible form to `/v1/workspace/jobs` and return a real run ID |
| `rally_list_my_jobs` | Search the authenticated workspace queue |
| `rally_open_job` | Open the actual run, agents, checks, and results |
| `rally_open_connection` | Navigate to real service setup; provider sign-in remains human-only |

The start tool shares the same validation, identity, idempotency key, D1 receipt,
runner queue, and workspace UI as the ordinary submit button.

### Isolated deployment path

The existing Worker continues to serve the `rally.agent9.dev` root from
`agent9-rally.pages.dev`. The isolated `/v2/` path serves
`rally-webmcp.pages.dev` while reusing the established same-origin sign-in,
authenticated APIs, and D1/R2 bindings.

The original Rally repository remains unchanged.

### Verification added

- Root VM coverage for two read-only public tools, GET-only behavior, visible UI
  updates, closed schemas, and lifecycle cleanup.
- Static and behavioral contracts for five authenticated workspace tools.
- A Worker routing test proving the original and WebMCP hosts fetch different
  Pages projects and strip credentials before the internal static fetch.
- Full Rally test coverage still runs through `make test`.

## Truthful boundaries

The code now supports starting real Rally jobs from the signed-in workspace.
These claims are still prohibited until separately verified:

- The existing Lyria run is not complete; its full independent listening check
  remains open.
- n8n is not connected in the derivative configuration.
- No tool currently creates an Agent9 post or returns a real content ID.
- The `/v2/` Worker route still requires deployment verification.
- A2A is inbound job intake; it is not presented as WebMCP or MCP.

## Challenge evidence to capture

1. Open the signed-in Rally workspace in ChatGPT's browser.
2. Show the five workspace tools.
3. Prepare one visible launch job.
4. Edit one line.
5. Start it after the browser's confirmation and capture the real run ID.
6. Open the same run and show agents, checks, and a deliverable.
7. Show the original job form still performs the same operation without WebMCP.
8. Show the source, CI run, and final Devpost **Submitted** state.
