---
name: tech-brief
description: Generate scheduled or on-demand multi-source tech brief reports for an Agent. Use this skill whenever the user asks for a tech daily, morning brief, evening brief, markdown news summary, or a cron-driven report over a specific time window using RSS feeds and Reddit sources. This skill is especially appropriate when the task includes a reporting window, source configuration, and an output directory, even if the user does not explicitly mention the skill.
---

# Tech Brief

Use this skill to help an Agent produce a markdown tech brief over a specific time window.

The Agent is responsible for the report itself.
The bundled Python script is only a data collection utility.
Do not let the script replace your judgment, synthesis, or writing.

## Core rule

Treat `scripts/fetch_sources.py` as a structured data fetcher.
It fetches and normalizes candidate items from RSS feeds and Reddit public JSON endpoints.
It does not decide what matters.
It does not write the final report.
You must read the fetched data, choose what deserves inclusion, merge overlapping topics, and write the final markdown report yourself.

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
- optional report profile JSON path
- optional report profile id
- output directory
- optional output filename
- optional maximum item count
- optional intermediate output directory for topic-selection artifacts

If the task comes from cron and these values are already explicit, do not ask unnecessary follow-up questions.
If a report profile is available, treat it as the authoritative source for report-level defaults.

## Execution flow

1. Read `references/execution-rules.md`.
2. Read `references/report-format.md` when drafting the final markdown.
3. Read `references/source-schema.md` if you need to understand the fetched JSON structure.
4. Read the active report profile when one is provided.
5. Run `scripts/fetch_sources.py` to generate one merged JSON file for the requested time range.
6. Read the generated JSON output and review `items` as the main candidate pool.
7. Build a topic-selection artifact that records candidate clusters, selected topics, merged items, and concise selection reasons.
8. Select items according to the active report profile or explicit user instructions.
9. Merge duplicates or near-duplicates across feeds when they describe the same event.
10. Draft `## 简报` and `## 摘要` as a paired list where every brief item has one matching detailed item.
11. Save the topic-selection artifact into a subdirectory separate from the final tech brief output.
12. Write the final markdown report.
13. Save the report into the requested output directory.
14. Confirm both output paths.

## Selection mechanism

Do not select items randomly and do not rely on freshness alone.
Use a lightweight editorial filter.
Use the active report profile as the authoritative source for report-level defaults such as item count, output paths, and editorial focus.
If no profile is provided, use general editorial judgment and keep the report compact, non-repetitive, and useful.

## Suggested curation steps

Use this order of operations:

1. Skim all fetched `items`.
2. Group obviously duplicated stories by shared URL, shared company/topic, or clearly overlapping headline meaning.
3. Identify the events with the highest editorial value for this reporting window.
4. Prefer a balanced mix instead of many variations of the same theme.
5. Use community signals from Reddit or Hacker News as supporting evidence, not as the only reason to include an item.
6. Draft the topic-selection artifact before writing the final report.
7. Write concise one-line brief bullets first.
8. Expand only the items that still feel important after the brief list is drafted.

## Topic-selection artifact

Before writing the final report, produce an intermediate artifact such as `selected-topics.json` or `selected-topics.md`.

The artifact should capture:

- selected topic title
- selected status
- short selection reason
- supporting `item` identifiers or URLs
- merged or related items when multiple sources describe the same event
- optional editorial note about why the topic matters

Save this artifact in a different subdirectory from the final report so the curation step can be reviewed independently.
For example:

- intermediate artifact under `.../selection/`
- final report under `.../reports/`

## Report-writing rules

When writing the report:

- prefer concise, information-dense Chinese writing unless the user requested another language
- keep the top brief section short and scannable
- make `## 简报` and `## 摘要` a strict one-to-one mapping
- keep the same item count in both sections
- keep the same ordering in both sections
- do not leave any brief item without a matching detailed item
- do not add any detailed item that does not appear in `## 简报`
- keep the detailed section grounded in the fetched items
- retain source links
- avoid filler language and vague claims
- if multiple items describe the same event, unify them into one stronger entry instead of listing all of them separately

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
