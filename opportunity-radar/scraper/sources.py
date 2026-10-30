"""Source adapters. Each returns a list of *raw* dicts:

    {source, title, url, body?, summary?, categories?, subjects?, meta_text?,
     deadline_text?, deadline?, rolling?, published?, org?, country?, type_hint?}

Adapters never raise for a single bad item; a whole-source failure raises and is
caught (and reported) by the runner so one broken site never stops the others.
"""
from __future__ import annotations

import json
import logging
import re
import time
from typing import Any, Callable, Iterable
from urllib.parse import urljoin, urlparse

import feedparser
import requests
from bs4 import BeautifulSoup

log = logging.getLogger("radar")

UA = ("Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) "
      "Chrome/126.0 Safari/537.36 OpportunityRadar/1.0 (+personal aggregator)")

_session = requests.Session()
_session.headers.update({"User-Agent": UA, "Accept-Language": "en;q=0.9,ar;q=0.6"})


def http_get(url: str, *, timeout: int = 25, tries: int = 3, accept: str | None = None) -> requests.Response:
    last: Exception | None = None
    for attempt in range(tries):
        try:
            headers = {"Accept": accept} if accept else None
            r = _session.get(url, timeout=timeout, headers=headers)
            if r.status_code in (429, 500, 502, 503, 504):
                raise requests.HTTPError(f"{r.status_code} for {url}")
            return r
        except (requests.RequestException,) as e:  # network hiccup → back off and retry
            last = e
            time.sleep(1.5 * (attempt + 1))
    raise RuntimeError(f"GET failed after {tries} tries: {url}: {last}")


def polite_pause() -> None:
    time.sleep(0.8)


# ── WordPress (REST API, falling back to RSS) ─────────────────

class WordPressSource:
    """opportunitiesforyouth.org, opportunityportal.info, scholarshipscorner.website"""

    def __init__(self, key: str, base: str, pages: int = 3):
        self.key, self.base, self.pages = key, base.rstrip("/"), pages

    def fetch(self) -> list[dict[str, Any]]:
        try:
            items = self._via_api()
            if items:
                return items
            log.info("[%s] REST API returned nothing, trying RSS", self.key)
        except Exception as e:  # API disabled / blocked → RSS
            log.info("[%s] REST API unavailable (%s), trying RSS", self.key, e)
        return self._via_rss()

    def _categories(self) -> dict[int, str]:
        out: dict[int, str] = {}
        for page in (1, 2):
            r = http_get(f"{self.base}/wp-json/wp/v2/categories?per_page=100&page={page}&_fields=id,name")
            if r.status_code != 200:
                break
            data = r.json()
            if not isinstance(data, list) or not data:
                break
            out.update({c["id"]: c["name"] for c in data if "id" in c})
            if len(data) < 100:
                break
        return out

    def _via_api(self) -> list[dict[str, Any]]:
        cats = {}
        try:
            cats = self._categories()
        except Exception:
            pass
        items: list[dict[str, Any]] = []
        for page in range(1, self.pages + 1):
            url = (f"{self.base}/wp-json/wp/v2/posts?per_page=50&page={page}"
                   "&_fields=id,date,link,title,excerpt,content,categories")
            r = http_get(url, accept="application/json")
            if r.status_code == 400 and page > 1:  # past the last page
                break
            if r.status_code != 200 or "json" not in r.headers.get("content-type", ""):
                raise RuntimeError(f"HTTP {r.status_code}")
            posts = r.json()
            if not isinstance(posts, list):
                raise RuntimeError("unexpected payload")
            for p in posts:
                items.append(parse_wp_post(self.key, p, cats))
            if len(posts) < 50:
                break
            polite_pause()
        return items

    def _via_rss(self) -> list[dict[str, Any]]:
        items: list[dict[str, Any]] = []
        for page in range(1, self.pages + 1):
            url = f"{self.base}/feed/" + (f"?paged={page}" if page > 1 else "")
            r = http_get(url, accept="application/rss+xml, application/xml")
            if r.status_code != 200:
                if page == 1:
                    raise RuntimeError(f"RSS HTTP {r.status_code}")
                break
            batch = parse_rss(self.key, r.content)
            if not batch:
                break
            items.extend(batch)
            polite_pause()
        return items


def parse_wp_post(source: str, p: dict[str, Any], cats: dict[int, str]) -> dict[str, Any]:
    return {
        "source": source,
        "title": (p.get("title") or {}).get("rendered", ""),
        "url": p.get("link", ""),
        "summary": (p.get("excerpt") or {}).get("rendered", ""),
        "body": (p.get("content") or {}).get("rendered", ""),
        "categories": [cats.get(c, "") for c in p.get("categories", [])],
        "published": (p.get("date") or "")[:10] or None,
    }


def parse_rss(source: str, content: bytes) -> list[dict[str, Any]]:
    feed = feedparser.parse(content)
    out = []
    for e in feed.entries:
        body = ""
        if e.get("content"):
            body = " ".join(c.get("value", "") for c in e.content)
        published = None
        if e.get("published_parsed"):
            published = time.strftime("%Y-%m-%d", e.published_parsed)
        out.append({
            "source": source,
            "title": e.get("title", ""),
            "url": e.get("link", ""),
            "summary": e.get("summary", ""),
            "body": body or e.get("summary", ""),
            "categories": [t.get("term", "") for t in e.get("tags", [])],
            "published": published,
        })
    return out


# ── ScholarshipsAds (server-rendered listing pages) ───────────

_SA_FUNDING = re.compile(r"fully funded|partial funding|full tuition", re.I)
_SA_DEGREE = re.compile(r"\b(masters|phd|bachelor|undergraduate|post doctorate|fellowship|short training|non-degree)\b", re.I)


def extract_article_text(html_text: str, limit: int = 9000) -> str:
    """Main article text of a detail page: the block with the most paragraph text,
    so sidebars listing other scholarships don't leak into requirement detection."""
    soup = BeautifulSoup(html_text, "lxml")
    for t in soup.find_all(["script", "style", "nav", "header", "footer", "aside", "form"]):
        t.decompose()
    best, best_len = None, 0
    for node in soup.find_all(["article", "main", "section", "div"]):
        ps = node.find_all(["p", "li"], recursive=True)
        n = sum(len(p.get_text(" ", strip=True)) for p in ps)
        # prefer the innermost block that still holds most of the text
        if n > best_len * 1.15 or (best is not None and n >= best_len * 0.9 and node in best.descendants):
            best, best_len = node, n
    node = best or soup.body or soup
    text = " ".join(p.get_text(" ", strip=True) for p in node.find_all(["h2", "h3", "p", "li"]))
    return re.sub(r"\s+", " ", text)[:limit]


class ScholarshipsAdsSource:
    BASE = "https://www.scholarshipsads.com"

    def __init__(self, pages: int = 6, details: int = 40):
        self.pages = pages
        self.details = details

    def _add_details(self, items: list[dict[str, Any]]) -> None:
        for it in items[: self.details]:
            try:
                r = http_get(it["url"])
                if r.status_code == 200:
                    it["body"] = f"{it.get('body', '')} {extract_article_text(r.text)}"
            except Exception as e:
                log.info("[scholarshipsads] detail %s: %s", it["url"], e)
            polite_pause()

    def fetch(self) -> list[dict[str, Any]]:
        items: list[dict[str, Any]] = []
        for listing in ("/latest-scholarships", "/internships"):
            for page in range(1, self.pages + 1 if listing == "/latest-scholarships" else 3):
                url = f"{self.BASE}{listing}" + (f"?page={page}" if page > 1 else "")
                r = http_get(url)
                if r.status_code != 200:
                    log.info("[scholarshipsads] %s → HTTP %s", url, r.status_code)
                    break
                batch = parse_scholarshipsads(r.text, self.BASE, internship=listing == "/internships")
                if not batch:
                    break
                items.extend(batch)
                polite_pause()
        self._add_details(items)
        return items


def parse_scholarshipsads(html_text: str, base: str, internship: bool = False) -> list[dict[str, Any]]:
    soup = BeautifulSoup(html_text, "lxml")
    out, seen = [], set()
    for h in soup.find_all(["h3", "h2"]):
        a = h.find("a", href=True)
        if not a:
            continue
        href = urljoin(base, a["href"])
        path = urlparse(href).path
        if urlparse(href).netloc.replace("www.", "") != "scholarshipsads.com" or path.startswith(("/blog", "/category", "/categories")):
            continue
        if href in seen:
            continue
        # Walk up to the card: the nearest ancestor that also holds a "Read More" link.
        card = h
        for _ in range(6):
            if card.parent is None:
                break
            card = card.parent
            if card.find("a", string=re.compile(r"read more", re.I)):
                break
        if len(card.find_all(["h3", "h2"])) > 2:  # walked too far (a whole list)
            card = h.parent
        seen.add(href)
        lis = [li.get_text(" ", strip=True) for li in card.find_all("li")]
        text = card.get_text(" ", strip=True)
        funding = next((t for t in lis if _SA_FUNDING.search(t)), "")
        degree = next((t for t in lis if _SA_DEGREE.search(t) and len(t) < 80), "")
        deadline_li = next((t for t in lis if t.lower().startswith("deadline")), "")
        # Subjects: the long comma-separated item.
        subjects_li = max((t for t in lis if t.count(",") >= 1 and t not in (degree, funding)), key=len, default="")
        subjects = [s.strip() for s in re.sub(r"\[\+\d+ More\]|\+\d+ More", ",", subjects_li).split(",") if s.strip()]
        if not subjects_li and any(t.lower() == "all subjects" for t in lis):
            subjects = ["All Subjects"]
        p = card.find("p")
        summary = p.get_text(" ", strip=True) if p else ""
        non_deadline = [t for t in lis if not t.lower().startswith("deadline")]
        country = non_deadline[-1] if non_deadline else None
        who = non_deadline[-2] if len(non_deadline) >= 2 else ""
        out.append({
            "source": "scholarshipsads",
            "title": a.get_text(" ", strip=True),
            "url": href,
            "summary": summary,
            "body": text,
            "subjects": subjects,
            "meta_text": " ".join([funding, degree] + ([deadline_li] if deadline_li else [])),
            "deadline_text": deadline_li or text,
            "rolling": bool(re.search(r"no single deadline|different for each|not one universal|depending on|\bopen\b$", text, re.I)) and not deadline_li,
            "countries": [c.strip() for c in (country or "").split(",") if c.strip()][:10],
            "eligibility_text": who if re.search(r"countr|nationalit|international|citizen|students|national", who, re.I) else "",
            "type_hint": "Internship" if internship else None,
        })
    return out


# ── Generic helpers for JavaScript-heavy sites ────────────────

_TITLE_KEYS = ("title_en", "title", "name_en", "name", "headline")
_URL_KEYS = ("url", "link", "permalink", "apply_url", "share_url", "web_url")
_SLUG_KEYS = ("slug", "seo_slug", "url_slug")
_DEADLINE_KEYS = ("deadline", "deadline_date", "application_deadline", "end_date", "closing_date", "close_date",
                  "expiry_date", "expire_date", "expires_at", "end_at", "last_date", "due_date")
_DESC_KEYS = ("summary", "short_description", "excerpt", "description_en", "description", "body", "content", "details")
_CAT_KEYS = ("type", "category", "category_name", "opportunity_type", "type_name", "categories", "tags", "field", "fields")
_ORG_KEYS = ("organization", "organisation", "org", "provider", "company", "institution", "publisher", "university")


def _first(d: dict, keys: Iterable[str]) -> Any:
    for k in keys:
        if k in d and d[k] not in (None, "", [], {}):
            return d[k]
    return None


def _as_text(v: Any) -> str:
    if v is None:
        return ""
    if isinstance(v, str):
        return v
    if isinstance(v, dict):
        return str(_first(v, ("name_en", "name", "title_en", "title", "label", "value")) or "")
    if isinstance(v, list):
        return ", ".join(_as_text(x) for x in v)
    return str(v)


def walk_json_for_opportunities(data: Any, make_url: Callable[[dict], str | None]) -> list[dict[str, Any]]:
    """Find opportunity-like objects anywhere inside a JSON payload."""
    found: list[dict[str, Any]] = []

    def visit(node: Any, depth: int = 0) -> None:
        if depth > 12:
            return
        if isinstance(node, dict):
            title = _first(node, _TITLE_KEYS)
            has_id = any(k in node for k in ("id", "_id", "uuid") + _SLUG_KEYS)
            signals = sum(1 for k in _DEADLINE_KEYS + _DESC_KEYS + _CAT_KEYS + _ORG_KEYS if k in node)
            if isinstance(title, str) and 8 <= len(title) <= 220 and has_id and signals >= 1:
                url = _first(node, _URL_KEYS)
                url = url if isinstance(url, str) and url.startswith("http") else make_url(node)
                if url:
                    found.append({
                        "title": title,
                        "url": url,
                        "summary": _as_text(_first(node, _DESC_KEYS))[:2000],
                        "body": _as_text(_first(node, ("description_en", "description", "body", "content", "details")))[:8000],
                        "categories": [_as_text(_first(node, _CAT_KEYS))],
                        "deadline": _as_text(_first(node, _DEADLINE_KEYS)) or None,
                        "org": _as_text(_first(node, _ORG_KEYS)) or None,
                    })
            for v in node.values():
                visit(v, depth + 1)
        elif isinstance(node, list):
            for v in node:
                visit(v, depth + 1)

    visit(data)
    return found


def parse_anchor_cards(html_text: str, base: str, pattern: re.Pattern, source: str) -> list[dict[str, Any]]:
    """Fallback: read opportunity links (and nearby text) from rendered HTML."""
    soup = BeautifulSoup(html_text, "lxml")
    out, seen = [], set()
    for a in soup.find_all("a", href=True):
        href = urljoin(base, a["href"]).split("#")[0]
        if not pattern.search(urlparse(href).path) or href in seen:
            continue
        heading = a.find(["h2", "h3", "h4", "h5"])
        title = (heading or a).get_text(" ", strip=True)
        card = a
        for _ in range(4):
            parent = card.parent
            if parent is None or len(parent.get_text(" ", strip=True)) > 600:
                break
            # Stop before the card swallows a neighbouring opportunity.
            other = {urljoin(base, x["href"]).split("#")[0] for x in parent.find_all("a", href=True)
                     if pattern.search(urlparse(urljoin(base, x["href"])).path)}
            if len(other - {href}) > 0:
                break
            card = parent
        card_text = card.get_text(" ", strip=True)
        if len(title) < 12 or title.lower() in ("apply now", "read more", "details"):
            # Title may live in a sibling heading of the card.
            h = card.find(["h2", "h3", "h4", "h5"])
            title = h.get_text(" ", strip=True) if h else ""
        if len(title) < 12:
            continue
        seen.add(href)
        out.append({
            "source": source,
            "title": title,
            "url": href,
            "summary": card_text.replace(title, "", 1)[:400],
            "body": card_text,
            "deadline_text": card_text,
            "rolling": bool(re.search(r"always open", card_text, re.I)),
        })
    return out


def render_with_browser(urls: list[str], wait_ms: int = 4500) -> list[tuple[str, str, list[Any]]]:
    """Render pages with headless Chromium (Playwright). Returns (url, html, json_payloads).
    Returns [] if Playwright isn't installed, so the run still succeeds."""
    try:
        from playwright.sync_api import sync_playwright
    except ImportError:
        log.warning("Playwright not installed; skipping JavaScript-rendered pages")
        return []
    results = []
    with sync_playwright() as pw:
        browser = pw.chromium.launch()
        ctx = browser.new_context(user_agent=UA.replace(" OpportunityRadar/1.0 (+personal aggregator)", ""),
                                  locale="en-US", viewport={"width": 1366, "height": 900})
        for url in urls:
            payloads: list[Any] = []

            def on_response(resp, payloads=payloads):
                try:
                    if "json" in (resp.headers.get("content-type") or "") and resp.request.resource_type in ("xhr", "fetch"):
                        payloads.append(resp.json())
                except Exception:
                    pass

            page = ctx.new_page()
            page.on("response", on_response)
            try:
                page.goto(url, wait_until="domcontentloaded", timeout=45000)
                page.wait_for_timeout(wait_ms)
                for _ in range(3):  # trigger lazy-loaded lists
                    page.mouse.wheel(0, 4000)
                    page.wait_for_timeout(900)
                results.append((url, page.content(), payloads))
            except Exception as e:
                log.info("render failed for %s: %s", url, e)
            finally:
                page.close()
        browser.close()
    return results


# ── For9a ─────────────────────────────────────────────────────

_FOR9A_LINK = re.compile(r"^/(en/)?opportunity/(?!category\b)[^/]+", re.I)


class For9aSource:
    BASE = "https://www.for9a.com"

    def __init__(self, paths: list[str]):
        self.paths = paths

    def _make_url(self, node: dict) -> str | None:
        slug = _first(node, _SLUG_KEYS)
        if isinstance(slug, str) and slug:
            return f"{self.BASE}/en/opportunity/{slug.strip('/')}"
        return None

    def _parse(self, html_text: str, payloads: list[Any]) -> list[dict[str, Any]]:
        items = parse_anchor_cards(html_text, self.BASE, _FOR9A_LINK, "for9a")
        soup = BeautifulSoup(html_text, "lxml")
        for tag in soup.find_all("script", id=re.compile(r"__NEXT_DATA__|__NUXT_DATA__")) + soup.find_all("script", type="application/json"):
            try:
                payloads.append(json.loads(tag.string or ""))
            except Exception:
                pass
        for p in payloads:
            for it in walk_json_for_opportunities(p, self._make_url):
                it["source"] = "for9a"
                items.append(it)
        return items

    def fetch(self) -> list[dict[str, Any]]:
        items: list[dict[str, Any]] = []
        need_browser = []
        for path in self.paths:
            url = self.BASE + path
            try:
                r = http_get(url)
            except Exception as e:
                log.info("[for9a] %s: %s", url, e)
                need_browser.append(url)
                continue
            if r.status_code == 404:
                log.info("[for9a] %s → 404, skipped", url)
                continue
            batch = self._parse(r.text, []) if r.status_code == 200 else []
            if batch:
                items.extend(batch)
            else:
                need_browser.append(url)
            polite_pause()
        if need_browser:
            log.info("[for9a] rendering %d page(s) in a headless browser", len(need_browser))
            for url, html_text, payloads in render_with_browser(need_browser):
                items.extend(self._parse(html_text, payloads))
        return items


# ── Foras.ps (client-side app; needs a browser) ───────────────

_FORAS_LINK = re.compile(r"/(opportunit(y|ies)|opp|details?|post|job|scholarship|training)s?/[\w%-]+", re.I)


class ForasSource:
    BASE = "https://foras.ps"

    def __init__(self, paths: list[str]):
        self.paths = paths

    def _make_url(self, node: dict) -> str | None:
        slug = _first(node, _SLUG_KEYS)
        oid = node.get("id") or node.get("_id")
        if slug:
            return f"{self.BASE}/opportunity/{slug}"
        if oid:
            return f"{self.BASE}/opportunity/{oid}"
        return None

    def fetch(self) -> list[dict[str, Any]]:
        items: list[dict[str, Any]] = []
        rendered = render_with_browser([self.BASE + p for p in self.paths], wait_ms=6000)
        if not rendered:
            raise RuntimeError("needs Playwright (headless browser) – installed automatically in GitHub Actions")
        for _url, html_text, payloads in rendered:
            items.extend(parse_anchor_cards(html_text, self.BASE, _FORAS_LINK, "foras"))
            for p in payloads:
                for it in walk_json_for_opportunities(p, self._make_url):
                    it["source"] = "foras"
                    items.append(it)
        return items


# ── Registry ──────────────────────────────────────────────────

SOURCE_META = {
    "opportunitiesforyouth": {"name": "Opportunities for Youth", "home": "https://opportunitiesforyouth.org/"},
    "opportunityportal": {"name": "Opportunity Portal", "home": "https://opportunityportal.info/"},
    "scholarshipscorner": {"name": "Scholarships Corner", "home": "https://scholarshipscorner.website/"},
    "scholarshipsads": {"name": "ScholarshipsAds", "home": "https://www.scholarshipsads.com/"},
    "for9a": {"name": "For9a", "home": "https://www.for9a.com/en"},
    "foras": {"name": "Foras", "home": "https://foras.ps/home"},
    "researchlist": {"name": "Academic research opportunities (GitHub)",
                     "home": "https://github.com/smsnobin77/Academic-research-opportunities-for-international-students"},
    "zapply": {"name": "Zapply Internships 2027 (GitHub)", "home": "https://github.com/zapplyjobs/Internships-2027"},
    "csprograms": {"name": "CS Everything but Internships (GitHub)", "home": "https://github.com/Julian048/CS-Everything-but-Internships"},
    "ugresearch": {"name": "Research Internships for Undergraduates (GitHub)",
                   "home": "https://github.com/zapplyjobs/Research-Internships-for-Undergraduates"},
    "daad": {"name": "DAAD Scholarship Database", "home": "https://www2.daad.de/deutschland/stipendium/datenbank/en/21148-scholarship-database/"},
}


def build_sources(cfg: dict[str, Any]) -> dict[str, Any]:
    s = cfg["sources"]
    reg: dict[str, Any] = {}
    if s.get("opportunitiesforyouth", {}).get("enabled"):
        reg["opportunitiesforyouth"] = WordPressSource("opportunitiesforyouth", "https://opportunitiesforyouth.org", s["opportunitiesforyouth"].get("pages", 3))
    if s.get("opportunityportal", {}).get("enabled"):
        reg["opportunityportal"] = WordPressSource("opportunityportal", "https://opportunityportal.info", s["opportunityportal"].get("pages", 3))
    if s.get("scholarshipscorner", {}).get("enabled"):
        reg["scholarshipscorner"] = WordPressSource("scholarshipscorner", "https://scholarshipscorner.website", s["scholarshipscorner"].get("pages", 3))
    if s.get("scholarshipsads", {}).get("enabled"):
        reg["scholarshipsads"] = ScholarshipsAdsSource(s["scholarshipsads"].get("pages", 6), s["scholarshipsads"].get("details", 40))
    if s.get("for9a", {}).get("enabled"):
        reg["for9a"] = For9aSource(s["for9a"].get("paths", ["/en/opportunity"]))
    if s.get("foras", {}).get("enabled"):
        reg["foras"] = ForasSource(s["foras"].get("paths", ["/home"]))
    from .github_lists import (GitHubListSource, parse_bullet_research_list, parse_internship_list,
                               parse_programs_list, parse_research_list)
    if s.get("researchlist", {}).get("enabled"):
        reg["researchlist"] = GitHubListSource("researchlist", s["researchlist"]["repo"], parse_research_list)
    if s.get("zapply", {}).get("enabled"):
        reg["zapply"] = GitHubListSource("zapply", s["zapply"]["repo"], parse_internship_list,
                                         sections=s["zapply"].get("sections"),
                                         sponsor_only=s["zapply"].get("visa_sponsorship_only", False))
    if s.get("csprograms", {}).get("enabled"):
        reg["csprograms"] = GitHubListSource("csprograms", s["csprograms"]["repo"], parse_programs_list)
    if s.get("ugresearch", {}).get("enabled"):
        reg["ugresearch"] = GitHubListSource("ugresearch", s["ugresearch"]["repo"], parse_bullet_research_list)
    if s.get("daad", {}).get("enabled"):
        from .daad import DAADSource
        d = s["daad"]
        reg["daad"] = DAADSource(origin_text=d.get("country_of_origin", "Palestin"), status_text=d.get("status", r"^\s*Graduates?\b"),
                                 max_pages=d.get("pages", 6), max_details=d.get("details", 80))
    return reg
