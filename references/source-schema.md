# Source Schema

The fetch script outputs one JSON document with top-level metadata and fetched items.

## Top-level structure

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

## Item structure

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

## Notes

- `items` is the main list the Agent should read for report writing.
- `sources` contains per-source diagnostics and counts.
- `summary` may be empty.
- `metadata` varies by source type.
- For Reddit items, `metadata` may include `reddit_url`, `external_url`, `score`, `num_comments`, `subreddit`, `sort`, and `priority`.
- For RSS items, `metadata` may include `author`, `tags`, and feed-specific fields.
