# WebMCP Challenge change record

This record gives judges a conservative, reproducible boundary between the
Rally snapshot prepared for All Things Agentic and the work added for the
WebMCP Challenge. The commit graph is authoritative if this narrative and the
repository ever disagree.

The [official rules](https://webmcp.devpost.com/rules) allow projects created
during the Submission Period and also allow existing projects that were
meaningfully extended with WebMCP during that period. Rally's first commit was
created after the period opened. Even so, this submission voluntarily treats
the final All Things Agentic snapshot as prior work so that the WebMCP-specific
extension is easy to audit.

## Evaluation boundary

| Evidence | Timestamp (UTC-04:00) | Meaning |
|---|---:|---|
| First repository commit `3d4fa99` | 2026-08-28 12:25:35 | Rally history begins inside the WebMCP Submission Period. |
| General browser-collaboration commit `c82ffcd` | 2026-08-30 08:37:07 | Added the three baseline WebMCP tools disclosed below. |
| Baseline commit `cf2e346098a136aa0a8e934d2e79b3b0306c5393` | 2026-08-31 19:51:31 | Final All Things Agentic source snapshot. |
| Annotated tag `baseline/all-things-agentic-2026` | 2026-08-31 22:21:36 | Immutable label for the same baseline commit. |

The annotated tag peels to the baseline commit:

```text
baseline/all-things-agentic-2026^{}
  = cf2e346098a136aa0a8e934d2e79b3b0306c5393
```

Judges may treat everything at or before that tag as context and prior work.
The WebMCP Challenge delta is the committed source after that tag.

## Disclosed baseline work

The baseline already included Rally's core accountable-agent runtime,
Cloudflare-backed public console, governed server-side connector architecture,
A2A surface, media-generation boundary, and three general WebMCP tools:

| Baseline tool | Existing behavior at the tag |
|---|---|
| `rally_list_public_runs` | Searches Rally's explicitly public run projection and synchronizes the visible console. |
| `rally_inspect_public_run` | Opens one public run and returns a bounded checklist and verification receipt. |
| `rally_draft_job` | Populates a visible job draft for human review without submitting it. |

These three tools demonstrate the underlying browser integration, but this
change record does not present them as post-baseline WebMCP Challenge work.

## WebMCP Challenge extension

The post-baseline work turns the existing surface into a challenge-specific,
human-agent creative workflow:

- `site/app.js` adds `rally_stage_challenge_song`, which stages a visible,
  editable Lyria 3 Pro commission. It reports that generation, storage, and
  transmission have not started and that human confirmation is required.
- `site/app.js` adds `rally_review_visible_song_task`, which reads the
  human-edited page draft as untrusted content, applies bounded deterministic
  checks, and returns the draft to the human for a decision.
- `site/index.html` and `site/styles.css` add the shared task receipt and a
  page-local semantic collaboration trail for agent staging, human revision,
  and agent review.
- `src/media.py` adds a WebMCP Challenge-specific music brief that keeps
  WebMCP, server-side MCP connectors, and A2A roles distinct; requires original
  work; and rejects artist imitation and unsupported claims.
- `tests/test_webmcp_runtime.mjs` exercises the registered runtime contract:
  stage, human edit, untrusted read-back, and review. The Python site and media
  tests add matching contract checks.
- `site/webmcp/` contains the dedicated judge-facing shared-browser studio.
  Its final committed implementation exposes four top-level imperative tools:
  `rally_webmcp_stage_song`, `rally_webmcp_stage_insights`,
  `rally_webmcp_stage_connector`, and
  `rally_webmcp_review_visible_draft`. The first three stage separate visible
  workflows; the fourth reads the current human-editable revision as untrusted
  content and updates its deterministic receipt. The committed implementation
  and tests, rather than mockups or future plans, define the submission.
- `tests/test_webmcp_studio_runtime.mjs` captures and invokes all four studio
  registrations, exercises song, Insights, and connector staging plus review,
  rejects invalid and cancelled calls, and proves the static studio has no
  network primitive.
- `docs/WEBMCP-CHALLENGE-SOURCEBOOK.md` records the controlling challenge and
  browser requirements used for release decisions.

No post-baseline browser tool should be credited with an external action it
does not perform. In the current contract, staging and review do **not**
generate audio, publish an article, connect a server, send a message, or deploy
to Cloudflare. Any later executor is part of the submission only if it appears
in a committed post-baseline diff, is demonstrated in the live app, and is
covered by the final evidence.

## What judges should evaluate

Please evaluate the complete user experience, but attribute the WebMCP
Challenge extension to the post-tag delta:

1. Real JavaScript tool registration with closed input schemas and bounded
   handlers.
2. Agent and human collaboration through the same visible, editable page
   state.
3. Explicit trust and authority boundaries: untrusted page content, no silent
   downstream action, and a retained human decision.
4. Three distinct WebMCP uses in one coherent studio: an original Lyria brief,
   an Agent9 Insights draft, and governed MCP connector onboarding.
5. Accurate separation of WebMCP, Rally's server-side MCP gateway, and A2A.
6. Runtime and media tests that verify the stated behavior and absence of
   silent external writes.

## Reproduce the comparison

```bash
git rev-parse baseline/all-things-agentic-2026^{}
git show --no-patch --format=fuller baseline/all-things-agentic-2026
git log --date=iso-strict --format='%H %aI %s' \
  baseline/all-things-agentic-2026..HEAD
git diff --stat baseline/all-things-agentic-2026...HEAD
git diff baseline/all-things-agentic-2026...HEAD
```

The submitted repository and live application must be frozen together after
the deadline so this comparison continues to match the experience judges see.
