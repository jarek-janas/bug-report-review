#!/usr/bin/env python3
"""Mechanical screening of a bug report. Signals only - no judgement.

Input:  a Jira issue JSON, a Jira `search` response, or plain report text.
        Rich text may be wiki markup (Data Center, REST v2) or Atlassian
        Document Format (Cloud, REST v3); files may be UTF-8 or UTF-16.
Output: deterministic signals as JSON (default) or a markdown table.

    python screen.py issue.json
    python screen.py --format md issue.json
    <your Jira tool> ... | python screen.py -
    python screen.py --text report.txt

The agent judges; this script only reports what is mechanically present.
Requires Python 3.9+, standard library only.
"""

from __future__ import annotations

import argparse
import functools
import json
import re
import sys
from typing import Any

# The default description template (assets/description-template.txt). A project
# with its own headings maps them onto these with `--alias "Heading=section"`.
TEMPLATE_SECTIONS = [
    "issue summary",
    "steps to reproduce",
    "expected results",
    "actual results",
    "workaround",
]

SECTION_ALIASES = {
    "summary": "issue summary",
    "description": "issue summary",
    "beschreibung": "issue summary",
    "steps": "steps to reproduce",
    "reproduction": "steps to reproduce",
    "schritte": "steps to reproduce",
    "expected result": "expected results",
    "expected behaviour": "expected results",
    "expected behavior": "expected results",
    "erwartetes ergebnis": "expected results",
    "actual result": "actual results",
    "actual behaviour": "actual results",
    "actual behavior": "actual results",
    "tatsaechliches ergebnis": "actual results",
    "workarounds": "workaround",
    "umgehung": "workaround",
}

# A heading is `h3. Title`, `### Title` or a fully bold line `*Title*` - but not a
# Jira bullet (`* step text`), which would otherwise shred the sections.
HEADING_RE = re.compile(
    r"^[ \t]*(?:"
    r"h[1-6]\.[ \t]*(?P<h>[^\n]{2,60}?)"
    r"|#{1,6}[ \t]+(?P<m>[^\n]{2,60}?)"
    r"|\*{1,2}(?P<b>[^*\n]{2,60}?)\*{1,2}"
    r")[ \t]*:?[ \t]*$",
    re.M,
)

# One stack frame, in the formats the common runtimes print.
TRACE_FRAME_RE = re.compile(
    r"^\s*at\s+[\w$.]+\.[\w$<>]+\("                                  # Java, .NET
    r"|^[ \t]*File \"[^\"\n]+\", line \d+"                            # Python
    r"|^[ \t]*at[ \t]+(?:[^\n(]*\()?"                                 # JavaScript,
    r"(?:[^\s()]+\.(?:[cm]?js|jsx|tsx?)|node:[^\s()]+):\d+:\d+\)?[ \t\r]*$",  # Node.js
    re.M,
)
CAUSED_BY_RE = re.compile(
    r"^\s*Caused by:"
    r"|^[ \t]*(?:The above exception was the direct cause|During handling of the above exception)",
    re.M,
)
EXCEPTION_RE = re.compile(
    r"\b(?:[\w.$]*(?:Exception|Error|Throwable)\b(?:\s*:|\s*\n)|ORA-\d{5}|SQLSTATE)",
)
EXCEPTION_MENTION_RE = re.compile(
    r"\b(exception|stacktrace|stack trace|traceback|fehlermeldung|nullpointer|timeout|"
    r"ora-\d{5}|error code|errorcode)\b",
    re.I,
)

CODE_BLOCK_RE = re.compile(r"\{code[^}]*\}|\{noformat\}|```", re.I)
IMAGE_EMBED_RE = re.compile(r"!\S+\.(?:png|jpe?g|gif|bmp)[^!]*!", re.I)
STEP_LINE_RE = re.compile(r"^\s*(?:[*#-]+|\d+[.)])\s+\S", re.M)
VERSION_RE = re.compile(r"\b\d+\.\d+(?:\.\d+){0,2}\b")
# Dotted quads are hosts, not releases: `10.26.150.10` must not become a version.
IPV4_RE = re.compile(r"\b(?:\d{1,3}\.){3}\d{1,3}\b")
# Neither are dates and measurements: `12.08.2026`, `3.5 s`, `20.5 %`, `section 4.2`.
# A log line's short date counts too when a time follows: `15.06. 15:09:26`.
DATE_RE = re.compile(
    r"\b(?:0?[1-9]|[12]\d|3[01])\.(?:0?[1-9]|1[0-2])\."
    r"(?:\d{4}\b|(?:\d{2})?(?=[ ,]+\d{1,2}:\d{2}))"
)
NOT_VERSION_RE = re.compile(
    r"(?<![\w.])\d+\.\d+ ?(?:ms|s|sec|seconds?|sekunden|min|minutes?|minuten|h|hours?"
    r"|stunden|%|[kmgt]b|kg|mm|cm|km|x)(?!\w)"
    r"|\b(?:section|chapter|step|abschnitt|kapitel|schritt) +\d+(?:\.\d+)+",
    re.I,
)
SQL_RE = re.compile(r"\b(?:select\s+.+\s+from|insert\s+into|update\s+\w+\s+set)\b", re.I)
CORRELATION_RE = re.compile(
    r"\b(?:correlation|request|session|trace|job|order|charge)[ _-]?(?:id|nr|no)\b", re.I
)
TIMESTAMP_RE = re.compile(
    r"\b\d{4}-\d{2}-\d{2}[ T]\d{2}:\d{2}|\b\d{1,2}\.\d{1,2}\.\d{2,4}[ ,]+\d{1,2}:\d{2}"
)
# `..._260812_132241.xml`, `..._2026-08-12T13-22.log`
FILENAME_TS_RE = re.compile(r"(?:\D|^)(\d{6}|\d{8})[_-]?(\d{6})(?:\D|$)|\d{4}-\d{2}-\d{2}")
FILENAME_ID_RE = re.compile(r"[A-Z]{2,}[-_]?\d{3,}|_\d{4,}(?:\D|$)")

# Only phrases that are safe to match mechanically. The C3 table in
# references/rubric.md is the full list the agent searches by reading.
REGRESSION_PHRASES = [
    "worked in", "was working in", "used to work", "worked fine", "worked until",
    "stopped working", "no longer works", "does not work since", "broken since",
    "fails since", "regression", "after the update", "after the upgrade",
    "after the migration", "since the update", "since version", "first noticed in",
    "funktionierte*", "hat funktioniert", "ging noch", "geht nicht mehr",
    "seit dem update", "seit version", "nach dem update", "nach der migration",
]

COMPARISON_PHRASES = [
    "works for", "works when", "only fails", "fails only", "but not",
    "but shown", "but works", "whereas", "compared to", "in contrast",
    "same for", "instead of", "while the",
    "funktioniert bei", "nur bei", "aber nicht", "aber bei", "im gegensatz",
]

MULTI_DEFECT_PHRASES = [
    # Low recall by design: this catches the *marker phrases* only. Two defects
    # in two plain sentences ("Editing fails. Deleting removes every entry.")
    # produce no hit at all - a `-` here is not evidence of a single defect.
    "and also", "additionally", "second issue", "another issue", "another bug",
    "unrelated", "by the way", "furthermore", "second problem",
    "zusaetzlich*", "ausserdem", "des weiteren", "zweites problem",
    "noch ein", "noch eine", "noch einen",
]

WORKAROUND_TRIGGER_PHRASES = [
    "only works when", "works if", "works only", "if you leave", "if the field",
    "after a restart", "avoid*", "as long as", "unless",
    "nur wenn", "funktioniert wenn", "wenn man", "solange", "vermeiden",
]

FREQUENCY_PHRASES = [
    "always", "every time", "reproducible", "not reproducible", "intermittent*",
    "sometimes", "randomly", "once", "sporadic*", "out of ten", "of 10",
    "immer", "jedes mal", "reproduzierbar*", "sporadisch*", "manchmal", "einmalig*",
]

PLACEHOLDER_STEP_PHRASES = [
    "some filters", "some data", "any order*", "some order*", "as usual",
    "check that", "verify that", "make sure", "irgendein*", "beliebig*",
]


def _phrases(text: str, phrases: list[str]) -> list[str]:
    """Whole words only - `once` must not fire on "concerned", nor `noch ein` on
    "noch einmal". A trailing `*` also matches inflected forms
    (`intermittent*` finds "intermittently")."""
    low = _normalize(text)
    return [p.rstrip("*") for p in phrases if _phrase_re(p).search(low)]


@functools.lru_cache(maxsize=None)
def _phrase_re(phrase: str) -> re.Pattern[str]:
    stem = re.escape(phrase.rstrip("*"))
    return re.compile(r"(?<!\w)" + stem + ("" if phrase.endswith("*") else r"(?!\w)"))


def _normalize(text: str) -> str:
    low = text.lower()
    for src, dst in (("ä", "ae"), ("ö", "oe"), ("ü", "ue"), ("ß", "ss")):
        low = low.replace(src, dst)
    # Descriptions wrap: "broken\nsince" must still match `broken since`.
    return re.sub(r"\s+", " ", low)


JIRA_MARKUP_RE = re.compile(r"^[ \t]*h[1-6]\.|\{code|\{noformat|!\S+\.(?:png|jpe?g|gif)", re.M | re.I)


def _sections(description: str) -> dict[str, Any]:
    """Split the description at headings; report which template sections are empty."""
    # In Jira markup `# text` is an ordered list item, not a heading.
    jira = bool(JIRA_MARKUP_RE.search(description))
    matches = [m for m in HEADING_RE.finditer(description)
               if not (jira and m.group("m") is not None)]
    found: dict[str, str] = {}
    seen: dict[str, int] = {}
    for i, m in enumerate(matches):
        raw = (m.group("h") or m.group("m") or m.group("b") or "").strip().lower().rstrip(":")
        key = SECTION_ALIASES.get(_normalize(raw), _normalize(raw))
        end = matches[i + 1].start() if i + 1 < len(matches) else len(description)
        body = description[m.end():end].strip()
        found[key] = (found.get(key, "") + "\n" + body).strip()
        seen[key] = seen.get(key, 0) + 1

    present = [s for s in TEMPLATE_SECTIONS if s in found]
    empty = [s for s in present if len(found[s].strip()) < 3]
    actual = found.get("actual results", "")
    return {
        "template_headings_found": present,
        "template_headings_missing": [s for s in TEMPLATE_SECTIONS if s not in found],
        "template_headings_empty": empty,
        # A second `Issue Summary` (or any repeated template section) usually
        # means a second defect pasted into the same report.
        "template_headings_repeated": [s for s in TEMPLATE_SECTIONS if seen.get(s, 0) > 1],
        "uses_default_template": len(present) >= 3,
        "actual_results_has_text": len(IMAGE_EMBED_RE.sub("", actual).strip()) >= 3,
        "other_headings": sorted(k for k in found if k not in TEMPLATE_SECTIONS),
        "_bodies": found,
    }


def _text_signals(text: str, sections: dict[str, Any] | None = None,
                  steps_text: str | None = None) -> dict[str, Any]:
    frames = TRACE_FRAME_RE.findall(text)
    # Host addresses, dates and measurements are not release numbers.
    cleaned = NOT_VERSION_RE.sub(" ", DATE_RE.sub(" ", IPV4_RE.sub(" ", text)))
    versions = sorted(set(VERSION_RE.findall(cleaned)))
    steps_body = (sections or {}).get("_bodies", {}).get("steps to reproduce", "")
    # Without a `Steps to Reproduce` section, fall back to the *description*
    # only. Counting bullets from comments reports steps a reader cannot follow.
    steps_scope = steps_body or (text if steps_text is None else steps_text)
    actual_body = (sections or {}).get("_bodies", {}).get("actual results", "")

    return {
        "length_chars": len(text),
        "stack_trace_frames": len(frames),
        "stack_trace_as_text": len(frames) >= 1,
        "caused_by_blocks": len(CAUSED_BY_RE.findall(text)),
        "exception_named": bool(EXCEPTION_RE.search(text)),
        "exception_mentioned_without_trace": bool(EXCEPTION_MENTION_RE.search(text))
        and not frames,
        "code_blocks": len(CODE_BLOCK_RE.findall(text)) // 2,
        "embedded_images": len(IMAGE_EMBED_RE.findall(text)),
        "actual_result_is_image_only": bool(actual_body)
        and bool(IMAGE_EMBED_RE.search(actual_body))
        and len(IMAGE_EMBED_RE.sub("", actual_body).strip()) < 40,
        "step_lines": len(STEP_LINE_RE.findall(steps_scope)),
        "steps_use_placeholders": _phrases(steps_scope, PLACEHOLDER_STEP_PHRASES),
        "versions_mentioned": versions,
        "distinct_versions_mentioned": len(versions),
        "regression_phrases": _phrases(text, REGRESSION_PHRASES),
        "comparison_phrases": _phrases(text, COMPARISON_PHRASES),
        "workaround_trigger_phrases": _phrases(text, WORKAROUND_TRIGGER_PHRASES),
        "frequency_phrases": _phrases(text, FREQUENCY_PHRASES),
        "multi_defect_phrases": _phrases(text, MULTI_DEFECT_PHRASES),
        "sql_statements": len(SQL_RE.findall(text)),
        "correlation_ids": bool(CORRELATION_RE.search(text)),
        "explicit_timestamps": len(TIMESTAMP_RE.findall(text)),
        "external_links": len(re.findall(r"https?://\S+", text)),
    }


EVIDENCE_LINK_TYPES = {
    "problem report": "origin",
    "request for support": "origin",
    "support": "origin",
    "test": "verification",
    "release": "scheduling",
    "pi objective": "scheduling",
    "epic": "scheduling",
}


def _classify_links(links: list[dict[str, Any]]) -> dict[str, Any]:
    """Linked issues are evidence sources - rank them so none is judged unread."""
    follow, detail = [], []
    for l in links:
        other = l.get("outwardIssue") or l.get("inwardIssue") or {}
        f = other.get("fields") or {}
        itype = ((f.get("issuetype") or {}).get("name") or "").lower()
        rel = (l.get("type") or {}).get(
            "outward" if l.get("outwardIssue") else "inward", ""
        ).lower()
        role = EVIDENCE_LINK_TYPES.get(itype, "")
        if "clone" in rel or "duplicate" in rel:
            role = "duplicate"
        elif "cause" in rel:
            role = "cause"
        elif not role and ("relate" in rel or "block" in rel):
            role = "related"
        entry = {
            "key": other.get("key"),
            "relation": rel,
            "issuetype": (f.get("issuetype") or {}).get("name"),
            "status": ((f.get("status") or {}).get("name")),
            "summary": f.get("summary"),
            "role": role or "other",
        }
        detail.append(entry)
        if entry["role"] in ("origin", "duplicate", "cause", "related", "verification"):
            follow.append(entry["key"])

    roles = [d["role"] for d in detail]
    return {
        "links_detail": detail,
        "links_to_follow": follow,
        "has_origin_ticket": "origin" in roles,
        "has_duplicate_or_clone": "duplicate" in roles,
        "has_cause_link": "cause" in roles,
        "has_verification_link": "verification" in roles,
    }


def _classify_attachments(attachments: list[dict[str, Any]]) -> dict[str, Any]:
    """Group attachments by evidential value - a text log outranks a screenshot."""
    buckets: dict[str, list[str]] = {
        "log_or_text": [], "payload": [], "archive": [], "image": [],
        "document": [], "other": [],
    }
    detail = []
    for a in attachments:
        name = a.get("filename", "")
        mime = (a.get("mimeType") or "").lower()
        size = a.get("size") or 0
        low = name.lower()
        if re.search(r"\.(log|txt|out|trace|err)$", low) or mime == "text/plain":
            bucket = "log_or_text"
        elif re.search(r"\.(xml|json|csv|sql|yaml|yml|har)$", low):
            bucket = "payload"
        elif re.search(r"\.(zip|7z|gz|tgz|rar|tar)$", low):
            bucket = "archive"
        elif re.search(r"\.(png|jpe?g|gif|bmp|svg)$", low) or mime.startswith("image/"):
            bucket = "image"
        elif re.search(r"\.(pdf|docx?|xlsx?|pptx?|msg|eml)$", low):
            bucket = "document"
        else:
            bucket = "other"
        buckets[bucket].append(name)
        detail.append({
            "filename": name, "class": bucket, "size_kb": round(size / 1024, 1),
            "timestamp_in_name": bool(FILENAME_TS_RE.search(name)),
            "id_in_name": bool(FILENAME_ID_RE.search(name)),
        })

    machine_readable = (
        buckets["log_or_text"] + buckets["payload"] + buckets["archive"]
    )
    return {
        "attachment_classes": {k: v for k, v in buckets.items() if v},
        "attachments_detail": detail,
        "has_text_log_attachment": bool(buckets["log_or_text"]),
        "has_payload_attachment": bool(buckets["payload"]),
        "unindexed_evidence_candidates": buckets["log_or_text"] + buckets["payload"],
        # Images can be downloaded and viewed, so they are evidence that must be
        # OPENED and transcribed - never evidence that can be discounted.
        "image_count": len(buckets["image"]),
        "images_to_open": buckets["image"],
        "largest_image_kb": max(
            [d["size_kb"] for d in detail if d["class"] == "image"], default=0
        ),
        "largest_archive_kb": max(
            [d["size_kb"] for d in detail if d["class"] == "archive"], default=0
        ),
        "evidence_needs_transcription": bool(detail) and not machine_readable
        and not buckets["document"],
        "filename_timestamps": [d["filename"] for d in detail if d["timestamp_in_name"]],
        "filename_ids": [d["filename"] for d in detail if d["id_in_name"]],
    }


def _plain(value: Any) -> str:
    """A rich-text field as text. Jira Data Center and REST v2 return wiki-markup
    strings; Jira Cloud REST v3 returns Atlassian Document Format (ADF) objects,
    rendered here as the equivalent wiki markup so every signal works the same."""
    if value is None:
        return ""
    if isinstance(value, str):
        return value
    if isinstance(value, dict) and value.get("type") == "doc":
        return re.sub(r"\n{3,}", "\n\n", _adf(value)).strip()
    return str(value)


def _adf(node: Any) -> str:
    if isinstance(node, list):
        return "".join(_adf(n) for n in node)
    if not isinstance(node, dict):
        return ""
    kind = node.get("type")
    attrs = node.get("attrs") or {}
    content = node.get("content") or []
    if kind == "text":
        links = [m.get("attrs", {}).get("href", "") for m in node.get("marks") or []
                 if m.get("type") == "link"]
        return " ".join([node.get("text") or ""] + links)
    if kind == "hardBreak":
        return "\n"
    if kind == "mention":
        return attrs.get("text") or ""
    if kind in ("inlineCard", "blockCard"):
        return f" {attrs.get('url') or ''} "
    if kind == "heading":
        return f"\nh{attrs.get('level', 3)}. {_adf(content).strip()}\n"
    if kind == "codeBlock":
        return "\n{code}\n" + _adf(content) + "\n{code}\n"
    if kind in ("bulletList", "orderedList"):
        mark = "1." if kind == "orderedList" else "*"
        return "\n" + "".join(f"{mark} {_adf(item.get('content') or []).strip()}\n"
                              for item in content if isinstance(item, dict))
    if kind == "mediaSingle":
        # An embedded image. ADF carries no file name; use the alt text when it
        # names an image file, otherwise a placeholder the image signals count.
        alt = next((re.sub(r"\s+", "_", (m.get("attrs") or {}).get("alt") or "")
                    for m in content if isinstance(m, dict)), "")
        name = alt if re.search(r"\.(?:png|jpe?g|gif|bmp)$", alt, re.I) else "image.png"
        return f"\n!{name}!\n"
    if kind in ("paragraph", "blockquote", "panel", "tableRow", "rule"):
        return "\n" + _adf(content) + "\n"
    return _adf(content)


def _issue_signals(issue: dict[str, Any]) -> dict[str, Any]:
    f = issue.get("fields") or {}
    description = _plain(f.get("description"))
    summary = f.get("summary") or ""
    environment = _plain(f.get("environment"))

    comments = ((f.get("comment") or {}).get("comments")) or []
    comment_text = "\n".join(_plain(c.get("body")) for c in comments)
    attachments = f.get("attachment") or []
    att = _classify_attachments(attachments)
    lnk = _classify_links(f.get("issuelinks") or [])

    sections = _sections(description)
    combined = f"{summary}\n{description}\n{comment_text}"

    signals = {
        "key": issue.get("key"),
        "issuetype": (f.get("issuetype") or {}).get("name"),
        "status": (f.get("status") or {}).get("name"),
        "priority": (f.get("priority") or {}).get("name"),
        "reporter": ((f.get("reporter") or {}).get("displayName")),
        "created": f.get("created"),
        "summary": summary,
        "summary_length": len(summary),
        "summary_words": len(summary.split()),
        "description_present": bool(description.strip()),
        "environment_set": bool(environment.strip()),
        "environment_is_image_only": bool(environment.strip())
        and bool(IMAGE_EMBED_RE.search(environment))
        and len(IMAGE_EMBED_RE.sub("", environment).strip()) < 20,
        "affects_versions": [v.get("name") for v in (f.get("versions") or [])],
        "fix_versions": [v.get("name") for v in (f.get("fixVersions") or [])],
        "components": [c.get("name") for c in (f.get("components") or [])],
        "labels": f.get("labels") or [],
        "issue_links": len(f.get("issuelinks") or []),
        "comment_count": len(comments),
        "attachment_count": len(attachments),
    }
    signals.update(att)
    signals.update(lnk)
    signals.update(sections)
    signals.pop("_bodies", None)
    signals["description_signals"] = _text_signals(description, sections,
                                                   steps_text=description)
    signals["combined_signals"] = _text_signals(combined, sections,
                                                steps_text=description)
    return signals


def _said(sig: dict[str, Any], key: str, phrases: list[str]) -> str:
    """`yes` when the report itself says it, `yes(c)` when only the comments do -
    often an analyst's later words, which must not flatter the report."""
    if not sig["combined_signals"][key]:
        return "-"
    own = sig.get("description_signals")
    if own is None or own[key] or _phrases(sig.get("summary") or "", phrases):
        return "yes"
    return "yes(c)"


def _row(sig: dict[str, Any]) -> dict[str, Any]:
    c = sig["combined_signals"]
    if sig.get("has_text_log_attachment") or sig.get("has_payload_attachment"):
        evidence = "log/payload"
    elif sig.get("evidence_needs_transcription"):
        evidence = "images only"
    elif sig.get("attachment_count"):
        evidence = "other"
    else:
        evidence = "-"
    if c["actual_result_is_image_only"]:
        actual = "image only"
    elif sig.get("actual_results_has_text"):
        actual = "text"
    else:
        actual = "-"
    biggest = max(sig.get("largest_image_kb") or 0, sig.get("largest_archive_kb") or 0)
    return {
        "key": sig.get("key") or "-",
        "template": "yes" if sig.get("uses_default_template") else "no",
        "empty sections": len(sig.get("template_headings_empty") or []),
        "steps": c["step_lines"],
        "trace": "text" if c["stack_trace_as_text"]
        else ("claimed" if c["exception_mentioned_without_trace"] else "-"),
        "actual result": actual,
        "versions": c["distinct_versions_mentioned"],
        "regression": _said(sig, "regression_phrases", REGRESSION_PHRASES),
        "delta": _said(sig, "comparison_phrases", COMPARISON_PHRASES),
        "workaround": _said(sig, "workaround_trigger_phrases", WORKAROUND_TRIGGER_PHRASES),
        "frequency": _said(sig, "frequency_phrases", FREQUENCY_PHRASES),
        "multi-defect": "yes" if sig.get("template_headings_repeated")
        else _said(sig, "multi_defect_phrases", MULTI_DEFECT_PHRASES),
        "attached evidence": evidence,
        "images to open": sig.get("image_count") or 0,
        "largest blob MB": round(biggest / 1024, 1) if biggest else 0,
        "follow links": ",".join(sig.get("links_to_follow") or []) or "-",
    }


def _markdown(rows: list[dict[str, Any]]) -> str:
    if not rows:
        return "_no issues_"
    cols = list(rows[0])
    out = ["| " + " | ".join(cols) + " |", "|" + "|".join("---" for _ in cols) + "|"]
    out += ["| " + " | ".join(str(r[c]) for c in cols) + " |" for r in rows]
    return "\n".join(out)


def _decode(data: bytes) -> str:
    """Windows tools write UTF-8 with a byte-order mark (`Out-File -Encoding
    utf8`) or UTF-16 (`>` in Windows PowerShell 5.1); older ones the ANSI code
    page. Accept all of them instead of failing on the first byte."""
    if data.startswith((b"\xff\xfe", b"\xfe\xff")):
        return data.decode("utf-16")
    try:
        return data.decode("utf-8-sig")
    except UnicodeDecodeError:
        print("warning: input is not UTF-8 - decoded as Windows-1252.", file=sys.stderr)
        return data.decode("cp1252", errors="replace")


def _load(path: str) -> str:
    # Read bytes, not text: on Windows, piped stdin is otherwise decoded with the
    # ANSI code page, and every phrase containing an umlaut silently stops matching.
    if path == "-":
        return _decode(sys.stdin.buffer.read())
    with open(path, "rb") as fh:
        return _decode(fh.read())


def main() -> int:
    for stream in (sys.stdout, sys.stderr):
        if hasattr(stream, "reconfigure"):
            stream.reconfigure(encoding="utf-8", errors="replace")

    ap = argparse.ArgumentParser(description="Mechanical bug report screening.")
    ap.add_argument("input", help="JSON file, or - for stdin")
    ap.add_argument("--text", action="store_true", help="input is plain report text")
    ap.add_argument("--format", choices=("json", "md"), default="json")
    ap.add_argument("--alias", action="append", default=[], metavar="HEADING=SECTION",
                    help="map a project's own heading onto a default template section "
                         f"({', '.join(TEMPLATE_SECTIONS)}); repeatable")
    args = ap.parse_args()

    for alias in args.alias:
        heading, _, section = alias.partition("=")
        heading = _normalize(heading.strip()).rstrip(":").strip()
        section = _normalize(section.strip())
        if not heading or section not in TEMPLATE_SECTIONS:
            print(f"error: --alias {alias!r} must be HEADING=SECTION, with SECTION one of: "
                  f"{', '.join(TEMPLATE_SECTIONS)}", file=sys.stderr)
            return 2
        SECTION_ALIASES[heading] = section

    raw = _load(args.input)

    if args.text:
        sections = _sections(raw)
        sig = {"key": None, **sections}
        sig.pop("_bodies", None)
        sig["combined_signals"] = _text_signals(raw, sections)
        signals = [sig]
    else:
        try:
            data = json.loads(raw)
        except json.JSONDecodeError as exc:
            print(f"error: input is not valid JSON ({exc}). "
                  f"Use --text for plain report text.", file=sys.stderr)
            return 2
        issues = data.get("issues") if isinstance(data, dict) else None
        if issues is None:
            issues = [data] if isinstance(data, dict) else list(data)
        signals = [_issue_signals(i) for i in issues]

    if args.format == "md":
        print(_markdown([_row(s) for s in signals]))
    else:
        # An empty search result prints `[]` - a sweep that matches nothing is normal.
        print(json.dumps(signals if len(signals) != 1 else signals[0], indent=2,
                         ensure_ascii=False))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
