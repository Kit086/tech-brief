# Execution Rules

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

## Recommended execution pattern

1. Confirm the reporting window.
2. Confirm the JSON source config file.
3. Run the fetch script with explicit `--from` and `--to` values when a window is provided.
4. Read the output JSON.
5. Review `items` first.
6. Use `sources` or source-level status only for diagnostics.
7. Curate and write the report.
8. Save the markdown file.

## Time handling

Prefer explicit ISO-8601 timestamps with offsets.
Example:

`2026-03-09T20:00:00+08:00`

If the task describes Beijing time, use `+08:00` unless the user gave another offset.

## Source handling

The bundled fetcher supports:

- RSS feeds
- Reddit public JSON only

Never use Reddit OAuth in this skill.

## Output handling

The fetcher writes structured JSON for Agent consumption.
The Agent writes the final markdown report separately.
