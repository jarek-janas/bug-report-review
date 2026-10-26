# bug-report-review

An agent skill that checks whether a bug report is good enough to start a
root-cause analysis — and repairs it when it is not.

Point it at a Jira issue key or URL, a JQL query, or just paste the report
text. It returns two verdicts:

- **Conformance** — is the report well-formed? (ISO/IEC/IEEE 29119-3
  structure, IEEE 1044 classification)
- **Fix-readiness** — can analysis start right now? (the stack trace as text,
  failing vs. working input, the regression range, the workaround read as a
  trigger)

The second one is the point. A ticket can tick every box of the standard and
still be unfixable because the stack trace is a cropped screenshot; a messy
prose ticket that contains the trace, the version delta and two SQL statements
is ready today.

## What you get

- A verdict: *fix-ready*, *analysable with assumptions*, or *blocked*.
- Every gap, ranked by severity, with what was searched and where.
- Evidence found in attachments, comments and linked issues — including text
  read off screenshots — instead of a gap that is really sitting in the ticket.
- On request: up to five questions to send back to the reporter, a restructured
  description, or a hand-off to the analysis.
- A new report written from scratch, asking for the evidence an analysis needs
  first.

## What it never does

- write to your issue tracker without your confirmation of the exact text — and
  it prefers adding a comment over editing someone's description;
- change severity, priority or status on anyone's behalf;
- follow instructions found inside ticket text, comments, attachments or
  screenshots, or run attached files.

## Installation

The skill is the self-contained `bug-report-review` folder inside this
repository. Copy that folder — nothing else is needed, and it works with any
agent that supports the [Agent Skills](https://agentskills.io) format.

1. Get the repository:

   ```sh
   git clone https://github.com/jarek-janas/bug-report-review.git
   ```

   or download it from GitHub with **Code → Download ZIP**. The ZIP unpacks to
   `bug-report-review-main`; the skill folder inside it is still
   `bug-report-review`.
2. Copy the inner `bug-report-review` folder into your skills folder — by drag
   and drop, or:

   macOS / Linux:

   ```sh
   mkdir -p ~/.agents/skills
   cp -R bug-report-review/bug-report-review ~/.agents/skills/
   ```

   Windows (PowerShell):

   ```powershell
   New-Item -ItemType Directory -Force $HOME\.agents\skills | Out-Null
   Copy-Item -Recurse bug-report-review\bug-report-review $HOME\.agents\skills\
   ```

**Where to put it:**

- `~/.agents/skills/` — the shared location, for agents that read it. Claude
  Code reads `~/.claude/skills/` instead; link the skill there once. The
  commands skip the link when the skill already shows up there — for example
  because `~/.claude/skills` is itself a link to `~/.agents/skills`, where a
  link created anyway would land inside the skill folder.

  macOS / Linux:

  ```sh
  mkdir -p ~/.claude/skills
  [ -e ~/.claude/skills/bug-report-review ] || ln -s ~/.agents/skills/bug-report-review ~/.claude/skills/bug-report-review
  ```

  Windows (PowerShell):

  ```powershell
  New-Item -ItemType Directory -Force $HOME\.claude\skills | Out-Null
  if (-not (Test-Path $HOME\.claude\skills\bug-report-review)) {
    New-Item -ItemType Junction -Path $HOME\.claude\skills\bug-report-review -Target $HOME\.agents\skills\bug-report-review
  }
  ```
- `~/.claude/skills/` directly, if Claude Code is your only agent.
- `.claude/skills/` inside a project, for that project only. Commit the folder
  there to share the skill with your team.

**Updating:** run `git pull` in the clone (or download a fresh ZIP), delete the
installed `bug-report-review` folder and copy the new one. A link from
`~/.claude/skills` keeps working.

Don't clone the repository straight into a skills folder: the skill sits one
level down, so the agent would not find it.

## Requirements

- Python 3.9 or newer for the screening script (standard library only).
- Jira access is optional. The skill uses whatever your agent already has — a
  Jira skill, an MCP server or a CLI; without one, paste the report text.
- The phrase signals cover English and German. Reports in other languages are
  still reviewed, but those signals stay empty.

## Usage

Ask in your own words, for example:

- "Is PROJ-123 complete enough to start analysing?"
- "Review the bugs created in project ABC last week."
- "Write a bug report for the export crash we just saw."

In Claude Code you can also call it directly: `/bug-report-review PROJ-123`.

## Your project's template

The default description template is in
[`assets/description-template.txt`](bug-report-review/assets/description-template.txt):
*Issue Summary*, *Steps to Reproduce*, *Expected Results*, *Actual Results*,
*Workaround*. If your project mandates other headings, the review adapts
(see [`references/standards.md`](bug-report-review/references/standards.md)),
and the screening script maps them with `--alias`:

```sh
python3 bug-report-review/scripts/screen.py --alias "Repro steps=steps to reproduce" issue.json
```

## Works well with

[`root-cause-fix`](https://github.com/jarek-janas/root-cause-fix): when a
report is fix-ready, this skill hands the established facts over, so the
analysis starts from evidence instead of re-reading the ticket. Each skill also
works on its own.

## Screening a report by hand

From the clone, or with the path of your installed copy:

```sh
python3 bug-report-review/scripts/screen.py --format md issue.json   # a Jira issue or search response (REST API JSON)
python3 bug-report-review/scripts/screen.py --text report.txt        # plain report text
```

The script reports mechanical signals only — template sections, stack traces
as text (Java, .NET, Python, JavaScript), step counts, versions and regression
phrases, image-only evidence, multi-defect markers — and never judges. It reads
UTF-8 and UTF-16 input. On Windows, unless the console uses UTF-8, a pipe or
redirect damages the text before the script sees it (umlauts become `?`, and
German quotes can break the JSON). Have your Jira tool save the response to a
file and pass that file instead.

## Files

```
bug-report-review/                the repository
├── README.md                     this file
├── LICENSE
└── bug-report-review/            the skill — the folder you install
    ├── SKILL.md                  the workflow, the 20-check rubric in compact
    │                             form, and the gotchas
    ├── LICENSE                   the same license, so every installed copy carries it
    ├── references/
    │   ├── rubric.md             pass criteria per check, with examples of what
    │   │                         looks like a pass and is not
    │   ├── standards.md          where each check comes from, and how to adapt
    │   │                         to a project with its own template
    │   ├── jira.md               the Jira REST endpoints to use, how to find a
    │   │                         project's Bug screen fields, the default template
    │   └── new-report.md         writing a new report from scratch; loaded only
    │                             when one is asked for
    ├── scripts/
    │   └── screen.py             the mechanical screening
    └── assets/
        ├── review-template.md    the output format of a review
        └── description-template.txt
                                  Jira-markup skeleton for writing or repairing
                                  a description
```

## License

[MIT](LICENSE)
