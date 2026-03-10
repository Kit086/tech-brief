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
- output directory
- optional output filename
- optional maximum item count
- optional intermediate output directory for topic-selection artifacts

If the task comes from cron and these values are already explicit, do not ask unnecessary follow-up questions.

## Execution flow

1. Read `references/execution-rules.md`.
2. Read `references/report-format.md` when drafting the final markdown.
3. Read `references/source-schema.md` if you need to understand the fetched JSON structure.
4. Run `scripts/fetch_sources.py` to generate one merged JSON file for the requested time range.
5. Read the generated JSON output and review `items` as the main candidate pool.
6. Build a topic-selection artifact that records candidate clusters, selected topics, merged items, and concise selection reasons.
7. Select roughly 10 to 20 items for `## 简报`, then expand the strongest subset in `## 摘要`.
8. Merge duplicates or near-duplicates across feeds when they describe the same event.
9. Save the topic-selection artifact into a subdirectory separate from the final tech brief output.
10. Write the final markdown report.
11. Save the report into the requested output directory.
12. Confirm both output paths.

## Selection mechanism

Do not select items randomly and do not rely on freshness alone.
Use a lightweight editorial filter.

When choosing items, prefer material that scores well on several of these dimensions:

- significance to the technology landscape
- relevance to AI, developer tools, infrastructure, open source, security, or major platform shifts
- relevance to public-market sentiment, major indexes such as Nasdaq, S&P 500, or SSE, and news likely to affect megacap technology stocks
- discussion intensity, such as strong Hacker News or Reddit engagement when available
- evidence of cross-source reinforcement, especially when the same event appears in both media and community sources
- novelty within the reporting window
- usefulness to a reader who wants a compact but meaningful picture of what changed

Avoid filling the report with repetitive items that all say nearly the same thing.
If multiple sources cover the same event, keep the strongest representation and use the other sources as supporting context.

## Suggested curation steps

Use this order of operations:

1. Skim all fetched `items`.
2. Group obviously duplicated stories by shared URL, shared company/topic, or clearly overlapping headline meaning.
3. Identify the events with the highest editorial value for this reporting window.
4. Give extra attention to items that may move public-market narratives around major indexes or megacap technology companies.
5. Prefer a balanced mix instead of twenty variations of the same theme.
6. Use community signals from Reddit or Hacker News as supporting evidence, not as the only reason to include an item.
7. Draft the topic-selection artifact before writing the final report.
8. Write concise one-line brief bullets first.
9. Expand only the items that still feel important after the brief list is drafted.

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
- the top brief section may scale up to about 20 items when the window is information-dense
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
