"""DAAD scholarship database, filtered to one country of origin (Palestinian Territories by default).

The database's option codes aren't documented, so each run reads the search form, picks the
options whose labels match the configured country and status, and queries with those values.
If the server returns no result links (JavaScript-only page), the page is rendered in a browser."""
from __future__ import annotations

import logging
import re
from typing import Any
from urllib.parse import parse_qs, urlencode, urljoin, urlparse

from bs4 import BeautifulSoup

from .sources import http_get, polite_pause, render_with_browser

log = logging.getLogger("radar")

BASE = "https://www2.daad.de/deutschland/stipendium/datenbank/en/21148-scholarship-database/"
_DETAIL_RE = re.compile(r"[?&]detail=(\d+)")


def find_option(html: str, label_pattern: str) -> tuple[str, str] | None:
    """(select name, option value) for the first <option> whose text matches label_pattern."""
    soup = BeautifulSoup(html, "lxml")
    rx = re.compile(label_pattern, re.I)
    for sel in soup.find_all("select"):
        name = sel.get("name") or sel.get("id")
        if not name:
            continue
        for opt in sel.find_all("option"):
            if rx.search(opt.get_text(" ", strip=True)) and opt.get("value") not in (None, ""):
                return name, opt["value"]
    return None


def parse_results(html: str) -> list[dict[str, Any]]:
    soup = BeautifulSoup(html, "lxml")
    out, seen = [], set()
    for a in soup.find_all("a", href=True):
        m = _DETAIL_RE.search(a["href"])
        if not m or m.group(1) in seen:
            continue
        title = a.get_text(" ", strip=True)
        card = a
        for _ in range(5):
            if card.parent is None or len(card.parent.find_all("a", href=_DETAIL_RE)) > 2:
                break
            card = card.parent
        if len(title) < 8:
            h = card.find(["h2", "h3", "h4", "h5"])
            title = h.get_text(" ", strip=True) if h else title
        if len(title) < 8:
            continue
        seen.add(m.group(1))
        text = card.get_text(" ", strip=True)
        out.append({
            "source": "daad",
            "title": title,
            "url": urljoin(BASE, f"?detail={m.group(1)}"),
            "summary": text.replace(title, "", 1)[:400],
            "body": text,
            "deadline_text": text,
            "_detail": m.group(1),
        })
    return out


_SECTION_WORDS = ("Application deadline", "Who can apply", "What can be funded", "Duration of the funding",
                  "Value", "Language skills", "Selection criteria", "Application requirements", "Objective")


def parse_detail(html: str) -> dict[str, Any]:
    soup = BeautifulSoup(html, "lxml")
    main = soup.find("main") or soup.body or soup
    for t in main.find_all(["script", "style", "nav", "footer", "form"]):
        t.decompose()
    text = re.sub(r"\s+", " ", main.get_text(" ", strip=True))
    h1 = soup.find("h1")
    sections: dict[str, str] = {}
    for word in _SECTION_WORDS:
        m = re.search(rf"{re.escape(word)}\??\s*(.{{0,600}}?)(?=\s(?:{'|'.join(map(re.escape, _SECTION_WORDS))})\b|$)", text)
        if m:
            sections[word] = m.group(1).strip()
    summary = sections.get("Objective") or sections.get("Who can apply") or text[:300]
    return {
        "title": h1.get_text(" ", strip=True) if h1 else None,
        "summary": summary[:400],
        "body": text[:8000],
        "deadline_text": "Deadline: " + sections["Application deadline"] if "Application deadline" in sections else None,
        "eligibility_text": sections.get("Who can apply", ""),
        "rolling": bool(re.search(r"depending on|varies|on request|any time", sections.get("Application deadline", ""), re.I)),
    }


class DAADSource:
    def __init__(self, origin_text: str = "Palestin", status_text: str = r"^\s*Graduates?\b", max_pages: int = 6, max_details: int = 80):
        self.origin_text, self.status_text = origin_text, status_text
        self.max_pages, self.max_details = max_pages, max_details

    def _search_url(self, params: dict[str, str], page: int) -> str:
        q = {"status": "", "origin": "", "subjectGrps": "", "intention": "", "daad": "", "q": "", "target": "", "back": "1"}
        q.update(params)
        q["page"] = str(page)
        return BASE + "?" + urlencode(q)

    def fetch(self) -> list[dict[str, Any]]:
        r = http_get(BASE)
        if r.status_code != 200:
            raise RuntimeError(f"HTTP {r.status_code}")
        form_html = r.text
        if "<select" not in form_html:
            rendered = render_with_browser([BASE], wait_ms=3000)
            form_html = rendered[0][1] if rendered else form_html
        params: dict[str, str] = {}
        for pattern, fallback in ((self.origin_text, "origin"), (self.status_text, "status")):
            found = find_option(form_html, pattern)
            if found:
                params[found[0]] = found[1]
            else:
                log.warning("[daad] no form option matching %r; searching without %s", pattern, fallback)
        items: list[dict[str, Any]] = []
        for page in range(1, self.max_pages + 1):
            url = self._search_url(params, page)
            r = http_get(url)
            batch = parse_results(r.text) if r.status_code == 200 else []
            if not batch and page == 1:
                rendered = render_with_browser([url], wait_ms=3500)
                batch = parse_results(rendered[0][1]) if rendered else []
            new = [b for b in batch if b["url"] not in {i["url"] for i in items}]
            if not new:
                break
            items.extend(new)
            polite_pause()
        for it in items[: self.max_details]:
            try:
                r = http_get(it["url"])
                if r.status_code == 200:
                    d = parse_detail(r.text)
                    for k, v in d.items():
                        if v:
                            it[k] = v
            except Exception as e:
                log.info("[daad] detail %s: %s", it["url"], e)
            polite_pause()
        for it in items:
            it.pop("_detail", None)
            it["meta_text"] = (it.get("meta_text") or "") + " Germany DAAD"
            it["countries"] = ["Germany"]
            it["open_to_origin"] = True
        return items
