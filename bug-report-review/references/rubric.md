# Rubric — pass criteria

Load this when a check is borderline, when the user challenges a verdict, or
when drafting reporter questions. Each check lists what makes it pass, what
looks like a pass but is not, and the gap severity.

Verdict per check: `pass` / `gap` / `n/a`. Never invent a fourth state, and never
mark `gap` on a check that cannot apply to this defect. `n/a` covers two cases —
the check cannot apply, or the data it needs was not available (pasted text
without fields, an attachment you could not download) — so always say which.

## Canonical check names

**Every id is written with its name**, and the name below is the only wording to
use (SKILL.md, step 4, explains why).

| id | Canonical name | id | Canonical name |
|---|---|---|---|
| A1 | Summary | C1 | Stack trace |
| A2 | Environment | C2 | Failing vs. working input |
| A3 | Affects Version/s | C3 | Regression range |
| A4 | Component/s | C4 | Workaround as a trigger |
| A5 | Occurrence time | C5 | Logs and attachments |
| B1 | Reproduction steps | D1 | Severity |
| B2 | Expected result | D2 | Priority |
| B3 | Actual result, verbatim | D3 | Problem category |
| B4 | Reproducibility | D4 | Links and references |
| B5 | One defect per report | D5 | Status and disposition |

The names are deliberately neutral, so the same wording serves a `pass` row and
a `gap` row. Group names, needed for the same reason: **A — Identification &
context**, **B — Reproduction**, **C — Isolation evidence**,
**D — Classification**.

Each check's own section heading below repeats its canonical name; if the two
ever disagree, the table wins.

## The evidence-location rule (applies to every check)

Evidence counts wherever it sits, as long as a reader can reach it from the
ticket. Three locations, three verdicts:

| Where the evidence is | Verdict | How to report it |
|---|---|---|
| In the report body, labelled | `pass` | quote it |
| In an attachment, a comment, a linked issue or a remote link | `pass`, and a separate **major** "not indexed" gap | cite the file or `KEY`, and say what to look for |
| Nowhere reachable | `gap` at its own severity | ask the reporter |

Never downgrade a check to `gap` because the evidence is in the wrong place.
Report the misplacement instead — it is a cheap fix and a different problem
from missing evidence. This rule overrides every per-check section below: the
same evidence is never recorded both as a pass and as a gap of the check itself.

"Not indexed" gaps count against **conformance** only. They never change the
fix-readiness verdict.

**Screenshots are inside that second row.** Attachments — images included — can
be downloaded and read (see [jira.md](jira.md)), so a screenshot is *unindexed*
evidence, not missing evidence. Open it, transcribe what it shows, and record a
**major** "not indexed" gap. A screenshot alone still fails conformance, because
a human cannot grep it, diff it or paste it into a test — but it does not block
fix-readiness.

The exception: evidence that is genuinely unusable — an archive too large to
open, a file in a format nobody can read, an image whose relevant region is
illegible or cropped away — is not reachable, so the check is a `gap` at its own
severity. "It is an image" is not a reason on its own.

How to read and transcribe attachments — what a screenshot can settle, how to
mark a transcription, why identifiers read off an image are only probable — is
in SKILL.md, step 1.

## A — Identification & context

### A1 Summary (major)

**Pass** — names object, observable failure and trigger, and would be
recognisable in a list of 200 issues:
`Order detail shows no lines for the current day when filtering by day`

**Not a pass** — a wish (`Improve order monitoring`), a location without a
symptom (`Problem in Order Monitoring`), a severity claim (`URGENT!!! broken`),
or a summary that only repeats the component name. A ticket key from another
system as the whole summary (`SUP#12345`) fails — prefix it, do not let it
replace the sentence.

### A2 Environment (major)

**Pass** — enough to rebuild the situation: system/host or plant, stage
(prod/test/dev), the release running there, and the client (browser/GUI
version) when the defect is user-facing. `Location: SITE-B / System:
app-prod-02` passes even in prose.

**Not a pass** — "on the test system" without naming it, or an `Environment`
field left empty while the information sits nowhere else.

### A3 Affects Version/s (major)

**Pass** — exactly one concrete build in which the failure was observed.

**Not a pass** — empty, a range, "latest", or a version that contradicts the
prose. If the field disagrees with the text, that contradiction is itself the
gap: report both values.

### A4 Component/s (minor)

**Pass** — set, and plausible for the described failure. A component that
routes the ticket to the wrong team is worse than an empty one; say so.

### A5 Occurrence time (major)

**Pass** — date **and** time with enough precision to pull the server log
(minute-level for a busy system), plus the timezone or site when the reporter
and the server differ. A timestamp embedded in an attachment filename
(`..._260812_132241.xml`) counts — say where you read it.

**Not a pass** — "yesterday", "since last week", or the Jira `created`
timestamp used as a substitute — reports are often filed days after the event.

## B — Reproduction

### B1 Reproduction steps (blocker)

**Pass** — starts from a known state (which user, which role, which screen or
entry point), lists the actions in order, and carries the **concrete data**:
the order number, the part id, the filter values, the payload. A reader who
has the system can follow them without asking anything.

**Not a pass** — steps written as capability (`Check that the data is shown
correctly based on the filters and configuration`) instead of instruction; the
reader cannot tell which filters. Also fails when the data is replaced by
placeholders (`select some order`) — the defect usually depends on *which* one.

**Downgrade to major when the failing state is constructible without the
reporter.** Steps are the *convenient* form of a reproduction, not the only
one. Downgrade when **all** of these hold:

1. the discriminating precondition is stated exactly (`a manufacturer with two
   or more entries`, `an order with no routing`) — not merely implied;
2. the screen, entry point or endpoint is identifiable, from the text, a field
   or a screenshot;
3. a developer can build the state from test data, without customer records.

It stays a **blocker** when the failure depends on production data nobody can
recreate, when the entry point is unknown, or when the precondition is the very
thing under investigation. Say which of the three conditions you relied on —
this downgrade decides the verdict, so it must be auditable.

### B2 Expected result (major)

**Pass** — a rule with a source: the specification, an acceptance criterion, a
prior release's behaviour, or the customer's contract. `The day view must show
the same 15 orders as the week view, because both aggregate the same records`.

**Not a pass** — "it should work", "as usual", or an expectation that is merely
the reporter's preference. If no source exists, the ticket may be a change
request, not a defect — flag that explicitly.

### B3 Actual result, verbatim (blocker)

**Pass** — the observable outcome **verbatim**: the exact message, the exact
number, the exact rendered value, copied as text.

**Not a pass** — a paraphrase (`throws an error`) or a classification
(`NullPointer somewhere in the export`).

**An image where the text belongs** is evidence in the wrong place, not missing
evidence. If the message is legible, transcribe it and mark the transcription
(SKILL.md, step 1): B3 passes, with a **major**
"not indexed" gap asking for the text in the ticket — an image cannot be
searched, diffed, or pasted into a test. B3 is a **blocker** gap when the region
is cropped, unreadable, or shows only a generic banner whose detail sits behind
a *Details* button nobody pressed.

### B4 Reproducibility (major)

**Pass** — one of: always; intermittent with a rate (`3 of 10 attempts`); once
and not reproduced since; or only under a named condition (`only after a
restart`, `only for site SITE-B`).

**Not a pass** — silence. An intermittent defect misread as deterministic
wastes an entire analysis cycle; this is why the check is major and not minor.

### B5 One defect per report (blocker)

**Pass** — a single failure with a single expected result.

**Not a pass** — "and also", "additionally", "second issue", `zusätzlich`,
`außerdem`, several `h3. Issue Summary` sections, or a numbered list of
unrelated symptoms. Propose a split: keep the defect with the best evidence in
this ticket, list the others for new tickets. Never analyse two defects in one
analysis — the fix for one will mask the other.

The screening script only matches those marker phrases (as whole words) and
repeated template sections, so a `-` in the `multi-defect` column proves
nothing. Two defects in two plain sentences produce
no hit at all. Count the distinct *expected results* the report implies, not the
connectives it uses.

**Downgrade to major when the symptoms share one testable cause.** Multiple
symptoms are not automatically multiple defects. Downgrade when you can state a
single mechanism that predicts *all* of them, and name it — "editing fails,
deleting removes every row and unlocking fails, because each operation matches
on the manufacturer name instead of the row key". Then the ticket is one defect
that was reported three times, and splitting it would scatter the evidence.

It stays a **blocker** when the symptoms are merely adjacent (same screen, same
customer, same week) with no mechanism connecting them, or when they would be
fixed by different teams. State the mechanism explicitly; "probably related" is
not one.

## C — Isolation evidence

This is the group that decides fix-readiness. Everything here answers the
question "what does it take to make the customer's error appear?".

### C1 Stack trace (blocker when an exception is involved)

**Pass** — the complete trace as text, from the message through every chained
cause (Java's `Caused by:` blocks, Python's "The above exception was the direct
cause…" sections), with at least one **application** frame (code from the
product, not only framework, runtime or container code) and its line number.

**Not a pass** — the first line only; a trace truncated above `Caused by:`; a
screenshot that crops the trace or leaves the application frame illegible.

**A trace inside an attachment** is evidence in the wrong place, not missing
evidence. Open the log or payload: if it holds the trace, C1 passes, with a
**major** "not indexed" gap — name the file, the timestamp and what to grep for.
C1 is a **blocker** gap only when no trace is reachable: none in the
attachments, or the attachment is unusable as filed — a multi-gigabyte archive,
a screenshot of a log viewer, or a format nobody on the team can open. Say which
of the two you are looking at, and name the file.

`n/a` — no exception is involved (a wrong number on a screen, a layout defect,
a performance complaint).

### C2 Failing vs. working input (blocker when the failure is data-dependent)

**Pass** — the two cases side by side: the record that fails and the comparable
record that works, with the values that differ visible. `order_id = 6086 fails,
order_id = 367 works; the failing one has line_no = 0`. An attached request payload
(`CompleteOrder.xml`) is the failing input in its most exact form and passes
the failing half of this check on its own.

**Not a pass** — only the failing case; or a working case from a different
scenario, which proves nothing. If no working case exists at all, that is
itself a finding: state that the failure is unconditional.

`n/a` — the failure occurs on every input.

### C3 Regression range (blocker when "used to work" is claimed)

**Pass** — a last-known-good and a first-bad build, however coarse:
`worked in 4.2, fails in 5.0`. Migration, configuration change and data
import count as boundaries too.

**Not a pass** — `Affects Version/s` alone; "it used to work" without a
version; "worked before the update" without naming the update.

Phrases that carry C3 evidence in prose — search for all of them before
declaring the gap:

| English | German |
|---|---|
| worked in, was working in, used to work | funktionierte in, hat funktioniert, lief |
| stopped working with, broken since, fails since | geht nicht mehr seit, seit dem Update, seit Version |
| after the upgrade/migration/patch | nach dem Update/der Migration |
| first noticed in, regression | erstmals aufgetreten in, Regression |

This table is the reference for your own reading. The screening script's
`regression` signal matches only phrases that are safe to match mechanically —
a bare *lief* would also hit *Lieferung* — so a `-` there does not mean these
phrases are absent.

`n/a` — the feature is new and has never worked.

### C4 Workaround as a trigger (major)

**Pass** — phrased so it names the condition: "it only works when the
comment field is left empty" tells you which input path builds the faulty
value. That sentence is worth more than the rest of the ticket.

**Not a pass** — an empty `Workaround` heading; "restart helps" without saying
what state the restart clears; "the user can do it manually" (that is relief,
not a trigger).

### C5 Logs and attachments (major)

**Pass** — log excerpts or files whose timestamps overlap the occurrence time
from A5, from the named system, with the relevant lines pointed at.
Correlation/request ids, session ids and job ids all count — including when they
appear only in the attachment names (`OrderService_77290.log` +
`ORD-77290_CompleteOrder.xml` share the order id 77290).

**Not a pass** — an unnamed archive; logs from a different day or host; a
screenshot of a log viewer.

## D — Classification (IEEE 1044)

### D1 Severity (major)

**Pass** — describes the effect on the system, chosen independently of who is
shouting: data loss / production stop / function unusable / degraded /
cosmetic. Justified in one clause.

**Not a pass** — severity set from customer pressure, or left at the default on
a ticket that describes a production stop.

### D2 Priority (major)

**Pass** — a scheduling decision with a reason: how many sites are affected,
whether a workaround exists, contractual deadlines.

**Not a pass** — priority mirroring severity one-to-one. They answer different
questions; if every ticket has priority = severity, the field carries no
information.

### D3 Problem category (minor)

**Pass** — the project's category field is set to something that would survive
review after the root cause is known (data, logic, interface, configuration,
documentation, performance).

Only demand this when the field exists on the project's screen — verify it as
[jira.md](jira.md) describes.

### D4 Links and references (major)

**Pass** — linked to duplicates, clones and predecessors, and to the change
suspected of causing it (`caused by`). Clones frequently hold the reproducing
data the main ticket lacks — that is why this is major, not cosmetic.

**Not a pass** — a related ticket mentioned as bare text in a comment without
a link. External references (support ticket ids and urls) should be recorded
in the field intended for them.

### D5 Status and disposition (minor)

**Pass** — status matches reality and, once closed, records the disposition
(fixed / duplicate / not reproducible / works as designed / deferred) with a
justification. A ticket closed as "not reproducible" without stating what was
attempted is a gap.

## Scoring

- **Blocker** — analysis cannot start; the next action is asking the reporter.
- **Major** — analysis can start, but a round-trip is likely.
- **Minor** — hygiene; process and reporting suffer, analysis does not.

Report counts per group and the ranked gap list. Do not compute a percentage:
a report at "80 %" that is missing C1 is not 80 % useful — it is blocked.
Blockers alone decide whether a report is *blocked*; without blockers, group C
decides between *fix-ready* (every applicable C check passes) and *analysable
with assumptions* (at least one C gap). "Not indexed" gaps never change the
verdict, and an `n/a` for missing data never improves it (SKILL.md, step 4).
