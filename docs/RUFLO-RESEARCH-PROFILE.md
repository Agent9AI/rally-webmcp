# Ruflo research profile

Scope: the guarded research control and its run-scoped execution boundary.

This document defines the shipped contract for Rally's guarded Ruflo control.
The browser may request the profile, but only the Worker producer gate and the
runner's immutable authority can activate it. It never widens connector
authority.

## Compact wireframe

```text
Expertise                 Autonomy
[ Focused | Specialist ]  [ Guarded | Resilient ]

┌ Research reserve             Standard · Ruflo off ┐
│ [ Review Ruflo reserve                            + ]
└─────────────────────────────────────────────────────┘

Expanded
┌ Research reserve             Standard · Ruflo off ┐
│ [ Review Ruflo reserve                            × ]
│ Ruflo shares run-only research routing + memory.   │
│ • no daemon/background workers                     │
│ • no shell, browser, or GitHub access               │
│ • no cross-run memory                               │
│ [ Arm Ruflo for this job ]                          │
└─────────────────────────────────────────────────────┘
```

## Control contract

| Element | Hook | Initial contract |
|---|---|---|
| Reserve root | `data-research-reserve` | `data-state="sealed"` |
| Cover button | `data-research-cover` | `aria-expanded="false"`; controls `research-reserve-panel` |
| Disclosure panel | `data-research-panel` | `hidden`; labelled by the cover button |
| Arm button | `data-research-arm` | `aria-pressed="false"`; described by the safety list |
| State announcement | `data-research-state` | `Standard · Ruflo off`; polite, atomic live status |
| Composer summary | `data-composer-research` | `Standard research` |

The cover is a disclosure control only. Opening or closing it never changes research mode. The arm button is the sole user action that may request Ruflo. Arming first reads the authenticated `GET /v1/workspace/capabilities` receipt and requires Ruflo `3.38.20` with `run_only` scope.

## States and transitions

### Sealed — default

- Root: `data-state="sealed"`
- Cover: `aria-expanded="false"`
- Panel: `hidden`
- Arm: `aria-pressed="false"`
- State: `Standard · Ruflo off`
- Composer: `Standard research`

### Reviewing

Activating the cover with pointer, Enter, or Space removes `hidden`, sets `aria-expanded="true"`, and moves focus only when the user explicitly opened the panel. Closing the cover restores focus to the cover and does not arm or disarm Ruflo.

### Arming

Activating the arm button begins the implemented bounded capability check. While pending:

- preserve the open panel and its safety copy;
- set the reserve or arm button `aria-busy="true"`;
- disable only the arm button to prevent duplicate requests;
- keep `aria-pressed="false"` and standard mode until the check succeeds.

### Armed

- Root: `data-state="armed"`
- Arm: `aria-pressed="true"`
- State: `Ruflo armed · this run only`
- Composer: `Ruflo research · this run only`

Amber and red are reserved for this state because arming expands cost and orchestration. Color is reinforced by the words `armed` and `this run only`; color never carries the state alone. Activating the pressed arm button disarms the reserve and returns to Standard.

### Failure or unavailable capability

An unsuccessful arm attempt must fail closed:

- remain in Standard mode;
- restore `aria-pressed="false"` and re-enable the arm button;
- keep the panel open with the preserved safety facts;
- announce `Standard · Ruflo unavailable` plus one actionable reason and retry path;
- return focus to the arm button if focus would otherwise be lost.

Failure never silently downgrades an already submitted Ruflo request or changes connectors. Before submission, the UI remains Standard. After submission, a runner-side pin or authority failure terminates the run as `research_unavailable` before model execution and returns an honest action-needed report.

Submitting or resetting the job snapshots the visible state. A fresh form returns to sealed Standard. Closing the assistant setup leaves the chosen state intact only for the current unsent form.

## Safety facts

When armed, Ruflo may provide shared research routing and run-only memory across the accountable Claude, Gemini, and Codex workers. It remains subordinate to Rally's existing ownership and independent-verification rules.

The exact facade allowlist is:

- `guidance_recommend`
- `guidance_workflow`
- `guidance_quickref`
- `hooks_route`
- `memory_store`
- `memory_retrieve`
- `memory_search`

`tools/list` is filtered into this deterministic order. A direct call to any
other name—including prefix collisions—is rejected locally with JSON-RPC
`-32601` and is never forwarded to Ruflo.

The profile explicitly provides:

- no daemon or background workers;
- no shell execution;
- no browser automation;
- no GitHub access;
- no memory shared with another run;
- no new connector, credential, or provider authority;
- no permission for a Ruflo helper to own or verify a Rally checklist item.

If any of these facts cannot be enforced, the arm operation fails and Standard remains selected.

## Accessibility and responsive behavior

- Both actions remain native buttons with at least a 44 CSS-pixel target; mobile raises the arm target to 48 pixels.
- Focus uses Rally's existing visible focus ring. No positive `tabindex` is introduced.
- The disclosure relationship is expressed with `aria-controls`, `aria-expanded`, and `hidden`.
- The pressed relationship is expressed independently with `aria-pressed`.
- State changes are announced through the dedicated polite live region, not by rewriting the button's accessible name.
- At narrow widths, the status label stacks above its value, long safety copy wraps, and the action remains full width.
- The cover icon rotation is non-essential and is disabled when reduced motion is requested.

## Verification matrix

The release gates recheck:

1. sealed → reviewing → sealed with pointer and keyboard;
2. reviewing → arming → armed;
3. reviewing → arming → unavailable → retry;
4. armed → disarmed;
5. form reset and composer summary synchronization;
6. 320 px, 640 px, and wide workspace layouts;
7. reduced-motion behavior and visible focus throughout.

## Runtime path

```text
visible arm control / WebMCP prepare
  → authenticated capability receipt
  → POST /v1/workspace/jobs with research_mode="ruflo"
  → durable dashboard envelope
  → runner verifies pinned Ruflo and writes run-private authority
  → strict Claude config | canonical Gemini config | isolated Codex overrides
  → Rally-owned MCP facade
  → seven reviewed tools only
```

The standard profile preserves the legacy job fingerprint and writes no Ruflo
files. Deployment must activate the consumer runner before enabling the Worker
producer flag, so a queued Ruflo job can never outrun its consumer.

Verification commands:

```bash
make test
make check
python3 -m unittest discover -s tests -p 'test_research.py'
python3 -m unittest discover -s tests -p 'test_ruflo_proxy.py'
```
