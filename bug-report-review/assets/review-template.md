# Bug report review — <KEY or title>

**Conformance:** <conforms / gaps in A,B,D> · **Fix-readiness:** <Fix-ready |
Analysable with assumptions | Blocked>

<One sentence, in plain language and free of check ids: what is missing before
analysis can start, or why it can start.>

## Blockers

| Finding | Check | What is needed |
|---|---|---|
| Stack trace | C1 | No trace as text — only `screenshot-2.png`, cropped above `Caused by:`. Needed: the full trace from the server log, pasted as text |

_(Omit this table when there are none, and say so explicitly.)_

## What the report already gives us

- **<Canonical name>** (<id>) — <quoted evidence>
- **Regression range** (C3) — "was working in 4.2 and stopped working with
  5.0" (description, ¶4)
- **Actual result, verbatim** (B3) — "Eintrag existiert bereits!" (transcribed
  from `Fehlermeldung.jpg`; not in the ticket text)

## Remaining gaps

Ranked blocker → major → minor, and within a severity by how much analysis each
one unblocks. Cap the table at ten rows: keep every blocker, fill with majors,
and close with one line naming the rest with their severities — _"and 3 further
gaps (1 major, 2 minor): …"_ — rather than dropping them silently.

| Finding | Check | Sev | Gap | Where it should live |
|---|---|---|---|---|
| Environment | A2 | major | Empty; the system is named nowhere | `Environment` field |
| Actual result, verbatim — not indexed | B3 | major | B3 passes on the transcription above, but the message exists only inside `Fehlermeldung.jpg` and cannot be searched or pasted into a test | `h3. Actual Results`, as text |
| Priority | D2 | major | Priority mirrors severity, no scheduling reason given | `Priority` + one clause |

_(and 2 further minor gaps: Component/s (A4), Problem category (D3).)_

## Scores

A check whose evidence exists but sits in an attachment, a comment or a linked
issue counts as **pass**, with the misplacement recorded separately — so the
columns need not sum to a clean verdict on their own.

| Group | pass | of which not indexed | gap | n/a |
|---|---|---|---|---|
| A — Identification & context | 3 | 1 | 2 | 0 |
| B — Reproduction | 2 | 1 | 3 | 0 |
| C — Isolation evidence | 1 | 0 | 3 | 1 |
| D — Classification | 3 | 0 | 2 | 0 |

## Assumptions I would have to make

1. <assumption> — confirm before analysis, because <consequence if wrong>.

## Next

<The single question that fits the verdict (step 4 of SKILL.md): draft
reporter questions / hand over for analysis / write the description.>

---

_Checks follow ISO/IEC/IEEE 29119-3 (structure) and IEEE 1044 (classification).
The letter-number ids are citations into `references/rubric.md`, where each
check's pass criteria are defined — quote the name, not the id, when talking to
anyone outside this review._
