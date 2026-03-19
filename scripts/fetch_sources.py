from __future__ import annotations

import argparse
import json
import re
import ssl
import sys
import time
from concurrent.futures import ThreadPoolExecutor, as_completed
from dataclasses import dataclass
from datetime import datetime, timedelta, timezone
from html import unescape
from pathlib import Path
from typing import Any
from urllib.error import HTTPError, URLError
from urllib.request import Request, urlopen

import feedparser

_SSL_CTX = ssl.create_default_context()
USER_AGENT = "tech-brief/0.0.5 (+https://github.com/Kit086/tech-brief)"
TIMEOUT_SECONDS = 30
RETRY_COUNT = 2
RETRY_DELAY_SECONDS = 3
MAX_WORKERS = 6
SUMMARY_MAX_CHARS = 280
REDDIT_BASE_URLS = [
    "https://www.reddit.com",
    "https://old.reddit.com",
]


@dataclass
class FetchWindow:
    start: datetime
    end: datetime


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Fetch RSS and Reddit sources into Agent-friendly JSON."
    )
    parser.add_argument(
        "--config", type=Path, required=True, help="Source config JSON path"
    )
    parser.add_argument(
        "--from",
        dest="from_time",
        type=str,
        help="Inclusive start time in ISO-8601 format",
    )
    parser.add_argument(
        "--to", dest="to_time", type=str, help="Inclusive end time in ISO-8601 format"
    )
    parser.add_argument(
        "--hours",
        type=int,
        default=24,
        help="Fallback lookback hours when --from is omitted",
    )
    parser.add_argument(
        "--output", type=Path, required=True, help="Output JSON file path"
    )
    parser.add_argument(
        "--source-ids",
        type=str,
        default="",
        help="Comma-separated source ids to include",
    )
    return parser.parse_args()


def parse_datetime(value: str) -> datetime:
    dt = datetime.fromisoformat(value.replace("Z", "+00:00"))
    if dt.tzinfo is None:
        dt = dt.replace(tzinfo=timezone.utc)
    return dt.astimezone(timezone.utc)


def build_window(args: argparse.Namespace) -> FetchWindow:
    end = parse_datetime(args.to_time) if args.to_time else datetime.now(timezone.utc)
    start = (
        parse_datetime(args.from_time)
        if args.from_time
        else end - timedelta(hours=args.hours)
    )
    return FetchWindow(start=start, end=end)


def load_config(path: Path) -> list[dict[str, Any]]:
    payload = json.loads(path.read_text(encoding="utf-8"))
    sources = payload.get("sources", [])
    enabled_sources = []
    for source in sources:
        if not source.get("enabled", True):
            continue
        enabled_sources.append(source)
    return enabled_sources


def select_sources(
    sources: list[dict[str, Any]], source_ids_arg: str
) -> list[dict[str, Any]]:
    source_ids = {part.strip() for part in source_ids_arg.split(",") if part.strip()}
    if not source_ids:
        return sources
    return [source for source in sources if source.get("id") in source_ids]


def strip_html(value: str) -> str:
    text = re.sub(r"<[^>]+>", " ", value)
    text = unescape(text)
    return re.sub(r"\s+", " ", text).strip()


def compact_summary(value: str) -> str:
    text = strip_html(value)
    if len(text) <= SUMMARY_MAX_CHARS:
        return text
    truncated = text[: SUMMARY_MAX_CHARS - 1].rstrip()
    if " " in truncated:
        truncated = truncated.rsplit(" ", 1)[0]
    return f"{truncated}…"


def compact_item_metadata(item: dict[str, Any]) -> dict[str, Any]:
    source_type = item.get("source_type")
    metadata = item.get("metadata") or {}
    if source_type == "rss":
        compacted = {
            "priority": metadata.get("priority", False),
        }
        tags = metadata.get("tags") or []
        useful_tags = [tag for tag in tags if tag]
        if useful_tags:
            compacted["tags"] = useful_tags[:3]
        return compacted
    if source_type == "reddit":
        compacted = {
            "score": metadata.get("score", 0),
            "num_comments": metadata.get("num_comments", 0),
            "subreddit": metadata.get("subreddit"),
            "priority": metadata.get("priority", False),
        }
        reddit_url = metadata.get("reddit_url")
        if reddit_url and reddit_url != item.get("url"):
            compacted["reddit_url"] = reddit_url
        return compacted
    return metadata


def compact_item(item: dict[str, Any]) -> dict[str, Any]:
    compacted = {
        "id": item.get("id"),
        "source_id": item.get("source_id"),
        "source_type": item.get("source_type"),
        "source_name": item.get("source_name"),
        "title": item.get("title"),
        "url": item.get("url"),
        "published_at": item.get("published_at"),
        "summary": compact_summary(item.get("summary") or ""),
        "metadata": compact_item_metadata(item),
    }
    return prune_empty_values(compacted)


def compact_source_result(result: dict[str, Any]) -> dict[str, Any]:
    compacted = {
        "source_id": result.get("source_id"),
        "source_type": result.get("source_type"),
        "name": result.get("name"),
        "status": result.get("status"),
        "error": result.get("error"),
        "count": result.get("count"),
        "priority": result.get("priority", False),
    }
    if result.get("source_type") == "reddit":
        compacted["subreddit"] = result.get("subreddit")
        if result.get("status") != "ok" or (result.get("attempts") or 1) > 1:
            compacted["attempts"] = result.get("attempts")
    return prune_empty_values(compacted)


def prune_empty_values(value: Any) -> Any:
    if isinstance(value, dict):
        cleaned = {}
        for key, nested in value.items():
            compacted = prune_empty_values(nested)
            if compacted is None:
                continue
            if compacted == "":
                continue
            if compacted == []:
                continue
            if compacted == {}:
                continue
            cleaned[key] = compacted
        return cleaned
    if isinstance(value, list):
        cleaned = []
        for nested in value:
            compacted = prune_empty_values(nested)
            if compacted is None:
                continue
            if compacted == "":
                continue
            cleaned.append(compacted)
        return cleaned
    return value


def normalize_rss_item(source: dict[str, Any], entry: Any) -> dict[str, Any]:
    published_at = pick_entry_datetime(entry)
    tags = []
    for tag in getattr(entry, "tags", []) or []:
        term = getattr(tag, "term", None)
        if term:
            tags.append(term)
    url = getattr(entry, "link", "") or ""
    title = getattr(entry, "title", "") or ""
    source_id = source.get("id", "")
    item_id = f"rss:{source_id}:{url or title}"
    return {
        "id": item_id,
        "source_id": source_id,
        "source_type": "rss",
        "source_name": source.get("name") or source_id,
        "title": title,
        "url": url,
        "published_at": published_at.isoformat() if published_at else None,
        "summary": compact_summary(
            getattr(entry, "summary", "") or getattr(entry, "description", "") or ""
        ),
        "metadata": {
            "tags": tags,
            "priority": bool(source.get("priority", False)),
        },
    }


def pick_entry_datetime(entry: Any) -> datetime | None:
    candidates = [
        getattr(entry, "published_parsed", None),
        getattr(entry, "updated_parsed", None),
        getattr(entry, "created_parsed", None),
    ]
    for candidate in candidates:
        if candidate is None:
            continue
        return datetime(*candidate[:6], tzinfo=timezone.utc)
    return None


def fetch_rss_source(source: dict[str, Any], window: FetchWindow) -> dict[str, Any]:
    url = source["url"]
    parsed = feedparser.parse(url, agent=USER_AGENT)
    items = []
    for entry in parsed.entries:
        normalized = normalize_rss_item(source, entry)
        published_at = normalized.get("published_at")
        if not published_at:
            continue
        item_dt = parse_datetime(published_at)
        if item_dt < window.start or item_dt > window.end:
            continue
        if not normalized.get("title") or not normalized.get("url"):
            continue
        items.append(normalized)
    items.sort(key=lambda item: item.get("published_at") or "", reverse=True)
    status = "ok"
    error = None
    if getattr(parsed, "bozo", 0):
        status = "warning"
        error = str(getattr(parsed, "bozo_exception", "feed parse warning"))
    return {
        "source_id": source.get("id"),
        "source_type": "rss",
        "name": source.get("name"),
        "status": status,
        "error": error,
        "count": len(items),
        "items": items,
        "priority": bool(source.get("priority", False)),
    }


def fetch_reddit_source(source: dict[str, Any], window: FetchWindow) -> dict[str, Any]:
    source_id = source["id"]
    subreddit = source["subreddit"]
    sort = source.get("sort", "hot")
    limit = int(source.get("limit", 25))
    min_score = int(source.get("min_score", 0))
    name = source.get("name", f"r/{subreddit}")
    priority = bool(source.get("priority", False))
    error_message = None

    for base_url in REDDIT_BASE_URLS:
        url = f"{base_url}/r/{subreddit}/{sort}.json?limit={limit}&raw_json=1"
        for attempt in range(RETRY_COUNT + 1):
            try:
                request = Request(
                    url,
                    headers={
                        "User-Agent": USER_AGENT,
                        "Accept": "application/json, text/javascript, */*; q=0.01",
                        "Accept-Language": "en-US,en;q=0.9",
                        "Referer": f"{base_url}/r/{subreddit}/",
                        "Origin": base_url,
                        "DNT": "1",
                        "Pragma": "no-cache",
                        "Cache-Control": "no-cache",
                    },
                )
                with urlopen(
                    request, timeout=TIMEOUT_SECONDS, context=_SSL_CTX
                ) as response:
                    payload = json.loads(response.read().decode("utf-8"))
                items = []
                children = payload.get("data", {}).get("children", [])
                for child in children:
                    post = child.get("data", {})
                    if not post:
                        continue
                    title = (post.get("title") or "").strip()
                    if not title:
                        continue
                    created_utc = post.get("created_utc")
                    if created_utc is None:
                        continue
                    published_at_dt = datetime.fromtimestamp(
                        created_utc, tz=timezone.utc
                    )
                    if published_at_dt < window.start or published_at_dt > window.end:
                        continue
                    if post.get("stickied", False):
                        continue
                    score = int(post.get("score", 0) or 0)
                    if score < min_score:
                        continue
                    permalink = f"https://www.reddit.com{post.get('permalink', '')}"
                    external_url = post.get("url") or ""
                    is_self = bool(post.get("is_self", True))
                    if (
                        is_self
                        or "reddit.com" in external_url
                        or "redd.it" in external_url
                    ):
                        final_url = permalink
                        external_url = None
                    else:
                        final_url = external_url
                    item_id = f"reddit:{source_id}:{final_url or title}"
                    items.append(
                        {
                            "id": item_id,
                            "source_id": source_id,
                            "source_type": "reddit",
                            "source_name": name,
                            "title": title,
                            "url": final_url,
                            "published_at": published_at_dt.isoformat(),
                            "summary": compact_summary(
                                post.get("link_flair_text") or ""
                            ),
                            "metadata": {
                                "reddit_url": permalink,
                                "score": score,
                                "num_comments": int(post.get("num_comments", 0) or 0),
                                "subreddit": subreddit,
                                "priority": priority,
                            },
                        }
                    )
                items.sort(
                    key=lambda item: item.get("published_at") or "", reverse=True
                )
                return {
                    "source_id": source_id,
                    "source_type": "reddit",
                    "name": name,
                    "status": "ok",
                    "error": None,
                    "count": len(items),
                    "items": items,
                    "priority": priority,
                    "subreddit": subreddit,
                    "sort": sort,
                    "attempts": attempt + 1,
                    "base_url": base_url,
                }
            except HTTPError as exc:
                error_message = f"HTTP {exc.code} from {base_url}"
                if exc.code == 429 and attempt < RETRY_COUNT:
                    time.sleep(10)
                    continue
                if exc.code == 403:
                    break
            except (URLError, OSError) as exc:
                error_message = f"{exc} from {base_url}"
            except Exception as exc:
                error_message = f"{exc} from {base_url}"
            if attempt < RETRY_COUNT:
                time.sleep(RETRY_DELAY_SECONDS)
    return {
        "source_id": source_id,
        "source_type": "reddit",
        "name": name,
        "status": "error",
        "error": error_message,
        "count": 0,
        "items": [],
        "priority": priority,
        "subreddit": subreddit,
        "sort": sort,
        "attempts": RETRY_COUNT + 1,
    }


def fetch_one(source: dict[str, Any], window: FetchWindow) -> dict[str, Any]:
    source_type = source.get("type")
    if source_type == "rss":
        return fetch_rss_source(source, window)
    if source_type == "reddit":
        return fetch_reddit_source(source, window)
    return {
        "source_id": source.get("id"),
        "source_type": source_type,
        "name": source.get("name"),
        "status": "error",
        "error": f"Unsupported source type: {source_type}",
        "count": 0,
        "items": [],
        "priority": bool(source.get("priority", False)),
    }


def flatten_items(results: list[dict[str, Any]]) -> list[dict[str, Any]]:
    items = []
    for result in results:
        items.extend(compact_item(item) for item in result.get("items", []))
    items.sort(key=lambda item: item.get("published_at") or "", reverse=True)
    return items


def write_output(output_path: Path, payload: dict[str, Any]) -> None:
    output_path.parent.mkdir(parents=True, exist_ok=True)
    output_path.write_text(
        json.dumps(payload, ensure_ascii=False, indent=2),
        encoding="utf-8",
    )


def main() -> int:
    args = parse_args()
    if not args.config.exists():
        raise FileNotFoundError(f"Config file not found: {args.config}")
    window = build_window(args)
    sources = load_config(args.config)
    selected_sources = select_sources(sources, args.source_ids)
    results = []
    with ThreadPoolExecutor(max_workers=MAX_WORKERS) as pool:
        future_map = {
            pool.submit(fetch_one, source, window): source
            for source in selected_sources
        }
        for future in as_completed(future_map):
            results.append(future.result())
    results.sort(
        key=lambda result: (
            not result.get("priority", False),
            -(result.get("count", 0) or 0),
        )
    )
    payload = {
        "fetched_at": datetime.now(timezone.utc).isoformat(),
        "from": window.start.isoformat(),
        "to": window.end.isoformat(),
        "config_path": str(args.config),
        "item_count": sum(result.get("count", 0) for result in results),
        "items": flatten_items(results),
        "sources": [compact_source_result(result) for result in results],
    }
    write_output(args.output, payload)
    print(args.output)
    return 0


if __name__ == "__main__":
    sys.exit(main())
