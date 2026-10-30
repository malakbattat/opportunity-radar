"""Adapters for curated opportunity lists kept as Markdown tables on GitHub."""
from __future__ import annotations

import re
from datetime import datetime, timedelta, timezone
from typing import Any
from urllib.parse import urlparse

from .sources import http_get

RAW = "https://raw.githubusercontent.com/{repo}/HEAD/README.md"

_LINK_RE = re.compile(r"\[([^\]]*)\]\((https?://[^)\s]+)\)")
_IMG_RE = re.compile(r"<img[^>]*>|!\[[^\]]*\]\([^)]*\)")
_TAG_RE = re.compile(r"<[^>]+>")
_HEADING_RE = re.compile(r"^(#{2,4})\s+(.*)$|<summary>.*?<h\d>(.*?)</h\d>", re.I)


def _plain(cell: str) -> str:
    cell = _IMG_RE.sub(" ", cell)
    cell = _LINK_RE.sub(lambda m: m.group(1), cell)
    cell = _TAG_RE.sub(" ", cell)
    cell = cell.replace("**", "").replace("__", "").replace("✨", "")
    cell = re.sub(r"[\U0001F300-\U0001FAFF☀-➿️]", "", cell)
    return re.sub(r"\s+", " ", cell).strip()


def _links(cell: str) -> list[tuple[str, str]]:
    return [(m.group(1), m.group(2)) for m in _LINK_RE.finditer(cell)]


def parse_markdown_tables(md: str) -> list[dict[str, Any]]:
    """Every table row as {section, headers, cells (raw), plain}."""
    rows: list[dict[str, Any]] = []
    section = ""
    headers: list[str] | None = None
    for line in md.splitlines():
        h = _HEADING_RE.search(line)
        if h:
            section = _plain(h.group(2) or h.group(3) or "")
            headers = None
            continue
        if not line.lstrip().startswith("|"):
            headers = None if line.strip() else headers
            continue
        cells = [c.strip() for c in line.strip().strip("|").split("|")]
        if headers is None:
            headers = [_plain(c).lower() for c in cells]
            continue
        if all(re.fullmatch(r":?-{2,}:?", c.replace(" ", "")) or not c for c in cells):
            continue
        rows.append({"section": section, "headers": headers, "cells": cells, "plain": [_plain(c) for c in cells]})
    return rows


def _col(row: dict[str, Any], *names: str) -> int | None:
    for i, h in enumerate(row["headers"]):
        if any(n in h for n in names):
            return i
    return None


def _get(row: dict[str, Any], idx: int | None, plain: bool = True) -> str:
    if idx is None or idx >= len(row["cells"]):
        return ""
    return row["plain"][idx] if plain else row["cells"][idx]


# ── smsnobin77/Academic-research-opportunities-for-international-students ──

def parse_research_list(md: str) -> list[dict[str, Any]]:
    out = []
    for row in parse_markdown_tables(md):
        name_i, dl_i, note_i = _col(row, "program", "name"), _col(row, "deadline"), _col(row, "comment", "note")
        if name_i is None:
            continue
        raw_name = _get(row, name_i, plain=False)
        links = _links(raw_name)
        if not links:
            continue
        title = _plain(re.sub(r"\[Link\]\([^)]*\)", "", raw_name, flags=re.I)) or links[0][0]
        note = _get(row, note_i)
        region = row["section"]
        out.append({
            "source": "researchlist",
            "title": title,
            "url": links[0][1],
            "summary": note,
            "body": note,
            "categories": ["Research", region],
            "meta_text": region if region in ("Europe", "Asia", "North America") else "",
            "deadline_text": _get(row, dl_i),
            "annual": True,
            "type_default": "Research",
        })
    return out


# ── zapplyjobs/Internships-2027 ───────────────────────────────

_AGE_RE = re.compile(r"(\d+)\s*(m|min|h|d|w|mo)\b", re.I)
_US_STATE = re.compile(r",\s*(A[LKZR]|C[AOT]|D[EC]|FL|GA|HI|I[DLNA]|K[SY]|LA|M[EDAINSOT]|N[EVHJMYCD]|O[HKR]|PA|RI|S[CD]|T[NX]|UT|V[TA]|W[AVIY])\b")


def _age_to_date(age: str, now: datetime) -> str | None:
    m = _AGE_RE.search(age or "")
    if not m:
        return None
    n, unit = int(m.group(1)), m.group(2).lower()
    delta = {"m": timedelta(minutes=n), "min": timedelta(minutes=n), "h": timedelta(hours=n), "d": timedelta(days=n),
             "w": timedelta(weeks=n), "mo": timedelta(days=30 * n)}[unit]
    return (now - delta).date().isoformat()


_RESEARCH_ROLE = re.compile(r"\bresearch (intern|scientist|engineer|assistant|associate|co-?op|fellow)|"
                            r"\b(ai|ml|machine learning|applied) research\b", re.I)


def parse_internship_list(md: str, sections: list[str] | None = None, now: datetime | None = None,
                          sponsor_only: bool = False) -> list[dict[str, Any]]:
    now = now or datetime.now(timezone.utc)
    wanted = [s.lower() for s in sections] if sections else None
    out = []
    for row in parse_markdown_tables(md):
        comp_i, role_i, loc_i = _col(row, "company"), _col(row, "role", "position"), _col(row, "location")
        if comp_i is None or role_i is None:
            continue
        sec = row["section"]
        if wanted and not any(w in sec.lower() for w in wanted):
            continue
        links = [u for _, u in _links(" ".join(row["cells"]))]
        if not links:
            continue
        company, role, loc = _get(row, comp_i), _get(row, role_i), _get(row, loc_i)
        if not company or not role:
            continue
        visa = _get(row, _col(row, "visa"))
        if sponsor_only and "sponsor" not in visa.lower():
            continue
        out.append({
            "source": "zapply",
            "title": f"{role} at {company}",
            "url": links[-1],
            "org": company,
            "summary": loc,
            "body": f"{role}. {sec}. {loc}.",
            "categories": [sec, "Internship"],
            "meta_text": sec,
            "countries": ["United States"],
            "published": _age_to_date(_get(row, _col(row, "posted", "age", "date")), now),
            "eligibility_text": "International applicants welcome with visa sponsorship" if "sponsor" in visa.lower() else "",
            "rolling": True,
            "type_hint": "Research" if _RESEARCH_ROLE.search(role) else "Internship",
            "_sponsor": "sponsor" in visa.lower(),
        })
    return out


# ── Julian048/CS-Everything-but-Internships ──────────────────

_JULIAN_TYPES = {
    "internship-matching fellowships": "Fellowship",
    "fellowships": "Fellowship",
    "externships": "Externship",
    "insight": "Externship",
    "mentorship": "Mentorship",
    "teaching": "Mentorship",
    "scholarships": "Scholarship",
}
_JULIAN_SKIP = ("special programs", "resources")


def parse_programs_list(md: str) -> list[dict[str, Any]]:
    out = []
    for row in parse_markdown_tables(md):
        sec = row["section"].lower()
        if any(s in sec for s in _JULIAN_SKIP):
            continue
        otype = next((t for k, t in _JULIAN_TYPES.items() if k in sec), None)
        if not otype:
            continue
        name_i, year_i, note_i = _col(row, "name"), _col(row, "year"), _col(row, "note")
        raw_name = _get(row, name_i, plain=False)
        links = _links(raw_name) or _links(_get(row, note_i, plain=False))
        if not links:
            continue
        title = _plain(raw_name)
        year = _get(row, year_i)
        note = _get(row, note_i)
        out.append({
            "source": "csprograms",
            "title": title,
            "url": links[0][1],
            "summary": note,
            "body": f"{note} Eligible: {year}.",
            "categories": [row["section"], otype],
            "meta_text": "",
            "type_hint": otype,
            "year_text": year,
            "diversity": "✨" in raw_name,
            "recurring": True,
            "eligibility_text": note,
        })
    return out


# ── zapplyjobs/Research-Internships-for-Undergraduates ───────

_BULLET_RE = re.compile(r"^\s*[*-]\s+(.*)$")
_H4_RE = re.compile(r"^####\s+(.*)$")
_SKIP_SECTIONS = ("for indian students",)


def parse_bullet_research_list(md: str) -> list[dict[str, Any]]:
    out = []
    country = ""
    skip = False
    for line in md.splitlines():
        h = _H4_RE.match(line) or re.match(r"^##\s+(.*)$", line)
        if h:
            country = _plain(h.group(1))
            skip = any(x in country.lower() for x in _SKIP_SECTIONS)
            continue
        m = _BULLET_RE.match(line)
        if not m or skip or not country:
            continue
        text = re.sub(r"\]\s+\(", "](", m.group(1))       # "[Name] (url)" typo in the list
        links = _links(text)
        if not links:
            continue
        name = links[0][0].strip()
        rest = _plain(_LINK_RE.sub(" ", text)).strip(" ,-–")
        before = _plain(text.split("[", 1)[0]).strip(" ,-–")
        title = f"{before} {name}".strip() if before and len(name) < 45 else name
        if rest and rest.lower() not in title.lower() and len(title) < 40 and len(rest) < 60 and not re.search(r"\b(only|for|application|aims)\b", rest, re.I):
            title = f"{title}, {rest}"
        host = urlparse(links[0][1]).netloc.lower().removeprefix("www.")
        out.append({
            "source": "ugresearch",
            "org": host,
            "title": title,
            "url": links[0][1],
            "summary": rest,
            "body": rest,
            "categories": ["Research", country],
            "meta_text": "Undergraduate research",
            "countries": [country] if country not in ("Multiple Countries", "Worldwide") else [],
            "type_default": "Research",
            "eligibility_text": rest,
            "recurring": True,
        })
    return out


class GitHubListSource:
    def __init__(self, key: str, repo: str, parser, **kwargs: Any):
        self.key, self.repo, self.parser, self.kwargs = key, repo, parser, kwargs

    def fetch(self) -> list[dict[str, Any]]:
        r = http_get(RAW.format(repo=self.repo), accept="text/plain")
        if r.status_code != 200:
            raise RuntimeError(f"HTTP {r.status_code} for {self.repo}")
        return self.parser(r.text, **self.kwargs)
