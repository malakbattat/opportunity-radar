"""Turn a raw scraped listing into a classified, scored opportunity.

Everything here is pure (no network), so it can be unit-tested with fixtures.
"""
from __future__ import annotations

import hashlib
import html
import re
from datetime import date, datetime, timedelta
from typing import Any

from dateutil import parser as dateparser

# ── Text helpers ──────────────────────────────────────────────

_TAG_RE = re.compile(r"<[^>]+>")
_WS_RE = re.compile(r"\s+")


def clean_text(value: str | None) -> str:
    """Strip HTML tags/entities and collapse whitespace."""
    if not value:
        return ""
    text = _TAG_RE.sub(" ", value)
    text = html.unescape(text)
    return _WS_RE.sub(" ", text).strip()


def shorten(text: str, limit: int = 260) -> str:
    text = clean_text(text)
    if len(text) <= limit:
        return text
    cut = text[:limit].rsplit(" ", 1)[0]
    return cut.rstrip(",.;:-– ") + "…"


def _phrase_regex(phrases: list[str]) -> re.Pattern | None:
    phrases = [p.strip().lower() for p in phrases if p and p.strip()]
    if not phrases:
        return None
    # Longest first so "data science" wins over "science".
    phrases.sort(key=len, reverse=True)
    alt = "|".join(re.escape(p) for p in phrases)
    return re.compile(rf"(?<![\w-])(?:{alt})(?![\w])", re.IGNORECASE)


def normalise_title(title: str) -> str:
    """Key used to spot the same opportunity posted on several sites."""
    t = clean_text(title).lower()
    t = re.sub(r"\(.*?\)|\[.*?\]", " ", t)
    t = re.sub(r"\b(19|20)\d{2}(\s*[-–/]\s*(19|20)?\d{2})?\b", " ", t)
    t = re.sub(r"\b(fully|partially)[ -]funded\b|\bfunded\b|\bpaid\b|\bfree\b|\bfor international students\b", " ", t)
    t = t.split("|")[0]
    t = re.sub(r"[^a-z0-9 ]+", " ", t)
    t = re.sub(r"\b(the|in|at|of|for|and|programme|program|applications?|open|now|call)\b", " ", t)
    return _WS_RE.sub(" ", t).strip()


_GENERIC = {"scholarship", "university", "fellowship", "internship", "uk", "usa", "us", "international",
            "student", "study", "europe", "graduate", "government", "master", "phd", "doctoral", "fully",
            "excellence", "award", "grant", "summer", "school", "research", "global", "national"}


def title_tokens(key: str) -> set[str]:
    """Singularised tokens of a normalised title, for fuzzy duplicate matching."""
    return {t[:-1] if len(t) > 4 and t.endswith("s") and not t.endswith("ss") else t for t in key.split()}


def same_opportunity(a_key: str, b_key: str) -> bool:
    if a_key == b_key:
        return True
    a, b = title_tokens(a_key), title_tokens(b_key)
    small, big = (a, b) if len(a) <= len(b) else (b, a)
    distinctive = small - _GENERIC
    if len(distinctive) < 2 or len(small) < 3:
        return False
    return len(small & big) / len(small) >= 0.85 and distinctive <= big


def make_id(url: str) -> str:
    return hashlib.sha1(url.strip().lower().rstrip("/").encode()).hexdigest()[:12]


# ── Type / degree detection ───────────────────────────────────

TYPE_RULES: list[tuple[str, list[str]]] = [
    ("Guide", [r"^how to\b", r"\bstep[- ]by[- ]step\b", r"\bguide\b", r"\btips\b", r"^list of\b",
               r"\bcomplete application guide\b", r"\bwhat to do before\b", r"\bdeadlines?:"]),
    ("Research", [r"\bresearch (internships?|program(me)?s?|fellowships?|experiences?|attachments?|school|initiative|academy|placements?|assistant|opportunit(y|ies))\b",
                  r"\bsummer research\b", r"\bundergraduate research\b", r"\bpre-?doctoral\b", r"\bpredoc\b",
                  r"\bvisiting (student|researcher)s? (research )?program", r"\b(surf|reu|rise|ureca|vsrp)\b",
                  r"\bresearch mentorship\b", r"\bmentorship program(me)?\b", r"\bresearch intern\b",
                  r"\bresearch\b[\w ]{0,25}\binternships?\b"]),
    ("Internship", [r"\bintern(ship)?s?\b", r"\btraineeships?\b", r"\btrainee\b", r"\bjunior fellows internship\b"]),
    ("Fellowship", [r"\bfellowships?\b", r"\bfellows\b", r"\bscholars? program(me)?\b"]),
    ("Summer school", [r"\bsummer (school|program(me)?|camp|research)\b", r"\bwinter school\b", r"\bcamp\b"]),
    ("Competition", [r"\bcompetitions?\b", r"\bhackathons?\b", r"\bchallenge\b", r"\bawards?\b",
                     r"\bprizes?\b", r"\bcontest\b", r"\bolympiad\b"]),
    ("Conference", [r"\bconferences?\b", r"\bsummit\b", r"\bforum\b", r"\bassembly\b", r"\bsymposium\b",
                    r"\bmodel united nations\b", r"\bmun\b"]),
    ("Exchange", [r"\bexchange program(me)?\b", r"\bexchange\b", r"\bugrad\b"]),
    ("Course", [r"\bcourses?\b", r"\btraining\b", r"\bbootcamp\b", r"\bworkshops?\b", r"\bcertificates?\b",
                r"\bmooc\b", r"\bacademy\b"]),
    ("Grant", [r"\bgrants?\b", r"\bcall for proposals\b", r"\bfunding call\b", r"\bseed funding\b"]),
    ("Job", [r"\bjobs?\b", r"\bvacanc(y|ies)\b", r"\bposition\b", r"\bhiring\b", r"\brecruitment\b"]),
    ("Volunteering", [r"\bvolunteer(ing)?\b"]),
    ("Scholarship", [r"\bscholarships?\b", r"\bbursar(y|ies)\b", r"\bstudentships?\b",
                     r"\bmaster'?s?\b", r"\bphd\b", r"\bdoctoral\b", r"\bdegree\b", r"\bmsc\b", r"\bmext\b"]),
]
_TYPE_COMPILED = [(name, [re.compile(p, re.IGNORECASE) for p in pats]) for name, pats in TYPE_RULES]

DEGREE_RULES: dict[str, list[str]] = {
    "bachelor": [r"\bbachelor'?s?\b", r"\bundergraduates?\b", r"\bundergrads?\b", r"\bugrad\b", r"\bbsc\b",
                 r"\bcollege students\b", r"\b(sophomores?|juniors?|seniors?|freshm[ae]n)\b", r"\bsurf\b", r"\breu\b",
                 r"\bgks-u\b", r"\bhigh school\b"],
    "masters": [r"\bmaster'?s?\b", r"\bmasters\b", r"\bmsc\b", r"\bm\.sc\b", r"\bmba\b", r"\bgraduate scholarships?\b",
                r"\bpostgraduate\b", r"\berasmus mundus\b", r"\bjoint master\b",
                r"\bgraduate(-level)? students\b", r"\bmsc students\b"],
    "phd": [r"\bph\.?d\b", r"(?<!pre-)(?<!pre)(?<!post-)(?<!post)\bdoctoral\b", r"\bdoctorate\b", r"\bdoctoral network\b"],
    "postdoc": [r"\bpost-?doc(toral)?\b", r"\bpost doctorate\b", r"\bsenior fellowship\b", r"\bpostdoctoral researchers?\b"],
}
_DEGREE_COMPILED = {k: [re.compile(p, re.IGNORECASE) for p in v] for k, v in DEGREE_RULES.items()}

ROLLING_RE = re.compile(r"\b(always open|rolling (basis|deadline|admissions?)|no (single|fixed) deadline|open all year|"
                        r"different (deadlines?|for each)|varies by (course|program))\b", re.IGNORECASE)

# Destination countries grouped into regions (used for the country/region filters).
REGIONS: dict[str, list[str]] = {
    "Europe": ["United Kingdom", "Germany", "France", "Netherlands", "Belgium", "Switzerland", "Austria", "Sweden",
               "Norway", "Denmark", "Finland", "Iceland", "Ireland", "Italy", "Spain", "Portugal", "Poland",
               "Czech Republic", "Hungary", "Greece", "Cyprus", "Malta", "Estonia", "Latvia", "Lithuania",
               "Luxembourg", "Romania", "Bulgaria", "Croatia", "Slovenia", "Slovakia", "Serbia", "Turkey"],
    "North America": ["United States", "Canada", "Mexico"],
    "Middle East & North Africa": ["Saudi Arabia", "United Arab Emirates", "Qatar", "Kuwait", "Oman", "Bahrain",
                                   "Jordan", "Lebanon", "Palestine", "Egypt", "Morocco", "Tunisia", "Algeria",
                                   "Iraq", "Israel"],
    "Asia": ["China", "Hong Kong", "Taiwan", "Japan", "South Korea", "Singapore", "Malaysia", "Thailand",
             "Indonesia", "Vietnam", "Philippines", "India", "Pakistan", "Bangladesh", "Kazakhstan", "Russia"],
    "Oceania": ["Australia", "New Zealand"],
    "Sub-Saharan Africa": ["South Africa", "Kenya", "Nigeria", "Ghana", "Rwanda", "Ethiopia", "Uganda", "Tanzania"],
    "Latin America": ["Brazil", "Chile", "Argentina", "Colombia", "Peru"],
    "Online": ["Online"],
}
COUNTRY_REGION = {c: r for r, cs in REGIONS.items() for c in cs}
_ALIASES = {"USA": "United States", "U.S.": "United States", "US": "United States", "United States of America": "United States",
"UK": "United Kingdom", "England": "United Kingdom", "Scotland": "United Kingdom",
            "Britain": "United Kingdom", "UAE": "United Arab Emirates", "Emirates": "United Arab Emirates",
            "Abu Dhabi": "United Arab Emirates", "Dubai": "United Arab Emirates", "Korea": "South Korea",
            "Türkiye": "Turkey", "Turkiye": "Turkey", "Holland": "Netherlands", "Czechia": "Czech Republic",
            "Remote": "Online", "Virtual": "Online", "Ramallah": "Palestine", "Gaza": "Palestine", "West Bank": "Palestine",
            "KSA": "Saudi Arabia"}
_REGION_WORDS = {"Europe": "Europe", "European": "Europe", "Asia": "Asia", "Africa": "Sub-Saharan Africa",
                 "North America": "North America", "Latin America": "Latin America", "South America": "Latin America",
                 "Oceania": "Oceania",
                 "Middle East": "Middle East & North Africa", "MENA": "Middle East & North Africa"}
_PLACE_NAMES = sorted(set(COUNTRY_REGION) | set(_ALIASES), key=len, reverse=True)
_COUNTRY_RE = re.compile(r"(?<![\w.])(" + "|".join(re.escape(c) for c in _PLACE_NAMES) + r")(?![\w])")
_REGION_RE = re.compile(r"(?<![\w])(" + "|".join(re.escape(r) for r in sorted(_REGION_WORDS, key=len, reverse=True)) + r")(?![\w])")
# Words that make "for Pakistani students" etc. about the applicant, not the destination.
_NATIONALITY_CTX = re.compile(r"\b(for|from)\s+[A-Z][a-z]+(\s+and\s+[A-Z][a-z]+)?\s+(students|citizens|nationals|applicants)\b")


def detect_type(title: str, categories: list[str], body: str) -> str:
    # Title is the strongest signal, then site categories, then body.
    for haystack in (title, " ".join(categories)):
        for name, pats in _TYPE_COMPILED:
            if any(p.search(haystack) for p in pats):
                return name
    for name, pats in _TYPE_COMPILED:
        if name in ("Guide", "Job", "Course", "Grant"):
            continue  # too noisy in long bodies
        if any(p.search(body[:1500]) for p in pats):
            return name
    return "Opportunity"


def detect_degrees(text: str) -> list[str]:
    return [k for k, pats in _DEGREE_COMPILED.items() if any(p.search(text) for p in pats)]


# Well-known institutions/programmes → host country, used only when no country is named.
_INSTITUTION_COUNTRY = {
    "nanyang": "Singapore", "ntu singapore": "Singapore", "nus": "Singapore", "a*star": "Singapore",
    "zhejiang": "China", "tsinghua": "China", "peking university": "China", "fudan": "China", "chinese government": "China",
    "csc scholarship": "China", "schwarzman": "China", "kaust": "Saudi Arabia", "mbzuai": "United Arab Emirates",
    "khalifa university": "United Arab Emirates", "hbku": "Qatar", "eth zurich": "Switzerland", "epfl": "Switzerland",
    "oxford": "United Kingdom", "cambridge": "United Kingdom", "imperial college": "United Kingdom", "chevening": "United Kingdom",
    "commonwealth": "United Kingdom", "mcgill": "Canada", "mccall macbain": "Canada", "university of toronto": "Canada",
    "mitacs": "Canada", "harvard": "United States", "stanford": "United States", "mit ": "United States",
    "fulbright": "United States", "max planck": "Germany", "daad": "Germany", "heilbronn": "Germany",
    "mext": "Japan", "university of tokyo": "Japan", "gks": "South Korea", "kaist": "South Korea",
    "eiffel": "France", "sciences po": "France", "swedish institute": "Sweden", "ku leuven": "Belgium",
    "weizmann": "Israel", "academia sinica": "Taiwan", "isdb": "Saudi Arabia",
}
_INSTITUTION_RE = re.compile(r"(?<![\w])(" + "|".join(re.escape(k.strip()) for k in sorted(_INSTITUTION_COUNTRY, key=len, reverse=True)) + r")(?![\w])", re.I)


def canon_country(name: str) -> str | None:
    name = name.strip()
    c = _ALIASES.get(name, name)
    return c if c in COUNTRY_REGION else None


def detect_countries(title: str, meta_text: str, extra: list[str] | None = None, short_body: str = "") -> list[str]:
    """Destination countries, most specific source first. Only short texts are searched,
    so long eligibility lists in article bodies don't pollute the result."""
    found: list[str] = []
    for name in extra or []:
        for part in re.split(r",|/|\band\b", name or ""):
            c = canon_country(part)
            if c and c not in found:
                found.append(c)
    for hay in (title, meta_text, short_body):
        if not hay:
            continue
        hay = _NATIONALITY_CTX.sub(" ", hay)
        for m in _COUNTRY_RE.finditer(hay):
            c = canon_country(m.group(1))
            if c and c not in found:
                found.append(c)
        if found:
            break
    if not found:
        m = _INSTITUTION_RE.search(f"{title} {meta_text}")
        if m:
            found.append(_INSTITUTION_COUNTRY.get(m.group(1).lower()) or _INSTITUTION_COUNTRY[m.group(1).lower() + " "])
    return found[:10]


def detect_region(countries: list[str], title: str, meta_text: str) -> list[str]:
    regions = []
    for c in countries:
        r = COUNTRY_REGION.get(c)
        if r and r not in regions:
            regions.append(r)
    if not regions:
        m = _REGION_RE.search(title + " " + meta_text)
        if m:
            regions.append(_REGION_WORDS[m.group(1)])
    return regions


# Who can apply — a hint, not a guarantee.
_OPEN_RE = re.compile(r"\b(all countries|all nationalities|any nationality|international (students|applicants|candidates|undergraduates)|"
                      r"open to global applicants|global applicants|international students eligible|open to international|"
                      r"enrolled at international universities|students worldwide|international applicants welcome|"
                      r"worldwide|open to (all|everyone|applicants from (all|any))|global applicants|developing countries|"
                      r"all eligible countries|non-eu|non-european)\b", re.IGNORECASE)
_RESTRICTED_RE = re.compile(
    r"\b((?<![Nn]on-)(?:[A-Z][a-z]+|U\.?S\.?|UK|EU|EEA)\s+(?:[Cc]itizens|[Nn]ationals|[Rr]esidents)(?:\s+only)?|"
    r"(?:citizens|nationals|residents)\s+only|must be (?:a |an )?(?:citizen|national|permanent resident) of [A-Z][\w ]{2,30}|"
    r"(?:for|open to)\s+(?:[A-Z][a-z]+(?:\s+and\s+[A-Z][a-z]+)?)\s+(?:[Ss]tudents|[Cc]itizens|[Nn]ationals|[Yy]outh)|"
    r"UK/EEA nationals|HBCU|"
    r"(?:enrolled|studying|program) (?:at|in) a U\.?S\.? (?:college|university|institution)|"
    r"(?:enrolled|students) (?:at|in) (?:a )?U\.?S\.?(?:-based)? (?:college|university|institution)s?|"
    r"limited to [A-Z][\w ]{3,40}partner universities)\b")
_RESTRICTED_FALSE = re.compile(r"^(?:for|open to)\s+(?:International|Graduate|Undergraduate|Foreign|All|Outstanding|Female|Young|Eligible|Talented|Women|Master|PhD)\b", re.I)


def detect_eligibility(strong: str, body: str) -> tuple[str | None, str | None]:
    """Return ("open" | "restricted" | None, short note)."""
    for text in (strong, body[:4000]):
        for m in _RESTRICTED_RE.finditer(text):
            phrase = m.group(1).strip()
            if _RESTRICTED_FALSE.search(phrase):
                continue
            return "restricted", phrase[:60]
        m = _OPEN_RE.search(text)
        if m:
            return "open", m.group(1)[:60]
    return None, None


# ── Deadline extraction ───────────────────────────────────────

_MONTHS = r"(?:jan|feb|mar|apr|may|jun|jul|aug|sep|sept|oct|nov|dec)[a-z]*\.?"
_DATE_PATTERNS = [
    rf"\d{{1,2}}(?:st|nd|rd|th)?\s+(?:of\s+)?{_MONTHS},?\s+\d{{4}}",   # 31st October 2026 / 01 Feb 2027
    rf"{_MONTHS}\s+\d{{1,2}}(?:st|nd|rd|th)?,?\s+\d{{4}}",              # October 31, 2026
    r"\d{4}-\d{2}-\d{2}",                                               # 2026-10-31
    r"\d{1,2}[./]\d{1,2}[./]\d{4}",                                     # 31/10/2026 (day-first)
]
_DATE_RE = re.compile("|".join(f"(?:{p})" for p in _DATE_PATTERNS), re.IGNORECASE)
_DEADLINE_CTX_RE = re.compile(
    r"(deadline|closing date|closes|apply (?:by|before|until)|applications? (?:close|due|must be|should be)|"
    r"last date|submit(?:ted)? (?:by|before)|due date|until)", re.IGNORECASE)
_DAYS_LEFT_RE = re.compile(r"(?:closes in|application closes in)\s+(\d{1,4})\s+days?|(\d{1,4})\s+days?\s+left", re.IGNORECASE)


def _parse_date(s: str) -> date | None:
    s = s.strip()
    iso = re.match(r"^(\d{4})-(\d{2})-(\d{2})", s)
    if iso:
        try:
            return date(int(iso[1]), int(iso[2]), int(iso[3]))
        except ValueError:
            return None
    try:
        d = dateparser.parse(s, dayfirst=True, fuzzy=True, default=datetime(1900, 1, 1))
    except (ValueError, OverflowError):
        return None
    if not d or d.year < 2000:
        return None
    return d.date()


def extract_deadline(text: str, today: date, hint: str | None = None) -> tuple[date | None, bool]:
    """Return (deadline, rolling). Looks for dates near deadline words."""
    candidates: list[date] = []
    lo, hi = today - timedelta(days=400), today + timedelta(days=900)

    for src in ([hint] if hint else []) + [text]:
        if not src:
            continue
        m = _DAYS_LEFT_RE.search(src)
        if m:
            n = int(m.group(1) or m.group(2))
            return today + timedelta(days=n), False
        for ctx in _DEADLINE_CTX_RE.finditer(src):
            window = src[ctx.start(): ctx.end() + 90]
            dm = _DATE_RE.search(window)
            if dm:
                d = _parse_date(dm.group(0))
                if d and lo <= d <= hi:
                    candidates.append(d)
        if candidates:
            break
    if candidates:
        # Prefer the earliest date that is still in the future; else the latest past one.
        future = sorted(d for d in candidates if d >= today)
        return (future[0] if future else max(candidates)), False
    rolling = bool(ROLLING_RE.search((hint or "") + " " + text[:4000]))
    return None, rolling


_MONTH_NUM = {m: i for i, m in enumerate(["jan", "feb", "mar", "apr", "may", "jun", "jul", "aug", "sep", "oct", "nov", "dec"], 1)}
_MONTH_DAY_RE = re.compile(rf"(?:(\d{{1,2}})(?:st|nd|rd|th)?\s+)?({_MONTHS})(?:\s+(\d{{1,2}})(?:st|nd|rd|th)?)?(?:,?\s*(\d{{4}}))?", re.I)
_TBD_RE = re.compile(r"\b(tbd|tba|to be (announced|determined)|not (yet )?announced|coming soon)\b", re.I)
_VARIES_RE = re.compile(r"\b(varies|various|multiple|different deadlines|depends)\b", re.I)
_ROLLING_WORDS = re.compile(r"\b(rolling|year[- ]round|ongoing|open all year|always open|any time|anytime)\b", re.I)


def _end_of_month(y: int, m: int) -> date:
    return (date(y + (m == 12), m % 12 + 1, 1) - timedelta(days=1))


def parse_recurring_deadline(text: str, today: date) -> tuple[date | None, bool, str | None]:
    """Deadlines from lists of yearly programmes, e.g. "February 02, 2026", "Oct 15 – Nov 30 (annually)",
    "January, 2026 (expected)", "TBD", "Rolling". Returns (date, estimated, note) where note is
    "rolling" | "tbd" | "varies" | None. Past dates are moved to the next yearly cycle and marked estimated."""
    text = (text or "").strip()
    if not text:
        return None, False, None
    full = [d for d in (_parse_date(m.group(0)) for m in _DATE_RE.finditer(text)) if d]
    estimated = bool(re.search(r"expected|tbd|approx|around|annually|every year|yearly|\(?est", text, re.I))
    if full:
        d = full[-1]
    else:
        parts = [m for m in _MONTH_DAY_RE.finditer(text) if m.group(2)]
        if not parts:
            if _ROLLING_WORDS.search(text):
                return None, False, "rolling"
            if _VARIES_RE.search(text):
                return None, False, "varies"
            if _TBD_RE.search(text):
                return None, False, "tbd"
            return None, False, None
        # Several months ("October / April") → the next one to come round.
        cands = []
        for m in parts:
            mon = _MONTH_NUM[m.group(2)[:3].lower()]
            day = m.group(1) or m.group(3)
            yr = int(m.group(4)) if m.group(4) else today.year
            try:
                cands.append(date(yr, mon, int(day)) if day else _end_of_month(yr, mon))
            except ValueError:
                cands.append(_end_of_month(yr, mon))
        if len(cands) > 1 and not any(m.group(4) for m in parts) and not re.search(r"[–-]", text):
            rolled = [c if c >= today else c.replace(year=c.year + 1) for c in cands]
            return min(rolled), True, None
        d = cands[-1]
        estimated = True
    while d < today:
        try:
            d = d.replace(year=d.year + 1)
        except ValueError:
            d = d + timedelta(days=365)
        estimated = True
    return d, estimated, None


_YEAR_ONLY_RE = re.compile(
    r"\b(first[- ]year|1st[- ]year|freshm[ae]n|second[- ]year|2nd[- ]year|sophomores?|third[- ]year|3rd[- ]year|juniors?|underclass(?:wo)?m[ae]n)\b"
    r"(?!\s*(and|&|or)\s*(up|above|older|later|beyond|seniors?))", re.I)
_YEAR_OPEN_RE = re.compile(r"\b(all students?|all years|any year|and up|or above|seniors?|final[- ]year|graduating|recent grad)", re.I)


def detect_year_limit(text: str, in_title: bool = False) -> str | None:
    """'2nd-year students only' style limits that exclude final-year students."""
    if not text or _YEAR_OPEN_RE.search(text):
        return None
    m = _YEAR_ONLY_RE.search(text)
    if m and in_title and m.group(1).lower().startswith("junior"):
        return None      # "Junior Fellows", "Junior Researcher" are role names, not a year of study
    return m.group(1).lower() if m else None


# ── Intakes: which semester / year an opportunity is for ─────

_SEASON_WORDS = {"spring": "spring", "summer": "summer", "fall": "fall", "autumn": "fall", "winter": "winter"}
_SEASON_RE = r"(spring|summer|fall|autumn|winter)"
_MONTH_SEASON = {1: "spring", 2: "spring", 3: "spring", 4: "spring", 5: "summer", 6: "summer", 7: "summer", 8: "summer",
                 9: "fall", 10: "fall", 11: "fall", 12: "winter"}
_INTAKE_PATTERNS = [
    # "winter semester 2027/28" (German-style terms) starts in October; "summer semester 2027" in April
    (re.compile(r"\bwinter (?:semester|term)\s*(20\d{2})", re.I), lambda m: f"{m[1]}-fall"),
    (re.compile(r"\bsummer (?:semester|term)\s*(20\d{2})", re.I), lambda m: f"{m[1]}-spring"),
    (re.compile(rf"\b{_SEASON_RE}\s+(?:[A-Za-z&'’]+\s+){{0,3}}['’]?(20\d{{2}})\b", re.I),
     lambda m: f"{m[2]}-{_SEASON_WORDS[m[1].lower()]}"),
    (re.compile(rf"\b(20\d{{2}})\s+{_SEASON_RE}\b", re.I), lambda m: f"{m[1]}-{_SEASON_WORDS[m[2].lower()]}"),
    (re.compile(rf"\b(?:\(|\b)({_MONTHS})\s+(20\d{{2}})(?:\)|\s+(?:intake|start|entry|cohort))", re.I),
     lambda m: f"{m[2]}-{_MONTH_SEASON[_MONTH_NUM[m[1][:3].lower()]]}"),
    (re.compile(r"\b(20\d{2})\s*[-–/]\s*(?:20)?(\d{2})\b"), lambda m: f"{m[1]}-ay" if 1 <= int(m[2]) % 100 - int(m[1]) % 100 <= 2 else None),
]
_YEAR_RE = re.compile(r"(?<![\d-])(20\d{2})(?![\d])")
_SEASON_ONLY_RE = re.compile(rf"\b{_SEASON_RE}\b(?!\s*(?:20\d{{2}}|['’]\d{{2}}))", re.I)
INTAKE_ORDER = {"": 1, "spring": 2, "summer": 4, "ay": 5, "fall": 6, "winter": 8}


def intake_sort_key(key: str) -> float:
    year, _, part = key.partition("-")
    return int(year) * 10 + INTAKE_ORDER.get(part, 1)


def detect_intakes(title: str, extra: str, deadline: date | None, annual: bool, today: date) -> tuple[list[str], bool]:
    """Intake keys such as "2027-summer", "2027-fall", "2027-ay" (academic year 2027–28) or "2027".
    Returns (keys, inferred). Inferred means the year came from the next deadline, not the text."""
    keys: list[str] = []
    text = f"{title} {extra}"
    for rx, make in _INTAKE_PATTERNS:
        for m in list(rx.finditer(text)):
            k = make(m)
            if k and k not in keys:
                keys.append(k)
            if k:
                text = text.replace(m.group(0), " ", 1)
    if not keys:
        for m in _YEAR_RE.finditer(title):
            y = int(m.group(1))
            if today.year - 1 <= y <= today.year + 3 and str(y) not in keys:
                keys.append(str(y))
    inferred = False
    season = _SEASON_ONLY_RE.search(title) or _SEASON_ONLY_RE.search(extra[:300])
    if deadline and season:
        s = _SEASON_WORDS[season.group(1).lower()]
        start_month = {"spring": 1, "summer": 6, "fall": 9, "winter": 12}[s]
        cycle = deadline.year if deadline.month <= start_month else deadline.year + 1
        cycle_key = f"{cycle}-{s}"
        # Lists of yearly programmes often still show last year's title ("… 2026").
        stale = [k for k in keys if int(k[:4]) < cycle]
        if annual or not keys or stale:
            keys = [k for k in keys if k not in stale]
            if cycle_key not in keys:
                keys.insert(0, cycle_key)
                inferred = True
    keys = sorted(set(keys), key=intake_sort_key)[:3]
    return keys, inferred


def intake_is_past(keys: list[str], today: date) -> bool:
    """True when every intake is already over (e.g. a "2025" programme seen in late 2026)."""
    if not keys:
        return False
    def past(k: str) -> bool:
        year, _, part = k.partition("-")
        y = int(year)
        if part == "":
            return y < today.year
        if part == "ay":
            return (y + 1, 6) < (today.year, today.month)
        end_month = {"spring": 5, "summer": 8, "fall": 12, "winter": 14}[part]
        return (y * 12 + end_month) < (today.year * 12 + today.month)
    return all(past(k) for k in keys)


# ── Requirements: English test, GPA, who it targets ──────────

_NO_ENGLISH_TEST = re.compile(
    r"\b(no (ielts|toefl|english (language )?(proficiency )?(test|certificate|score))s?(\s+(is|are))?(\s+(required|needed|necessary))?|"
    r"without (an? )?(ielts|toefl|english test)|(ielts|toefl|english (language )?test)s?(\s+(is|are))? not (required|mandatory|needed|necessary)|"
    r"(ielts|toefl|english)( requirement)? (is )?waived|(ielts|english( language)?|language) waiver|"
    r"medium of instruction|moi (letter|certificate)|english proficiency letter|no language (test|certificate) required)\b", re.I)
_ENGLISH_TEST = re.compile(r"\b(ielts|toefl|pte academic|duolingo english test|cambridge (c1|c2|advanced|proficiency))\b", re.I)
_IELTS_MIN = re.compile(r"\bielts\b[^.;\n]{0,40}?\b([4-8](?:\.[05])?)\b", re.I)
_GPA_HIGH = re.compile(
    r"\b((?:c?gpa|grade point average)[^.;\n]{0,40}?\b(?:3\.[5-9]\d?|4\.0)\b|first[- ]class(?: honours| degree)?|1st class|"
    r"top (?:1|2|3|5|10|15) ?(?:%|percent)|(?:outstanding|exceptional|excellent|exceptionally strong) academic (?:record|achievements?|performance|results)|"
    r"(?:minimum|at least)(?: of)? (?:85|88|90|95) ?%|academic excellence)(?!\w)", re.I)
_GPA_MODERATE = re.compile(
    r"\b((?:c?gpa|grade point average)[^.;\n]{0,40}?\b(?:2\.[5-9]\d?|3\.[0-4]\d?)\b|upper second|2:1|second[- ]class upper|"
    r"good academic (?:record|standing)|(?:minimum|at least)(?: of)? (?:65|70|75|80) ?%)(?!\w)", re.I)
_WOMEN = re.compile(
    r"\b(for (?:young )?women|women (?:in|into) (?:stem|tech|technology|ai|computing|computer science|engineering|science|data)|"
    r"female (?:students|applicants|researchers|scientists|engineers|undergraduates)|self[- ]identify as (?:a )?wom[ae]n|"
    r"identify as women|girls in (?:stem|tech|ai)|women and non[- ]binary|women scholars?)\b", re.I)


def detect_requirements(text: str, cfg: dict[str, Any], title: str = "") -> dict[str, Any]:
    out: dict[str, Any] = {"english_test": None, "english_min": None, "gpa_level": None, "gpa_note": None, "for_women": False}
    if _NO_ENGLISH_TEST.search(text):
        out["english_test"] = "not_required"
    elif _ENGLISH_TEST.search(text):
        out["english_test"] = "required"
        m = _IELTS_MIN.search(text)
        if m and 4 <= float(m.group(1)) <= 8.5:
            out["english_min"] = float(m.group(1))
    m = _GPA_HIGH.search(text)
    if m:
        out["gpa_level"], out["gpa_note"] = "high", m.group(1)[:60]
    else:
        comp = _phrase_regex(cfg.get("very_competitive", []))
        cm = comp.search(title) if comp else None
        if cm:
            out["gpa_level"], out["gpa_note"] = "high", None
        else:
            m = _GPA_MODERATE.search(text)
            if m:
                out["gpa_level"], out["gpa_note"] = "moderate", m.group(1)[:60]
    out["for_women"] = bool(_WOMEN.search(text))
    return out


# ── Scoring ───────────────────────────────────────────────────

class Classifier:
    def __init__(self, cfg: dict[str, Any], today: date | None = None):
        self.cfg = cfg
        self.today = today or date.today()
        self.fields = {
            key: {"label": f["label"], "weight": f["weight"], "re": _phrase_regex(f["keywords"])}
            for key, f in cfg["fields"].items()
        }
        self.off_re = _phrase_regex(cfg["off_topic"]["keywords"])
        self.prestige_re = _phrase_regex(cfg["prestige"]["names"])
        self.funding = {k: {"points": v["points"], "re": _phrase_regex(v["keywords"])} for k, v in cfg["funding"].items()}
        self.ignore_re = _phrase_regex(cfg.get("ignore_phrases", []))
        of = cfg.get("open_field") or {}
        self.open_field_re = _phrase_regex(of.get("keywords", []))
        self.open_field_bonus = of.get("bonus", 0)
        self.final_year_re = _phrase_regex(cfg.get("profile", {}).get("final_year_keywords", []))
        self.nat_re = _phrase_regex(cfg.get("profile", {}).get("nationality_terms", []))

    def _field_scores(self, strong: str, body: str) -> dict[str, float]:
        """Strong text (title, subjects, categories, summary) counts fully;
        body text counts half and needs two separate mentions."""
        if self.ignore_re:
            strong = self.ignore_re.sub(" ", strong)
            body = self.ignore_re.sub(" ", body)
        out: dict[str, float] = {}
        for key, f in self.fields.items():
            if not f["re"]:
                continue
            if f["re"].search(strong):
                out[key] = f["weight"]
            elif len(f["re"].findall(body)) >= 2:
                out[key] = f["weight"] * 0.5
        # "Medical AI" also fires when both AI/data and health signals are strong.
        if "medical_ai" not in out and ("ai_ml" in out or "data_science" in out) and ("health" in out or "biomed" in out):
            if max(out.get("ai_ml", 0), out.get("data_science", 0)) >= 30 and max(out.get("health", 0), out.get("biomed", 0)) >= 18:
                out["medical_ai"] = self.fields["medical_ai"]["weight"] * 0.8
        return out

    def _funding(self, strong: str, body: str) -> tuple[str | None, int]:
        # "partially funded" must be checked before the generic "funded" in paid.
        order = ["fee_based", "fully_funded", "partial", "paid"]
        for scope_text, scale in ((strong, 1.0), (body[:5000], 0.7)):
            for key in order:
                f = self.funding.get(key)
                if f and f["re"] and f["re"].search(scope_text):
                    return key, round(f["points"] * scale)
        return None, 0

    def classify(self, raw: dict[str, Any]) -> dict[str, Any] | None:
        title = clean_text(raw.get("title"))
        url = (raw.get("url") or "").strip()
        if not title or not url:
            return None
        body = clean_text(raw.get("body"))
        summary_src = raw.get("summary") or body
        categories = [clean_text(c) for c in raw.get("categories", []) if c]
        subjects = [clean_text(s) for s in raw.get("subjects", []) if s]
        meta_text = " ".join(categories + subjects + [clean_text(raw.get("meta_text"))])
        strong = " ".join([title, meta_text, clean_text(raw.get("summary"))])

        otype = raw.get("type_hint") or detect_type(title, categories, body)
        if otype == "Opportunity" and raw.get("type_default"):
            otype = raw["type_default"]
        degrees = sorted(set(detect_degrees(title + " " + meta_text) or detect_degrees(body[:3000])),
                         key=["bachelor", "masters", "phd", "postdoc"].index)

        deadline_estimated, deadline_note = False, None
        if raw.get("annual"):
            deadline, deadline_estimated, deadline_note = parse_recurring_deadline(raw.get("deadline_text") or "", self.today)
            rolling = deadline_note == "rolling"
        else:
            deadline, rolling = extract_deadline(body, self.today, hint=raw.get("deadline_text"))
            if raw.get("deadline"):
                deadline = raw["deadline"] if isinstance(raw["deadline"], date) else _parse_date(str(raw["deadline"])) or deadline
            rolling = rolling or bool(raw.get("rolling"))
        if raw.get("recurring") and not deadline:
            deadline_note = "recurring"
        intakes, intake_inferred = detect_intakes(title, clean_text(raw.get("summary"))[:400] + " " + clean_text(raw.get("meta_text")),
                                                  deadline, bool(raw.get("annual")), self.today)

        fields = self._field_scores(strong.lower(), body.lower())
        weights = sorted(fields.values(), reverse=True)
        relevance = (weights[0] + 0.35 * sum(weights[1:])) if weights else 0
        relevance = min(relevance, 50)

        funding_key, funding_pts = self._funding(strong, body)
        prestige_hit = self.prestige_re.search(title + " " + meta_text + " " + clean_text(raw.get("org"))) if self.prestige_re else None
        if not prestige_hit and self.prestige_re:
            prestige_hit = self.prestige_re.search(body[:800])
        prestige = self.cfg["prestige"]["bonus"] if prestige_hit else 0

        degree_pts = max([self.cfg.get("degree_bonus", {}).get(d, 0) for d in degrees] or [0])
        open_bonus = 0
        if not fields and self.open_field_re and self.open_field_re.search(strong):
            open_bonus = self.open_field_bonus
        penalty = 0
        if not fields and self.off_re and self.off_re.search(title + " " + meta_text):
            penalty += self.cfg["off_topic"]["penalty"]
        if otype == "Guide":
            penalty += 40

        # Profile: what suits a final-year undergraduate heading to a master's.
        prof = self.cfg.get("profile", {})
        type_pts = prof.get("type_bonus", {}).get(otype, 0)
        current_ug = otype in prof.get("current_student_types", []) and "bachelor" in degrees
        ug_pts = prof.get("current_undergrad_bonus", 0) if current_ug else 0
        final_pts = prof.get("final_year_bonus", 0) if self.final_year_re and self.final_year_re.search(strong + " " + body[:1500]) else 0
        ba_only = otype == "Scholarship" and degrees == ["bachelor"]
        ba_pen = prof.get("bachelor_degree_scholarship_penalty", 0) if ba_only else 0
        year_limit = detect_year_limit(raw.get("year_text") or "") or detect_year_limit(title, in_title=True)
        year_pen = prof.get("year_restricted_penalty", 0) if year_limit else 0

        phd_only = degrees in (["phd"], ["phd", "postdoc"], ["postdoc"]) \
            and not (self.final_year_re and self.final_year_re.search(strong))
        phd_pen = prof.get("phd_only_penalty", 0) if phd_only else 0
        if phd_pen:
            degree_pts = 0

        req = detect_requirements(f"{strong} {body[:6000]} {clean_text(raw.get('eligibility_text'))}", self.cfg, title)
        elig_text = f"{title} {meta_text} {clean_text(raw.get('summary'))} {clean_text(raw.get('eligibility_text'))} {body[:3000]}"
        targets_me = bool(raw.get("open_to_origin")) or bool(self.nat_re and self.nat_re.search(elig_text))
        nat_pts = prof.get("nationality_bonus", 0) if targets_me else 0
        women_pts = prof.get("women_bonus", 0) if req["for_women"] and prof.get("gender") == "female" else 0
        no_test_pts = prof.get("no_english_test_bonus", 0) if req["english_test"] == "not_required" and not prof.get("english_score") else 0

        score = 6 + relevance + open_bonus + funding_pts + prestige + degree_pts + type_pts + ug_pts + final_pts \
            + nat_pts + women_pts + no_test_pts - penalty - ba_pen - year_pen - phd_pen
        # Programmes only for doctoral study or current PhD students stay below "high value" for now.
        phd_level = bool(degrees) and set(degrees) <= {"phd", "postdoc"}
        cap = prof.get("phd_only_max_score")
        uncapped = int(max(0, min(100, round(score))))
        score = min(uncapped, cap) if (phd_level and cap is not None) else uncapped

        # Breakdown shown under "Why this score": [code, points, detail]. The site turns codes into words.
        ranked_fields = [k for k, _ in sorted(fields.items(), key=lambda kv: -kv[1])]
        why: list[list] = [["base", 6, None]]
        if relevance:
            why.append(["topic", round(relevance), ranked_fields[:3]])
        if open_bonus:
            why.append(["open_field", open_bonus, None])
        if funding_pts:
            why.append([funding_key, funding_pts, None])
        if prestige:
            why.append(["prestige", prestige, prestige_hit.group(0)])
        if degree_pts:
            why.append(["level", degree_pts, max(degrees, key=lambda d: self.cfg.get("degree_bonus", {}).get(d, 0))])
        if type_pts:
            why.append(["type", type_pts, otype])
        if ug_pts:
            why.append(["current_undergrad", ug_pts, None])
        if final_pts:
            why.append(["final_year", final_pts, None])
        if penalty and otype != "Guide":
            why.append(["off_topic", -penalty, None])
        if ba_pen:
            why.append(["bachelor_degree", -ba_pen, None])
        if year_pen:
            why.append(["year_limit", -year_pen, year_limit])
        if phd_pen:
            why.append(["phd_only", -phd_pen, None])
        if nat_pts:
            why.append(["nationality", nat_pts, prof.get("nationality")])
        if women_pts:
            why.append(["women", women_pts, None])
        if no_test_pts:
            why.append(["no_english_test", no_test_pts, None])
        if score < uncapped:
            raw_total = sum(w[1] for w in why)
            why.append(["phd_cap", score - min(raw_total, 100), None])

        short_body = body if len(body) < 700 else ""
        extra = raw.get("countries") or ([raw["country"]] if raw.get("country") else [])
        countries = detect_countries(title, meta_text, extra, short_body)
        regions = detect_region(countries, title, meta_text)
        eligibility, eligibility_note = detect_eligibility(strong, body)
        if raw.get("eligibility_text"):
            eligibility, eligibility_note = detect_eligibility(raw["eligibility_text"], "") if detect_eligibility(raw["eligibility_text"], "")[0] else (eligibility, eligibility_note)
        tier = "top" if score >= self.cfg["top_pick"] else "high" if score >= self.cfg["high_value"] else "standard"

        return {
            "id": make_id(url),
            "title": title,
            "url": url,
            "source": raw["source"],
            "org": clean_text(raw.get("org")) or None,
            "summary": shorten(summary_src),
            "type": otype,
            "degrees": degrees,
            "fields": [k for k, _ in sorted(fields.items(), key=lambda kv: -kv[1])],
            "funding": funding_key,
            "country": countries[0] if countries else None,
            "countries": countries,
            "regions": regions,
            "eligibility": eligibility,
            "eligibility_note": eligibility_note,
            "deadline": deadline.isoformat() if deadline else None,
            "deadline_estimated": bool(deadline and deadline_estimated),
            "deadline_note": deadline_note,
            "year_limit": year_limit,
            "intakes": intakes,
            "intake_inferred": intake_inferred,
            "past_intake": intake_is_past(intakes, self.today) and not (deadline and deadline >= self.today),
            "diversity": bool(raw.get("diversity")),
            "english_test": req["english_test"],
            "english_min": req["english_min"],
            "gpa_level": req["gpa_level"],
            "gpa_note": req["gpa_note"],
            "for_women": req["for_women"],
            "targets_me": targets_me,
            "phd_level": phd_level,
            "rolling": rolling and not deadline,
            "published": raw.get("published"),
            "prestige": bool(prestige_hit),
            "score": score,
            "tier": tier,
            "why": why,
            "_key": normalise_title(title),
        }
