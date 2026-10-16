"""Expand an nlc_spec.json into a page plan, then render interior + cover PDFs."""

import random
from pathlib import Path

from reportlab.pdfgen import canvas

import re

from nlc import kidpages as K
from nlc import pages as P
from nlc import puzzles
from nlc.theme import Theme, ThemedGeometry, draw_chrome
from nlc.specs import PT, TRIMS, Geometry, cover_dims, validate, COVER_SPINE_TEXT_MIN_PAGES

PRESETS = {
    "journal": {"sections": [{"type": "lined", "count": 100, "header": ""}]},
    "dot_journal": {"sections": [{"type": "dotted", "count": 110}]},
    "sketchbook": {"sections": [{"type": "blank", "count": 100}]},
    "gratitude_journal": {"sections": [{"type": "gratitude", "count": 100}]},
    "daily_planner": {"sections": [{"type": "daily_planner", "count": 110}]},
    "weekly_planner": {"sections": [
        {"type": "monthly_calendar", "count": 12}, {"type": "weekly_planner", "count": 53},
        {"type": "lined", "count": 20, "header": "Notes"}]},
    "habit_tracker": {"sections": [{"type": "habit_tracker", "count": 24}, {"type": "lined", "count": 20, "header": "Notes"}]},
    "reading_log": {"sections": [{"type": "log_table", "count": 100, "title": "Reading Log",
        "columns": ["Title", "Author", "Started", "Finished", "Rating"], "widths": [3, 2, 1.2, 1.2, 1]}]},
    "workout_log": {"sections": [{"type": "log_table", "count": 100, "title": "Workout Log",
        "columns": ["Date", "Exercise", "Sets", "Reps", "Weight", "Notes"], "widths": [1.2, 3, 0.8, 0.8, 1, 2.5]}]},
    "password_log": {"sections": [{"type": "password", "count": 104, "alphabetical": True}]},
    "address_book": {"sections": [{"type": "address", "count": 104, "alphabetical": True}]},
    "meal_planner": {"sections": [{"type": "meal_planner", "count": 52}, {"type": "grocery_list", "count": 52}]},
    "recipe_book": {"sections": [{"type": "recipe", "count": 100}]},
    "budget_planner": {"sections": [{"type": "budget", "count": 24}, {"type": "log_table", "count": 24,
        "title": "Expense Tracker", "columns": ["Date", "Description", "Category", "Amount"], "widths": [1, 3, 1.6, 1.2]}]},
    "blood_pressure_log": {"trim": "8.5x11", "sections": [{"type": "log_table", "count": 100, "title": "Blood Pressure Log",
        "columns": ["Date", "Time", "Systolic", "Diastolic", "Pulse", "Notes"], "widths": [1.2, 1, 1, 1, 0.9, 2.5]}]},
    "glucose_log": {"sections": [{"type": "log_table", "count": 100, "title": "Blood Sugar Log",
        "columns": ["Date", "Fasting", "Before Meal", "After Meal", "Bedtime", "Notes"], "widths": [1.2, 1, 1.2, 1.2, 1, 2]}]},
    "medication_log": {"sections": [{"type": "log_table", "count": 100, "title": "Medication Log",
        "columns": ["Date", "Medication", "Dose", "Time", "Taken"], "widths": [1.2, 2.5, 1.2, 1, 0.8]}]},
    "mileage_log": {"trim": "8.5x11", "sections": [{"type": "log_table", "count": 100, "title": "Mileage Log",
        "columns": ["Date", "Purpose", "Start Odo", "End Odo", "Miles", "Parking/Tolls"], "widths": [1.2, 3, 1.2, 1.2, 0.9, 1.3]}]},
    "sleep_log": {"sections": [{"type": "log_table", "count": 100, "title": "Sleep Log",
        "columns": ["Date", "Bedtime", "Wake", "Hours", "Quality 1-5", "Notes"], "widths": [1.2, 1, 1, 0.8, 1, 2.5]}]},
    "wordsearch": {"sections": [{"type": "wordsearch", "count": 1, "size": 15, "difficulty": "medium",
        "puzzles": [{"title": "Puzzle 1", "words": ["EXAMPLE", "WORDS", "GO", "HERE"]}], "solutions": True}]},
    "sudoku": {"sections": [{"type": "sudoku", "count": 100, "difficulty": "medium", "solutions": True}]},
    "maze": {"sections": [{"type": "maze", "count": 50, "cols": 22, "rows": 30, "solutions": True}]},
    "kids_activity": {
        "trim": "8.5x11", "page_count": 48, "pad_with": "notes",
        "card_fields": ["Player name:", "Shirt number:", "Team name:", "My secret skill:"],
        "theme": {
            "mascot": {"name": "Buddy", "style": "ball_buddy"},
            "palette": {"ink": "#1c1c1c", "tone": "#d6d6d6"},
            "frame": "stitched", "icon": "star",
            "fonts": {"display": "Fredoka-Bold.ttf", "body": "Nunito-Regular.ttf",
                      "body_bold": "Nunito-Bold.ttf", "body_italic": "Nunito-Italic.ttf"},
            "notes_title": "Buddy's Notes", "answer_line": "Peeking is allowed. Buddy won't tell.",
            "lines": ["EDIT: a joke in your book's voice", "EDIT: a fun fact you have verified",
                      "EDIT: a mini challenge", "EDIT: a friendly taunt", "EDIT: a pep line", "EDIT: a silly warning",
                      "EDIT: a tip from the mascot", "EDIT: a question for the reader"]},
        "sections": [
            {"type": "pages", "items": [
                {"type": "prompt", "kind": "opinion", "phase": "Warm-up", "line": "EDIT",
                 "text": "EDIT: a specific, surprising scenario a child can answer in three sentences."},
                {"type": "prompt", "kind": "wyr", "phase": "Warm-up", "line": "EDIT", "text": "Would you rather...",
                 "options": ["EDIT option A", "EDIT option B"]},
                {"type": "doodle", "phase": "Warm-up", "starter": "ball", "line": "EDIT",
                 "text": "EDIT: a directed drawing challenge with a printed starter (boot, ball, goal, stadium, shirt, "
                         "trophy, pitch, panels, badge, scoreboard, face)."},
                {"type": "prompt", "kind": "ranking", "phase": "Warm-up", "line": "EDIT", "items": 5,
                 "text": "EDIT: rank five specific things from best to worst."}]},
            {"type": "wordsearch", "count": 1, "size": 10, "difficulty": "easy", "phase": "Warm-up", "line": "EDIT",
             "puzzles": [{"title": "EDIT", "blurb": "EDIT: mascot speech line.",
                          "words": ["EDIT", "ME", "WITH", "TWELVE", "THEMED", "WORDS"],
                          "secret": {"word": "EDIT", "clue": "EDIT: a clue for the hidden word."}}], "solutions": True},
            {"type": "maze", "count": 1, "cols": 8, "rows": 10, "collect": 3, "phase": "Warm-up", "line": "EDIT",
             "titles": ["EDIT"], "blurbs": ["EDIT: mascot speech line."]},
            {"type": "pages", "items": [
                {"type": "report", "phase": "Full time", "line": "EDIT", "header": "Player Report"}]}]},
    "coloring": {"single_sided": True, "sections": [{"type": "coloring", "count": 40, "art_dir": "art"}]},
}

PUZZLE_TYPES = {"wordsearch", "sudoku", "maze"}
SOL_PER_PAGE = {"wordsearch": (2, 3), "sudoku": (2, 3), "maze": (2, 2)}


def default_spec(book_type: str, title: str = "Untitled") -> dict:
    if book_type not in PRESETS:
        raise ValueError(f"Unknown type '{book_type}'. Options: {', '.join(PRESETS)}")
    return {
        "title": title, "subtitle": "", "author": "", "publisher": "Independently Published",
        "copyright_year": "2026", "trim": "6x9", "paper": "white", "bleed": False,
        "page_count": 120, "pad_with": "lined", "seed": 1,
        "front_matter": ["title", "copyright", "belongs_to"],
        "cover": {"bg": "#1f3a5f", "fg": "#ffffff", "accent": "#f2b134", "image": "",
                  "back_description": "", "tagline": ""},
        "coloring_prompts": [],
        "single_sided": False,
        **PRESETS[book_type],
    }


def _task(fn, **kw):
    return (fn, kw)


META_KEYS = {"type", "header", "title", "phase", "line", "mood", "art_prompt", "art"}
MOODS = ["happy", "wink", "cheer", "happy", "tough"]


def art_name(item: dict) -> str:
    """Project-relative PNG name for a page's illustration slot (Ideogram output goes here)."""
    if item.get("art"):
        return item["art"]
    words = re.sub(r"[^a-z0-9 ]", "", (item.get("title") or item.get("text") or "page").lower()).split()[:4]
    return "art/" + ("-".join(words) or "page") + ".png"


def collect_art_prompts(spec: dict) -> list[tuple[str, str]]:
    """(filename, prompt) for every page item that carries an `art_prompt` (for Ideogram)."""
    out = []
    for sec in spec.get("sections", []):
        for it in (sec.get("prompts") or []) + (sec.get("items") or []):
            if isinstance(it, dict) and it.get("art_prompt"):
                out.append((art_name(it), it["art_prompt"]))
    return out


def build_plan(spec: dict, base: Path, strict: bool = False) -> tuple[list, list[str]]:
    """Return ([(renderer, kwargs), ...], warnings) — one entry per interior page."""
    rng = random.Random(spec.get("seed", 1))
    warnings, plan = [], []
    theme = Theme(spec["theme"], base) if spec.get("theme") else None
    if theme:
        warnings += [f"font not found, using built-in fallback: {f}" for f in theme.missing_fonts]
    meta = {k: spec.get(k, "") for k in ("title", "subtitle", "author", "publisher")}
    meta["year"] = spec.get("copyright_year", "")
    counter = [0]

    def task(fn, chrome=None, **kw):
        if theme:
            kw["theme"] = theme
            if chrome is not None:
                kw["_chrome"] = chrome
        return (fn, kw)

    def mk_chrome(sec, item, default_header, idx=0):
        if not theme or sec.get("chrome") is False:
            return None
        item = item if isinstance(item, dict) else {}
        lines = sec.get("lines")
        line = item.get("line") or (lines[idx % len(lines)] if lines else sec.get("line")) or theme.line_for(counter[0])
        mood = item.get("mood") or sec.get("mood") or MOODS[counter[0] % len(MOODS)]
        counter[0] += 1
        return {"header": item.get("header") or item.get("title") or sec.get("header") or sec.get("title")
                or default_header, "phase": item.get("phase", sec.get("phase", "")), "line": line, "mood": mood}

    for fm in spec.get("front_matter", []):
        if theme and fm == "title":
            plan.append(task(K.title_page_themed, **meta))
        elif theme and fm == "belongs_to":
            plan.append(task(K.belongs_themed, fields=spec.get("card_fields")))
        else:
            plan.append(task(P.REGISTRY[fm], **meta))
    sol_blocks: dict[str, list] = {}
    single = spec.get("single_sided", False)

    def item_task(sec, raw, idx, default_type):
        item = {"text": raw} if isinstance(raw, str) else dict(raw)
        ityp = item.get("type", default_type)
        opts = {k: v for k, v in item.items() if k not in META_KEYS}
        if item.get("art_prompt") or item.get("art"):
            opts["art"] = str(base / art_name(item))
        if ityp in ("prompt", "prompt_card"):
            if theme:
                opts.setdefault("kind", "opinion")
                return task(K.prompt_card, mk_chrome(sec, item, theme.headers.get(opts["kind"], "Challenge"), idx),
                            **opts)
            return task(P.prompt_page, prompt=item.get("text", ""))
        if ityp == "doodle":
            return task(K.doodle, mk_chrome(sec, item, "Doodle Challenge", idx), **opts)
        if ityp == "report":
            return task(K.report, mk_chrome(sec, item, "Player Report", idx), **opts)
        if ityp == "notes":
            return task(K.notes_page, mk_chrome(sec, item, "Notes", idx), **opts)
        if ityp in P.REGISTRY:
            opts = {k: v for k, v in opts.items() if not (theme and k == "header")}
            return task(P.REGISTRY[ityp], mk_chrome(sec, item, item.get("header", ityp.title()), idx), **opts)
        raise ValueError(f"Unknown page type '{ityp}'")

    for sec in spec["sections"]:
        t, n = sec["type"], int(sec.get("count", 1))
        opts = {k: v for k, v in sec.items() if k not in
                ("type", "count", "solutions", "puzzles", "prompts", "items", "phase", "line", "lines", "mood",
                 "chrome", "titles", "blurbs", "collect")}
        if t in ("prompt", "doodle", "pages"):
            items = sec.get("prompts") if t == "prompt" else sec.get("items")
            for i, raw in enumerate(items or []):
                plan.append(item_task(sec, raw, i, {"prompt": "prompt", "doodle": "doodle"}.get(t, "notes")))
        elif t in ("report", "notes"):
            for i in range(n):
                plan.append(item_task(sec, dict(opts), i, t))
        elif t in P.REGISTRY:
            if theme:
                opts.pop("header", None)
            default_h = sec.get("header") or sec.get("title") or t.replace("_", " ").title()
            if sec.get("alphabetical"):
                letters = [chr(65 + i // per) for i in range(n) for per in [max(1, n // 26)]][:n]
                letters = [min(l, "Z") for l in letters]
                opts.pop("alphabetical")
                plan += [task(P.REGISTRY[t], mk_chrome(sec, {}, default_h, i), letter=l, **opts)
                         for i, l in enumerate(letters)]
            else:
                plan += [task(P.REGISTRY[t], mk_chrome(sec, {}, default_h, i), **opts) for i in range(n)]
        elif t in PUZZLE_TYPES:
            items = []
            for i in range(n):
                title = f"Puzzle {i + 1}"
                extra = {}
                if t == "wordsearch":
                    pz = sec.get("puzzles") or []
                    if i >= len(pz):
                        raise ValueError(f"wordsearch needs {n} entries in 'puzzles' (have {len(pz)})")
                    cfg = pz[i]
                    secret = cfg.get("secret", "")
                    secret = secret.get("word", "") if isinstance(secret, dict) else secret
                    data = puzzles.make_wordsearch(cfg["words"], cfg.get("size", sec.get("size", 15)),
                                                   cfg.get("difficulty", sec.get("difficulty", "medium")), rng,
                                                   secret=secret)
                    if data["skipped"]:
                        warnings.append(f"wordsearch {i + 1}: skipped words {data['skipped']}")
                    title = cfg.get("title", title)
                    clue = cfg.get("clue") or (cfg["secret"].get("clue", "") if isinstance(cfg.get("secret"), dict) else "")
                    extra = {"blurb": cfg.get("blurb", ""), "clue": clue if secret else ""}
                    renderer, item = P.wordsearch_page, cfg
                elif t == "sudoku":
                    data = puzzles.make_sudoku(sec.get("difficulty", "medium"), rng)
                    renderer, item = P.sudoku_page, {}
                else:
                    data = puzzles.make_maze(sec.get("cols", 22), sec.get("rows", 30), rng)
                    k = int(sec.get("collect", 0))
                    if k:
                        path = data["path"]
                        data["stars"] = [path[round(len(path) * (j + 1) / (k + 1))] for j in range(k)]
                    titles, blurbs = sec.get("titles") or [], sec.get("blurbs") or []
                    title = titles[i] if i < len(titles) else (f"{sec.get('header', 'Maze')} {i + 1}")
                    extra = {"blurb": blurbs[i] if i < len(blurbs) else ""}
                    renderer, item = P.maze_page, {}
                plan.append(task(renderer, mk_chrome(sec, {**item, "title": title}, title, i), data=data,
                                 title=title, **extra))
                items.append((title, data))
            if sec.get("solutions", True):
                sol_blocks.setdefault(t, []).extend(items)
        elif t == "coloring":
            art = base / sec.get("art_dir", "art")
            for i in range(n):
                files = sorted(art.glob(f"{i + 1:03d}.*")) if art.exists() else []
                img = files[0] if files else art / f"{i + 1:03d}.png"
                if not files:
                    warnings.append(f"missing art: {img}")
                plan.append(task(P.coloring_page, image=str(img), strict=strict, label=f"page {i + 1}"))
                if single:
                    plan.append(task(P.blank))
        else:
            raise ValueError(f"Unknown section type '{t}'")

    for kind, items in sol_blocks.items():
        c_, r_ = SOL_PER_PAGE[kind]
        for i in range(0, len(items), c_ * r_):
            ch = None
            if theme:
                ch = {"header": spec.get("answer_header", "Answer Key"), "phase": "No peeking!",
                      "line": theme.cfg.get("answer_line", "Stuck? It's allowed. Just don't tell the others."),
                      "mood": "wink"}
            plan.append(task(P.solutions_page, ch, items=items[i:i + c_ * r_], kind=kind, cols=c_, rows=r_))

    target = int(spec.get("page_count") or 0)
    if target and len(plan) > target:
        raise ValueError(f"Content needs {len(plan)} pages but page_count is {target}. "
                         f"Raise page_count or reduce section counts.")
    if not target:
        target = max(24, len(plan))
    if target % 2:
        target += 1
    pad = spec.get("pad_with", "lined")
    pad_pages = spec.get("pad_pages") or []
    k = 0
    while len(plan) < target:
        if theme and pad in ("lined", "notes"):
            if pad_pages:
                fn_, kw_ = item_task({"chrome": True}, pad_pages[k % len(pad_pages)], k, "notes")
            else:
                fn_, kw_ = task(K.notes_page, mk_chrome({}, {}, theme.cfg.get("notes_title", "Coach's Notes"), k))
            plan.append((fn_, {**kw_, "_pad": True}))
            k += 1
        else:
            fn_, kw_ = task(P.REGISTRY[pad], header="Notes") if pad == "lined" else task(P.REGISTRY[pad])
            plan.append((fn_, {**kw_, "_pad": True}))
    return plan, warnings


def build_interior(spec: dict, plan: list, out: Path) -> Geometry:
    pages = len(plan)
    validate(spec["trim"], spec["paper"], pages)
    tw, th = TRIMS[spec["trim"]]
    g = Geometry(tw, th, pages, bool(spec.get("bleed", False)))
    c = canvas.Canvas(str(out), pagesize=(g.page_w, g.page_h))
    c.setTitle(spec["title"])
    c.setAuthor(spec.get("author", ""))
    for i, (fn, kw) in enumerate(plan, 1):
        kw = dict(kw)
        chrome = kw.pop("_chrome", None)
        if chrome is not None:
            draw_chrome(c, g, i, kw["theme"], **chrome)
            fn(c, ThemedGeometry(g), i, **kw)
        else:
            fn(c, g, i, **kw)
        c.showPage()
    c.save()
    return g


def _hex(value: str):
    value = value.lstrip("#")
    return tuple(int(value[i:i + 2], 16) / 255 for i in (0, 2, 4))


def build_cover(spec: dict, pages: int, out: Path, base: Path) -> dict:
    from reportlab.lib.utils import ImageReader, simpleSplit
    tw, th = TRIMS[spec["trim"]]
    d = cover_dims((tw, th), pages, spec["paper"])
    W, H, S = d["width"] * PT, d["height"] * PT, d["spine"] * PT
    B, tw_p, th_p = 0.125 * PT, tw * PT, th * PT
    cv = spec.get("cover", {})
    c = canvas.Canvas(str(out), pagesize=(W, H))
    c.setTitle(spec["title"] + " (cover)")
    bg, fg, ac = _hex(cv.get("bg", "#1f3a5f")), _hex(cv.get("fg", "#ffffff")), _hex(cv.get("accent", "#f2b134"))
    c.setFillColorRGB(*bg)
    c.rect(0, 0, W, H, stroke=0, fill=1)
    fx = B + tw_p + S                     # front panel left edge
    img = cv.get("image")
    if img and (base / img).exists():
        c.drawImage(ImageReader(str(base / img)), fx, 0, tw_p + B, H, preserveAspectRatio=False)
    safe = 0.375 * PT
    c.setFillColorRGB(*fg)
    maxw = tw_p - 2 * safe
    y = H - B - th_p * 0.22
    size = 34
    lines = simpleSplit(spec["title"].upper(), "Helvetica-Bold", size, maxw)
    if len(lines) > 3:
        size = 26
        lines = simpleSplit(spec["title"].upper(), "Helvetica-Bold", size, maxw)
    c.setFont("Helvetica-Bold", size)
    cx = fx + tw_p / 2
    for ln in lines:
        c.drawCentredString(cx, y, ln)
        y -= size * 1.15
    c.setFillColorRGB(*ac)
    c.rect(cx - 50, y + size * 0.5, 100, 3, stroke=0, fill=1)
    y -= size * 0.6
    c.setFillColorRGB(*fg)
    if spec.get("subtitle"):
        c.setFont("Helvetica", 14)
        for ln in simpleSplit(spec["subtitle"], "Helvetica", 14, maxw):
            c.drawCentredString(cx, y, ln)
            y -= 18
    if spec.get("author"):
        c.setFont("Helvetica-Bold", 14)
        c.drawCentredString(cx, B + safe, spec["author"])
    # Back cover
    bx0, bw = B + safe, tw_p - 2 * safe
    by = H - B - safe - 20
    if cv.get("tagline"):
        c.setFont("Helvetica-Bold", 16)
        for ln in simpleSplit(cv["tagline"], "Helvetica-Bold", 16, bw):
            c.drawString(bx0, by, ln)
            by -= 21
        by -= 8
    c.setFont("Helvetica", 11)
    for para in cv.get("back_description", "").split("\n"):
        for ln in (simpleSplit(para, "Helvetica", 11, bw) if para.strip() else [""]):
            c.drawString(bx0, by, ln)
            by -= 15
    # Barcode zone: 2.0 x 1.2 in, bottom-right of back cover
    c.setFillColorRGB(1, 1, 1)
    c.rect(B + tw_p - 0.25 * PT - 2.0 * PT, B + 0.25 * PT, 2.0 * PT, 1.2 * PT, stroke=0, fill=1)
    # Spine text (KDP recommends only for 79+ pages)
    if pages >= COVER_SPINE_TEXT_MIN_PAGES:
        c.saveState()
        c.translate(B + tw_p + S / 2, H / 2)
        c.rotate(-90)
        c.setFillColorRGB(*fg)
        fs = min(18.0, S * 0.55)
        while c.stringWidth(spec["title"], "Helvetica-Bold", fs) > th_p - 2 * safe and fs > 6:
            fs -= 1
        c.setFont("Helvetica-Bold", fs)
        c.drawCentredString(0, -fs * 0.35, spec["title"])
        c.restoreState()
    c.save()
    return d


def kdp_report(spec: dict, pages: int, g: Geometry, cover: dict, warnings: list[str]) -> str:
    tw, th = TRIMS[spec["trim"]]
    bleed = "yes" if g.bleed else 'no (choose "No Bleed" in KDP)'
    lines = [
        f"# KDP Upload Specs — {spec['title']}", "",
        f"- **Trim size:** {tw} x {th} in ({spec['trim']})",
        f"- **Paper / ink:** {spec['paper']}",
        f"- **Page count:** {pages}",
        f"- **Interior bleed:** {bleed}",
        f"- **Margins:** gutter {g.gutter} in, outside/top/bottom {g.outer} in",
        f"- **Spine width:** {cover['spine']} in"
        + ("" if pages >= COVER_SPINE_TEXT_MIN_PAGES else " (under 79 pages: no spine text)"),
        f"- **Full-wrap cover size:** {cover['width']} x {cover['height']} in (includes 0.125 in bleed)",
        "", "## Files", "- `interior.pdf` — upload as manuscript",
        "- `cover.pdf` — upload as print-ready cover (verify against KDP's cover calculator)",
        "", "## Before you publish",
        "- Run KDP's online previewer and fix any bleed/margin warnings.",
        "- Low-content books (journals, planners, logs, puzzles) may use KDP's free ISBN; "
        "mark the book as low-content in KDP if it applies.",
        "- Make sure every font, image, and word list is yours or properly licensed.",
    ]
    if warnings:
        lines += ["", "## Warnings"] + [f"- {w}" for w in warnings]
    return "\n".join(lines) + "\n"
