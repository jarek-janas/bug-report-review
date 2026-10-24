# Fetching reports from Jira

Read Jira through whatever integration the environment provides — a Jira or
Atlassian skill, an MCP server, or a CLI. Never build authentication headers or
handle tokens yourself; if the only way in would be a raw token, ask the user to
paste the report instead.

The endpoints below are the Jira REST API, version 2, which Jira Data Center
and Jira Cloud both serve. Tools that wrap the API usually accept these paths or
expose the same data under similar names. Paths are relative to the Jira base
URL; `ABC-123` stands for the issue key and `ABC` for the project.

## One issue, everything the review needs

```
GET /rest/api/2/issue/ABC-123?fields=summary,description,environment,versions,fixVersions,components,priority,status,resolution,issuetype,labels,issuelinks,attachment,created,updated,reporter,assignee,comment&expand=changelog
```

- `comment` in `fields` returns the comments inline — always request it. Missing
  evidence is regularly in a comment, and reporting a gap that is already
  answered discredits the whole review.
- `expand=changelog` shows whether priority, severity or status were changed
  and by whom (checks D1, D2, D5). Drop it for sweeps; it is large.
- Save the response to a file and feed it to `scripts/screen.py`. Version 2
  returns rich text as wiki markup; the script also accepts the Atlassian
  Document Format that version 3 returns.

## Links

- Linked issues are listed in `fields.issuelinks`. Fetch each one with
  `?fields=summary,issuetype,status,description` — step 1 of SKILL.md says which
  kinds of link usually hold the missing evidence.
- Remote links (CI builds, branches, support-system tickets):
  `GET /rest/api/2/issue/ABC-123/remotelink`.

## Attachments — including images

Each entry in `fields.attachment` carries `id`, `filename`, `mimeType`, `size`
and `content`; `content` is the download URL. Fetch the file into the temporary
folder the interaction rules in SKILL.md name, then read it as step 1 describes.

## Which fields the project's Bug screen actually has

Check this before demanding a field. The create screen is what the reporter
saw:

```
GET /rest/api/2/issue/createmeta/ABC/issuetypes          # issue types and their ids
GET /rest/api/2/issue/createmeta/ABC/issuetypes/<id>     # fields on that type's create screen
```

If those are unavailable, fall back to the edit screen of an existing issue of
the project: `GET /rest/api/2/issue/ABC-123/editmeta`. It usually lists far
more fields — triage and workflow fields no reporter ever sees — so a field
that appears only there is not one the reporter should have filled. Both list
each field with its `name` and whether it is `required`.

`required` is a lower bound, not a contract: a workflow validator can demand a
field the metadata calls optional. If a create answers `400` with "This field
is required", show the user that error rather than guessing a value.

- Many Bug screens carry no "Steps to Reproduce" and no "Severity" field — the
  evidence legitimately belongs in `description`. Reporting "Severity not set"
  on such a project is a false positive.
- `Severity` may exist globally as a `customfield_*` and still be absent from
  the Bug screen. Resolve ids per project; never hard-code a `customfield_*`
  number into a review.
- To find a field id by name across the instance: `GET /rest/api/2/field`, then
  match on `name`. Ids differ between instances — always resolve, never assume.
- The older form `GET /rest/api/2/issue/createmeta?projectKeys=ABC` is gone on
  recent Jira versions. It answers `404 "Issue Does Not Exist"`, which looks
  like a permissions failure and is not.

## Quality sweep over many issues

URL-encode the JQL. Keep `maxResults` small and request only what the sweep
needs:

```
GET /rest/api/2/search?jql=<url-encoded JQL>&maxResults=25&fields=summary,description,environment,versions,components,priority,attachment,issuelinks,created,reporter
```

for example with the JQL
`project = ABC AND issuetype = Bug AND created >= -30d ORDER BY created DESC`.
Jira Cloud has replaced this endpoint with `GET /rest/api/3/search/jql`, which
takes `jql`, `maxResults` and `fields` the same way and also returns an
`issues` list.

`scripts/screen.py` accepts the search response directly and emits one row per
issue. Screen mechanically first, then read only the worst offenders in full —
do not pull descriptions of 200 issues into context.

## Default description template

The skill's default template
([assets/description-template.txt](../assets/description-template.txt)) uses
these Jira-markup headings:

```
h3. Issue Summary
h3. Steps to Reproduce
h3. Expected Results
h3. Actual Results
h3. Workaround
```

A project that mandates other headings is covered in
[standards.md](standards.md), *Adapting to a project that mandates its own
template*.

Common failure modes:

- headings present, `Workaround` and `Environment` empty;
- steps written as capabilities ("Check that the data is shown correctly") so
  the concrete filter values are lost;
- actual result delegated to `!screenshot-1.png|thumbnail!`;
- tickets that ignore the template entirely and open with
  `Location: … / System: … / Description:` free prose — these are often *richer*
  in isolation evidence than the templated ones. Screen the content, not the
  shape.

Note that the template has no section for isolation evidence. When rewriting a
description, put the trace, the failing/working delta and the regression range
under `h3. Actual Results` and `h3. Workaround` rather than inventing headings
the project does not use — unless the user wants the template extended.

## Writing back

Writes need explicit confirmation of the exact text. Prefer a comment over
editing someone else's description:

```
POST /rest/api/2/issue/ABC-123/comment
{"body": "h3. Report review\n..."}
```

Version 2 takes the comment body as wiki markup; version 3 expects Atlassian
Document Format.

Never change `priority`, `severity`, `status` or `resolution` on behalf of
someone else, and never edit a customer-visible description without the
reporter's agreement — the ticket is a record.

## Error responses

Treat an error body as an error, never as data. A `404` on an issue key that
exists usually means the endpoint shape changed (see `createmeta` above) or the
issue is in a project you cannot browse.
