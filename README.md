# Opportunity Radar

A self-updating website that gathers scholarships, research programmes, fellowships, master's and
PhD programmes and internships from nine sources, then **scores each one for relevance and value**,
with extra weight on research and fellowships for final-year undergraduates and master's applicants,
on STEM, data science, AI and medical AI, on full funding, and on recognisable programmes.
Available in **English and Arabic**.

It runs for free on GitHub: a scheduled job refreshes the data every hour and publishes the site to
GitHub Pages. No server, no database, no API keys.

**Sources:** Opportunities for Youth, Opportunity Portal, Scholarships Corner, ScholarshipsAds, For9a,
Foras, the [DAAD scholarship database](https://www2.daad.de/deutschland/stipendium/datenbank/en/21148-scholarship-database/)
(filtered to applicants from the Palestinian Territories), plus four curated GitHub lists:
[Research Internships for Undergraduates](https://github.com/zapplyjobs/Research-Internships-for-Undergraduates),
[Academic Research Opportunities for International Students](https://github.com/smsnobin77/Academic-research-opportunities-for-international-students),
[Zapply Internships 2027](https://github.com/zapplyjobs/Internships-2027) and
[CS Everything but Internships](https://github.com/Julian048/CS-Everything-but-Internships).
Internship data from Zapply is credited and linked as their terms require, and it is kept out of the RSS feed.

---

## What you get

**Finding things fast**
- **Numbered pages** of 10 results (or 20 or 50); the page is part of the link, so it can be shared.
- **Quick views:** Top matches, Research programmes, Fellowships, Medical AI and data, Fully funded master's,
  Paid internships, Closing within 30 days, New this week.
- **Filters:** type, level, deadline window (7 / 30 / 60 / 90 days, rolling, or a date range), destination region
  and country, field, funding, nationality-limited, year-of-study limited (e.g. "second-year only"),
  fee-charging events, recognised programmes, minimum score, date added, and source.
  Every option shows how many results it would give.
- **Active filter pills** above the results, each removable with one click.
- **Search** in English or Arabic; a minus before a word excludes it (`-mba`).
- **Sort** by best match, deadline (grouped by month), recently added, or A to Z; **detailed or compact** rows.

**Understanding each opportunity**
- **Scored 0–100.** Field match + funding + prestige + level, plus a profile for a final-year undergraduate
  heading to a master's: research programmes and fellowships score higher, as do programmes open to current
  undergraduates; scholarships for *starting* a bachelor's, PhD-only internships and programmes limited to
  first- or second-year students score lower. *High value* = 62+, *Top pick* = 78+. All tunable in `config.yaml`.
- **Yearly programmes** whose listed deadline has passed are moved to next year's cycle and marked *Expected*.
- **Details panel:** why it got its score, destination, who can apply, fields, and every site it's listed on.
- **Deadline runway:** the next 90 days of high-value deadlines (hollow dots are expected dates).
- **Duplicates merged** across sources.

**Tuned to a profile**
- Default profile: Palestinian, female, final-year Computer Science (PTUK), no IELTS yet. Anyone can set
  their own under **Profile** (nationality, gender, IELTS score); it's saved in their browser only.
- **For you** filters: open to applicants from your country, no IELTS required (or within your IELTS score),
  no very high GPA required, fully funded, programmes for women, and hide year-of-study limited programmes.
- Listings limited to other nationalities are flagged "Not open to applicants from …"; programmes aimed at
  Palestinian, Arab or MENA applicants are marked and ranked higher.
- English test (not required / IELTS minimum) and grade expectations (top grades / good grades) are read from
  listing and detail pages; well-known highly selective programmes are marked "Top grades expected".
- **PhD-only programmes are kept below "high value"** (max score 55) for now; master's and undergraduate
  research rank first. Change `phd_only_max_score` in `config.yaml` later.

**Intakes and the archive**
- **Intake** for each listing (Spring / Summer / Fall / Winter 2027, academic year 2027–28, or just 2027), read
  from the title or worked out from the next deadline for yearly programmes. Filter by year or semester, or sort
  by intake to see the list in sections.
- **Three collections:** *Open* (still accepting applications), *My list* (what you saved or are tracking,
  including closed ones) and *Archive*.
- **Lifecycle, checked every hour:**
  - *New* – added in the last 7 days.
  - *Closing soon* – deadline within 14 days (amber).
  - *Closed* – the day after its deadline it moves to the Archive, with the date the next cycle is expected.
  - *Ended* – a post whose semester or year is already over (e.g. "… 2025") goes straight to the Archive,
    with the next expected cycle.
  - *No longer listed* – a listing without a deadline that its source removed (after 75 days unseen).
  - *Reopened* – when an archived programme comes back with a new deadline it returns to Open, marked Reopened.
  - Archived items are kept for 400 days, long enough to see the next year's cycle. Internship job posts from
    Zapply are dropped instead of archived.
- **Deadline radar:** high-value deadlines in the next 90 days, plus every opportunity scoring 80+ in a
  3–12 month zone and a no-fixed-date zone.

**Keeping track**
- **My list:** Interested, Applying, Applied; hide what isn't for you (with undo). Stored in the browser only.
- **Calendar subscription:** subscribe once in Google, Apple or Outlook Calendar to `calendar.ics`
  (high-value deadlines) or `calendar-all.ics` (all deadlines); both refresh every hour, with reminders a week
  and a day before. **My list** deadlines and your own target dates download as a calendar file.
- **Application checklist** on every saved item (CV, statement of purpose, recommendation letters, transcript,
  English test, passport…, adjusted to the type), with your own items, notes and a target date; progress shows
  in My list.
- **CSV export** of the current results.
- **Live updates:** an open tab picks up new listings by itself.
- **Arabic** with a right-to-left layout; the choice is remembered. Listings keep their original language.
- Filters remembered between visits; **Copy link** shares the exact view. **RSS feed** at `/feed.xml`.
- Dark mode, mobile filter sheet, keyboard friendly (`/` focuses search).

---

## Set it up (about 5 minutes)

1. **Create a repository.** On GitHub, click **New repository**, name it `opportunity-radar`
   (public, so Pages is free), and create it empty.
2. **Upload the files.** Unzip this project and push it:
   ```bash
   cd opportunity-radar
   git init -b main
   git add .
   git commit -m "Opportunity Radar"
   git remote add origin https://github.com/<your-username>/opportunity-radar.git
   git push -u origin main
   ```
   (Or use **Add file → Upload files** on GitHub and drag the whole folder in — make sure the
   hidden `.github` folder comes along.)
3. **Turn on Pages.** Repo **Settings → Pages → Build and deployment → Source: GitHub Actions**.
4. **Run it once.** **Actions** tab → *Update opportunities and publish site* → **Run workflow**.
   The first run takes ~3 minutes (it installs a headless browser for the two JavaScript sites).
5. **Open your site** at `https://<your-username>.github.io/opportunity-radar/`.
   Optionally paste that URL into `site.base_url` in `config.yaml` (it's also detected automatically).

From then on it refreshes **every hour** (at 23 minutes past), and again whenever you edit `config.yaml`.

### How the hourly updates work
- **23 quick checks a day** read only each site's newest listings (about a minute each).
- **One deep scan a day** (at 04:23 UTC by default) reads several pages per site to catch anything older
  and to refresh deadlines. Clicking **Run workflow** in the Actions tab always does a deep scan.
- **The site is republished every hour**, so "Updated" on the page is always accurate, but a commit is
  only made when the listings actually change. Your history stays readable instead of filling with
  24 identical commits a day.
- **Pages left open update themselves.** An open tab checks for new data every 10 minutes. If new
  opportunities arrived, a bar offers to show them, and they're marked *Just added*.

Tune it in `config.yaml` under `schedule` (which hour does the deep scan, how many pages a quick check reads).
To change the frequency itself, edit the `cron` line in `.github/workflows/update.yml`:
`"23 * * * *"` is hourly, `"23 */3 * * *"` every 3 hours, `"23 4 * * *"` once a day.

> **Keep the repository public.** Public repos get unlimited free GitHub Actions minutes. A private repo
> gets 2,000 free minutes a month, and hourly runs use roughly 1,500–2,200, so for a private repo
> switch to every 2–3 hours. GitHub may also start scheduled runs a few minutes late at busy times.

> The site ships with ~50 real listings captured on 28 Oct 2026 so it isn't empty before the
> first run. The first automated run replaces and extends them with live data from all six sources.

---

## Make it yours — `config.yaml`

Everything about *what counts as interesting* lives in one file:

| Setting | What it does |
|---|---|
| `fields` | Your interest areas, each with a `weight` and keyword list. Add e.g. `quantum` or `robotics` here, or raise `medical_ai` further. |
| `funding` | Points for fully funded / paid / partial, and a penalty for fee-based events. |
| `prestige` | Names that earn a bonus. Add universities or companies you care about. |
| `profile` | Nationality, gender and IELTS score used for ranking and the default site profile; plus who the ranking is tuned for: bonuses by type (Research, Fellowship…), for programmes open to current undergraduates and for final-year students; penalties for bachelor's-entry scholarships, PhD-only roles and year-limited programmes. |
| `open_field` | Bonus for awards open to every field of study (Gates Cambridge, Rhodes…). |
| `ignore_phrases` | Phrases ignored when matching, e.g. "health insurance" so it doesn't count as a health topic. |
| `degree_bonus` | Extra points per level (master's is boosted by default). |
| `off_topic` | Small penalty for clearly unrelated areas when nothing else matched. |
| `high_value`, `top_pick` | Score thresholds for the two badges. |
| `min_score` | Anything below this isn't shown at all. |
| `sources` | Turn sources on/off, pages to read, and per-source rules (e.g. Zapply: sections, visa sponsorship only, minimum score). |
| `retention` | When items move to the archive and how long the archive keeps them. |
| `runway_shelf_min` | Minimum score for points beyond 90 days or with no fixed date on the radar (default 80). |

Commit the change and the workflow re-scores everything automatically.

---

## Run it on your computer

```bash
python -m venv .venv && source .venv/bin/activate      # Windows: .venv\Scripts\activate
pip install -r requirements.txt
python -m playwright install chromium                   # only needed for For9a and Foras
python -m scraper.run                                   # fetch + score → docs/data/opportunities.json
python -m http.server -d docs 8000                      # then open http://localhost:8000
```

Useful options: `python -m scraper.run --only scholarshipsads,opportunityportal -v`
Tests (offline, using saved sample pages): `python -m pytest -q`

---

## How it works

```
GitHub Actions (hourly: quick check; once a day: deep scan)
  └─ scraper/sources.py   fetch each site
       • WordPress REST API, falling back to RSS   → Opportunities for Youth, Opportunity Portal, Scholarships Corner
       • listing-page parser (funding, level, subjects, deadline)   → ScholarshipsAds
       • HTML + embedded JSON, headless browser if needed   → For9a
       • headless browser, reads the app's own data requests   → Foras
  └─ scraper/github_lists.py   Markdown tables from the three GitHub lists (read every hour)
  └─ scraper/classify.py  type · level · fields · funding · deadline · country · score
  └─ scraper/run.py       merge duplicates · keep history (first seen, "new") · drop expired · write JSON + RSS
  └─ commit docs/data → deploy docs/ to GitHub Pages
```

A site that fails on a given day doesn't break anything: its previous listings are kept, and
**Sources** on the site shows when each one last worked.

### Reliability notes
- **WordPress sites and ScholarshipsAds** are server-rendered and parse reliably.
- **For9a** uses bot protection on some pages, and **Foras** is a fully client-side app, so both
  go through a real headless browser. They're the most likely to need a tweak if those sites
  change their layout. Check **Sources** on your site after the first run; if one shows 0 items,
  open an issue in your repo with the Actions log and adjust the link patterns at the top of
  `For9aSource` / `ForasSource` in `scraper/sources.py`.
- Deadlines, destination countries and "who can apply" are read from the listing text. If a site
  doesn't state them, the row says so. Treat the nationality hint as a hint, and always confirm on
  the official page before applying.

### Adding another site
Write a class with a `fetch()` method that returns raw dicts (`title`, `url`, plus whatever you
have: `body`, `summary`, `deadline_text`, `categories`…), register it in `build_sources()`,
and add it to `SOURCE_META`. If the site runs WordPress, it's one line:
`WordPressSource("key", "https://example.org")`.

---

## Sharing it

- Send the Pages link — it's public and works on phones.
- Share a **filtered view**: set filters, click *Copy link to this view*.
- Point friends to `/feed.xml` for a feed of new high-value picks.
- Want a nicer address? Settings → Pages → **Custom domain**.
- Friends with different interests can **fork** the repo and edit `config.yaml` to get their own radar.

## Being a good citizen
The scraper identifies itself, pauses between requests, reads only listing pages and a few
pages per site (only the newest page on hourly checks), and always links back to the original post. Listings and summaries
belong to their sites; this tool just points you to them.
