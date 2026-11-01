(() => {
  "use strict";

  const $ = (s, el = document) => el.querySelector(s);
  const $$ = (s, el = document) => [...el.querySelectorAll(s)];
  const DAY = 86400000;
  const PREVIEW = !!window.__RADAR_PREVIEW__;

  const store = {
    get(k, d) { try { const v = localStorage.getItem(k); return v ? JSON.parse(v) : d; } catch { return d; } },
    set(k, v) { try { localStorage.setItem(k, JSON.stringify(v)); } catch {} },
  };

  const STRINGS = {
    en: {
      "site.title": "Opportunity Radar",
      "site.tagline": "Scholarships, research, fellowships and internships in STEM and AI.",
      "skip": "Skip to results", "nav.sources": "Sources", "nav.rss": "RSS feed", "nav.share": "Copy link", "lang.other": "العربية",
      "quick.label": "Quick views", "quick.top": "Top matches", "quick.research": "Research programmes", "quick.fellow": "Fellowships",
      "quick.medai": "Medical AI and data", "quick.masters": "Fully funded master's", "quick.intern": "Paid internships",
      "quick.soon": "Closing within 30 days", "quick.new": "New this week",
      "runway.title": "Deadlines", "runway.urgent": "Next 2 weeks", "runway.today": "Today",
      "runway.empty": "No high-value deadlines for these filters.", "runway.note": "{n} on the radar",
      "filters": "Filters", "clear": "Clear all", "close": "Close", "search": "Search", "search.ph": "Search",
      "show": "Show", "view.all": "All", "view.high": "High value", "view.top": "Top picks",
      "sect.type": "Type", "sect.level": "Level", "sect.deadline": "Deadline", "sect.dest": "Destination", "sect.fields": "Field",
      "sect.funding": "Funding", "sect.quality": "Eligibility and quality", "sect.added": "Added", "sect.source": "Source",
      "dl.any": "Any time", "dl.7": "Next 7 days", "dl.30": "Next 30 days", "dl.60": "Next 60 days", "dl.90": "Next 90 days",
      "dl.rolling": "Rolling", "dl.custom": "Choose dates", "from": "From", "to": "To",
      "dl.undated": "Include no deadline", "country.ph": "Find a country",
      "q.restricted": "Hide nationality-limited", "q.year": "Hide year-of-study limited", "q.fees": "Hide fee-charging events",
      "q.prestige": "Recognised programmes only", "q.min": "Minimum score", "any": "Any",
      "added.1": "Last 24 hours", "added.7": "Last 7 days", "added.30": "Last 30 days",
      "sort": "Sort", "sort.score": "Best match", "sort.deadline": "Deadline", "sort.new": "Recently added", "sort.az": "A to Z",
      "perPage": "Per page", "layout": "Layout", "dens.detailed": "Detailed", "dens.compact": "Compact", "export": "Export CSV",
      "fresh.text": "{n} new since you opened this page", "fresh.show": "Show",
      "count.hv": "{n} high value", "count.soon": "{n} closing within 2 weeks", "range": "{a}–{b} of {n}",
      "pages": "Pages", "prev": "Previous", "next": "Next", "page": "Page {n}",
      "empty.title": "No matches", "empty.remove": "Remove “{x}”", "empty.clear": "Clear all filters", "mine.empty": "Your list is empty",
      "top": "Top pick", "new": "New", "justAdded": "Just added", "via": "via {s}", "alsoOn": "+{n}", "limited": "May be limited: {x}",
      "diversity": "Diversity programme", "estimated": "Expected",
      "details": "Details", "hideDetails": "Hide details", "save": "Save", "saved": "In my list", "calendar": "Add to calendar",
      "notForMe": "Not for me", "unhide": "Unhide",
      "due.rolling": "Rolling", "due.rollingU": "apply any time", "due.none": "Not listed", "due.noneU": "check the page",
      "due.closed": "Closed", "due.today": "Today", "due.tbd": "Not announced", "due.varies": "Varies", "due.recurring": "Yearly",
      "due.expectedD": "around {d}",
      "d.why": "Why this score", "d.dest": "Destination", "d.who": "Who can apply", "d.level": "Level", "d.fields": "Fields",
      "d.listed": "Listed on", "d.dates": "Dates", "d.posted": "posted {d}", "d.added": "added {d}", "d.track": "Track",
      "d.notTracking": "Not tracking", "d.open": "Open the listing", "d.notStated": "Not stated", "d.openTo": "Open ({x})",
      "d.yearOnly": "Only for {x} students",
      "why.base": "Starting points", "why.topic": "Field match: {x}", "why.open_field": "Open to all fields",
      "why.fully_funded": "Fully funded", "why.paid": "Paid or stipend", "why.partial": "Partial funding", "why.fee_based": "Charges a fee",
      "why.prestige": "Recognised: {x}", "why.level": "{x} level", "why.type": "{x}", "why.current_undergrad": "Open to current undergraduates",
      "why.final_year": "Suits final-year students", "why.off_topic": "Outside the focus fields", "why.bachelor_degree": "For starting a bachelor's",
      "why.year_limit": "Only for {x} students", "why.phd_only": "For current PhD students", "why.not_open": "Not open to you: {x}",
      "t.saved": "Saved", "t.removed": "Removed from your list", "t.hidden": "Hidden", "t.undo": "Undo", "t.cleared": "Filters cleared",
      "t.copied": "Link copied", "t.copyFail": "Copy the link from the address bar", "t.calendar": "Calendar file downloaded",
      "t.exported": "Exported {n}", "t.latest": "Showing the latest listings", "t.marked": "Marked: {x}",
      "updated": "Updated", "loadError": "The list didn't load. Refresh the page to try again.",
      "src.listed": "{n} listed", "src.checked": "checked {x}", "src.failed": "Last check failed", "src.pending": "Not checked yet",
      "credits": "Listings from", "online": "Online",
      "year.first-year": "first-year", "year.second-year": "second-year", "year.third-year": "third-year", "year.underclass": "first- and second-year",
      "tab.open": "Open", "tab.mine": "My list", "tab.archive": "Archive", "collections": "Collections",
      "sect.intake": "Intake", "intake.none": "Not stated", "intake.groupNone": "Intake not stated", "sort.intake": "Intake",
      "season.spring": "Spring {y}", "season.summer": "Summer {y}", "season.fall": "Fall {y}", "season.winter": "Winter {y}",
      "season.ay": "{y}–{y2s}", "season.year": "{y}", "intake.expected": "expected", "d.intake": "Intake",
      "reopened": "Reopened",
      "arch.closed": "Closed", "arch.past_intake": "Ended", "arch.removed": "No longer listed",
      "arch.next": "expected again around {d}", "arch.nextIntake": "next cycle {x}",
      "arch.group": "Expected to reopen {m}", "arch.groupNone": "Reopening not known",
      "arch.loading": "Loading the archive…", "empty.archive": "Nothing in the archive yet",
      "nav.profile": "Profile", "nav.calendar": "Calendar", "runway.later": "3–12 months", "runway.nodate": "No fixed date",
      "sect.you": "For you", "profile.edit": "Edit", "you.eligible": "Open to applicants from {c}", "you.noIelts": "No IELTS required",
      "you.noIeltsScore": "No IELTS needed, or IELTS {x} is enough", "you.gpa": "No very high GPA required", "you.funded": "Fully funded",
      "you.women": "Programmes for women",
      "profile.title": "Your profile", "profile.nationality": "Nationality", "profile.gender": "Gender", "profile.female": "Female",
      "profile.male": "Male", "profile.none": "Prefer not to say", "profile.english": "IELTS score", "profile.noScore": "No score yet",
      "profile.save": "Save profile", "cancel": "Cancel", "profile.noIelts": "no IELTS yet", "profile.ielts": "IELTS {x}",
      "profile.other": "Other", "t.profileSaved": "Profile saved",
      "tag.noIelts": "No IELTS", "tag.ielts": "IELTS {x}", "tag.englishTest": "English test", "tag.topGrades": "Top grades expected",
      "tag.women": "For women", "elig.no": "Not open to applicants from {c}", "elig.match": "Open to applicants from {c}",
      "d.english": "English test", "d.englishNone": "Not required", "d.englishMin": "IELTS {x} or equivalent", "d.englishReq": "Required",
      "d.grades": "Grades", "d.gradesHigh": "Top grades expected", "d.gradesMod": "Good grades", "d.forYou": "For you",
      "why.nationality": "Open to applicants from {x}", "why.women": "Programme for women", "why.no_english_test": "No English test needed",
      "why.phd_cap": "PhD-level, kept below high value",
      "ck.title": "Checklist", "ck.cv": "CV", "ck.sop": "Statement of purpose", "ck.motivation": "Motivation letter",
      "ck.recs": "Two recommendation letters", "ck.rec": "Recommendation letter", "ck.transcript": "Transcript",
      "ck.degree": "Degree certificate or expected-graduation letter", "ck.english": "English test (IELTS or TOEFL)",
      "ck.passport": "Passport copy", "ck.form": "Application form", "ck.research": "Research interests or project choice",
      "ck.portfolio": "GitHub or portfolio link", "ck.add": "Add an item", "ck.addBtn": "Add", "ck.notes": "Notes",
      "ck.target": "My target date", "ck.progress": "{a}/{b} ready", "ck.remove": "Remove",
      "cal.title": "Calendar", "cal.high": "High-value deadlines", "cal.all": "All deadlines", "cal.google": "Add to Google Calendar",
      "cal.apple": "Apple or Outlook", "cal.copy": "Copy link", "cal.mine": "My list", "cal.download": "Download my list's deadlines",
      "t.calMine": "Downloaded {n}", "cal.empty": "Your list has no deadlines yet",
      "feed.what": "New high-value picks", "feed.feedly": "Open in Feedly", "feed.inoreader": "Open in Inoreader",
    },
    ar: {
      "site.title": "رادار الفرص",
      "site.tagline": "منح دراسية وبرامج بحثية وزمالات وتدريب في العلوم والتقنية والذكاء الاصطناعي.",
      "skip": "انتقل إلى النتائج", "nav.sources": "المصادر", "nav.rss": "خلاصة RSS", "nav.share": "نسخ الرابط", "lang.other": "English",
      "quick.label": "عروض سريعة", "quick.top": "الأنسب", "quick.research": "برامج بحثية", "quick.fellow": "زمالات",
      "quick.medai": "الذكاء الاصطناعي الطبي والبيانات", "quick.masters": "ماجستير ممول بالكامل", "quick.intern": "تدريب مدفوع",
      "quick.soon": "تُغلق خلال 30 يومًا", "quick.new": "جديد هذا الأسبوع",
      "runway.title": "المواعيد النهائية", "runway.urgent": "الأسبوعان القادمان", "runway.today": "اليوم",
      "runway.empty": "لا مواعيد لفرص عالية القيمة بهذه التصفية.", "runway.note": "{n} على الرادار",
      "filters": "التصفية", "clear": "مسح الكل", "close": "إغلاق", "search": "بحث", "search.ph": "ابحث",
      "show": "عرض", "view.all": "الكل", "view.high": "عالية القيمة", "view.top": "الأفضل",
      "sect.type": "النوع", "sect.level": "المستوى", "sect.deadline": "الموعد النهائي", "sect.dest": "الوجهة", "sect.fields": "المجال",
      "sect.funding": "التمويل", "sect.quality": "الأهلية والجودة", "sect.added": "تاريخ الإضافة", "sect.source": "المصدر",
      "dl.any": "أي وقت", "dl.7": "خلال 7 أيام", "dl.30": "خلال 30 يومًا", "dl.60": "خلال 60 يومًا", "dl.90": "خلال 90 يومًا",
      "dl.rolling": "مفتوح باستمرار", "dl.custom": "اختر التواريخ", "from": "من", "to": "إلى",
      "dl.undated": "تضمين ما ليس له موعد", "country.ph": "ابحث عن دولة",
      "q.restricted": "إخفاء المقيدة بجنسيات", "q.year": "إخفاء المقيدة بسنة دراسية", "q.fees": "إخفاء الفعاليات برسوم",
      "q.prestige": "البرامج المعروفة فقط", "q.min": "الحد الأدنى للتقييم", "any": "الكل",
      "added.1": "آخر 24 ساعة", "added.7": "آخر 7 أيام", "added.30": "آخر 30 يومًا",
      "sort": "الترتيب", "sort.score": "الأنسب", "sort.deadline": "الأقرب موعدًا", "sort.new": "الأحدث إضافة", "sort.az": "أبجديًا",
      "perPage": "لكل صفحة", "layout": "طريقة العرض", "dens.detailed": "مفصّل", "dens.compact": "مختصر", "export": "تصدير CSV",
      "fresh.text": "{n} جديدة منذ فتح الصفحة", "fresh.show": "عرض",
      "count.hv": "{n} عالية القيمة", "count.soon": "{n} تُغلق خلال أسبوعين", "range": "{a}–{b} من {n}",
      "pages": "الصفحات", "prev": "السابق", "next": "التالي", "page": "الصفحة {n}",
      "empty.title": "لا نتائج مطابقة", "empty.remove": "إزالة «{x}»", "empty.clear": "مسح كل عوامل التصفية", "mine.empty": "قائمتك فارغة",
      "top": "الأفضل", "new": "جديد", "justAdded": "أُضيفت للتو", "via": "عبر {s}", "alsoOn": "+{n}", "limited": "قد تكون مقيدة: {x}",
      "diversity": "برنامج للتنوع", "estimated": "متوقع",
      "details": "التفاصيل", "hideDetails": "إخفاء التفاصيل", "save": "حفظ", "saved": "في قائمتي", "calendar": "أضف إلى التقويم",
      "notForMe": "لا تناسبني", "unhide": "إظهار",
      "due.rolling": "مفتوح", "due.rollingU": "التقديم في أي وقت", "due.none": "غير محدد", "due.noneU": "راجع الصفحة",
      "due.closed": "مغلقة", "due.today": "اليوم", "due.tbd": "لم يُعلن", "due.varies": "متغيّر", "due.recurring": "سنوي",
      "due.expectedD": "نحو {d}",
      "d.why": "سبب التقييم", "d.dest": "الوجهة", "d.who": "من يمكنه التقديم", "d.level": "المستوى", "d.fields": "المجالات",
      "d.listed": "مدرجة في", "d.dates": "التواريخ", "d.posted": "نُشرت {d}", "d.added": "أُضيفت {d}", "d.track": "المتابعة",
      "d.notTracking": "بدون متابعة", "d.open": "فتح الإعلان", "d.notStated": "غير مذكور", "d.openTo": "مفتوحة ({x})",
      "d.yearOnly": "لطلاب {x} فقط",
      "why.base": "نقاط البداية", "why.topic": "تطابق المجال: {x}", "why.open_field": "مفتوحة لكل التخصصات",
      "why.fully_funded": "ممولة بالكامل", "why.paid": "مدفوعة أو بمكافأة", "why.partial": "تمويل جزئي", "why.fee_based": "تتطلب رسومًا",
      "why.prestige": "جهة معروفة: {x}", "why.level": "مستوى {x}", "why.type": "{x}", "why.current_undergrad": "متاحة لطلاب البكالوريوس الحاليين",
      "why.final_year": "تناسب طلاب السنة الأخيرة", "why.off_topic": "خارج المجالات المستهدفة", "why.bachelor_degree": "لبدء درجة البكالوريوس",
      "why.year_limit": "لطلاب {x} فقط", "why.phd_only": "لطلاب الدكتوراه الحاليين", "why.not_open": "غير متاحة لك: {x}",
      "t.saved": "حُفظت", "t.removed": "أُزيلت من قائمتك", "t.hidden": "أُخفيت", "t.undo": "تراجع", "t.cleared": "مُسحت عوامل التصفية",
      "t.copied": "نُسخ الرابط", "t.copyFail": "انسخ الرابط من شريط العنوان", "t.calendar": "نُزّل ملف التقويم",
      "t.exported": "صُدّرت {n}", "t.latest": "تُعرض أحدث الفرص", "t.marked": "تم التحديد: {x}",
      "updated": "آخر تحديث", "loadError": "تعذّر تحميل القائمة. حدّث الصفحة للمحاولة مجددًا.",
      "src.listed": "{n} مدرجة", "src.checked": "فُحصت {x}", "src.failed": "فشل آخر فحص", "src.pending": "لم يُفحص بعد",
      "credits": "الفرص مأخوذة من", "online": "عن بُعد",
      "year.first-year": "السنة الأولى", "year.second-year": "السنة الثانية", "year.third-year": "السنة الثالثة", "year.underclass": "السنتين الأولى والثانية",
      "tab.open": "مفتوحة", "tab.mine": "قائمتي", "tab.archive": "الأرشيف", "collections": "المجموعات",
      "sect.intake": "موعد البدء", "intake.none": "غير مذكور", "intake.groupNone": "موعد البدء غير مذكور", "sort.intake": "موعد البدء",
      "season.spring": "ربيع {y}", "season.summer": "صيف {y}", "season.fall": "خريف {y}", "season.winter": "شتاء {y}",
      "season.ay": "{y}–{y2}", "season.year": "{y}", "intake.expected": "متوقع", "d.intake": "موعد البدء",
      "reopened": "أُعيد فتحها",
      "arch.closed": "أُغلقت", "arch.past_intake": "انتهت", "arch.removed": "لم تعد مدرجة",
      "arch.next": "متوقع مجددًا نحو {d}", "arch.nextIntake": "الدورة القادمة {x}",
      "arch.group": "يُتوقع فتحها في {m}", "arch.groupNone": "موعد إعادة الفتح غير معروف",
      "arch.loading": "جارٍ تحميل الأرشيف…", "empty.archive": "لا شيء في الأرشيف بعد",
      "nav.profile": "ملفي", "nav.calendar": "التقويم", "runway.later": "3–12 شهرًا", "runway.nodate": "دون موعد محدد",
      "sect.you": "لك", "profile.edit": "تعديل", "you.eligible": "متاحة للمتقدمين من {c}", "you.noIelts": "دون اشتراط IELTS",
      "you.noIeltsScore": "دون IELTS، أو تكفي درجة {x}", "you.gpa": "دون اشتراط معدل مرتفع جدًا", "you.funded": "ممولة بالكامل",
      "you.women": "برامج للنساء",
      "profile.title": "ملفك الشخصي", "profile.nationality": "الجنسية", "profile.gender": "الجنس", "profile.female": "أنثى",
      "profile.male": "ذكر", "profile.none": "أفضّل عدم الذكر", "profile.english": "درجة IELTS", "profile.noScore": "لا توجد درجة بعد",
      "profile.save": "حفظ الملف", "cancel": "إلغاء", "profile.noIelts": "دون IELTS بعد", "profile.ielts": "IELTS {x}",
      "profile.other": "أخرى", "t.profileSaved": "حُفظ الملف",
      "tag.noIelts": "دون IELTS", "tag.ielts": "IELTS {x}", "tag.englishTest": "اختبار إنجليزي", "tag.topGrades": "معدل مرتفع مطلوب",
      "tag.women": "للنساء", "elig.no": "غير متاحة للمتقدمين من {c}", "elig.match": "متاحة للمتقدمين من {c}",
      "d.english": "اختبار اللغة الإنجليزية", "d.englishNone": "غير مطلوب", "d.englishMin": "IELTS {x} أو ما يعادله", "d.englishReq": "مطلوب",
      "d.grades": "المعدل", "d.gradesHigh": "يتطلب معدلًا مرتفعًا جدًا", "d.gradesMod": "معدل جيد", "d.forYou": "لك",
      "why.nationality": "متاحة للمتقدمين من {x}", "why.women": "برنامج للنساء", "why.no_english_test": "لا يتطلب اختبار لغة",
      "why.phd_cap": "مستوى دكتوراه، أُبقي دون عالية القيمة",
      "ck.title": "قائمة التجهيز", "ck.cv": "السيرة الذاتية", "ck.sop": "بيان الغرض", "ck.motivation": "رسالة الدافع",
      "ck.recs": "رسالتا توصية", "ck.rec": "رسالة توصية", "ck.transcript": "كشف العلامات",
      "ck.degree": "شهادة التخرج أو إفادة التخرج المتوقع", "ck.english": "اختبار اللغة (IELTS أو TOEFL)",
      "ck.passport": "نسخة جواز السفر", "ck.form": "نموذج التقديم", "ck.research": "الاهتمامات البحثية أو اختيار المشروع",
      "ck.portfolio": "رابط GitHub أو ملف الأعمال", "ck.add": "أضف بندًا", "ck.addBtn": "إضافة", "ck.notes": "ملاحظات",
      "ck.target": "موعدي المستهدف", "ck.progress": "{a}/{b} جاهزة", "ck.remove": "حذف",
      "cal.title": "التقويم", "cal.high": "مواعيد الفرص عالية القيمة", "cal.all": "كل المواعيد", "cal.google": "إضافة إلى تقويم Google",
      "cal.apple": "Apple أو Outlook", "cal.copy": "نسخ الرابط", "cal.mine": "قائمتي", "cal.download": "تنزيل مواعيد قائمتي",
      "t.calMine": "نُزّلت {n}", "cal.empty": "لا مواعيد في قائمتك بعد",
      "feed.what": "أحدث الفرص عالية القيمة", "feed.feedly": "فتح في Feedly", "feed.inoreader": "فتح في Inoreader",
    },
  };

  const NOUNS = {
    en: {
      opportunity: { one: "{n} opportunity", other: "{n} opportunities" },
      result: { one: "Show {n} result", other: "Show {n} results" },
      dayLeft: { one: "day left", other: "days left" },
    },
    ar: {
      opportunity: { zero: "لا فرص", one: "فرصة واحدة", two: "فرصتان", few: "{n} فرص", many: "{n} فرصة", other: "{n} فرصة" },
      result: { zero: "لا نتائج", one: "عرض نتيجة واحدة", two: "عرض نتيجتين", few: "عرض {n} نتائج", many: "عرض {n} نتيجة", other: "عرض {n} نتيجة" },
      dayLeft: { zero: "يوم متبقٍ", one: "يوم متبقٍ", two: "يومان متبقيان", few: "أيام متبقية", many: "يومًا متبقيًا", other: "يوم متبقٍ" },
    },
  };

  const LABELS = {
    en: {
      type: { Research: "Research", Scholarship: "Scholarship", Fellowship: "Fellowship", Internship: "Internship", "Summer school": "Summer school",
        Exchange: "Exchange", Competition: "Competition", Course: "Course", Conference: "Conference", Grant: "Grant", Job: "Job",
        Volunteering: "Volunteering", Externship: "Externship", Mentorship: "Mentorship", Opportunity: "Other" },
      degree: { bachelor: "Bachelor's", masters: "Master's", phd: "PhD", postdoc: "Postdoc" },
      funding: { fully_funded: "Fully funded", paid: "Paid or stipend", partial: "Partial funding", fee_based: "Charges a fee", none: "Not stated" },
      status: { interested: "Interested", applying: "Applying", applied: "Applied", hidden: "Hidden" },
      region: { "Europe": "Europe", "North America": "North America", "Middle East & North Africa": "Middle East & North Africa", "Asia": "Asia",
        "Oceania": "Oceania", "Sub-Saharan Africa": "Sub-Saharan Africa", "Latin America": "Latin America", "Online": "Online" },
      field: {},
    },
    ar: {
      type: { Research: "بحث علمي", Scholarship: "منحة دراسية", Fellowship: "زمالة", Internship: "تدريب", "Summer school": "مدرسة صيفية",
        Exchange: "تبادل طلابي", Competition: "مسابقة", Course: "دورة", Conference: "مؤتمر", Grant: "منحة تمويل", Job: "وظيفة",
        Volunteering: "تطوع", Externship: "برنامج تعريفي", Mentorship: "إرشاد", Opportunity: "أخرى" },
      degree: { bachelor: "بكالوريوس", masters: "ماجستير", phd: "دكتوراه", postdoc: "ما بعد الدكتوراه" },
      funding: { fully_funded: "ممولة بالكامل", paid: "مدفوعة أو بمكافأة", partial: "تمويل جزئي", fee_based: "برسوم", none: "غير مذكور" },
      status: { interested: "مهتم", applying: "أقدّم", applied: "قدّمت", hidden: "مخفية" },
      region: { "Europe": "أوروبا", "North America": "أمريكا الشمالية", "Middle East & North Africa": "الشرق الأوسط وشمال أفريقيا", "Asia": "آسيا",
        "Oceania": "أوقيانوسيا", "Sub-Saharan Africa": "أفريقيا جنوب الصحراء", "Latin America": "أمريكا اللاتينية", "Online": "عن بُعد" },
      field: { medical_ai: "الذكاء الاصطناعي الطبي", ai_ml: "الذكاء الاصطناعي وتعلم الآلة", data_science: "علم البيانات",
        computing: "علوم الحاسوب", biomed: "العلوم الطبية الحيوية", health: "الطب والصحة", engineering: "الهندسة", science: "العلوم والرياضيات" },
    },
  };

  const ISO = {
    "United Kingdom": "GB", "Germany": "DE", "France": "FR", "Netherlands": "NL", "Belgium": "BE", "Switzerland": "CH", "Austria": "AT",
    "Sweden": "SE", "Norway": "NO", "Denmark": "DK", "Finland": "FI", "Iceland": "IS", "Ireland": "IE", "Italy": "IT", "Spain": "ES",
    "Portugal": "PT", "Poland": "PL", "Czech Republic": "CZ", "Hungary": "HU", "Greece": "GR", "Cyprus": "CY", "Malta": "MT",
    "Estonia": "EE", "Latvia": "LV", "Lithuania": "LT", "Luxembourg": "LU", "Romania": "RO", "Bulgaria": "BG", "Croatia": "HR",
    "Slovenia": "SI", "Slovakia": "SK", "Serbia": "RS", "Turkey": "TR", "United States": "US", "Canada": "CA", "Mexico": "MX",
    "Saudi Arabia": "SA", "United Arab Emirates": "AE", "Qatar": "QA", "Kuwait": "KW", "Oman": "OM", "Bahrain": "BH", "Jordan": "JO",
    "Lebanon": "LB", "Palestine": "PS", "Egypt": "EG", "Morocco": "MA", "Tunisia": "TN", "Algeria": "DZ", "Iraq": "IQ", "Israel": "IL",
    "China": "CN", "Hong Kong": "HK", "Taiwan": "TW", "Japan": "JP", "South Korea": "KR", "Singapore": "SG", "Malaysia": "MY",
    "Thailand": "TH", "Indonesia": "ID", "Vietnam": "VN", "Philippines": "PH", "India": "IN", "Pakistan": "PK", "Bangladesh": "BD",
    "Kazakhstan": "KZ", "Russia": "RU", "Australia": "AU", "New Zealand": "NZ", "South Africa": "ZA", "Kenya": "KE", "Nigeria": "NG",
    "Ghana": "GH", "Rwanda": "RW", "Ethiopia": "ET", "Uganda": "UG", "Tanzania": "TZ", "Brazil": "BR", "Chile": "CL", "Argentina": "AR",
    "Colombia": "CO", "Peru": "PE",
  };

  const SOURCE_NAMES = {
    opportunitiesforyouth: "Opportunities for Youth", opportunityportal: "Opportunity Portal", scholarshipscorner: "Scholarships Corner",
    scholarshipsads: "ScholarshipsAds", for9a: "For9a", foras: "Foras", researchlist: "Academic Research Opportunities",
    zapply: "Zapply Internships 2027", csprograms: "CS Everything but Internships",
    ugresearch: "Research Internships for Undergraduates", daad: "DAAD Scholarship Database",
  };
  const SOURCE_HOME = {
    opportunitiesforyouth: "https://opportunitiesforyouth.org/", opportunityportal: "https://opportunityportal.info/",
    scholarshipscorner: "https://scholarshipscorner.website/", scholarshipsads: "https://www.scholarshipsads.com/",
    for9a: "https://www.for9a.com/en", foras: "https://foras.ps/home",
    researchlist: "https://github.com/smsnobin77/Academic-research-opportunities-for-international-students",
    zapply: "https://github.com/zapplyjobs/Internships-2027", csprograms: "https://github.com/Julian048/CS-Everything-but-Internships",
    ugresearch: "https://github.com/zapplyjobs/Research-Internships-for-Undergraduates",
    daad: "https://www2.daad.de/deutschland/stipendium/datenbank/en/21148-scholarship-database/",
  };
  const activeSources = () => DATA?.sources ? Object.keys(SOURCE_NAMES).filter(k => k in DATA.sources) : [];
  const AI_FIELDS = new Set(["medical_ai", "ai_ml", "data_science"]);
  const TYPE_ORDER = ["Research", "Fellowship", "Scholarship", "Internship", "Summer school", "Exchange", "Externship", "Mentorship",
    "Competition", "Course", "Conference", "Grant", "Job", "Volunteering", "Opportunity"];
  const REGION_ORDER = ["Europe", "North America", "Middle East & North Africa", "Asia", "Oceania", "Sub-Saharan Africa", "Latin America", "Online"];
  const YEAR_KEY = { "first-year": "first-year", "1st-year": "first-year", freshman: "first-year", freshmen: "first-year",
    "second-year": "second-year", "2nd-year": "second-year", sophomore: "second-year", sophomores: "second-year",
    "third-year": "third-year", "3rd-year": "third-year", junior: "third-year", juniors: "third-year",
    underclassmen: "underclass", underclassman: "underclass", underclasswomen: "underclass" };

  let lang = store.get("radar:lang", null) || ((navigator.language || "").toLowerCase().startsWith("ar") ? "ar" : "en");
  let locale, fmtDate, fmtShort, fmtMonth, rtf, nf, plurals, regionNames;
  let arRegionNames = null;
  try { arRegionNames = new Intl.DisplayNames(["ar"], { type: "region" }); } catch {}

  function setupLocale() {
    locale = lang === "ar" ? "ar-u-nu-latn" : "en-GB";
    fmtDate = new Intl.DateTimeFormat(locale, { day: "numeric", month: "short", year: "numeric" });
    fmtShort = new Intl.DateTimeFormat(locale, { day: "numeric", month: "short" });
    fmtMonth = new Intl.DateTimeFormat(locale, { month: "long", year: "numeric" });
    rtf = new Intl.RelativeTimeFormat(locale, { numeric: "auto" });
    nf = new Intl.NumberFormat(locale);
    plurals = new Intl.PluralRules(lang);
    regionNames = lang === "ar" ? arRegionNames : null;
  }

  const t = (key, vars = {}) => {
    const s = STRINGS[lang][key] ?? STRINGS.en[key] ?? key;
    return s.replace(/\{(\w+)\}/g, (_, k) => vars[k] ?? "");
  };
  const tn = (noun, n) => {
    const forms = NOUNS[lang][noun];
    return (forms[plurals.select(n)] ?? forms.other).replace("{n}", nf.format(n));
  };
  const SEP = () => (lang === "ar" ? "، " : ", ");
  const L = (group, key) => LABELS[lang][group]?.[key] ?? LABELS.en[group]?.[key] ?? (group === "field" ? FIELD_LABELS[key] : null) ?? key;
  const countryName = c => {
    if (c === "Online") return t("online");
    if (!regionNames || !ISO[c]) return c;
    try { return regionNames.of(ISO[c]) || c; } catch { return c; }
  };
  const yearLabel = y => t("year." + (YEAR_KEY[y] || "second-year"));

  const DEMONYMS = {
    Palestine: ["palestinian", "palestine", "west bank", "gaza"], Jordan: ["jordanian", "jordan"], Egypt: ["egyptian", "egypt"],
    Lebanon: ["lebanese", "lebanon"], Syria: ["syrian", "syria"], Iraq: ["iraqi", "iraq"], "Saudi Arabia": ["saudi"],
    "United Arab Emirates": ["emirati", "uae"], Qatar: ["qatari", "qatar"], Kuwait: ["kuwaiti"], Oman: ["omani"], Bahrain: ["bahraini"],
    Yemen: ["yemeni", "yemen"], Morocco: ["moroccan", "morocco"], Tunisia: ["tunisian", "tunisia"], Algeria: ["algerian", "algeria"],
    Libya: ["libyan", "libya"], Sudan: ["sudanese", "sudan"], Turkey: ["turkish", "türkiye"], Pakistan: ["pakistani"], India: ["indian"],
    Bangladesh: ["bangladeshi"], Indonesia: ["indonesian"], Malaysia: ["malaysian"], Nigeria: ["nigerian"], Kenya: ["kenyan"],
    Ghana: ["ghanaian"], Ethiopia: ["ethiopian"], "South Africa": ["south african"], "United States": ["u.s.", "us citizens", "american", "united states", "us institution", "u.s. college"],
    "United Kingdom": ["uk", "british"], Canada: ["canadian"], Sweden: ["swedish"], Germany: ["german"], France: ["french"],
    Brazil: ["brazilian"], Mexico: ["mexican"], China: ["chinese"], Japan: ["japanese"], "South Korea": ["korean"],
  };
  const ARAB = ["Palestine", "Jordan", "Egypt", "Lebanon", "Syria", "Iraq", "Saudi Arabia", "United Arab Emirates", "Qatar", "Kuwait", "Oman",
    "Bahrain", "Yemen", "Morocco", "Tunisia", "Algeria", "Libya", "Sudan"];
  const NATIONALITIES = [...new Set([...Object.keys(ISO), ...Object.keys(DEMONYMS)])];
  let profile = null;
  const defaultProfile = () => ({ nationality: DATA?.profile?.nationality || "Palestine", gender: DATA?.profile?.gender ?? "female",
    english: DATA?.profile?.english_score ?? null });
  function natTerms(nat) {
    const terms = [...(DEMONYMS[nat] || []), nat.toLowerCase()];
    if (ARAB.includes(nat)) terms.push("arab", "mena", "middle east", "developing countr");
    else if (["Asia", "Sub-Saharan Africa", "Latin America"].includes(REGION_OF[nat])) terms.push("developing countr");
    if (REGION_OF[nat] === "Sub-Saharan Africa") terms.push("african");
    return terms;
  }
  const REGION_OF = {};
  function eligibilityFor(it) {
    const nat = profile?.nationality;
    if (!nat) return null;
    const terms = natTerms(nat);
    const has = txt => terms.some(term => txt.includes(term));
    if (it.eligibility === "restricted") return has((it.eligibility_note || "").toLowerCase()) ? "match" : "no";
    if (nat === (DATA?.profile?.nationality || "Palestine") && it.targets_me) return "match";
    if (nat !== (DATA?.profile?.nationality || "Palestine") && has(`${it.title} ${it.summary || ""}`.toLowerCase())) return "match";
    return null;
  }
  const englishOk = it => it.english_test === "not_required" || (profile?.english && it.english_min && it.english_min <= profile.english);
  const ago = iso => {
    const mins = Math.round((new Date(iso) - Date.now()) / 60000);
    if (Math.abs(mins) < 60) return rtf.format(Math.min(mins, -1), "minute");
    const h = Math.round(mins / 60);
    if (Math.abs(h) < 36) return rtf.format(h, "hour");
    return rtf.format(Math.round(h / 24), "day");
  };

  let DATA = null, ITEMS = [], ARCHIVE = [], FIELD_LABELS = {};
  let archiveState = "idle";
  let today = startOfDay(new Date());
  let perPage = store.get("radar:perPage", 10);
  let density = store.get("radar:density", "detailed");
  let status = store.get("radar:status", {});
  for (const id of store.get("radar:saved", [])) if (!status[id]) status[id] = "interested";
  const saveStatus = () => store.set("radar:status", status);
  const expandedIds = new Set();
  const justAdded = new Set();
  let pending = null, lastCheck = Date.now(), currentList = [];

  const defaults = () => ({
    tab: "open", q: "", view: "all", mine: [], fields: [], type: [], degree: [], funding: [], source: [], countries: [], regions: [],
    intakes: [], intakeYears: [], dl: "any", from: "", to: "", includeUndated: false,
    minScore: 0, prestige: false, eligibleOnly: false, noIelts: false, noHighGpa: false, fullyFunded: false, womenOnly: false,
    hideYear: false, hideFees: true, added: "any",
    sort: "score", page: 1,
  });
  let state = defaults();
  const SHORT = { tab: "tb", q: "q", view: "v", mine: "my", fields: "f", type: "t", degree: "l", funding: "m", source: "s", countries: "c", regions: "r",
    intakes: "in", intakeYears: "iy", dl: "d", from: "df", to: "dt", includeUndated: "u", minScore: "min", prestige: "p",
    eligibleOnly: "el", noIelts: "ni", noHighGpa: "ng", fullyFunded: "ff", womenOnly: "wo",
    hideYear: "hy", hideFees: "hf", added: "a", sort: "o", page: "pg" };

  function encodeState(s) {
    const d = defaults(), p = new URLSearchParams();
    for (const [k, short] of Object.entries(SHORT)) {
      const v = s[k], dv = d[k];
      if (Array.isArray(v)) { if (v.length) p.set(short, v.join(",")); }
      else if (typeof v === "boolean") { if (v !== dv) p.set(short, v ? "1" : "0"); }
      else if (v !== dv && v !== "") p.set(short, String(v));
    }
    return p.toString();
  }
  function decodeState(str) {
    const s = defaults(), p = new URLSearchParams(str);
    for (const [k, short] of Object.entries(SHORT)) {
      if (!p.has(short)) continue;
      const raw = p.get(short);
      if (Array.isArray(s[k])) s[k] = raw ? raw.split(",") : [];
      else if (typeof s[k] === "boolean") s[k] = raw === "1";
      else if (typeof s[k] === "number") s[k] = Math.max(Number(raw) || 0, k === "page" ? 1 : 0);
      else s[k] = raw;
    }
    if (s.view === "mine") { s.view = "all"; s.tab = "mine"; }
    if (p.get("hr") === "1") s.eligibleOnly = true;
    if (!["open", "mine", "archive"].includes(s.tab)) s.tab = "open";
    return s;
  }
  function persist() {
    const enc = encodeState(state);
    try { history.replaceState(null, "", enc ? "#" + enc : location.pathname + location.search); } catch {}
    store.set("radar:last", encodeState({ ...state, page: 1 }));
  }

  function startOfDay(d) { const x = new Date(d); x.setHours(0, 0, 0, 0); return x; }
  function parseDay(iso) { const [y, m, d] = iso.slice(0, 10).split("-").map(Number); return new Date(y, m - 1, d); }
  const displayTitle = s => s.replace(/\s*\|\s*/g, " – ");
  function el(tag, cls, text) {
    const e = document.createElement(tag);
    if (cls) e.className = cls;
    if (text != null) e.textContent = text;
    return e;
  }
  const auto = e => { e.dir = "auto"; return e; };

  function deadlineOk(it, s) {
    const dl = it._days;
    if (s.tab === "archive") return true;
    if (s.tab === "open" && dl !== null && dl < 0) return false;
    if (s.dl === "any") return true;
    if (s.dl === "rolling") return dl === null && (it.rolling || it.deadline_note === "rolling");
    if (dl === null) return s.includeUndated;
    if (s.dl === "custom") {
      const ts = parseDay(it.deadline).getTime();
      if (s.from && ts < parseDay(s.from).getTime()) return false;
      if (s.to && ts > parseDay(s.to).getTime()) return false;
      return true;
    }
    return dl >= 0 && dl <= Number(s.dl);
  }

  function pool(s = state) {
    if (s.tab === "archive") return ARCHIVE;
    if (s.tab === "mine") return [...ITEMS, ...ARCHIVE].filter(it => status[it.id]);
    return ITEMS;
  }

  function matches(it, s, ignore) {
    const st = status[it.id];
    if (s.tab === "mine") {
      if (!st) return false;
      if (ignore !== "mine" && s.mine.length && !s.mine.includes(st)) return false;
      if (ignore !== "mine" && !s.mine.includes("hidden") && st === "hidden") return false;
    } else if (st === "hidden") return false;
    if (s.view === "high" && it.tier === "standard") return false;
    if (s.view === "top" && it.tier !== "top") return false;
    if (ignore !== "dl" && !deadlineOk(it, s)) return false;
    if (ignore === "dl" && s.tab === "open" && it._days !== null && it._days < 0) return false;
    if (it.score < s.minScore) return false;
    if (s.prestige && !it.prestige) return false;
    if (s.eligibleOnly && it._elig === "no") return false;
    if (s.noIelts && !englishOk(it)) return false;
    if (s.noHighGpa && it.gpa_level === "high") return false;
    if (s.fullyFunded && it.funding !== "fully_funded") return false;
    if (s.womenOnly && !it.for_women) return false;
    if (s.hideYear && it.year_limit) return false;
    if (s.hideFees && it.funding === "fee_based" && ignore !== "funding" && !s.funding.includes("fee_based")) return false;
    if (s.tab !== "archive" && s.added !== "any" && (it._addedDays === null || it._addedDays > Number(s.added))) return false;
    if (ignore !== "fields" && s.fields.length && !s.fields.some(f => it.fields.includes(f))) return false;
    if (ignore !== "type" && s.type.length && !s.type.includes(it.type)) return false;
    if (ignore !== "degree" && s.degree.length && !s.degree.some(d => it.degrees.includes(d))) return false;
    if (ignore !== "funding" && s.funding.length && !s.funding.includes(it.funding || "none")) return false;
    if (ignore !== "source" && s.source.length && !it._sources.some(x => s.source.includes(x))) return false;
    if (ignore !== "intakeYears" && s.intakeYears.length && !it._intakeYears.some(y => s.intakeYears.includes(y))) return false;
    if (ignore !== "intakes" && s.intakes.length && !s.intakes.some(k => k === "none" ? !it.intakes.length : it.intakes.includes(k))) return false;
    if (ignore !== "dest" && (s.countries.length || s.regions.length)) {
      const okC = s.countries.some(c => it.countries.includes(c));
      const okR = s.regions.some(r => it.regions.includes(r));
      if (!okC && !okR) return false;
    }
    if (s.q) {
      for (const w of s.q.toLowerCase().split(/\s+/).filter(Boolean)) {
        if (w.startsWith("-") && w.length > 1) { if (it._hay.includes(w.slice(1))) return false; }
        else if (!it._hay.includes(w)) return false;
      }
    }
    return true;
  }

  const dayKey = x => {
    const d = x._archived ? x._reopenDays : x._days;
    return d === null ? 1e6 : d < 0 ? 2e6 - d : d;
  };
  const byDeadline = (a, b) => dayKey(a) - dayKey(b) || b.score - a.score;
  const SORTS = {
    score: (a, b) => (a._no - b._no) || b.score - a.score || byDeadline(a, b),
    deadline: byDeadline,
    intake: (a, b) => a._intakeOrder - b._intakeOrder || b.score - a.score,
    new: (a, b) => (b._archived ? (b.archived_at || "").localeCompare(a.archived_at || "") : 0)
      || (b.first_seen || "").localeCompare(a.first_seen || "") || (b.published || "").localeCompare(a.published || "") || b.score - a.score,
    az: (a, b) => a._title.localeCompare(b._title, locale),
  };

  const INTAKE_ORDER = { "": 1, spring: 2, summer: 4, ay: 5, fall: 6, winter: 8 };
  const intakeOrder = k => { const [y, part = ""] = k.split("-"); return Number(y) * 10 + (INTAKE_ORDER[part] ?? 1); };
  function intakeLabel(k) {
    const [y, part = ""] = k.split("-");
    if (part === "ay") return t("season.ay", { y, y2: String(Number(y) + 1), y2s: String(Number(y) + 1).slice(2) });
    if (!part) return t("season.year", { y });
    return t("season." + part, { y });
  }

  const QUICK = [
    { id: "top", set: { view: "high" } },
    { id: "research", set: { type: ["Research"] } },
    { id: "fellow", set: { type: ["Fellowship"] } },
    { id: "medai", set: { fields: ["medical_ai", "ai_ml", "data_science"] } },
    { id: "masters", set: { degree: ["masters"], funding: ["fully_funded"] } },
    { id: "intern", set: { type: ["Internship"], funding: ["fully_funded", "paid"] } },
    { id: "soon", set: { dl: "30", sort: "deadline" } },
    { id: "new", set: { added: "7", sort: "new" } },
  ];
  const quickActive = q => Object.entries(q.set).every(([k, v]) =>
    Array.isArray(v) ? v.length === state[k].length && v.every(x => state[k].includes(x)) : state[k] === v);

  function renderQuick() {
    $("#quick").replaceChildren(...QUICK.map(q => {
      const on = quickActive(q);
      const b = el("button", "quick-btn", t("quick." + q.id));
      b.type = "button";
      b.setAttribute("aria-pressed", String(on));
      b.append(el("em", null, nf.format(ITEMS.filter(it => matches(it, { ...defaults(), ...q.set })).length)));
      b.addEventListener("click", () => { state = on ? defaults() : { ...defaults(), ...q.set }; syncControls(); update(); ensureArchive(); });
      return b;
    }));
  }

  function counts(ignore, getter) {
    const m = new Map();
    for (const it of pool()) if (matches(it, state, ignore)) for (const v of getter(it)) m.set(v, (m.get(v) || 0) + 1);
    return m;
  }
  function toggleIn(key, value, on) {
    state[key] = on ? [...new Set([...state[key], value])] : state[key].filter(v => v !== value);
    state.page = 1;
    update();
  }
  function chip(key, value, label, count, extra = "") {
    const wrap = el("label", "chip" + extra);
    const input = document.createElement("input");
    input.type = "checkbox"; input.value = value; input.checked = state[key].includes(value);
    input.id = `chip-${key}-${String(value).replace(/\W+/g, "-")}`;
    wrap.htmlFor = input.id;
    input.addEventListener("change", () => toggleIn(key, value, input.checked));
    const span = el("span", null, label);
    span.append(el("em", null, nf.format(count)));
    wrap.append(input, span);
    return wrap;
  }
  function renderChipGroup(id, key, options, getter, ignore = key, cls = () => "") {
    const c = counts(ignore, getter);
    $("#" + id).replaceChildren(...options.filter(([v]) => c.get(v) || state[key].includes(v))
      .map(([v, label]) => chip(key, v, label, c.get(v) || 0, cls(v))));
  }
  function renderCountries() {
    const c = counts("dest", it => it.countries);
    const q = $("#countryQ").value.trim().toLowerCase();
    const list = [...c.keys(), ...state.countries.filter(x => !c.has(x))]
      .filter(name => !q || name.toLowerCase().includes(q) || countryName(name).toLowerCase().includes(q))
      .sort((a, b) => (state.countries.includes(b) - state.countries.includes(a)) || (c.get(b) || 0) - (c.get(a) || 0)
        || countryName(a).localeCompare(countryName(b), locale));
    $("#f-countries").replaceChildren(...list.map(name => {
      const id = "ctry-" + name.replace(/\W+/g, "-");
      const lab = el("label", "check");
      lab.htmlFor = id;
      const input = document.createElement("input");
      input.type = "checkbox"; input.id = id; input.checked = state.countries.includes(name);
      input.addEventListener("change", () => toggleIn("countries", name, input.checked));
      lab.append(input, el("span", null, countryName(name)), el("em", null, nf.format(c.get(name) || 0)));
      return lab;
    }));
  }
  function renderFacets() {
    renderChipGroup("f-type", "type", [...new Set(pool().map(i => i.type))].sort((a, b) => TYPE_ORDER.indexOf(a) - TYPE_ORDER.indexOf(b))
      .map(v => [v, L("type", v)]), it => [it.type]);
    renderChipGroup("f-degree", "degree", ["bachelor", "masters", "phd", "postdoc"].map(v => [v, L("degree", v)]), it => it.degrees);
    renderChipGroup("f-fields", "fields", Object.keys(FIELD_LABELS).map(v => [v, L("field", v)]), it => it.fields, "fields",
      v => AI_FIELDS.has(v) ? " ai" : "");
    renderChipGroup("f-funding", "funding", ["fully_funded", "paid", "partial", "fee_based", "none"].map(v => [v, L("funding", v)]),
      it => [it.funding || "none"]);
    renderChipGroup("f-source", "source", activeSources().map(k => [k, SOURCE_NAMES[k]]), it => it._sources);
    renderChipGroup("f-regions", "regions", REGION_ORDER.map(r => [r, L("region", r)]), it => it.regions, "dest");
    renderChipGroup("f-status", "mine", Object.keys(LABELS.en.status).map(v => [v, L("status", v)]),
      it => status[it.id] ? [status[it.id]] : [], "mine");
    const years = [...new Set(pool().flatMap(i => i._intakeYears))].sort();
    renderChipGroup("f-intakeYears", "intakeYears", years.map(y => [y, y]), it => it._intakeYears);
    const keys = [...new Set(pool().flatMap(i => i.intakes))].filter(k => k.includes("-")).sort((a, b) => intakeOrder(a) - intakeOrder(b));
    renderChipGroup("f-intakes", "intakes", [...keys.map(k => [k, intakeLabel(k)]), ["none", t("intake.none")]],
      it => it.intakes.length ? it.intakes : ["none"]);
    renderCountries();
    $("#f-status").hidden = state.tab !== "mine";
    renderTabs();
    for (const em of $$("[data-dl]")) em.textContent = nf.format(pool().filter(it => matches(it, { ...state, dl: em.dataset.dl, includeUndated: false })).length);
    const badge = (id, n) => { $("#" + id).textContent = n ? nf.format(n) : ""; };
    badge("b-deadline", (state.dl !== "any" ? 1 : 0) + (state.includeUndated ? 1 : 0));
    badge("b-intake", state.intakes.length + state.intakeYears.length);
    badge("b-dest", state.countries.length + state.regions.length);
    badge("b-fields", state.fields.length);
    badge("b-degree", state.degree.length);
    badge("b-type", state.type.length);
    badge("b-funding", state.funding.length);
    badge("b-quality", (state.minScore ? 1 : 0) + (state.prestige ? 1 : 0) + (state.hideFees ? 0 : 1));
    badge("b-you", ["eligibleOnly", "noIelts", "noHighGpa", "fullyFunded", "womenOnly", "hideYear"].filter(k => state[k]).length);
    renderProfileLine();
    badge("b-added", state.added !== "any" ? 1 : 0);
    badge("b-source", state.source.length);
  }

  function activePills() {
    const out = [];
    const add = (label, clear) => out.push({ label, clear });
    const drop = (key, v) => () => { state[key] = state[key].filter(x => x !== v); };
    if (state.q) add(`${t("search")}: ${state.q}`, () => { state.q = ""; });
    if (state.view !== "all") add(t("view." + state.view), () => { state.view = "all"; });
    for (const m of state.mine) add(L("status", m), drop("mine", m));
    if (state.dl !== "any") {
      const lab = state.dl === "custom"
        ? `${state.from ? fmtShort.format(parseDay(state.from)) : "…"} – ${state.to ? fmtShort.format(parseDay(state.to)) : "…"}`
        : t("dl." + state.dl);
      add(lab, () => { state.dl = "any"; state.from = state.to = ""; });
    }
    if (state.includeUndated && state.dl !== "any") add(t("dl.undated"), () => { state.includeUndated = false; });
    for (const y of state.intakeYears) add(y, drop("intakeYears", y));
    for (const k of state.intakes) add(k === "none" ? `${t("sect.intake")}: ${t("intake.none")}` : intakeLabel(k), drop("intakes", k));
    for (const v of state.type) add(L("type", v), drop("type", v));
    for (const v of state.degree) add(L("degree", v), drop("degree", v));
    for (const r of state.regions) add(L("region", r), drop("regions", r));
    for (const c of state.countries) add(countryName(c), drop("countries", c));
    for (const f of state.fields) add(L("field", f), drop("fields", f));
    for (const v of state.funding) add(L("funding", v), drop("funding", v));
    if (state.minScore) add(`${t("q.min")} ${nf.format(state.minScore)}`, () => { state.minScore = 0; });
    if (state.prestige) add(t("q.prestige"), () => { state.prestige = false; });
    if (state.eligibleOnly) add(t("you.eligible", { c: countryName(profile.nationality) }), () => { state.eligibleOnly = false; });
    if (state.noIelts) add(t("you.noIelts"), () => { state.noIelts = false; });
    if (state.noHighGpa) add(t("you.gpa"), () => { state.noHighGpa = false; });
    if (state.fullyFunded) add(t("you.funded"), () => { state.fullyFunded = false; });
    if (state.womenOnly) add(t("you.women"), () => { state.womenOnly = false; });
    if (state.hideYear) add(t("q.year"), () => { state.hideYear = false; });
    if (!state.hideFees) add(L("funding", "fee_based"), () => { state.hideFees = true; });
    if (state.added !== "any") add(t("added." + state.added), () => { state.added = "any"; });
    for (const v of state.source) add(SOURCE_NAMES[v], drop("source", v));
    return out;
  }
  function renderProfileLine() {
    if (!profile) return;
    const bits = [countryName(profile.nationality)];
    if (profile.gender) bits.push(t("profile." + profile.gender));
    bits.push(profile.english ? t("profile.ielts", { x: nf.format(profile.english) }) : t("profile.noIelts"));
    $("#profileSummary").textContent = bits.join(SEP());
    $("#eligibleLabel").textContent = t("you.eligible", { c: countryName(profile.nationality) });
    $("#noIeltsLabel").textContent = profile.english ? t("you.noIeltsScore", { x: nf.format(profile.english) }) : t("you.noIelts");
    $("label[for=womenOnly]").hidden = profile.gender === "male";
  }

  function renderTabs() {
    const visibleOpen = ITEMS.filter(i => status[i.id] !== "hidden").length;
    const mine = [...ITEMS, ...ARCHIVE].filter(i => status[i.id] && status[i.id] !== "hidden").length
      || Object.values(status).filter(v => v !== "hidden").length;
    const arch = archiveState === "ready" ? ARCHIVE.filter(i => status[i.id] !== "hidden").length : (DATA?.archive_count ?? 0);
    $("#n-open").textContent = nf.format(visibleOpen);
    $("#n-mine").textContent = mine ? nf.format(mine) : "";
    $("#n-archive").textContent = arch ? nf.format(arch) : "";
    for (const b of $$("#tabs .tab")) b.setAttribute("aria-pressed", String(b.dataset.tab === state.tab));
    document.body.dataset.tab = state.tab;
  }

  async function ensureArchive() {
    const needed = state.tab === "archive" || (state.tab === "mine" && Object.keys(status).some(id => !ITEMS.some(i => i.id === id)));
    if (!needed || archiveState !== "idle") return;
    archiveState = "loading";
    if (state.tab === "archive") $("#count").textContent = t("arch.loading");
    let data = window.__RADAR_ARCHIVE__;
    if (!data) {
      try {
        const r = await fetch("data/archive.json", { cache: "no-cache" });
        data = r.ok ? await r.json() : { items: [] };
      } catch { data = { items: [] }; }
    }
    const gen = DATA?.generated_at ? new Date(DATA.generated_at) : new Date();
    const live = new Set(ITEMS.map(i => i.id));
    ARCHIVE = (data.items || []).filter(i => !live.has(i.id)).map(i => prep(i, gen, true));
    archiveState = "ready";
    update();
  }

  function renderPills() {
    const pills = activePills();
    const box = $("#pills");
    box.hidden = !pills.length;
    $("#activeCount").textContent = pills.length ? nf.format(pills.length) : "";
    if (!pills.length) { box.replaceChildren(); return; }
    const clear = el("button", "linkish", t("clear"));
    clear.type = "button";
    clear.addEventListener("click", resetAll);
    box.replaceChildren(...pills.map(p => {
      const b = el("button", "pill");
      b.type = "button";
      b.append(el("span", null, p.label), el("i", null, "✕"));
      b.setAttribute("aria-label", t("empty.remove", { x: p.label }));
      b.addEventListener("click", () => { p.clear(); state.page = 1; syncControls(); update(); });
      return b;
    }), clear);
  }

  const ZONE = { a: [0, 64], b: [67, 84], c: [87, 100] };
  function dayToX(d) {
    if (d <= 90) return ZONE.a[0] + d / 90 * (ZONE.a[1] - ZONE.a[0]);
    const f = Math.min(1, (d - 90) / (365 - 90));
    return ZONE.b[0] + f * (ZONE.b[1] - ZONE.b[0]);
  }

  function blip(it, x, lane, when) {
    const b = el("button", "blipbtn" + (it._days !== null && it._days <= 14 ? " urgent" : "") + (it.tier === "top" ? " top" : "")
      + (it.deadline_estimated ? " est" : "") + (it.score >= (DATA?.thresholds?.shelf ?? 80) ? " high80" : ""));
    b.type = "button";
    b.setAttribute("role", "listitem");
    b.style.insetInlineStart = x + "%";
    b.style.bottom = (30 + 16 + lane * 22) + "px";
    const dot = el("i");
    dot.style.width = dot.style.height = (9 + Math.round(Math.max(0, it.score - 50) / 50 * 7)) + "px";
    const tip = el("span", "tip");
    tip.append(auto(el("span", null, displayTitle(it.title))), el("small", null, `${nf.format(it.score)}${SEP()}${(it.deadline_estimated ? t("estimated") + SEP() : "")}${when}`));
    b.append(dot, tip);
    b.setAttribute("aria-label", `${displayTitle(it.title)}. ${when}`);
    b.addEventListener("click", () => jumpTo(it.id));
    return b;
  }

  function renderRunway(visible) {
    const min80 = DATA?.thresholds?.shelf ?? 80;
    const live = visible.filter(i => !i._archived && !(i._days !== null && i._days < 0));
    const near = live.filter(i => i.tier !== "standard" && i._days !== null && i._days <= 90);
    const later = live.filter(i => i.score >= min80 && i._days !== null && i._days > 90);
    const undated = live.filter(i => i.score >= min80 && i._days === null).sort((a, b) => b.score - a.score);

    const track = el("div", "runway-track");
    const urgent = el("div", "runway-urgent", t("runway.urgent"));
    urgent.style.inlineSize = (dayToX(14) - ZONE.a[0]) + "%";
    const zb = el("div", "runway-zone", t("runway.later"));
    zb.style.insetInlineStart = (ZONE.b[0] - 1.5) + "%"; zb.style.inlineSize = (ZONE.b[1] - ZONE.b[0] + 3) + "%";
    const zc = el("div", "runway-zone", t("runway.nodate"));
    zc.style.insetInlineStart = (ZONE.c[0] - 1.5) + "%"; zc.style.inlineSize = (ZONE.c[1] - ZONE.c[0] + 1.5) + "%";
    track.append(urgent, zb, zc, el("div", "runway-axis"));
    const tick = (x, label, cls = "") => {
      const tk = el("span", "runway-tick" + cls, label);
      tk.style.insetInlineStart = x + "%";
      track.append(tk);
    };
    for (let d = 0; d <= 90; d += 15) tick(dayToX(d), d === 0 ? t("runway.today") : fmtShort.format(new Date(today.getTime() + d * DAY)), d === 0 ? " today" : "");
    const fmtMon = new Intl.DateTimeFormat(locale, { month: "short", year: "numeric" });
    for (const d of [180, 365]) tick(dayToX(d), fmtMon.format(new Date(today.getTime() + d * DAY)));

    let plotted = 0;
    const place = (items, xOf) => {
      const lanes = [];
      for (const it of items.sort((a, b) => a._days - b._days || b.score - a.score)) {
        const x = xOf(it);
        let lane = lanes.findIndex(last => x - last >= 2.6);
        if (lane === -1) { lane = lanes.length; lanes.push(x); } else lanes[lane] = x;
        if (lane > 3) continue;
        const when = it._days === 0 ? t("due.today") : `${nf.format(it._days)} ${tn("dayLeft", it._days)}`;
        track.append(blip(it, x, lane, when));
        plotted++;
      }
    };
    place(near, it => dayToX(it._days));
    place(later, it => dayToX(it._days));
    const cols = Math.max(1, Math.ceil(undated.length / 4));
    undated.slice(0, cols * 4).forEach((it, i) => {
      const col = Math.floor(i / 4), lane = i % 4;
      const x = ZONE.c[0] + (col + 0.5) * ((ZONE.c[1] - ZONE.c[0]) / cols);
      const when = it.rolling || it.deadline_note === "rolling" ? t("due.rolling") : t(it.deadline_note ? "due." + it.deadline_note : "due.none");
      track.append(blip(it, x, lane, when));
      plotted++;
    });
    if (!plotted) track.append(el("div", "runway-empty", t("runway.empty")));
    $("#runway").replaceChildren(track);
    $("#runwayNote").textContent = plotted ? t("runway.note", { n: nf.format(plotted) }) : "";
  }

  function jumpTo(id) {
    let idx = currentList.findIndex(i => i.id === id);
    if (idx === -1) { state = { ...defaults(), sort: state.sort, tab: ITEMS.some(i => i.id === id) ? "open" : state.tab }; syncControls(); update(); idx = currentList.findIndex(i => i.id === id); }
    if (idx === -1) return;
    const page = Math.floor(idx / perPage) + 1;
    if (page !== state.page) { state.page = page; persist(); renderList(); renderPager(); renderCount(); }
    const row = document.getElementById("op-" + id);
    if (!row) return;
    row.scrollIntoView({ behavior: matchMedia("(prefers-reduced-motion: reduce)").matches ? "auto" : "smooth", block: "center" });
    row.classList.remove("flash"); void row.offsetWidth; row.classList.add("flash");
    row.querySelector(".title a")?.focus({ preventScroll: true });
  }

  const ICON = {
    star: '<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" aria-hidden="true"><path d="M12 3.5l2.6 5.3 5.9.9-4.3 4.1 1 5.8L12 16.9l-5.2 2.7 1-5.8-4.3-4.1 5.9-.9z"/></svg>',
    cal: '<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" aria-hidden="true"><rect x="3.5" y="5" width="17" height="15" rx="2"/><path d="M3.5 10h17M8 3v4M16 3v4"/></svg>',
    hide: '<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" aria-hidden="true"><path d="M3 3l18 18M10.6 6.1A9.7 9.7 0 0 1 12 6c5 0 9 6 9 6a16 16 0 0 1-3 3.4M6.6 7.6C4.4 9.1 3 12 3 12s4 6 9 6c1.4 0 2.7-.4 3.9-1"/><path d="M9.9 9.9a3 3 0 0 0 4.2 4.2"/></svg>',
    more: '<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" aria-hidden="true"><path d="M6 9l6 6 6-6"/></svg>',
  };
  ICON.starOn = ICON.star.replace('fill="none"', 'fill="currentColor"');

  function archivedDue(it) {
    const due = el("div", "due closed");
    const reason = it.archive_reason || "closed";
    due.append(el("span", "n", t("arch." + reason)));
    if (reason === "past_intake" && it.intakes.length) due.append(el("span", "d", it.intakes.map(intakeLabel).join(SEP())));
    else if (reason === "closed" && it.deadline) due.append(el("span", "d", fmtDate.format(parseDay(it.deadline))));
    else if (it.archived_at) due.append(el("span", "d", fmtDate.format(new Date(it.archived_at))));
    if (it.reopens) due.append(el("span", "u next", t("arch.next", { d: fmtDate.format(parseDay(it.reopens)) })));
    else if (it.reopens_intake) due.append(el("span", "u next", t("arch.nextIntake", { x: intakeLabel(it.reopens_intake) })));
    return due;
  }

  function cleanSummary(title, summary) {
    let s = (summary || "").trim();
    const head = title.trim().toLowerCase();
    if (head.length > 12 && s.toLowerCase().startsWith(head)) s = s.slice(title.trim().length).replace(/^[\s|:–—-]+/, "");
    return s.length > 20 ? s : (summary || "");
  }
  function dueBlock(it) {
    if (it._archived) return archivedDue(it);
    const due = el("div", "due");
    const dl = it._days;
    if (dl === null) {
      due.classList.add("open");
      const note = it.deadline_note;
      if (it.rolling || note === "rolling") due.append(el("span", "n", t("due.rolling")), el("span", "u", t("due.rollingU")));
      else if (note === "tbd" || note === "varies" || note === "recurring") due.append(el("span", "n", t("due." + note)), el("span", "u", t("due.noneU")));
      else due.append(el("span", "n", t("due.none")), el("span", "u", t("due.noneU")));
    } else if (dl < 0) {
      due.classList.add("closed");
      due.append(el("span", "n", t("due.closed")), el("span", "d", fmtDate.format(parseDay(it.deadline))));
    } else {
      if (dl <= 14) due.classList.add("urgent");
      if (it.deadline_estimated) due.classList.add("est");
      due.append(el("span", "n", dl === 0 ? t("due.today") : nf.format(dl)));
      if (dl > 0) due.append(el("span", "u", tn("dayLeft", dl)));
      const date = fmtDate.format(parseDay(it.deadline));
      if (it.deadline_estimated) due.append(el("span", "d", t("estimated")), el("span", "d nowrap", t("due.expectedD", { d: date })));
      else due.append(el("span", "d nowrap", date));
    }
    return due;
  }

  function dial(it) {
    const d = el("div", "dial");
    const r = 20, c = 2 * Math.PI * r;
    d.innerHTML = `<svg viewBox="0 0 48 48" aria-hidden="true"><circle class="bg" cx="24" cy="24" r="${r}"/><circle class="fg" cx="24" cy="24" r="${r}" stroke-dasharray="${(it.score / 100 * c).toFixed(1)} ${c.toFixed(1)}"/></svg>`;
    d.append(el("b", null, nf.format(it.score)));
    d.setAttribute("role", "img");
    d.setAttribute("aria-label", `${it.score} / 100`);
    return d;
  }

  function setStatus(it, value, row) {
    if (value) status[it.id] = value; else delete status[it.id];
    saveStatus();
    if (value === "hidden") toast(t("t.hidden"), () => { delete status[it.id]; saveStatus(); update(); });
    else toast(value === "interested" ? t("t.saved") : value ? t("t.marked", { x: L("status", value) }) : t("t.removed"));
    if (value === "hidden" || state.tab === "mine") update();
    else { row.replaceWith(rowFor(it)); renderFacets(); }
  }

  function whyLabel(w) {
    const [code, , detail] = w;
    if (w.length === 2 && !STRINGS.en["why." + code]) return code;
    if (code === "topic") return t("why.topic", { x: (detail || []).map(f => L("field", f)).join(SEP()) });
    if (code === "level") return t("why.level", { x: L("degree", detail) });
    if (code === "type") return t("why.type", { x: L("type", detail) });
    if (code === "year_limit") return t("why.year_limit", { x: yearLabel(detail) });
    if (code === "prestige") return t("why.prestige", { x: detail });
    if (code === "not_open") return t("why.not_open", { x: detail || "" });
    if (code === "nationality") return t("why.nationality", { x: countryName(detail || "Palestine") });
    return t("why." + code);
  }

  function detailsPanel(it, row) {
    const p = el("div", "details");
    const why = el("div", "why");
    why.append(el("h4", null, t("d.why")));
    const ul = el("ul");
    for (const w of it.why || []) {
      if (!Array.isArray(w)) continue;
      const li = el("li");
      li.append(auto(el("span", null, whyLabel(w))), el("b", w[1] < 0 ? "neg" : null, (w[1] > 0 ? "+" : "") + nf.format(w[1])));
      ul.append(li);
    }
    why.append(ul);

    const facts = el("dl", "facts");
    const fact = (k, v) => {
      if (!v) return;
      facts.append(el("dt", null, k));
      const dd = el("dd");
      if (typeof v === "string") { dd.textContent = v; auto(dd); } else dd.append(v);
      facts.append(dd);
    };
    fact(t("d.dest"), it.countries.length ? it.countries.map(countryName).join(SEP()) : it.regions.map(r => L("region", r)).join(SEP()) || t("d.notStated"));
    const who = [];
    if (it.eligibility === "restricted") who.push(t("limited", { x: it.eligibility_note }));
    else if (it.eligibility === "open") who.push(t("d.openTo", { x: it.eligibility_note }));
    if (it.year_limit) who.push(t("d.yearOnly", { x: yearLabel(it.year_limit) }));
    if (it.diversity) who.push(t("diversity"));
    fact(t("d.who"), who.join(SEP()) || t("d.notStated"));
    if (it._elig) fact(t("d.forYou"), t(it._elig === "no" ? "elig.no" : "elig.match", { c: countryName(profile.nationality) }));
    fact(t("d.english"), it.english_test === "not_required" ? t("d.englishNone") : it.english_min ? t("d.englishMin", { x: nf.format(it.english_min) })
      : it.english_test === "required" ? t("d.englishReq") : t("d.notStated"));
    fact(t("d.grades"), it.gpa_level === "high" ? t("d.gradesHigh") + (it.gpa_note ? ` (${it.gpa_note})` : "")
      : it.gpa_level === "moderate" ? `${t("d.gradesMod")} (${it.gpa_note})` : t("d.notStated"));
    if (it.intakes.length) fact(t("d.intake"), it.intakes.map(intakeLabel).join(SEP()) + (it.intake_inferred ? ` (${t("intake.expected")})` : ""));
    fact(t("d.level"), it.degrees.map(d => L("degree", d)).join(SEP()));
    fact(t("d.fields"), it.fields.map(f => L("field", f)).join(SEP()));
    const srcs = el("span");
    [{ source: it.source, url: it.url }, ...it.also_on].forEach((s, i) => {
      if (i) srcs.append(document.createTextNode(SEP()));
      const a = el("a", null, SOURCE_NAMES[s.source] || s.source);
      a.href = s.url; a.target = "_blank"; a.rel = "noopener";
      srcs.append(a);
    });
    fact(t("d.listed"), srcs);
    fact(t("d.dates"), [it.published && t("d.posted", { d: fmtDate.format(parseDay(it.published)) }),
      it.first_seen && t("d.added", { d: fmtDate.format(new Date(it.first_seen)) })].filter(Boolean).join(SEP()));

    const track = el("div", "tracker");
    track.append(el("h4", null, t("d.track")));
    const seg = el("div", "seg seg-inline");
    seg.setAttribute("role", "group");
    seg.setAttribute("aria-label", t("d.track"));
    for (const v of ["", "interested", "applying", "applied"]) {
      const b = el("button", null, v ? L("status", v) : t("d.notTracking"));
      b.type = "button";
      b.setAttribute("aria-pressed", String((status[it.id] || "") === v));
      b.addEventListener("click", () => setStatus(it, v, row));
      seg.append(b);
    }
    const open = el("a", "btn open-btn", t("d.open"));
    open.href = it.url; open.target = "_blank"; open.rel = "noopener";
    track.append(seg, open);
    p.append(why, facts, track);
    if (status[it.id] && status[it.id] !== "hidden") p.append(checklistPanel(it, row));
    return p;
  }

  let checks = store.get("radar:check", {});
  const saveChecks = () => store.set("radar:check", checks);
  function checklistKeys(it) {
    const base = it.type === "Scholarship"
      ? ["cv", "sop", "recs", "transcript", "degree", "english", "passport", "form"]
      : ["Research", "Fellowship", "Summer school", "Internship", "Exchange"].includes(it.type)
        ? ["cv", "motivation", "rec", "transcript", "research", "portfolio", "passport"]
        : ["cv", "motivation", "form"];
    return base.filter(k => k !== "english" || it.english_test !== "not_required");
  }
  function checkProgress(it) {
    const c = checks[it.id];
    const keys = checklistKeys(it);
    const custom = c?.c || [];
    const done = keys.filter(k => c?.d?.includes(k)).length + custom.filter(x => x[1]).length;
    return { done, total: keys.length + custom.length, target: c?.t || null };
  }
  function checklistPanel(it, row) {
    const c = checks[it.id] || (checks[it.id] = { d: [], c: [], n: "", t: "" });
    const box = el("div", "checklist-panel");
    const prog = checkProgress(it);
    const head = el("div", "ck-head");
    head.append(el("h4", null, t("ck.title")), el("span", "ck-prog", t("ck.progress", { a: nf.format(prog.done), b: nf.format(prog.total) })));
    const bar = el("div", "ck-bar");
    const fill = el("i");
    fill.style.inlineSize = (prog.total ? prog.done / prog.total * 100 : 0) + "%";
    bar.append(fill);
    const list = el("ul", "ck-list");
    const refresh = () => { saveChecks(); const fresh = rowFor(it); row.replaceWith(fresh); fresh.querySelector(".checklist-panel")?.scrollIntoView({ block: "nearest" }); };
    checklistKeys(it).forEach(k => {
      const li = el("li");
      const id = `ck-${it.id}-${k}`;
      const lab = el("label", "check");
      lab.htmlFor = id;
      const cb = document.createElement("input");
      cb.type = "checkbox"; cb.id = id; cb.checked = c.d.includes(k);
      cb.addEventListener("change", () => { c.d = cb.checked ? [...new Set([...c.d, k])] : c.d.filter(x => x !== k); refresh(); });
      lab.append(cb, el("span", null, t("ck." + k)));
      li.append(lab);
      list.append(li);
    });
    c.c.forEach((item, i) => {
      const li = el("li");
      const id = `ckc-${it.id}-${i}`;
      const lab = el("label", "check");
      lab.htmlFor = id;
      const cb = document.createElement("input");
      cb.type = "checkbox"; cb.id = id; cb.checked = !!item[1];
      cb.addEventListener("change", () => { item[1] = cb.checked; refresh(); });
      lab.append(cb, auto(el("span", null, item[0])));
      const rm = el("button", "linkish ck-rm", t("ck.remove"));
      rm.type = "button";
      rm.addEventListener("click", () => { c.c.splice(i, 1); refresh(); });
      li.append(lab, rm);
      list.append(li);
    });
    const addRow = el("div", "ck-add");
    const input = document.createElement("input");
    input.type = "text"; input.id = `cka-${it.id}`; input.placeholder = t("ck.add"); input.setAttribute("aria-label", t("ck.add"));
    const addBtn = el("button", "btn btn-ghost", t("ck.addBtn"));
    addBtn.type = "button";
    const add = () => { const v = input.value.trim(); if (v) { c.c.push([v, false]); refresh(); } };
    addBtn.addEventListener("click", add);
    input.addEventListener("keydown", e => { if (e.key === "Enter") { e.preventDefault(); add(); } });
    addRow.append(input, addBtn);
    const side = el("div", "ck-side");
    const tl = el("label", null, t("ck.target"));
    tl.htmlFor = `ckt-${it.id}`;
    const date = document.createElement("input");
    date.type = "date"; date.id = `ckt-${it.id}`; date.value = c.t || "";
    date.addEventListener("change", () => { c.t = date.value; saveChecks(); });
    const nl = el("label", null, t("ck.notes"));
    nl.htmlFor = `ckn-${it.id}`;
    const notes = document.createElement("textarea");
    notes.id = `ckn-${it.id}`; notes.rows = 3; notes.value = c.n || "";
    notes.addEventListener("input", () => { c.n = notes.value; saveChecks(); });
    side.append(tl, date, nl, notes);
    const main = el("div", "ck-main");
    main.append(list, addRow);
    box.append(head, bar, main, side);
    return box;
  }

  function rowFor(it) {
    const expanded = expandedIds.has(it.id);
    const st = status[it.id];
    const li = el("li", `row ${it.tier}` + (expanded ? " expanded" : "") + (it._archived ? " archived" : ""));
    li.id = "op-" + it.id;

    const body = el("div", "body");
    const h = el("h3", "title");
    const a = auto(el("a", null, displayTitle(it.title)));
    a.href = it.url; a.target = "_blank"; a.rel = "noopener";
    h.append(a);
    if (it.tier === "top") h.append(el("span", "tier-note", t("top")));
    if (justAdded.has(it.id)) h.append(el("span", "newbadge", t("justAdded")));
    else if (it._reopened) h.append(el("span", "newbadge", t("reopened")));
    else if (it._new) h.append(el("span", "newbadge", t("new")));
    if (st && st !== "hidden") {
      h.append(el("span", "status-note s-" + st, L("status", st)));
      const pr = checkProgress(it);
      if (checks[it.id] && pr.total) h.append(el("span", "ck-note", t("ck.progress", { a: nf.format(pr.done), b: nf.format(pr.total) })));
    }
    body.append(h);

    const meta = el("p", "meta");
    const names = it.countries.map(countryName);
    const places = names.length ? (names.length > 2 ? `${names.slice(0, 2).join(SEP())} +${names.length - 2}` : names.join(SEP()))
      : (it.regions[0] ? L("region", it.regions[0]) : "");
    if (it.org && !it.title.includes(it.org)) meta.append(auto(el("span", "place", it.org)));
    if (places) meta.append(el("span", "place", places));
    if (it._elig === "no") meta.append(auto(el("span", "restricted", `${t("elig.no", { c: countryName(profile.nationality) })}: ${it.eligibility_note}`)));
    else if (it._elig === "match") meta.append(el("span", "fits", t("elig.match", { c: countryName(profile.nationality) })));
    else if (it.eligibility === "restricted") meta.append(auto(el("span", "restricted", t("limited", { x: it.eligibility_note }))));
    if (it.year_limit) meta.append(el("span", "restricted", t("d.yearOnly", { x: yearLabel(it.year_limit) })));
    meta.append(el("span", "src", t("via", { s: SOURCE_NAMES[it.source] || it.source }) + (it.also_on.length ? " " + t("alsoOn", { n: nf.format(it.also_on.length) }) : "")));
    body.append(meta);
    if (density === "detailed" && it._summary) body.append(auto(el("p", "summary", it._summary)));

    const tags = el("div", "tags");
    tags.append(el("span", "tag type", L("type", it.type)));
    for (const k of it.intakes.slice(0, 2)) tags.append(el("span", "tag intake" + (it.intake_inferred ? " est" : ""), intakeLabel(k)));
    if (it.degrees.length) tags.append(el("span", "tag", it.degrees.map(d => L("degree", d)).join(" · ")));
    if (it.funding) tags.append(el("span", "tag " + (it.funding === "fee_based" ? "fee" : "money"), L("funding", it.funding)));
    if (it.english_test === "not_required") tags.append(el("span", "tag money", t("tag.noIelts")));
    else if (it.english_min) tags.append(el("span", "tag" + (profile?.english && it.english_min <= profile.english ? " money" : ""), t("tag.ielts", { x: nf.format(it.english_min) })));
    if (it.gpa_level === "high") tags.append(el("span", "tag fee", t("tag.topGrades")));
    if (it.for_women) tags.append(el("span", "tag f-ai", t("tag.women")));
    for (const f of it.fields.slice(0, density === "detailed" ? 2 : 1)) tags.append(el("span", "tag" + (AI_FIELDS.has(f) ? " f-ai" : ""), L("field", f)));
    if (it.diversity && density === "detailed") tags.append(el("span", "tag", t("diversity")));
    body.append(tags);

    const actions = el("div", "actions");
    const mk = (html, label, fn, pressed) => {
      const b = el("button");
      b.type = "button";
      b.innerHTML = html;
      b.append(el("span", "lbl", label));
      b.title = label;
      if (pressed !== undefined) b.setAttribute("aria-pressed", String(pressed));
      b.addEventListener("click", fn);
      actions.append(b);
      return b;
    };
    const det = mk(ICON.more, expanded ? t("hideDetails") : t("details"), () => {
      expanded ? expandedIds.delete(it.id) : expandedIds.add(it.id);
      li.replaceWith(rowFor(it));
      document.querySelector(`#op-${it.id} .details-btn`)?.focus();
    });
    det.className = "details-btn";
    det.setAttribute("aria-expanded", String(expanded));
    const saved = st && st !== "hidden";
    mk(saved ? ICON.starOn : ICON.star, saved ? t("saved") : t("save"), () => setStatus(it, saved ? "" : "interested", li), !!saved);
    if (!PREVIEW && !it._archived && it._days !== null && it._days >= 0) mk(ICON.cal, t("calendar"), () => downloadIcs(it));
    mk(ICON.hide, st === "hidden" ? t("unhide") : t("notForMe"), () => setStatus(it, st === "hidden" ? "" : "hidden", li));
    body.append(actions);

    li.append(dial(it), body, dueBlock(it));
    if (expanded) li.append(detailsPanel(it, li));
    return li;
  }

  function download(name, type, text) {
    const a = document.createElement("a");
    a.href = URL.createObjectURL(new Blob([text], { type }));
    a.download = name;
    document.body.append(a); a.click(); a.remove();
    setTimeout(() => URL.revokeObjectURL(a.href), 2000);
  }
  function downloadIcs(it) {
    const d = it.deadline.replaceAll("-", "");
    const next = new Date(parseDay(it.deadline).getTime() + DAY);
    const dEnd = `${next.getFullYear()}${String(next.getMonth() + 1).padStart(2, "0")}${String(next.getDate()).padStart(2, "0")}`;
    const esc = s => String(s).replace(/[\\,;]/g, m => "\\" + m).replace(/\n/g, "\\n");
    const stamp = new Date().toISOString().replace(/[-:]/g, "").replace(/\.\d+Z$/, "Z");
    download(it.title.replace(/[^\w]+/g, "-").slice(0, 60) + ".ics", "text/calendar", [
      "BEGIN:VCALENDAR", "VERSION:2.0", "PRODID:-//Opportunity Radar//EN", "BEGIN:VEVENT",
      `UID:${it.id}@opportunity-radar`, `DTSTAMP:${stamp}`, `DTSTART;VALUE=DATE:${d}`, `DTEND;VALUE=DATE:${dEnd}`,
      `SUMMARY:${esc("Deadline: " + it.title)}`, `URL:${it.url}`, `DESCRIPTION:${esc(it.url)}`,
      "BEGIN:VALARM", "TRIGGER:-P7D", "ACTION:DISPLAY", `DESCRIPTION:${esc(it.title)}`, "END:VALARM",
      "END:VEVENT", "END:VCALENDAR",
    ].join("\r\n"));
    toast(t("t.calendar"));
  }
  function icsFor(items) {
    const esc = x => String(x).replace(/[\\,;]/g, m => "\\" + m).replace(/\n/g, "\\n");
    const stamp = new Date().toISOString().replace(/[-:]/g, "").replace(/\.\d+Z$/, "Z");
    const ymd = d => `${d.getFullYear()}${String(d.getMonth() + 1).padStart(2, "0")}${String(d.getDate()).padStart(2, "0")}`;
    const out = ["BEGIN:VCALENDAR", "VERSION:2.0", "PRODID:-//Opportunity Radar//EN", "X-WR-CALNAME:Opportunity Radar"];
    for (const [it, day, label] of items) {
      out.push("BEGIN:VEVENT", `UID:${it.id}-${label.length}@opportunity-radar`, `DTSTAMP:${stamp}`,
        `DTSTART;VALUE=DATE:${ymd(day)}`, `DTEND;VALUE=DATE:${ymd(new Date(day.getTime() + DAY))}`,
        `SUMMARY:${esc(label + ": " + it.title)}`, `URL:${it.url}`, `DESCRIPTION:${esc(it.url)}`,
        "BEGIN:VALARM", "TRIGGER:-P7D", "ACTION:DISPLAY", `DESCRIPTION:${esc(it.title)}`, "END:VALARM", "END:VEVENT");
    }
    out.push("END:VCALENDAR");
    return out.join("\r\n");
  }
  function downloadMine() {
    const rows = [];
    for (const it of [...ITEMS, ...ARCHIVE]) {
      const st = status[it.id];
      if (!st || st === "hidden") continue;
      if (it.deadline && it._days !== null && it._days >= 0) rows.push([it, parseDay(it.deadline), it.deadline_estimated ? "Expected deadline" : "Deadline"]);
      const target = checks[it.id]?.t;
      if (target) rows.push([it, parseDay(target), "My target"]);
    }
    if (!rows.length) { toast(t("cal.empty")); return; }
    download("my-opportunities.ics", "text/calendar", icsFor(rows));
    toast(t("t.calMine", { n: nf.format(rows.length) }));
  }
  function renderCalendarDialog() {
    const box = $("#calFeeds");
    box.replaceChildren(...[["calendar.ics", "cal.high"], ["calendar-all.ics", "cal.all"]].map(([file, key]) => {
      const https = new URL(file, location.href.split("#")[0]).href;
      const webcal = https.replace(/^https?:/, "webcal:");
      const row = el("div", "cal-feed");
      row.append(el("h3", null, t(key)));
      const links = el("div", "cal-links");
      const g = el("a", "btn", t("cal.google"));
      g.href = "https://calendar.google.com/calendar/r?cid=" + encodeURIComponent(webcal); g.target = "_blank"; g.rel = "noopener";
      const a = el("a", "btn btn-ghost", t("cal.apple"));
      a.href = webcal;
      const copy = el("button", "btn btn-ghost", t("cal.copy"));
      copy.type = "button";
      copy.addEventListener("click", async () => {
        try { await navigator.clipboard.writeText(https); toast(t("t.copied")); } catch { toast(https); }
      });
      const url = el("code", "cal-url", https);
      links.append(g, a, copy);
      row.append(links, url);
      return row;
    }));
  }
  function renderFeedDialog() {
    const url = new URL("feed.xml", location.href.split("#")[0]).href;
    const row = el("div", "cal-feed");
    row.append(el("h3", null, t("feed.what")));
    const links = el("div", "cal-links");
    const f = el("a", "btn", t("feed.feedly"));
    f.href = "https://feedly.com/i/subscription/feed/" + encodeURIComponent(url); f.target = "_blank"; f.rel = "noopener";
    const i = el("a", "btn btn-ghost", t("feed.inoreader"));
    i.href = "https://www.inoreader.com/?add_feed=" + encodeURIComponent(url); i.target = "_blank"; i.rel = "noopener";
    const copy = el("button", "btn btn-ghost", t("cal.copy"));
    copy.type = "button";
    copy.addEventListener("click", async () => {
      try { await navigator.clipboard.writeText(url); toast(t("t.copied")); } catch { toast(url); }
    });
    links.append(f, i, copy);
    row.append(links, el("code", "cal-url", url));
    $("#feedLinks").replaceChildren(row);
  }
  function fillProfileForm() {
    const sel = $("#pfNationality");
    const opts = NATIONALITIES.map(n => [n, countryName(n)]).sort((a, b) => a[1].localeCompare(b[1], locale));
    sel.replaceChildren(...opts.map(([v, label]) => Object.assign(document.createElement("option"), { value: v, textContent: label })));
    sel.value = profile.nationality;
    $$('input[name="pfGender"]').forEach(r => { r.checked = r.value === (profile.gender || ""); });
    $("#pfEnglish").value = profile.english ?? "";
  }
  function saveProfile() {
    const eng = parseFloat($("#pfEnglish").value);
    profile = { nationality: $("#pfNationality").value, gender: ($$('input[name="pfGender"]').find(r => r.checked) || {}).value || "",
      english: Number.isFinite(eng) ? eng : null };
    store.set("radar:profile", profile);
    for (const it of [...ITEMS, ...ARCHIVE]) it._elig = eligibilityFor(it);
    update();
    toast(t("t.profileSaved"));
  }

  function exportCsv() {
    const cols = ["title", "url", "score", "type", "intake", "levels", "fields", "funding", "countries", "deadline", "deadline_estimated", "eligibility", "source", "my_status", "status"];
    const q = v => `"${String(v ?? "").replace(/"/g, '""')}"`;
    const rows = currentList.map(it => [it.title, it.url, it.score, it.type, it.intakes.join("; "), it.degrees.join("; "), it.fields.join("; "), it.funding || "",
      it.countries.join("; "), it.deadline || it.deadline_note || (it.rolling ? "rolling" : ""), it.deadline_estimated ? "yes" : "",
      it.eligibility_note || "", SOURCE_NAMES[it.source], status[it.id] || "", it._archived ? it.archive_reason : "open"].map(q).join(","));
    download(`opportunities-${new Date().toISOString().slice(0, 10)}.csv`, "text/csv", "﻿" + [cols.join(","), ...rows].join("\n"));
    toast(t("t.exported", { n: tn("opportunity", currentList.length) }));
  }

  const pageCount = () => Math.max(1, Math.ceil(currentList.length / perPage));

  function renderList() {
    const list = $("#list");
    list.className = "list " + density;
    const start = (state.page - 1) * perPage;
    const frag = document.createDocumentFragment();
    let lastGroup = null;
    for (const it of currentList.slice(start, start + perPage)) {
      let g = null;
      if (state.sort === "deadline") {
        if (it._archived) g = it.reopens ? t("arch.group", { m: fmtMonth.format(parseDay(it.reopens)) }) : t("arch.groupNone");
        else g = it._days === null ? t("due.none") : it._days < 0 ? t("due.closed") : it._days <= 7 ? t("dl.7") : fmtMonth.format(parseDay(it.deadline));
      } else if (state.sort === "intake") {
        g = it.intakes.length ? intakeLabel(it.intakes[0]) : t("intake.groupNone");
      }
      if (g !== null && g !== lastGroup) { frag.append(el("li", "group-head", g)); lastGroup = g; }
      frag.append(rowFor(it));
    }
    list.replaceChildren(frag);
  }

  function pageButton(label, page, opts = {}) {
    const b = el("button", "pg" + (opts.cls ? " " + opts.cls : ""), label);
    b.type = "button";
    if (opts.current) b.setAttribute("aria-current", "page");
    if (opts.disabled) b.disabled = true;
    b.setAttribute("aria-label", opts.aria || t("page", { n: nf.format(page) }));
    b.addEventListener("click", () => goToPage(page));
    return b;
  }
  function renderPager() {
    const pager = $("#pager");
    const total = pageCount();
    pager.hidden = total <= 1;
    if (total <= 1) { pager.replaceChildren(); return; }
    const cur = state.page;
    const narrow = matchMedia("(max-width: 520px)").matches;
    const nums = new Set([1, total, cur, cur - 1, cur + 1]);
    if (!narrow && cur <= 3) [2, 3, 4].forEach(n => nums.add(n));
    if (!narrow && cur >= total - 2) [total - 1, total - 2, total - 3].forEach(n => nums.add(n));
    const sorted = [...nums].filter(n => n >= 1 && n <= total).sort((a, b) => a - b);
    const items = [pageButton(t("prev"), cur - 1, { cls: "pg-step", disabled: cur === 1, aria: t("prev") })];
    let prev = 0;
    for (const n of sorted) {
      if (n - prev > 1) items.push(el("span", "pg-gap", "…"));
      items.push(pageButton(nf.format(n), n, { current: n === cur }));
      prev = n;
    }
    items.push(pageButton(t("next"), cur + 1, { cls: "pg-step", disabled: cur === total, aria: t("next") }));
    pager.replaceChildren(...items);
  }
  function goToPage(n) {
    state.page = Math.min(Math.max(1, n), pageCount());
    persist();
    renderList(); renderPager(); renderCount();
    const top = $("#results").getBoundingClientRect().top + window.scrollY - 8;
    window.scrollTo({ top, behavior: matchMedia("(prefers-reduced-motion: reduce)").matches ? "auto" : "smooth" });
    $("#results").focus({ preventScroll: true });
  }

  function renderCount() {
    const n = currentList.length;
    const count = $("#count");
    count.replaceChildren(el("b", null, tn("opportunity", n)));
    const hv = currentList.filter(i => i.tier !== "standard").length;
    const soon = currentList.filter(i => i._days !== null && i._days >= 0 && i._days <= 14).length;
    if (hv) count.append(document.createTextNode(SEP() + t("count.hv", { n: nf.format(hv) })));
    if (soon) count.append(document.createTextNode(SEP()), el("span", "soon", t("count.soon", { n: nf.format(soon) })));
    if (n > perPage) {
      const a = (state.page - 1) * perPage + 1, b = Math.min(state.page * perPage, n);
      count.append(el("span", "range", t("range", { a: nf.format(a), b: nf.format(b), n: nf.format(n) })));
    }
    $("#railDone").textContent = tn("result", n);
  }

  function renderEmpty() {
    const empty = $("#empty");
    empty.hidden = currentList.length > 0;
    if (empty.hidden) return;
    const mineEmpty = state.tab === "mine" && !Object.keys(status).length;
    const archEmpty = state.tab === "archive" && archiveState === "ready" && !ARCHIVE.length;
    const loading = state.tab !== "open" && archiveState === "loading";
    $("#emptyTitle").textContent = loading ? t("arch.loading") : mineEmpty ? t("mine.empty") : archEmpty ? t("empty.archive") : t("empty.title");
    const pills = mineEmpty || archEmpty || loading ? [] : activePills().slice(0, 4);
    const all = el("button", "btn", mineEmpty || archEmpty ? t("tab.open") : t("empty.clear"));
    all.type = "button";
    all.hidden = loading;
    all.addEventListener("click", mineEmpty || archEmpty ? () => setTab("open") : resetAll);
    $("#emptyActions").replaceChildren(...pills.map(p => {
      const b = el("button", "btn btn-ghost", t("empty.remove", { x: p.label }));
      b.type = "button";
      b.addEventListener("click", () => { p.clear(); syncControls(); update(); });
      return b;
    }), all);
  }

  function setTab(tab) {
    state.tab = tab;
    state.page = 1;
    if (tab !== "mine") state.mine = [];
    syncControls(); update(); ensureArchive();
  }

  function update() {
    currentList = pool().filter(i => matches(i, state));
    for (const i of currentList) i._no = eligibilityFor(i) === "no" ? 1 : 0;
    currentList.sort(SORTS[state.sort] || SORTS.score);
    state.page = Math.min(Math.max(1, state.page || 1), pageCount());
    persist();
    renderQuick(); renderFacets(); renderPills(); renderRunway(currentList);
    renderList(); renderPager(); renderCount(); renderEmpty();
  }

  function syncControls() {
    $("#q").value = state.q;
    $$('input[name="view"]').forEach(r => { r.checked = r.value === state.view; });
    $$('input[name="dl"]').forEach(r => { r.checked = r.value === state.dl; });
    $$('input[name="added"]').forEach(r => { r.checked = r.value === state.added; });
    $("#dateRange").hidden = state.dl !== "custom";
    $("#dlFrom").value = state.from; $("#dlTo").value = state.to;
    $("#includeUndated").checked = state.includeUndated;
    $("#includeUndated").closest("label").hidden = state.dl === "any" || state.dl === "rolling";
    $("#minScore").value = state.minScore; $("#minScoreOut").textContent = state.minScore ? nf.format(state.minScore) : t("any");
    $("#prestigeOnly").checked = state.prestige;
    for (const k of ["eligibleOnly", "noIelts", "noHighGpa", "fullyFunded", "womenOnly"]) $("#" + k).checked = state[k];
    $("#hideYear").checked = state.hideYear;
    $("#hideFees").checked = state.hideFees;
    $("#sort").value = state.sort;
    $("#perPage").value = String(perPage);
    $("#dens-detailed").setAttribute("aria-pressed", String(density === "detailed"));
    $("#dens-compact").setAttribute("aria-pressed", String(density === "compact"));
  }

  function resetAll() { state = { ...defaults(), sort: state.sort }; syncControls(); update(); toast(t("t.cleared")); }

  let toastTimer;
  function toast(msg, undo) {
    const box = $("#toast");
    box.replaceChildren(el("span", null, msg));
    if (undo) {
      const b = el("button", null, t("t.undo"));
      b.type = "button";
      b.addEventListener("click", () => { undo(); box.classList.remove("show"); });
      box.append(b);
    }
    box.classList.add("show");
    clearTimeout(toastTimer);
    toastTimer = setTimeout(() => box.classList.remove("show"), undo ? 5000 : 2400);
  }

  function renderSources() {
    const src = DATA?.sources || {};
    $("#sourcesList").replaceChildren(...activeSources().map(key => {
      const s = src[key] || {};
      const li = el("li");
      const a = el("a", null, SOURCE_NAMES[key]);
      a.href = s.home || SOURCE_HOME[key]; a.target = "_blank"; a.rel = "noopener";
      const info = el("span");
      const st = s.status || {};
      if (st.ok) info.textContent = `${t("src.listed", { n: nf.format(s.items || 0) })}${SEP()}${t("src.checked", { x: ago(s.last_ok) })}`;
      else if (st.ok === false) { info.className = "bad"; info.textContent = t("src.failed"); }
      else info.textContent = t("src.pending");
      li.append(a, info);
      return li;
    }));
  }
  function renderCredits() {
    const p = $("#credits");
    const keys = activeSources();
    if (!keys.length) { p.replaceChildren(); return; }
    p.replaceChildren(document.createTextNode(t("credits") + " "));
    keys.forEach((k, i) => {
      const a = el("a", null, SOURCE_NAMES[k]);
      a.href = SOURCE_HOME[k]; a.target = "_blank"; a.rel = "noopener";
      p.append(a, document.createTextNode(i < keys.length - 1 ? SEP() : "."));
    });
  }
  function renderUpdated() {
    if (!DATA) return;
    const up = $("#updated");
    up.replaceChildren(document.createTextNode(t("updated") + " "), el("b", null, ago(DATA.generated_at)),
      document.createTextNode(SEP() + tn("opportunity", ITEMS.length)));
    up.title = new Date(DATA.generated_at).toLocaleString(locale);
  }

  function applyLanguage() {
    setupLocale();
    const root = document.documentElement;
    root.lang = lang;
    root.dir = lang === "ar" ? "rtl" : "ltr";
    document.title = t("site.title");
    for (const n of $$("[data-i18n]")) n.textContent = t(n.dataset.i18n);
    for (const n of $$("[data-i18n-ph]")) n.placeholder = t(n.dataset.i18nPh);
    for (const n of $$("[data-i18n-label]")) n.setAttribute("aria-label", t(n.dataset.i18nLabel));
    const lb = $("#langBtn");
    lb.textContent = t("lang.other");
    lb.lang = lang === "ar" ? "en" : "ar";
    renderCredits();
    if (DATA) { renderUpdated(); syncControls(); update(); }
  }

  function bind() {
    const set = (k, v) => { state[k] = v; state.page = 1; update(); };
    let qTimer;
    $("#q").addEventListener("input", e => { clearTimeout(qTimer); qTimer = setTimeout(() => set("q", e.target.value.trim()), 150); });
    $$('input[name="view"]').forEach(r => r.addEventListener("change", () => set("view", r.value)));
    $$('input[name="dl"]').forEach(r => r.addEventListener("change", () => { state.dl = r.value; syncControls(); set("dl", r.value); }));
    $$('input[name="added"]').forEach(r => r.addEventListener("change", () => set("added", r.value)));
    $("#dlFrom").addEventListener("change", e => set("from", e.target.value));
    $("#dlTo").addEventListener("change", e => set("to", e.target.value));
    $("#includeUndated").addEventListener("change", e => set("includeUndated", e.target.checked));
    for (const b of $$("#tabs .tab")) b.addEventListener("click", () => setTab(b.dataset.tab));
    $("#minScore").addEventListener("input", e => { $("#minScoreOut").textContent = Number(e.target.value) ? nf.format(Number(e.target.value)) : t("any"); });
    $("#minScore").addEventListener("change", e => set("minScore", Number(e.target.value)));
    $("#prestigeOnly").addEventListener("change", e => set("prestige", e.target.checked));
    for (const k of ["eligibleOnly", "noIelts", "noHighGpa", "fullyFunded", "womenOnly"]) $("#" + k).addEventListener("change", e => set(k, e.target.checked));
    $("#hideYear").addEventListener("change", e => set("hideYear", e.target.checked));
    $("#hideFees").addEventListener("change", e => set("hideFees", e.target.checked));
    $("#sort").addEventListener("change", e => set("sort", e.target.value));
    $("#perPage").addEventListener("change", e => { perPage = Number(e.target.value) || 10; store.set("radar:perPage", perPage); state.page = 1; update(); });
    $("#countryQ").addEventListener("input", renderCountries);
    $("#resetBtn").addEventListener("click", resetAll);
    for (const d of ["detailed", "compact"]) $("#dens-" + d).addEventListener("click", () => { density = d; store.set("radar:density", d); syncControls(); renderList(); });
    $("#exportBtn").addEventListener("click", exportCsv);
    $("#langBtn").addEventListener("click", () => { lang = lang === "ar" ? "en" : "ar"; store.set("radar:lang", lang); applyLanguage(); });
    if (PREVIEW) { $("#exportBtn").hidden = true; $("#rssLink").hidden = true; }

    const rail = $("#rail"), scrim = $("#scrim");
    const openRail = () => { rail.classList.add("open"); scrim.hidden = false; $("#railOpen").setAttribute("aria-expanded", "true"); $("#q").focus(); };
    const closeRail = () => { rail.classList.remove("open"); scrim.hidden = true; $("#railOpen").setAttribute("aria-expanded", "false"); $("#railOpen").focus(); };
    $("#railOpen").addEventListener("click", openRail);
    $("#railClose").addEventListener("click", closeRail);
    $("#railDone").addEventListener("click", () => { closeRail(); window.scrollTo({ top: $("#results").offsetTop - 8 }); });
    scrim.addEventListener("click", closeRail);
    document.addEventListener("keydown", e => {
      if (e.key === "Escape" && rail.classList.contains("open")) closeRail();
      const tag = document.activeElement?.tagName;
      if (e.key === "/" && tag !== "INPUT" && tag !== "SELECT" && tag !== "TEXTAREA") {
        e.preventDefault();
        if (matchMedia("(max-width: 900px)").matches) openRail();
        $("#q").focus();
      }
    });
    $("#shareBtn").addEventListener("click", async () => {
      const enc = encodeState(state);
      const link = location.href.split("#")[0] + (enc ? "#" + enc : "");
      try { await navigator.clipboard.writeText(link); toast(t("t.copied")); } catch { toast(t("t.copyFail")); }
    });
    const pdlg = $("#profileDialog");
    const openProfile = () => { fillProfileForm(); pdlg.showModal ? pdlg.showModal() : pdlg.setAttribute("open", ""); };
    $("#profileBtn").addEventListener("click", openProfile);
    $("#profileEdit").addEventListener("click", openProfile);
    pdlg.addEventListener("close", () => { if (pdlg.returnValue === "save") saveProfile(); });
    const cdlg = $("#calendarDialog");
    $("#calendarBtn").addEventListener("click", () => { renderCalendarDialog(); cdlg.showModal ? cdlg.showModal() : cdlg.setAttribute("open", ""); });
    const fdlg = $("#feedDialog");
    $("#rssLink").addEventListener("click", () => { renderFeedDialog(); fdlg.showModal ? fdlg.showModal() : fdlg.setAttribute("open", ""); });
    $("#calMine").addEventListener("click", downloadMine);
    if (PREVIEW) $("#calendarBtn").hidden = true;
    const dlg = $("#sourcesDialog");
    $("#sourcesBtn").addEventListener("click", () => { renderSources(); dlg.showModal ? dlg.showModal() : dlg.setAttribute("open", ""); });
    $("#freshBtn").addEventListener("click", applyPending);
    matchMedia("(max-width: 520px)").addEventListener("change", renderPager);
    window.addEventListener("hashchange", () => {
      const enc = location.hash.slice(1);
      if (enc === encodeState(state)) return;
      state = decodeState(enc); syncControls(); update();
    });
  }

  function prep(i, gen, archived = false) {
    const it = { ...i, degrees: i.degrees || [], fields: i.fields || [], also_on: i.also_on || [], intakes: i.intakes || [],
      countries: i.countries || (i.country ? [i.country] : []), regions: i.regions || [] };
    it._archived = archived;
    it._days = it.deadline ? Math.round((parseDay(it.deadline) - today) / DAY) : null;
    it._reopenDays = it.reopens ? Math.round((parseDay(it.reopens) - today) / DAY) : null;
    it._addedDays = it.first_seen ? (gen - new Date(it.first_seen)) / DAY : null;
    const pub = it.published ? parseDay(it.published) : null;
    it._new = !archived && it._addedDays !== null && it._addedDays <= 7 && (!pub || (gen - pub) / DAY <= 10) && !it.reopened_at;
    it._reopened = !archived && it.reopened_at && (gen - new Date(it.reopened_at)) / DAY <= 14;
    it._sources = [it.source, ...it.also_on.map(a => a.source)];
    it._title = displayTitle(it.title).toLowerCase();
    it._summary = cleanSummary(it.title, it.summary);
    it._intakeYears = [...new Set(it.intakes.map(k => k.slice(0, 4)))];
    it._intakeOrder = it.intakes.length ? intakeOrder(it.intakes[0]) : 1e9;
    if (it.countries.length === 1 && it.regions.length === 1) REGION_OF[it.countries[0]] = it.regions[0];
    it._elig = eligibilityFor(it);
    const words = [it.title, it.org, it.summary, it.type, it.eligibility_note, ...it.countries, ...it.regions, ...it.degrees,
      ...it.fields.map(f => FIELD_LABELS[f] || f)];
    for (const lg of ["en", "ar"]) {
      words.push(LABELS[lg].type[it.type], ...it.degrees.map(d => LABELS[lg].degree[d]), ...it.regions.map(r => LABELS[lg].region[r]));
      for (const k of it.intakes) {
        const [y, part = ""] = k.split("-");
        if (part && part !== "ay") words.push(STRINGS[lg]["season." + part].replace("{y}", y));
      }
    }
    words.push(...it.fields.map(f => LABELS.ar.field[f]));
    if (arRegionNames) words.push(...it.countries.map(c => (ISO[c] ? arRegionNames.of(ISO[c]) : "")));
    it._hay = words.filter(Boolean).join(" ").toLowerCase();
    return it;
  }

  function prepare(data, refresh = false) {
    DATA = data;
    today = startOfDay(new Date());
    FIELD_LABELS = data.field_labels || {};
    profile = store.get("radar:profile", null) || defaultProfile();
    const gen = data.generated_at ? new Date(data.generated_at) : new Date();
    ITEMS = (data.items || []).map(i => prep(i, gen));
    if (refresh && archiveState === "ready") { archiveState = "idle"; ARCHIVE = []; }
    renderUpdated(); renderCredits();
    if (refresh) { const y = window.scrollY; update(); window.scrollTo(0, y); ensureArchive(); return; }
    const hash = location.hash.slice(1);
    state = hash.includes("=") ? decodeState(hash) : decodeState(store.get("radar:last", ""));
    syncControls();
    update();
    ensureArchive();
  }

  async function checkForUpdates() {
    lastCheck = Date.now();
    let data;
    try {
      const r = await fetch("data/opportunities.json", { cache: "no-cache" });
      if (!r.ok) return;
      data = await r.json();
    } catch { return; }
    if (!data?.generated_at || data.generated_at === DATA?.generated_at) return;
    const known = new Set(ITEMS.map(i => i.id));
    const added = (data.items || []).filter(i => !known.has(i.id));
    if (!added.length) { prepare(data, true); return; }
    pending = { data, added: added.map(i => i.id) };
    $("#freshText").textContent = t("fresh.text", { n: tn("opportunity", added.length) });
    $("#fresh").hidden = false;
  }
  function applyPending() {
    if (!pending) return;
    pending.added.forEach(id => justAdded.add(id));
    prepare(pending.data, true);
    pending = null;
    $("#fresh").hidden = true;
    toast(t("t.latest"));
  }
  function startLiveUpdates() {
    if (PREVIEW) return;
    setInterval(checkForUpdates, 10 * 60 * 1000);
    setInterval(renderUpdated, 60 * 1000);
    document.addEventListener("visibilitychange", () => { if (!document.hidden && Date.now() - lastCheck > 5 * 60 * 1000) checkForUpdates(); });
  }

  async function load() {
    bind();
    applyLanguage();
    if (window.__RADAR_DATA__) return prepare(window.__RADAR_DATA__);
    try {
      const r = await fetch("data/opportunities.json", { cache: "no-cache" });
      if (!r.ok) throw new Error("HTTP " + r.status);
      prepare(await r.json());
      startLiveUpdates();
    } catch {
      $("#updated").textContent = t("loadError");
    }
  }

  load();
})();
