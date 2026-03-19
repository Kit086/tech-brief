---
name: tech-brief
description: Generate scheduled or on-demand multi-source tech brief reports for an Agent. Use this skill whenever the user asks for a tech daily, morning brief, evening brief, markdown news summary, or a cron-driven report over a specific time window using RSS feeds and Reddit sources. This skill is especially appropriate when the task includes a reporting window, source configuration, and an output directory, even if the user does not explicitly mention the skill.
---

# Tech Brief

Use this skill to help an Agent produce a markdown tech brief over a specific time window.

Read the relevant JSON config files before doing anything else.
If you skip the config files, you are likely to miss required sources, language settings, output paths, item counts, or editorial focus.

The Agent is responsible for the report itself.
The bundled Python script is only a data collection utility.
Do not let the script replace your judgment, synthesis, or writing.

## Core rule

Treat `scripts/fetch_sources.py` as a structured data fetcher.
It fetches and normalizes candidate items from RSS feeds and Reddit public JSON endpoints.
It does not decide what matters.
It does not write the final report.
You must read the fetched data, choose what deserves inclusion, merge overlapping topics, and write the final markdown report yourself.
You must also read the active source config JSON and the active report profile JSON before fetching or writing.

## Mandatory config-first behavior

Before running the fetcher or drafting the report, read the relevant JSON config files.
Do not assume default sources, language, output directories, or report size from memory.
Do not start writing until you have checked the config files actually in use.

Treat these files as authoritative when they are provided:

- `configs/sources.json`
- `configs/report-profiles.json`

If only example files exist, read these instead:

- `configs/sources.example.json`
- `configs/report-profiles.example.json`

At minimum, verify:

- which sources are enabled or present
- which source ids the task expects
- report language
- report name
- timezone
- output directory
- default brief item count
- editorial focus

If a requested behavior conflicts with the active config, follow explicit user instructions and mention the override.

## When to use this skill

Use this skill when the task involves any of the following:

- generating a tech daily, morning brief, evening brief, or topic brief
- generating a markdown report from RSS feeds and Reddit sources
- running a scheduled report for a provided time range
- saving a report into a target directory
- producing a Chinese-language summary over a specific reporting window

## Inputs to collect

Before execution, identify or confirm these fields when they are not already present:

- report name
- time range start
- time range end
- timezone
- source config JSON path
- report profile JSON path when one exists
- optional report profile id
- output directory
- optional output filename
- optional maximum item count

If the task comes from cron and these values are already explicit, do not ask unnecessary follow-up questions.
If a report profile is available, treat it as the authoritative source for report-level defaults.
If a source config is available, treat it as the authoritative source for what can actually be fetched.

## Execution flow

1. Read the active source config JSON before anything else.
2. Read the active report profile JSON before anything else when one exists.
3. Confirm the reporting window, timezone, language, output directory, brief item count, and editorial focus.
4. Run `scripts/fetch_sources.py` with explicit `--from` and `--to` values to generate one merged JSON file for the requested time range.
5. Read the generated JSON output and review `items` first.
6. Select the most important topics, merging duplicates or near-duplicates across feeds when they describe the same event.
7. Draft a brief section and a matching detailed section as a paired list where every brief item has one matching detailed item.
8. Write the final markdown report and save it into the requested output directory.
9. Confirm the output path.

## Agent-first boundary

The Agent owns the final report.
Python only fetches and normalizes candidate data.

Do not shift any of these responsibilities into Python:

- deciding what is important
- selecting the final top items
- merging overlapping stories into a single narrative
- writing the brief bullets
- writing the detailed summaries
- writing the final markdown report

## Supported source types

The bundled fetcher supports:

- RSS feeds
- Reddit public JSON only

Never use Reddit OAuth in this skill.

## Time handling

Prefer explicit ISO-8601 timestamps with offsets.
Example:

`2026-03-09T20:00:00+08:00`

If the task describes Beijing time, use `+08:00` unless the user gave another offset.

## Selection mechanism

Do not select items randomly and do not rely on freshness alone.
Use a lightweight editorial filter.
Use the active report profile as the authoritative source for report-level defaults such as item count, output paths, and editorial focus.
If no profile is provided, use general editorial judgment and keep the report compact, non-repetitive, and useful.

Prefer this order:

1. Skim all fetched `items`.
2. Group duplicated or overlapping stories.
3. Pick the events with the highest editorial value for the reporting window.
4. Prefer a balanced mix instead of many variations of the same theme.
5. Use community signals from Reddit or Hacker News as supporting evidence, not as the only reason to include an item.

## Fetched JSON schema you must understand

The fetch script outputs one JSON document with top-level metadata and fetched items.

Top-level structure:

```json
{
  "fetched_at": "2026-03-10T08:05:00+00:00",
  "from": "2026-03-09T12:00:00+00:00",
  "to": "2026-03-10T00:00:00+00:00",
  "config_path": "configs/sources.json",
  "items": [],
  "sources": []
}
```

Item structure:

```json
{
  "id": "reddit:ml:https://example.com",
  "source_id": "ml",
  "source_type": "reddit",
  "source_name": "r/MachineLearning",
  "title": "Example title",
  "url": "https://example.com",
  "published_at": "2026-03-10T07:12:00+00:00",
  "summary": "optional short source summary",
  "metadata": {}
}
```

Important notes:

- `items` is the main list you should read for report writing
- `sources` is a diagnostics-only list and should not contain duplicated full item bodies
- `summary` may be empty and may be compacted into short plain text
- `metadata` varies by source type and is intentionally compact
- for Reddit items, `metadata` may include `reddit_url`, `score`, `num_comments`, `subreddit`, and `priority`
- for RSS items, `metadata` may include `tags` and `priority`

## Report-writing rules

When writing the report:

- prefer concise, information-dense Chinese writing unless the user requested another language
- actually use the language from the active report profile or explicit user instruction
- keep the top brief section short and scannable
- make the brief section and the detailed section a strict one-to-one mapping
- keep the same item count in both sections
- keep the same ordering in both sections
- do not leave any brief item without a matching detailed item
- do not add any detailed item that does not appear in the brief section
- keep the detailed section grounded in the fetched items
- retain source links
- avoid filler language and vague claims
- if multiple items describe the same event, unify them into one stronger entry instead of listing all of them separately

Use this structure unless the user explicitly requested another format.
The section titles are illustrative and should be localized to the report language.

```md
# 2026-03-10 Tech Brief (2026-03-10 08:00)

## [brief section title]

1. ...
2. ...
3. ...

## [detailed section title]

### 1. Headline
https://example.com

Write the detailed summary here.
```

Formatting guidance:

- the title should include the report date and the visible report end time
- the brief section should follow the active report profile or explicit user instruction for item count
- the detailed section must expand every item listed in the brief section
- the brief section and the detailed section must have the same item count and the same order
- keep links directly under each item heading
- prefer factual, compressed wording
- avoid repeating the same context in every paragraph

## Data-fetching rule

The fetch script may return more items than you need.
That is expected.
Do not dump all fetched items into the report.
Curate aggressively.

## Failure handling

If fetching partially fails:

- continue if enough high-quality material remains
- mention major source failures briefly in your final response if they materially affect coverage

If fetching fully fails:

- report the failure clearly
- include the command used
- suggest the most likely next fix, such as checking the config JSON or network access

## Output requirement

Save the final report as markdown in the requested output directory.
If no filename is specified, derive one from the report name and report end time.
