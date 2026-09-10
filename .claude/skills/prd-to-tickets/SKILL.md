---
name: prd-to-tickets
description: Use when a product owner or PM provides a PRD, spec, feature brief, or requirements doc and wants it broken down into Jira-ready Epics and Stories with acceptance criteria. Produces a Word (.docx) document for the user to review and amend before anything is created in Jira — this skill never creates or modifies Jira issues directly. Triggers on requests like "turn this PRD into tickets", "create epics and stories from this spec", "break this down for Jira", "generate acceptance criteria for these requirements".
---

# PRD → Epics & Tickets (Word draft)

Turn a PRD/spec into a clean, Jira-ready breakdown of Epics and Stories with
acceptance criteria, delivered as a **Word document draft** — never write
directly to Jira. The output is something a product owner can read, edit,
and reorganize before anyone imports it.

## Process

### 1. Get the source material

You need the actual PRD/spec content before doing anything else. Accept it
as:
- A file path in the repo or an uploaded/attached document (read it fully —
  use the `docx` or `pdf` skill if it's a `.docx`/`.pdf`, plain `Read` for
  markdown/text).
- Pasted text in the conversation.

If nothing has been provided yet, ask for it (file, paste, or upload) rather
than guessing at scope. Do not fabricate requirements that aren't in the
source.

### 2. Clarify only real blockers

Skim the PRD for gaps that would force you to guess at scope: missing user
roles/personas, no success criteria, contradictory requirements, or a scope
boundary that's genuinely unclear (e.g. "is X in or out of this release?").
Batch these into a single round of targeted questions (`AskUserQuestion`).

Don't ask about things you can reasonably infer or that a PM would rather
adjust in the Word doc afterward (e.g. exact story point sizing, minor
wording). Default to producing a complete draft and flagging assumptions
inline (see step 6) rather than stalling on every ambiguity.

### 3. Identify Epics

Group the PRD's functionality into Epics — the major themes or deliverable
chunks of work (typically 3–8 for a normal PRD). Each Epic should be:
- Independently shippable or at least independently meaningful as a
  milestone.
- Named as a short noun phrase (e.g. "Rate Alert Notifications", not
  "Implement the alerting system so users can be notified").

Skip epics for pure infrastructure/tech-debt unless the PRD calls it out —
stay scoped to what the PRD actually asks for.

### 4. Break each Epic into Stories

Under each Epic, write Stories that are:
- **Small and testable** — one story = one piece of demonstrably-working
  behavior. If a story needs "and" to describe it, consider splitting it.
- **Independent where possible** — call out dependencies explicitly rather
  than silently ordering them.
- Written from the user/actor's perspective when the PRD describes
  user-facing behavior; written as a plain task when it's backend/technical
  (data model, API contract, infra) with no natural "user".

Follow INVEST (Independent, Negotiable, Valuable, Estimable, Small,
Testable) as the quality bar.

### 5. Write acceptance criteria

Every story gets 3–6 acceptance criteria in **Given/When/Then** form,
covering the happy path plus the real edge cases the PRD implies (errors,
empty states, permission boundaries, limits). Avoid vague criteria like
"works correctly" — each one must be checkable by someone who didn't write
the code.

### 6. Assemble the Word document

Use the `docx` skill to generate the file. Structure:

- **Title page / header**: PRD name, source document reference, date
  generated, "DRAFT — for review before Jira import" notice.
- **Summary table**: one row per Epic with a short description and story
  count, so the PO can see the shape of the breakdown at a glance.
- **Assumptions & Open Questions** section: anything you inferred rather
  than found explicitly in the PRD, and anything still ambiguous that the
  PO should resolve before import. Be honest here — this is what makes the
  draft safe to hand off.
- **One section per Epic** (Heading 1: `EPIC-<n>: <name>`), containing:
  - A 2–4 sentence Epic description (the "why").
  - Each Story (Heading 2: `<n>.<m> <story title>`) with:
    - User story statement (`As a ___, I want ___, so that ___`) or task
      description for non-user-facing stories.
    - Bulleted Acceptance Criteria (Given/When/Then).
    - A blank "Notes" line if there's a dependency or open question specific
      to that story.

Use real Word styles (Heading 1/2, bullet lists, a proper table) — not
manually bolded plain paragraphs — so the doc is easy to navigate and the PO
can comment/track-change it in Word.

Save the file with a descriptive name, e.g. `<prd-name>-tickets-draft.docx`.

### 7. Deliver and hand off

Send the finished `.docx` to the user (`SendUserFile`). In your reply,
summarize: how many Epics/Stories were produced, and point to the
Assumptions & Open Questions section as the first thing to check. Remind
them this is a draft — nothing has been created in Jira, and they should
review/amend it before doing so.

## Quality checklist before delivering

- [ ] Every story has acceptance criteria — none skipped.
- [ ] No story silently invents functionality not implied by the PRD.
- [ ] Titles are concise (aim under ~8 words) and describe outcomes, not
      implementation steps.
- [ ] Assumptions/open questions are called out, not buried or omitted.
- [ ] The doc uses real Word heading/list styles, not manual formatting.
