# WebMCP Challenge change record

This record gives judges a conservative, reproducible boundary between the
Rally snapshot prepared for All Things Agentic and the integrated Rally v2 work
added for the WebMCP Challenge. The commit graph is authoritative if this
narrative and the repository ever disagree.

The [Official Rules](https://webmcp.devpost.com/rules) allow new projects and
existing projects meaningfully extended with WebMCP during the Submission
Period. Rally's history began after that period opened. Even so, this derivative
voluntarily treats the final All Things Agentic snapshot as prior work so the
challenge-specific delta is unambiguous.

## Evaluation boundary

| Evidence | Timestamp (UTC-04:00) | Meaning |
|---|---:|---|
| First repository commit `3d4fa99` | 2026-08-28 12:25:35 | Rally history begins inside the WebMCP Submission Period |
| General browser collaboration `c82ffcd` | 2026-08-30 08:37:07 | Three baseline page tools were added before the conservative boundary |
| Baseline commit `cf2e346098a136aa0a8e934d2e79b3b0306c5393` | 2026-08-31 19:51:31 | Final All Things Agentic source snapshot |
| Annotated tag `baseline/all-things-agentic-2026` | 2026-08-31 22:21:36 | Immutable label for the baseline commit |

```text
baseline/all-things-agentic-2026^{}
  = cf2e346098a136aa0a8e934d2e79b3b0306c5393
```

Judges may treat everything at or before that tag as context and prior work.
The WebMCP Challenge delta is the committed source after the tag.

## Disclosed baseline

The baseline already contained Rally's accountable-agent runtime, Cloudflare
Worker/D1 public console, governed server-side connector architecture, A2A
boundary, media-generation boundary, and these three root-page WebMCP tools:

| Baseline tool | Behavior at the tag |
|---|---|
| `rally_list_public_runs` | Read and filter Rally's explicitly public projection while synchronizing the visible console |
| `rally_inspect_public_run` | Open one public run and return a bounded checklist and verification receipt |
| `rally_draft_job` | Populate a visible governed job draft without submitting it |

Those tools remain part of the complete seven-tool product, but this record
does not present them as post-baseline challenge work.

## Post-baseline WebMCP Challenge extension

The final challenge experience is integrated directly into the root Rally v2
page and its existing product narrative.

### Root product and browser runtime

- `site/index.html` integrates the WebMCP story into the event bar, hero,
  navigation, proof counters, shared launch workspace, three workflow editors,
  receipts, semantic trail, effect flags, and WebMCP/Rally/MCP/A2A protocol map.
- `site/styles.css` supplies the responsive, accessible integrated workspace
  without replacing Rally's original product experience.
- `site/app.js` retains the three disclosed baseline tools and adds four
  top-level imperative tools, producing the final seven-tool registry:

| Added tool | Implemented root-page effect |
|---|---|
| `rally_stage_challenge_song` | Stage a visible, editable, original Lyria 3 Pro commission and synchronize the underlying Rally job draft |
| `rally_stage_insights_draft` | Stage a visible Agent9 Insights title, deck, and article while accurately describing—but not invoking—the human-approved n8n-to-EmDash draft route |
| `rally_stage_connector_plan` | Stage one fixed-profile MCP admission plan without accepting an endpoint or credential |
| `rally_review_visible_draft` | Read the selected human-edited song, Insights, or connector draft as untrusted data and update its deterministic receipt |

The root runtime also adds:

- closed schemas and matching handler validation;
- compact structured results;
- execution cancellation checks;
- one registration-lifecycle `AbortController` released on `pagehide`;
- visible human revision tracking without copying field contents; and
- explicit `generated`, `transmitted`, `stored`, `published`, and `connected`
  false-effect fields for the three stage tools and generic reviewer.

### Governed media and product narrative

- `src/media.py` adds the WebMCP Challenge-specific Lyria brief and routing
  contract. It teaches WebMCP, keeps WebMCP/MCP/A2A distinct, requires original
  work, rejects named-artist imitation, and preserves the existing generation
  and independent-verification boundary.
- `src/runner.py` keeps the browser-prepared creative task inside Rally's
  existing deterministic authority and media receipt path; the browser tool
  itself does not invoke that path.

### Verification and evidence

- `tests/test_webmcp_runtime.mjs` captures all seven root registrations and
  behaviorally tests public D1 reads, governed job drafting, song staging,
  Insights staging, connector staging, human edit and untrusted review,
  execution and lifecycle abort, closed inputs, compact receipts, and absence
  of unintended writes.
- `tests/test_site.py` checks the integrated root markup, seven-tool copy,
  feature detection, and security headers.
- `tests/test_media.py` checks WebMCP-specific Lyria routing, protocol accuracy,
  originality, and bounded media behavior.
- `README.md`, `docs/WEBMCP-PRODUCT-FRAME.md`, and
  `docs/WEBMCP-CHALLENGE-SOURCEBOOK.md` document the final root product,
  official requirements, and truthful execution boundaries.

## What the seven tools do not prove

No WebMCP stage or review tool generates a song, submits a job, invokes n8n,
creates an EmDash record, publishes an article, authorizes or connects an MCP
server, sends a message, or deploys to Cloudflare.

The public evidence tools make bounded GET requests to Rally's explicitly
public Cloudflare D1 projection. The draft, stage, and review tools add no
network write. Any downstream executor is challenge evidence only if it is
committed, tested, demonstrated in the live app, and accurately described.

WebMCP also does not grant Rally browser-wide recording. The semantic trail
contains only Rally tool turns and committed field-revision labels on the
current page—not history, other tabs, screenshots, field contents, raw
keystrokes, cookies, credentials, or model reasoning.

## What judges should evaluate

Please evaluate the complete Rally v2 experience, while attributing the
post-tag challenge delta to:

1. seven real top-level `document.modelContext` registrations in the root app;
2. three materially different uses inside one coherent Rally workspace;
3. structured public-evidence inspection before creative action;
4. shared visible state, human revision, and untrusted agent read-back;
5. explicit separation of WebMCP, governed server-side MCP, A2A, and Rally
   authority; and
6. behavioral tests proving cancellation, validation, compact receipts, and no
   silent external writes.

## Reproduce the comparison

```bash
git rev-parse baseline/all-things-agentic-2026^{}
git show --no-patch --format=fuller baseline/all-things-agentic-2026
git log --date=iso-strict --format='%H %aI %s' \
  baseline/all-things-agentic-2026..HEAD
git diff --stat baseline/all-things-agentic-2026...HEAD
git diff baseline/all-things-agentic-2026...HEAD -- \
  site/index.html site/app.js site/styles.css \
  src/media.py src/runner.py tests/test_webmcp_runtime.mjs
```

The submitted repository, root Pages deployment, README, and video must be
frozen together after the deadline so this comparison continues to match what
judges can run.
