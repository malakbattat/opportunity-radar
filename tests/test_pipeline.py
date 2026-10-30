"""Offline tests: parsers + classifier against fixtures that mirror each site.

Run:  python -m pytest -q
"""
import json
from datetime import date
from pathlib import Path

import yaml

from scraper.classify import Classifier, extract_deadline, normalise_title
from scraper.run import dedupe
from scraper.sources import ForasSource, For9aSource, parse_rss, parse_scholarshipsads, parse_wp_post, walk_json_for_opportunities

FIX = Path(__file__).parent / "fixtures"
ROOT = Path(__file__).parent.parent
TODAY = date(2026, 10, 28)
CFG = yaml.safe_load((ROOT / "config.yaml").read_text())
CLF = Classifier(CFG, today=TODAY)


def by_title(items, needle):
    return next(i for i in items if needle.lower() in i["title"].lower())


def test_scholarshipsads_cards():
    raw = parse_scholarshipsads((FIX / "scholarshipsads.html").read_text(), "https://www.scholarshipsads.com")
    assert len(raw) == 3, [r["title"] for r in raw]          # blog link excluded
    items = [CLF.classify(r) for r in raw]
    hbku = by_title(items, "HBKU")
    assert hbku["deadline"] == "2027-02-01"
    assert hbku["funding"] == "fully_funded"
    assert {"masters", "phd"} <= set(hbku["degrees"])
    assert "ai_ml" in hbku["fields"] and "data_science" in hbku["fields"]
    assert hbku["country"] == "Qatar"
    assert hbku["tier"] in ("high", "top")
    gates = by_title(items, "Gates Cambridge")
    assert gates["rolling"] and gates["deadline"] is None and gates["prestige"]
    honjo = by_title(items, "Honjo")
    assert honjo["deadline"] == "2026-10-31" and honjo["funding"] == "partial"
    assert honjo["score"] < hbku["score"]


def test_wordpress_api_posts():
    posts = json.loads((FIX / "wp_posts.json").read_text())
    raw = [parse_wp_post("scholarshipscorner", p, {5: "Fellowships", 9: "Opportunities", 12: "Guidelines", 7: "Conferences"}) for p in posts]
    items = [CLF.classify(r) for r in raw]
    daad = by_title(items, "DAAD Heilbronn")
    assert daad["type"] == "Fellowship"
    assert daad["deadline"] == "2027-01-15"
    assert daad["fields"][0] in ("medical_ai", "ai_ml")
    assert daad["phd_level"] and daad["score"] <= CFG["profile"]["phd_only_max_score"]      # postdoc-only → not high value
    guide = by_title(items, "How to Apply")
    assert guide["type"] == "Guide"
    udga = by_title(items, "Diplomats")
    assert udga["type"] == "Conference" and udga["funding"] == "fee_based"
    assert udga["score"] < 20
    assert "health" not in udga["fields"]                     # "health insurance" ignored


def test_rss_fallback():
    raw = parse_rss("opportunityportal", (FIX / "rss.xml").read_bytes())
    assert len(raw) == 2 and raw[0]["published"] == "2026-07-21"
    items = [CLF.classify(r) for r in raw]
    undp = by_title(items, "UNDP")
    assert undp["type"] == "Internship" and undp["deadline"] == "2026-11-30"
    assert undp["funding"] in ("fully_funded", "paid")
    cw = by_title(items, "Commonwealth")
    assert cw["deadline"] == "2026-12-10" and "masters" in cw["degrees"]


def test_for9a_html_and_next_data():
    src = For9aSource([])
    raw = src._parse((FIX / "for9a.html").read_text(), [])
    titles = [r["title"] for r in raw]
    assert any("Artificial Intelligence in the UAE" in t for t in titles)
    assert any("KAUST" in t for t in titles)
    assert any("Marie Skłodowska-Curie" in t for t in titles)
    assert not any("Master's" == t for t in titles)          # category link skipped
    items = [CLF.classify(r) for r in raw]
    mbz = by_title(items, "Artificial Intelligence in the UAE")
    assert mbz["deadline"] == "2026-11-04"                   # "closes in 7 days"
    kaust = by_title(items, "KAUST")
    assert kaust["rolling"] and kaust["prestige"]
    msca = by_title(items, "Curie")
    assert msca["deadline"] == "2026-11-23" and msca["url"].endswith("Marie-Sklodowska-Curie-Postdoctoral-Fellowship-2026")


def test_foras_json_walker():
    payload = json.loads((FIX / "foras.json").read_text())
    found = walk_json_for_opportunities(payload, ForasSource([])._make_url)
    assert len(found) == 2                                   # the bare {"id","name"} city is ignored
    for f in found:
        f["source"] = "foras"
    items = [CLF.classify(r) for r in found]
    da = by_title(items, "Data Analyst")
    assert da["type"] == "Internship" and da["deadline"] == "2026-11-20" and "data_science" in da["fields"]


def test_deadline_parsing_variants():
    cases = {
        "Deadline: 01 Feb 2027": "2027-02-01",
        "Application deadline is January 15, 2027.": "2027-01-15",
        "Apply before 31st December 2026 to be considered": "2026-12-31",
        "Closing date: 2026-12-05": "2026-12-05",
        "Applications close 30/11/2026": "2026-11-30",
        "95 days left": "2027-01-31",
    }
    for text, want in cases.items():
        got, _ = extract_deadline(text, TODAY)
        assert got and got.isoformat() == want, (text, got)
    d, rolling = extract_deadline("Applications are accepted on a rolling basis.", TODAY)
    assert d is None and rolling


def test_dedupe_across_sources():
    a = CLF.classify({"source": "opportunityportal", "title": "Swedish Institute Scholarship for Global Professionals 2027 (Fully Funded)",
                      "url": "https://opportunityportal.info/si-scholarship-for-global-professionals/"})
    b = CLF.classify({"source": "scholarshipsads", "title": "Swedish Institute Scholarship for Global Professionals 2027-2028",
                      "url": "https://www.scholarshipsads.com/si-global-professionals", "deadline_text": "Deadline: 10 Feb 2027"})
    assert normalise_title(a["title"]) == normalise_title(b["title"])
    merged = dedupe([a, b])
    assert len(merged) == 1 and merged[0]["deadline"] == "2027-02-10" and len(merged[0]["also_on"]) == 1


def test_history_keeps_first_seen_and_drops_merged_duplicates():
    from scraper.run import merge_history
    a = CLF.classify({"source": "scholarshipsads", "title": "France Eiffel Excellence Scholarship | Fully Funded",
                      "url": "https://www.scholarshipsads.com/france-eiffel-excellence-scholarship", "deadline_text": "Deadline: 06 Jan 2027"})
    b = CLF.classify({"source": "scholarshipscorner", "title": "Eiffel Excellence Scholarship 2027 in France | Study in Europe",
                      "url": "https://scholarshipscorner.website/eiffel-excellence-scholarship/"})
    old_b = dict(b, first_seen="2026-10-01T00:00:00+00:00", last_seen="2026-10-01T00:00:00+00:00", also_on=[])
    old_a = dict(a, first_seen="2026-09-01T00:00:00+00:00", last_seen="2026-10-01T00:00:00+00:00", also_on=[])
    fresh = dedupe([a, b])
    out, _ = merge_history(fresh, [old_a, old_b], CFG, TODAY, "2026-10-28T05:00:00+00:00", set())
    assert len(out) == 1 and out[0]["first_seen"].startswith("2026-09-01")
    # A closed item moves to the archive with an expected reopening date.
    closed = dict(a, id="x", url="https://e.x/closed", _key="something else entirely", deadline="2026-09-01",
                  first_seen="2026-08-01", last_seen="2026-09-01")
    act, arch = merge_history([], [closed], CFG, TODAY, "2026-10-28T05:00:00+00:00", set())
    assert all(i["id"] != "x" for i in act)
    assert arch[0]["id"] == "x" and arch[0]["archive_reason"] == "closed" and arch[0]["reopens"] == "2027-09-01"


def test_countries_regions_and_eligibility():
    from scraper.classify import detect_countries, detect_eligibility
    # Multi-country host list from ScholarshipsAds, plus region.
    it = CLF.classify({"source": "scholarshipsads", "title": "Erasmus Mundus PlantHealth Scholarship 2027 in Europe | Fully Funded",
                       "url": "https://x.y/a", "countries": ["France", "Italy", "Germany", "Spain"],
                       "eligibility_text": "All countries"})
    assert it["countries"] == ["France", "Italy", "Germany", "Spain"] and it["regions"] == ["Europe"]
    assert it["eligibility"] == "open"
    # Applicant nationality is not the destination.
    assert detect_countries("Italy Scholarships for Pakistani Students 2027", "") == ["Italy"]
    assert detect_countries("Fully Funded Internship in the UAE", "") == ["United Arab Emirates"]
    assert detect_countries("Data Analyst Internship – Ramallah (Paid)", "") == ["Palestine"]
    # Eligibility hints
    assert detect_eligibility("Fulbright Swedish Scholar Program Swedish Citizens", "")[0] == "restricted"
    assert detect_eligibility("Italy Scholarships for Pakistani Students", "")[0] == "restricted"
    assert detect_eligibility("Scholarship for International Students", "")[0] == "open"
    assert detect_eligibility("Open to non-EU citizens worldwide", "")[0] == "open"
    # Region word with no country
    eu = CLF.classify({"source": "x", "title": "Summer School in Europe on Machine Learning", "url": "https://x.y/b"})
    assert eu["countries"] == [] and eu["regions"] == ["Europe"]


def test_score_breakdown_adds_up():
    raw = parse_scholarshipsads((FIX / "scholarshipsads.html").read_text(), "https://www.scholarshipsads.com")
    for r in raw:
        it = CLF.classify(r)
        total = max(0, min(100, sum(w[1] for w in it["why"])))   # score is capped at 100
        assert abs(total - it["score"]) <= 1, it["why"]


def test_institution_country_hint():
    from scraper.classify import detect_countries
    assert detect_countries("Nanyang President's Graduate Scholarship 2027 (Fully Funded)", "") == ["Singapore"]
    assert detect_countries("Fully Funded PhD at KAUST", "") == ["Saudi Arabia"]
    assert detect_countries("Rhodes Scholarship 2027 in UK at Oxford", "") == ["United Kingdom"]


def test_quick_mode_limits_and_change_detection():
    import copy
    from scraper.run import apply_quick_limits, fingerprint
    cfg = copy.deepcopy(CFG)
    apply_quick_limits(cfg)
    assert cfg["sources"]["scholarshipscorner"]["pages"] == 1
    assert cfg["sources"]["scholarshipsads"]["pages"] == 2
    assert len(cfg["sources"]["for9a"]["paths"]) == 3
    a = {"generated_at": "2026-10-29T05:23:00+00:00", "site": {}, "thresholds": {},
         "items": [{"id": "x", "score": 50, "last_seen": "2026-10-29T05:23:00+00:00"}]}
    b = dict(a, generated_at="2026-10-29T06:23:00+00:00",
             items=[{"id": "x", "score": 50, "last_seen": "2026-10-29T06:23:00+00:00"}])
    assert fingerprint(a) == fingerprint(b)                      # only timestamps moved → no commit
    c = dict(b, items=b["items"] + [{"id": "y", "score": 70}])
    assert fingerprint(a) != fingerprint(c)                      # a new listing → commit


def test_research_list_from_github():
    from scraper.github_lists import parse_research_list
    raw = parse_research_list((FIX / "research_list.md").read_text())
    assert len(raw) == 7 and all(r["url"].startswith("http") for r in raw)
    items = {i["title"]: i for i in map(CLF.classify, raw)}
    asu = items["ASU Summer Research Initiative (SURI)"]
    assert asu["type"] == "Research" and asu["deadline"] == "2027-02-02" and asu["deadline_estimated"]
    assert asu["eligibility"] == "open" and asu["countries"] == [] and asu["regions"] == ["North America"]
    cmu = next(v for k, v in items.items() if k.startswith("CMU LTI"))
    assert cmu["url"].startswith("https://forms.gle/")
    kaust = next(v for k, v in items.items() if "KAUST" in k)
    assert kaust["rolling"] and kaust["deadline"] is None and kaust["countries"] == ["Saudi Arabia"]
    rise = next(v for k, v in items.items() if "DAAD RISE" in k)
    assert rise["deadline"] == "2026-11-30" and rise["countries"] == ["Germany"]
    aalto = next(v for k, v in items.items() if "Aalto" in k)
    assert {"bachelor", "masters"} <= set(aalto["degrees"]) and aalto["tier"] in ("high", "top"), aalto["why"]


def test_internship_list_sections_and_fields():
    from datetime import datetime, timezone
    from scraper.github_lists import parse_internship_list
    md = (FIX / "internships.md").read_text()
    now = datetime(2026, 10, 29, 12, tzinfo=timezone.utc)
    raw = parse_internship_list(md, sections=["Software Engineering", "Data Science"], now=now)
    assert {r["categories"][0] for r in raw} == {"Software Engineering", "Data Science & AI"}   # Business skipped
    kla = next(r for r in raw if "KLA" in r["title"])
    assert kla["title"] == "Software Engineer Intern at KLA" and kla["published"] == "2026-10-29"
    assert kla["url"].startswith("https://zapply.jobs/")
    item = CLF.classify(kla)
    assert item["type"] == "Internship" and item["countries"] == ["United States"] and item["eligibility"] == "open"
    ds = [CLF.classify(r) for r in raw if "Data Scien" in r["title"]]
    assert ds and all("data_science" in d["fields"] for d in ds)


def test_cs_programs_list():
    from scraper.github_lists import parse_programs_list
    raw = parse_programs_list((FIX / "cs_programs.md").read_text())
    kinds = {r["type_hint"] for r in raw}
    assert {"Fellowship", "Externship", "Scholarship"} <= kinds
    assert not any("ColorStack" == r["title"] for r in raw)                   # resources section skipped
    items = [CLF.classify(r) for r in raw]
    mlh = next(i for i in items if i["title"] == "MLH Fellowship")
    assert mlh["deadline_note"] == "recurring" and mlh["funding"] == "paid"
    deshaw = [i for i in items if "DE Shaw" in i["title"]]
    assert deshaw and all(i["year_limit"] == "second-year" for i in deshaw)
    assert all(d["score"] < mlh["score"] for d in deshaw)
    assert any(i["diversity"] for i in items)


def test_intakes():
    from scraper.classify import detect_intakes, intake_is_past
    cases = {
        "Summer 2027 Data Science Intern": ["2027-summer"],
        "Research Intern (Winter 2027)": ["2027-winter"],
        "2027 Spring Intern - Data Science": ["2027-spring"],
        "Data Science Co-Op (January 2027)": ["2027-spring"],
        "Erasmus Mundus MAPP Scholarship 2027-2029": ["2027-ay"],
        "Columbia University Fellowships 2027–28": ["2027-ay"],
        "Study in Germany winter semester 2027/28": ["2027-fall"],
        "Gates Cambridge Scholarship 2027 in UK": ["2027"],
        "MBZUAI Aspire Ph.D. Fellowship": [],
    }
    for title, want in cases.items():
        assert detect_intakes(title, "", None, False, TODAY)[0] == want, title
    # A yearly list still titled "… 2026" moves to next summer's cycle, from its next deadline.
    keys, inferred = detect_intakes("UIUC++ Summer Research in Software Engineering (SRSE 2026)", "", date(2027, 4, 15), True, TODAY)
    assert keys == ["2027-summer"] and inferred
    assert intake_is_past(["2025"], TODAY) and intake_is_past(["2025-ay"], TODAY) and intake_is_past(["2026-summer"], TODAY)
    assert not intake_is_past(["2026"], TODAY) and not intake_is_past(["2026-fall"], TODAY) and not intake_is_past([], TODAY)


def test_archive_lifecycle():
    from scraper.run import merge_history
    stamp1, stamp2 = "2026-10-28T05:00:00+00:00", "2027-10-20T05:00:00+00:00"
    mk = lambda **kw: CLF.classify({"source": "scholarshipsads", "url": "https://x.y/eth", "title": "ETH Zurich Excellence Scholarship 2027",
                                     "deadline_text": kw.get("dl", "Deadline: 30 Nov 2026")})
    first = mk()
    act, arch = merge_history([first], [], CFG, TODAY, stamp1, set(), [])
    assert len(act) == 1 and not arch
    # The deadline passes; the site still shows the old post → it goes to the archive, not back to open.
    later = date(2026, 12, 5)
    act, arch = merge_history([mk()], act, CFG, later, "2026-12-05T05:00:00+00:00", set(), arch)
    assert not act and arch[0]["archive_reason"] == "closed" and arch[0]["reopens"] == "2027-11-30"
    archived_at = arch[0]["archived_at"]
    act, arch = merge_history([mk()], act, CFG, date(2026, 12, 6), "2026-12-06T05:00:00+00:00", set(), arch)
    assert arch[0]["archived_at"] == archived_at                       # stays put, date unchanged
    # Next year the post is updated with a new deadline → back to open, marked reopened.
    act, arch = merge_history([mk(dl="Deadline: 30 Nov 2027")], act, CFG, date(2027, 10, 20), stamp2, set(), arch)
    assert len(act) == 1 and act[0]["reopened_at"] == stamp2 and not arch
    # Past-intake posts (e.g. "2025") go straight to the archive.
    old = CLF.classify({"source": "scholarshipscorner", "url": "https://x.y/old", "title": "Leadership Certification London 2025"})
    act2, arch2 = merge_history([old], [], CFG, TODAY, stamp1, set(), [])
    assert not act2 and arch2[0]["archive_reason"] == "past_intake"
    # Zapply job posts are dropped, not archived, once they vanish.
    job = dict(CLF.classify({"source": "zapply", "url": "https://z.y/1", "title": "Data Science Intern at X"}),
               first_seen=stamp1, last_seen="2026-10-20T00:00:00+00:00")
    act3, arch3 = merge_history([], [job], CFG, TODAY, stamp1, set(), [])
    assert not act3 and not arch3


def test_requirements_and_profile_signals():
    from scraper.classify import detect_requirements
    r = detect_requirements("Applicants do not need IELTS; no IELTS required for this programme.", CFG)
    assert r["english_test"] == "not_required"
    r = detect_requirements("Proof of English: IELTS overall 6.5 or TOEFL iBT 90.", CFG)
    assert r["english_test"] == "required" and r["english_min"] == 6.5
    assert detect_requirements("Minimum CGPA of 3.5 out of 4.0 required.", CFG)["gpa_level"] == "high"
    assert detect_requirements("Applicants should be in the top 10% of their class.", CFG)["gpa_level"] == "high"
    assert detect_requirements("A minimum GPA of 3.0 is required.", CFG)["gpa_level"] == "moderate"
    assert detect_requirements("Rhodes Scholarship 2027", CFG, "Rhodes Scholarship 2027")["gpa_level"] == "high"
    assert detect_requirements("A fellowship for women in computing and AI.", CFG)["for_women"]
    # Programmes aimed at Palestinians score higher for the default profile.
    base = {"source": "opportunitiesforyouth", "url": "https://x.y/p", "title": "Summer Research Internship in Data Science 2027 (Fully Funded)"}
    plain = CLF.classify(base)
    pal = CLF.classify(dict(base, url="https://x.y/q", summary="Open to Palestinian students from the West Bank and Gaza."))
    assert pal["targets_me"] and pal["score"] > plain["score"]
    assert any(w[0] == "nationality" for w in pal["why"])


def test_phd_only_programmes_stay_below_high_value():
    it = CLF.classify({"source": "scholarshipsads", "url": "https://x.y/phd", "title": "Fully Funded PhD Scholarship in Artificial Intelligence at Oxford",
                       "meta_text": "Fully Funded PhD", "subjects": ["Artificial Intelligence", "Data Science"]})
    assert it["phd_level"] and it["score"] <= CFG["profile"]["phd_only_max_score"] and it["tier"] == "standard"
    assert sum(w[1] for w in it["why"]) == it["score"]
    both = CLF.classify({"source": "scholarshipsads", "url": "https://x.y/msphd", "title": "Fully Funded Master's and PhD Scholarship in AI at Oxford",
                         "meta_text": "Fully Funded Masters, PhD", "subjects": ["Artificial Intelligence"]})
    assert not both["phd_level"] and both["tier"] in ("high", "top")


def test_undergrad_research_bullets():
    from scraper.github_lists import parse_bullet_research_list
    raw = parse_bullet_research_list((FIX / "ug_research.md").read_text())
    titles = [r["title"] for r in raw]
    assert any("Robotics Institute for Summer Scholars" in t for t in titles)
    assert not any("IIT" in t for t in titles)                                   # "for Indian students" section skipped
    items = {i["title"]: i for i in map(CLF.classify, raw)}
    qr = next(v for k, v in items.items() if k.startswith("QRLSSP"))
    assert qr["eligibility"] == "restricted" and qr["countries"] == ["United States"]
    mbz = next(v for k, v in items.items() if "Research internship program for AI" in k)
    assert mbz["type"] == "Research" and mbz["countries"] == ["United Arab Emirates"]


def test_daad_form_discovery_and_results():
    from scraper.daad import find_option, parse_detail, parse_results
    html = (FIX / "daad_search.html").read_text()
    assert find_option(html, "Palestin") == ("origin", "152")
    assert find_option(html, CFG["sources"]["daad"]["status"]) == ("status", "2")
    res = parse_results(html)
    assert len(res) == 2 and res[0]["url"].endswith("detail=50076777")
    d = parse_detail((FIX / "daad_detail.html").read_text())
    assert d["deadline_text"].startswith("Deadline: 31 January 2027")
    raw = dict(res[0], **{k: v for k, v in d.items() if v}, countries=["Germany"], open_to_origin=True)
    it = CLF.classify(raw)
    assert it["targets_me"] and it["deadline"] == "2027-01-31" and it["english_test"] == "required" and "masters" in it["degrees"]


def test_calendar_feed_is_valid():
    from datetime import datetime, timezone
    from scraper.run import build_ics
    it = CLF.classify({"source": "scholarshipsads", "url": "https://x.y/c", "title": "ETH Zurich Excellence Scholarship & Opportunity Programme 2027, Switzerland",
                       "deadline_text": "Deadline: 30 Nov 2026", "summary": "Full master's scholarship; covers living costs, tuition waiver."})
    ics = build_ics([it], "Test", datetime(2026, 10, 29, tzinfo=timezone.utc))
    lines = ics.split("\r\n")
    assert lines[0] == "BEGIN:VCALENDAR" and "DTSTART;VALUE=DATE:20261130" in lines and lines.count("BEGIN:VALARM") == 2
    assert all(len(l.encode()) <= 75 for l in lines)
    assert "\\," in ics and "\;" in ics                                            # escaped text


def test_detail_page_text_ignores_sidebars():
    from scraper.classify import detect_requirements
    from scraper.sources import extract_article_text
    text = extract_article_text((FIX / "sa_detail.html").read_text())
    assert "medium of instruction" in text and "3.8" not in text
    r = detect_requirements(text, CFG)
    assert r["english_test"] == "not_required" and r["gpa_level"] is None
