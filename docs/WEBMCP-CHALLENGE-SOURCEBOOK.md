# WebMCP Challenge sourcebook

Verified against official Devpost and OpenAI material on August 31, 2026. This
is a release reference, not a replacement for the
[Official Rules](https://webmcp.devpost.com/rules). The rules state that they
prevail over inconsistent challenge materials.

## Authoritative clock

| Event | Official Rules time |
|---|---|
| Registration and Submission Period | August 25, 2026 at 11:00 AM PT through September 3, 2026 at 1:00 PM PT |
| Judging Period | September 4, 2026 at 10:00 AM PT through September 21, 2026 at 5:00 PM PT |
| Winners announced | On or around September 23, 2026 at 2:00 PM PT |

The submission deadline is **Thursday, September 3, 2026 at 1:00 PM PDT**,
which is **4:00 PM EDT / 20:00 UTC**. The public
[schedule](https://webmcp.devpost.com/details/dates) shows noon for the opening
time, while the rules show 11:00 AM. The deadline is consistent; use the rules
for the conflicting start time.

## Final submission means submitted

A saved draft is not an entry. Before the deadline:

1. Complete every required Devpost step.
2. Add all teammates and confirm that each invitation was accepted.
3. Agree to the terms and click the final **Submit project** control.
4. Confirm the green submission notification.
5. Confirm that My Projects labels the entry **Submitted**, not Draft.

The [organizer deadline update](https://webmcp.devpost.com/updates/46123-halfway-there-where-are-you)
and [Devpost's submission instructions](https://help.devpost.com/article/122-how-to-enter-a-submission)
both distinguish a draft from a submitted project. Devpost's
[form guide](https://help.devpost.com/article/126-know-your-submission-steps)
describes the standard team, project name, tagline, project story, technology
tags, live link, media, additional-details, terms, and final-submit steps.

## Required project and submission

The project must be a working WebMCP-powered web app in which people and agents
can interact, collaborate, and create together. It must run consistently on
its intended platform and behave as shown in the description and video.

The submission must include:

- A working live URL accessible in ChatGPT's in-app browser or Google Chrome
  with WebMCP enabled.
- Testing instructions and credentials if authentication is required.
- A text description explaining why the use case fits WebMCP, how it improves
  the user experience, what people and agents can now do together, and how
  WebMCP was implemented.
- A public GitHub, GitLab, or Bitbucket repository containing all source,
  assets, and instructions needed for the project to function.
- A detectable open-source license visible at the top/About area of the
  repository.
- A public YouTube demonstration video that is **less than three minutes** and
  includes both a clear working demo and narration covering what was built and
  how WebMCP was used.
- English materials, or complete English translations of every submitted
  artifact and testing instruction.

The live project must remain free and available without restriction to the
Sponsor, Administrator, and judges through the end of judging. Judges may test
it, but they may instead judge from the submitted description, images, video,
and repository. See the [overview](https://webmcp.devpost.com/),
[rules](https://webmcp.devpost.com/rules), and
[resources/FAQ](https://webmcp.devpost.com/resources).

## New and existing work

A project may be created during the Submission Period. A project that existed
before the period must be meaningfully extended with WebMCP after the period
began, and only the new work is evaluated. The entrant must distinguish prior
work from new work with dated commits or equivalent evidence.

Rally's conservative boundary is documented in
[`HACKATHON_CHANGES.md`](../HACKATHON_CHANGES.md): tag
`baseline/all-things-agentic-2026` resolves to commit `cf2e346`, and the
post-tag commit range is the challenge extension.

Third-party SDKs, APIs, data, code, media, and other materials may be used only
with the necessary authorization and licenses. The project must be original,
entrant-owned, non-infringing, and free of malicious code.

## Video and music constraints

Challenge-specific rules require YouTube even though generic Devpost forms can
embed other hosts. Use a duration below 3:00, make the video public rather than
private or unlisted, and include explanatory narration. The organizer states
that AI text-to-speech narration is acceptable; music without narration is not.

Do not include third-party trademarks, copyrighted music, samples, lyrics, or
other protected material without permission. A Lyria demonstration should use
an original composition and retain evidence that the API and generated output
are authorized for the submission. The
[organizer build update](https://webmcp.devpost.com/updates/46116-6-days-left-to-build)
contains the current video clarification.

## Judging and tie-break order

Stage One is pass/fail: the project must meet a baseline of viability, fit the
theme, and reasonably apply the required featured technology.

Projects that pass are scored equally on:

1. **WebMCP Leverage** — thorough, skillful, working, non-trivial use.
2. **Execution** — a coherent runnable product rather than only a proof of
   concept.
3. **Potential Impact** — a credible problem, audience, and demonstrated
   solution.
4. **Creativity & Ambition** — novelty and differentiation.

Ties are resolved in that same order: WebMCP Leverage, Execution, Potential
Impact, then Creativity & Ambition. If all four remain tied, the judges vote.
Judging may use one or more rounds and may combine expert, peer, or automated
analysis. The [rules](https://webmcp.devpost.com/rules) are controlling.

## Browser and API compatibility

The rules tell entrants to test with either:

- the ChatGPT desktop app's in-app browser; or
- Chrome 149 or later after enabling
  `chrome://flags/#enable-webmcp-testing` and restarting Chrome.

OpenAI's current [Site tools documentation](https://learn.chatgpt.com/docs/webmcp)
adds these judge-facing constraints:

- Register tools with JavaScript through `document.modelContext.registerTool`
  in the top-level page.
- ChatGPT's browser does not currently expose declarative HTML-form tools or
  tools registered inside iframes.
- Tools belong to their page and may become unavailable after navigation or
  closure.
- GPT-5.6 Sol and Terra support site tools; Luna currently has them disabled.
- Site tools are not currently available in Enterprise or Edu workspaces.
- Preserve the ordinary interface for people and browsers without WebMCP.

Compatibility is established by testing the deployed URL, not merely by
registering tools in a local development browser.

## Security and truthful effects

Website-provided tool definitions, page content, and results are untrusted.
OpenAI documents a safety review for each built-in-browser invocation, while
ordinary confirmation requirements still apply to consequential actions.
Those checks do not make a website or its output trustworthy.

Each Rally tool should therefore:

- use a narrow, closed input schema and bounded values;
- describe side effects accurately;
- use the application's existing authentication, authorization, and input
  validation;
- return enough information to verify the result;
- treat human-editable or externally sourced page content as untrusted; and
- distinguish staging from generation, publication, connection, deployment,
  or any other external write.

WebMCP is not a browser-wide interaction recorder. The browser can show recent
tool activity, but the page does not thereby gain access to other tabs,
browsing history, screenshots, credentials, or raw keystrokes.

## Post-deadline freeze

Before the deadline, drafts may be edited freely. After the deadline, use the
strictest official challenge instruction and do not change:

- the Devpost submission;
- the submitted repository or referenced branch/tag;
- the live site;
- the YouTube video; or
- the team roster.

The [FAQ](https://webmcp.devpost.com/resources) warns that changes during
judging can risk eligibility and recommends continuing only in a separate
fork. Keep the submitted version frozen until the actual winner announcement.
The rules allow only Sponsor/Devpost-approved, substantively identical
corrections for third-party rights, personal information, or inappropriate
material.

There is a wording conflict: Rule 6 and generic Devpost help permit changes to
the portfolio copy after the deadline, while the challenge FAQ and organizer
updates say not to touch the repo or live site. The safe release policy is the
full freeze above.

## Known official ambiguities and clarifications

- **Submission opening time:** rules say 11:00 AM PT; schedule says noon. The
  rules prevail. The closing time is consistently 1:00 PM PDT.
- **Video typo:** one FAQ sentence says there is no video, but the rules,
  overview, FAQ's video answer, and organizer updates all require one.
- **Repository snippet:** the rules show a `search_products` registration
  snippet without clearly saying whether that exact tool is mandatory. A
  [public question](https://webmcp.devpost.com/forum_topics/45006-enforced-code-snippet-requested)
  remained unanswered at verification time. Expose the real registration code
  prominently rather than relying only on a framework abstraction.
- **Dataset scope:** an organizer clarified that a representative test dataset
  is acceptable when it is sufficient to run and evaluate the project; the
  repo still needs everything necessary to function. See the
  [organizer reply](https://webmcp.devpost.com/forum_topics/45004-must-a-public-repo-include-the-full-production-dataset-for-an-existing-webmcp-app).
- **Multiple submissions:** multiple substantially different projects are
  allowed, but an organizer stated that an entrant will not win more than once.
  See the [manager clarification](https://webmcp.devpost.com/forum_topics/44943-clarification-on-submission-limit-one-entry-per-entrant).
- **A2A:** the official challenge pages do not list A2A as a requirement or
  judging category. It may provide context, but it cannot substitute for the
  required working WebMCP implementation.

## Official source index

- [Challenge overview](https://webmcp.devpost.com/)
- [Official Rules](https://webmcp.devpost.com/rules)
- [Schedule](https://webmcp.devpost.com/details/dates)
- [Resources and FAQ](https://webmcp.devpost.com/resources)
- [Organizer: halfway checklist](https://webmcp.devpost.com/updates/46123-halfway-there-where-are-you)
- [Organizer: build and video guidance](https://webmcp.devpost.com/updates/46116-6-days-left-to-build)
- [Devpost: submission steps](https://help.devpost.com/article/126-know-your-submission-steps)
- [Devpost: how to enter a submission](https://help.devpost.com/article/122-how-to-enter-a-submission)
- [OpenAI: Site tools (WebMCP)](https://learn.chatgpt.com/docs/webmcp)
