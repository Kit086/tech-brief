# Tech Brief

`tech-brief` is an Agent-first skill for generating scheduled or on-demand markdown tech brief reports over a defined time window.

## Design boundary

- The Agent decides what matters, merges overlapping stories, and writes the final markdown report.
- Python only fetches and normalizes candidate data from RSS feeds and Reddit public JSON.

## Skill layout

```text
tech-brief/
├── SKILL.md
├── scripts/
│   └── fetch_sources.py
├── references/
├── assets/
├── configs/
│   ├── sources.example.json
│   └── report-profiles.example.json
├── pyproject.toml
└── README.md
```

## Installation

Clone this repository into a location where your Agent or local workspace can access it.

```bash
git clone https://github.com/Kit086/tech-brief.git
```

The skill itself is defined by `SKILL.md` together with `scripts/`, `references/`, `assets/`, and `configs/`.

Before customizing sources or report defaults, copy the example config files into your own working files:

```bash
copy configs\sources.example.json configs\sources.json
copy configs\report-profiles.example.json configs\report-profiles.json
```

Use your copied `sources.json` and `report-profiles.json` for customization.
This helps prevent your custom sources or report defaults from being overwritten when you update the skill repository later.

## Environment

To run `scripts/fetch_sources.py`, you need:

- Python 3.13 or newer
- the Python dependency declared in `pyproject.toml`
- network access to the configured RSS feeds and Reddit public JSON endpoints

If you prefer plain `pip`, install the dependency manually:

```bash
pip install feedparser
```

## Development

`uv` is optional and is only recommended for local development and verification.

Example:

```bash
uv sync
```

## Fetcher usage

Example:

```bash
python scripts/fetch_sources.py \
  --config configs/sources.example.json \
  --from 2026-03-09T20:00:00+08:00 \
  --to 2026-03-10T08:00:00+08:00 \
  --output tmp/fetched-items.json
```

The fetcher writes a JSON document with:

- top-level fetch metadata
- `items` for Agent consumption
- `sources` for source-level diagnostics