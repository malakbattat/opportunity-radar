"""Fetch → classify → de-duplicate → merge with history → write docs/data + RSS.

Usage:
    python -m scraper.run                 # live run (all enabled sources)
    python -m scraper.run --only scholarshipsads,opportunityportal
    python -m scraper.run --raw seed.json # classify a saved list of raw items (offline)
"""
from __future__ import annotations

import argparse
import hashlib
import json
import logging
import os
import sys
import time
from datetime import date, datetime, timedelta, timezone
from email.utils import format_datetime
from pathlib import Path
from typing import Any
from xml.sax.saxutils import escape

import yaml

from .classify import REGIONS, Classifier, intake_is_past, same_opportunity
from .sources import SOURCE_META, build_sources

ROOT = Path(__file__).resolve().parent.parent
DATA_FILE = ROOT / "docs" / "data" / "opportunities.json"
ARCHIVE_FILE = ROOT / "docs" / "data" / "archive.json"
FEED_FILE = ROOT / "docs" / "feed.xml"
CONFIG_FILE = ROOT / "config.yaml"

log = logging.getLogger("radar")


def load_config() -> dict[str, Any]:
    with open(CONFIG_FILE, encoding="utf-8") as f:
        return yaml.safe_load(f)


def load_archive() -> list[dict[str, Any]]:
    if ARCHIVE_FILE.exists():
        try:
            return json.loads(ARCHIVE_FILE.read_text(encoding="utf-8")).get("items", [])
        except json.JSONDecodeError:
            log.warning("Archive file is corrupt; starting a new one")
    return []


def load_previous() -> dict[str, Any]:
    if DATA_FILE.exists():
        try:
            return json.loads(DATA_FILE.read_text(encoding="utf-8"))
        except json.JSONDecodeError:
            log.warning("Existing data file is corrupt; starting fresh")
    return {"items": [], "sources": {}}


def dedupe(items: list[dict[str, Any]]) -> list[dict[str, Any]]:
    """Merge the same opportunity listed on several sites (by URL, then title key).
    Keeps the highest-scoring copy and records the others under also_on."""
    by_key: dict[str, dict[str, Any]] = {}
    url_to_key: dict[str, str] = {}
    for it in sorted(items, key=lambda x: -x["score"]):
        key = url_to_key.get(it["id"]) or (it["_key"] if len(it["_key"]) >= 12 else it["id"])
        if key not in by_key and len(it["_key"]) >= 12:
            # Same opportunity, differently worded title on another site?
            key = next((k for k, v in by_key.items() if v["source"] != it["source"] and same_opportunity(k, it["_key"])), key)
        if key in by_key:
            keep = by_key[key]
            if it["source"] != keep["source"] and it["url"] not in [a["url"] for a in keep["also_on"]]:
                keep["also_on"].append({"source": it["source"], "url": it["url"]})
            # Fill gaps from the duplicate.
            for f in ("deadline", "country", "org", "funding", "eligibility", "eligibility_note"):
                if not keep.get(f) and it.get(f):
                    keep[f] = it[f]
            keep["degrees"] = sorted(set(keep["degrees"]) | set(it["degrees"]), key=["bachelor", "masters", "phd", "postdoc"].index)
            keep["fields"] = keep["fields"] + [f for f in it["fields"] if f not in keep["fields"]]
            for f in ("countries", "regions", "intakes"):
                keep[f] = keep.get(f, []) + [c for c in it.get(f, []) if c not in keep.get(f, [])]
            if it.get("rolling") and not keep.get("deadline"):
                keep["rolling"] = True
            continue
        it = dict(it)
        it["also_on"] = []
        by_key[key] = it
        url_to_key[it["id"]] = key
    return list(by_key.values())


REOPEN_TYPES = {"Scholarship", "Fellowship", "Research", "Summer school", "Exchange", "Competition", "Conference",
                "Grant", "Externship", "Mentorship", "Course", "Internship"}


def _expected_reopen(item: dict[str, Any], cfg: dict[str, Any], today: date) -> str | None:
    """Most programmes run every year: estimate the next cycle from the last deadline."""
    if not item.get("deadline") or item.get("type") not in REOPEN_TYPES:
        return None
    if cfg.get("sources", {}).get(item["source"], {}).get("recurring") is False:
        return None
    d = date.fromisoformat(item["deadline"])
    while d <= today:
        try:
            d = d.replace(year=d.year + 1)
        except ValueError:
            d += timedelta(days=365)
    return d.isoformat()


def _expected_intake(item: dict[str, Any], cfg: dict[str, Any], today: date) -> str | None:
    """For programmes whose semester/year is over, the same intake one cycle later (e.g. Summer 2026 → Summer 2027)."""
    if item.get("type") not in REOPEN_TYPES or not item.get("intakes"):
        return None
    if cfg.get("sources", {}).get(item["source"], {}).get("recurring") is False:
        return None
    key = item["intakes"][-1]
    year, _, part = key.partition("-")
    y = int(year)
    start_month = {"": 1, "spring": 1, "summer": 6, "ay": 9, "fall": 9, "winter": 12}.get(part, 1)
    while y * 12 + start_month <= today.year * 12 + today.month:     # first cycle that hasn't started yet
        y += 1
    return f"{y}-{part}" if part else str(y)


def merge_history(fresh: list[dict[str, Any]], previous: list[dict[str, Any]], cfg: dict[str, Any],
                  today: date, run_stamp: str, failed_sources: set[str],
                  archive: list[dict[str, Any]] | None = None) -> tuple[list[dict[str, Any]], list[dict[str, Any]]]:
    """Returns (open items, archive).

    Open: deadline today or later, or no deadline and still listed by its source.
    Archive: closed (deadline passed), past_intake (its year/semester is over) or removed (no longer
    listed by its source). Archived items that come back with a new cycle return to open, marked reopened."""
    ret = cfg["retention"]
    src_cfg = cfg.get("sources", {})
    grace_closed = timedelta(days=ret.get("keep_after_deadline_days", 0))
    prev_by_id = {p["id"]: p for p in previous}
    prev_by_key = {p.get("_key"): p for p in previous if p.get("_key")}
    arch_by_id = {a["id"]: a for a in archive or []}
    arch_by_key = {a.get("_key"): a for a in archive or [] if a.get("_key")}
    active: dict[str, dict[str, Any]] = {}
    to_archive: list[tuple[dict[str, Any], str]] = []

    def closed(it: dict[str, Any]) -> bool:
        return bool(it.get("deadline")) and date.fromisoformat(it["deadline"]) < today - grace_closed

    for it in fresh:
        old = prev_by_id.get(it["id"]) or prev_by_key.get(it["_key"])
        arch = arch_by_id.get(it["id"]) or arch_by_key.get(it["_key"])
        it["last_seen"] = run_stamp
        if closed(it):
            to_archive.append((it, "closed"))
            it["first_seen"] = (old or arch or {}).get("first_seen", run_stamp)
            continue
        if it.get("past_intake"):
            to_archive.append((it, "past_intake"))
            it["first_seen"] = (old or arch or {}).get("first_seen", run_stamp)
            continue
        if old:
            it["first_seen"] = old["first_seen"]
            if old.get("reopened_at"):
                it["reopened_at"] = old["reopened_at"]
        elif arch:
            it["first_seen"] = run_stamp
            it["reopened_at"] = run_stamp
        else:
            it["first_seen"] = run_stamp
        active[it["id"]] = it

    seen_keys = [it["_key"] for it, _ in to_archive] + [it["_key"] for it in active.values()]
    seen_urls = {a["url"] for it in active.values() for a in it.get("also_on", [])}
    seen_ids = set(active) | {it["id"] for it, _ in to_archive}
    for p in previous:
        if p["id"] in seen_ids or p["url"] in seen_urls:
            continue
        if p.get("_key") and any(same_opportunity(p["_key"], k) for k in seen_keys):
            continue
        if closed(p):
            to_archive.append((p, "closed"))
            continue
        if p.get("deadline"):
            active[p["id"]] = p          # still open; the source may just be slow or failing today
            continue
        last_seen = date.fromisoformat(p.get("last_seen", run_stamp)[:10])
        grace = src_cfg.get(p["source"], {}).get("keep_unseen_days", ret["keep_unseen_rolling_days"])
        grace *= 3 if p["source"] in failed_sources else 1
        if (today - last_seen).days <= grace:
            active[p["id"]] = p
        else:
            to_archive.append((p, "removed"))

    items = sorted(active.values(), key=lambda i: (-i["score"], i.get("deadline") or "9999"))
    overflow = items[ret["max_items"]:]
    items = items[: ret["max_items"]]
    to_archive += [(i, "removed") for i in overflow]

    # Archive: keep the first archived_at, refresh the rest, drop what came back or got too old.
    out: dict[str, dict[str, Any]] = {a["id"]: a for a in archive or [] if a["id"] not in active}
    for it, reason in to_archive:
        if src_cfg.get(it["source"], {}).get("archive") is False:
            continue
        prior = out.get(it["id"])
        rec = dict(it)
        rec["archive_reason"] = reason
        rec["archived_at"] = prior["archived_at"] if prior else run_stamp
        rec["reopens"] = _expected_reopen(rec, cfg, today) if reason == "closed" else None
        rec["reopens_intake"] = _expected_intake(rec, cfg, today) if reason in ("closed", "past_intake") else None
        out[it["id"]] = rec
    keep_days = ret.get("archive_days", 400)
    arch_items = [a for a in out.values()
                  if (today - date.fromisoformat(a["archived_at"][:10])).days <= keep_days]
    for a in arch_items:            # refresh the estimate as time passes
        if a.get("archive_reason") == "closed":
            a["reopens"] = _expected_reopen(a, cfg, today)
        if a.get("archive_reason") in ("closed", "past_intake"):
            a["reopens_intake"] = _expected_intake(a, cfg, today)
    arch_items.sort(key=lambda a: a["archived_at"], reverse=True)
    return items, arch_items[: ret.get("archive_max", 2000)]


def _ics_escape(text: str) -> str:
    return str(text).replace("\\", "\\\\").replace(";", "\\;").replace(",", "\\,").replace("\n", "\\n")


def _ics_fold(line: str) -> str:
    """Fold content lines to 75 octets, as calendar apps expect."""
    out, buf = [], b""
    for ch in line:
        enc = ch.encode("utf-8")
        if len(buf) + len(enc) > (75 if not out else 74):
            out.append(buf.decode("utf-8"))
            buf = b""
        buf += enc
    out.append(buf.decode("utf-8"))
    return "\r\n ".join(out)


def build_ics(items: list[dict[str, Any]], name: str, now: datetime, base_url: str = "") -> str:
    stamp = now.strftime("%Y%m%dT%H%M%SZ")
    lines = ["BEGIN:VCALENDAR", "VERSION:2.0", "PRODID:-//Opportunity Radar//EN", "CALSCALE:GREGORIAN", "METHOD:PUBLISH",
             f"X-WR-CALNAME:{_ics_escape(name)}", "X-WR-TIMEZONE:UTC", "REFRESH-INTERVAL;VALUE=DURATION:PT1H", "X-PUBLISHED-TTL:PT1H"]
    for it in items:
        d = date.fromisoformat(it["deadline"])
        prefix = "Expected deadline" if it.get("deadline_estimated") else "Deadline"
        desc = [it["url"], f"Score {it['score']}/100 · {it['type']}"]
        if it.get("summary"):
            desc.append(it["summary"])
        if base_url:
            desc.append(base_url)
        lines += ["BEGIN:VEVENT", f"UID:{it['id']}@opportunity-radar", f"DTSTAMP:{stamp}",
                  f"DTSTART;VALUE=DATE:{d.strftime('%Y%m%d')}", f"DTEND;VALUE=DATE:{(d + timedelta(days=1)).strftime('%Y%m%d')}",
                  f"SUMMARY:{_ics_escape(prefix + ': ' + it['title'])}", f"URL:{it['url']}",
                  f"DESCRIPTION:{_ics_escape(chr(10).join(desc))}", "TRANSP:TRANSPARENT"]
        for trigger in ("-P7D", "-P1D"):
            lines += ["BEGIN:VALARM", "ACTION:DISPLAY", f"TRIGGER:{trigger}", f"DESCRIPTION:{_ics_escape(prefix + ': ' + it['title'])}", "END:VALARM"]
        lines.append("END:VEVENT")
    lines.append("END:VCALENDAR")
    return "\r\n".join(_ics_fold(l) for l in lines) + "\r\n"


def write_calendars(items: list[dict[str, Any]], cfg: dict[str, Any], now: datetime) -> None:
    today = now.date()
    dated = sorted((i for i in items if i.get("deadline") and date.fromisoformat(i["deadline"]) >= today),
                   key=lambda i: i["deadline"])
    base = cfg["site"].get("base_url") or ""
    title = cfg["site"].get("title", "Opportunity Radar")
    (ROOT / "docs" / "calendar.ics").write_text(
        build_ics([i for i in dated if i["tier"] in ("high", "top")], f"{title}: high-value deadlines", now, base), encoding="utf-8")
    (ROOT / "docs" / "calendar-all.ics").write_text(build_ics(dated, f"{title}: all deadlines", now, base), encoding="utf-8")


def write_feed(items: list[dict[str, Any]], cfg: dict[str, Any], now: datetime) -> None:
    base = (cfg["site"].get("base_url") or "").rstrip("/")
    no_feed = {k for k, v in cfg.get("sources", {}).items() if v.get("in_feed") is False}
    picks = [i for i in items if i["tier"] in ("top", "high") and i["source"] not in no_feed]
    picks.sort(key=lambda i: i.get("first_seen", ""), reverse=True)
    entries = []
    for i in picks[:60]:
        when = datetime.fromisoformat(i.get("first_seen", now.isoformat())[:19]).replace(tzinfo=timezone.utc)
        bits = [i["type"], f"score {i['score']}"]
        if i.get("deadline"):
            bits.append(f"deadline {i['deadline']}")
        if i.get("funding"):
            bits.append(i["funding"].replace("_", " "))
        desc = " · ".join(bits) + (f" — {i['summary']}" if i.get("summary") else "")
        entries.append(
            "<item>"
            f"<title>{escape(i['title'])}</title>"
            f"<link>{escape(i['url'])}</link>"
            f"<guid isPermaLink=\"false\">{i['id']}</guid>"
            f"<pubDate>{format_datetime(when)}</pubDate>"
            f"<category>{escape(i['type'])}</category>"
            f"<description>{escape(desc)}</description>"
            "</item>"
        )
    xml = ('<?xml version="1.0" encoding="UTF-8"?>\n<rss version="2.0"><channel>'
           f"<title>{escape(cfg['site']['title'])} — high-value picks</title>"
           f"<link>{escape(base or 'https://github.com')}</link>"
           f"<description>{escape(cfg['site']['tagline'])}</description>"
           f"<lastBuildDate>{format_datetime(now)}</lastBuildDate>"
           + "".join(entries) + "</channel></rss>\n")
    FEED_FILE.write_text(xml, encoding="utf-8")


def apply_quick_limits(cfg: dict[str, Any]) -> None:
    """Hourly quick check: read only each site's newest listings."""
    q = cfg.get("schedule", {}).get("quick_check", {})
    src = cfg["sources"]
    for key in ("opportunitiesforyouth", "opportunityportal", "scholarshipscorner"):
        if key in src:
            src[key]["pages"] = min(src[key].get("pages", 3), q.get("wordpress_pages", 1))
    if "scholarshipsads" in src:
        src["scholarshipsads"]["pages"] = min(src["scholarshipsads"].get("pages", 6), q.get("scholarshipsads_pages", 2))
    if "scholarshipsads" in src:
        src["scholarshipsads"]["details"] = q.get("scholarshipsads_details", 0)
    if "daad" in src:
        src["daad"]["details"] = q.get("daad_details", 0)
        src["daad"]["pages"] = min(src["daad"].get("pages", 6), 2)
    if "for9a" in src and src["for9a"].get("paths"):
        src["for9a"]["paths"] = src["for9a"]["paths"][: q.get("for9a_paths", 3)]


_VOLATILE = {"generated_at", "last_seen", "last_ok", "status", "scan"}


def fingerprint(payload: dict[str, Any]) -> str:
    """Hash of the listings, ignoring timestamps that change on every run."""
    def strip(x: Any) -> Any:
        if isinstance(x, dict):
            return {k: strip(v) for k, v in sorted(x.items()) if k not in _VOLATILE}
        if isinstance(x, list):
            return [strip(v) for v in x]
        return x
    core = {"items": strip(payload.get("items", [])), "site": payload.get("site"), "thresholds": payload.get("thresholds")}
    return hashlib.sha1(json.dumps(core, sort_keys=True, ensure_ascii=False).encode()).hexdigest()


def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser(description="Update Opportunity Radar data")
    ap.add_argument("--only", help="comma-separated source keys to run")
    ap.add_argument("--raw", help="classify raw items from a JSON file instead of scraping")
    ap.add_argument("--today", help="override today's date (YYYY-MM-DD), for testing")
    ap.add_argument("--mode", choices=["auto", "quick", "full"], default="full",
                    help="quick = newest listings only; full = deep scan; auto = full once a day, quick otherwise")
    ap.add_argument("-v", "--verbose", action="store_true")
    args = ap.parse_args(argv)
    logging.basicConfig(level=logging.DEBUG if args.verbose else logging.INFO, format="%(message)s")

    cfg = load_config()
    if os.environ.get("RADAR_BASE_URL") and not cfg["site"].get("base_url"):
        cfg["site"]["base_url"] = os.environ["RADAR_BASE_URL"]
    now = datetime.now(timezone.utc).replace(microsecond=0)
    today = date.fromisoformat(args.today) if args.today else now.date()
    run_stamp = now.isoformat()
    clf = Classifier(cfg, today=today)
    previous = load_previous()

    mode = args.mode
    if mode == "auto":
        full_hour = cfg.get("schedule", {}).get("full_scan_hour_utc", 4)
        mode = "full" if now.hour == full_hour or not previous.get("items") else "quick"
    if mode == "quick":
        apply_quick_limits(cfg)
    log.info("Mode: %s scan", mode)

    raw_items: list[dict[str, Any]] = []
    status: dict[str, Any] = {}
    if args.raw:
        raw_items = json.loads(Path(args.raw).read_text(encoding="utf-8"))
        for key in {r["source"] for r in raw_items}:
            status[key] = {"ok": True, "count": sum(1 for r in raw_items if r["source"] == key), "error": None}
    else:
        sources = build_sources(cfg)
        if args.only:
            wanted = set(args.only.split(","))
            sources = {k: v for k, v in sources.items() if k in wanted}
        for key, src in sources.items():
            t0 = time.time()
            try:
                got = src.fetch()
                raw_items.extend(got)
                status[key] = {"ok": True, "count": len(got), "error": None}
                log.info("✓ %-22s %4d items  (%.1fs)", key, len(got), time.time() - t0)
            except Exception as e:  # one broken site never stops the run
                status[key] = {"ok": False, "count": 0, "error": str(e)[:300]}
                log.warning("✗ %-22s failed: %s", key, e)

    classified = [c for c in (clf.classify(r) for r in raw_items) if c]
    src_cfg = cfg.get("sources", {})
    classified = [c for c in classified if c["type"] != "Guide"
                  and c["score"] >= src_cfg.get(c["source"], {}).get("min_score", cfg["min_score"])]
    fresh = dedupe(classified)

    failed = {k for k, s in status.items() if not s["ok"]}
    if not fresh and previous["items"]:
        log.error("No items scraped from any source; keeping previous data untouched.")
        return 1

    prev_archive = load_archive()
    items, archive = merge_history(fresh, previous.get("items", []), cfg, today, run_stamp, failed, prev_archive)

    # Carry forward last-good info for sources that failed this time.
    prev_sources = previous.get("sources", {})
    sources_out = {}
    for key, meta in SOURCE_META.items():
        if not src_cfg.get(key, {}).get("enabled"):
            continue
        st = status.get(key) or prev_sources.get(key, {}).get("status") or {"ok": None, "count": 0, "error": "not run"}
        last_ok = run_stamp if st.get("ok") else prev_sources.get(key, {}).get("last_ok")
        sources_out[key] = {**meta, "status": st, "last_ok": last_ok,
                            "items": sum(1 for i in items if i["source"] == key or any(a["source"] == key for a in i.get("also_on", [])))}

    payload = {
        "generated_at": run_stamp,
        "site": cfg["site"],
        "thresholds": {"high_value": cfg["high_value"], "top_pick": cfg["top_pick"], "shelf": cfg.get("runway_shelf_min", 80)},
        "field_labels": {k: v["label"] for k, v in cfg["fields"].items()},
        "regions": list(REGIONS.keys()),
        "profile": {k: cfg.get("profile", {}).get(k) for k in ("nationality", "gender", "english_score")},
        "sources": sources_out,
        "count": len(items),
        "items": items,
    }
    payload["scan"] = mode
    changed = fingerprint(payload) != fingerprint(previous) or fingerprint({"items": archive}) != fingerprint({"items": prev_archive})
    new_ids = {i["id"] for i in items} - {i["id"] for i in previous.get("items", [])}

    DATA_FILE.parent.mkdir(parents=True, exist_ok=True)
    payload["archive_count"] = len(archive)
    DATA_FILE.write_text(json.dumps(payload, ensure_ascii=False, indent=1), encoding="utf-8")
    ARCHIVE_FILE.write_text(json.dumps({"generated_at": run_stamp, "count": len(archive), "items": archive},
                                       ensure_ascii=False, indent=1), encoding="utf-8")
    write_feed(items, cfg, now)
    write_calendars(items, cfg, now)

    hv = sum(1 for i in items if i["tier"] != "standard")
    log.info("Wrote %d opportunities (%d high value, %d new) → %s; listings %s",
             len(items), hv, len(new_ids), DATA_FILE.relative_to(ROOT), "changed" if changed else "unchanged")
    # Tell the GitHub workflow whether there's anything worth committing.
    if os.environ.get("GITHUB_OUTPUT"):
        with open(os.environ["GITHUB_OUTPUT"], "a", encoding="utf-8") as f:
            f.write(f"changed={'true' if changed else 'false'}\nnew_count={len(new_ids)}\n")
    return 0


if __name__ == "__main__":
    sys.exit(main())
