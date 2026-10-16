"""Expand an nlc_spec.json into a page plan, then render interior + cover PDFs."""

import random
from pathlib import Path

from reportlab.pdfgen import canvas

from nlc import pages as P
from nlc import puzzles
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


def build_plan(spec: dict, base: Path, strict: bool = False) -> tuple[list, list[str]]:
    """Return ([(renderer, kwargs), ...], warnings) — one entry per interior page."""
    rng = random.Random(spec.get("seed", 1))
    warnings, plan = [], []
    meta = {k: spec.get(k, "") for k in ("title", "subtitle", "author", "publisher")}
    meta["year"] = spec.get("copyright_year", "")
    for fm in spec.get("front_matter", []):
        plan.append(_task(P.REGISTRY[fm], **meta))
    sol_blocks = []
    single = spec.get("single_sided", False)

    for sec in spec["sections"]:
        t, n = sec["type"], int(sec.get("count", 1))
        opts = {k: v for k, v in sec.items() if k not in ("type", "count", "solutions", "puzzles", "prompts")}
        if t == "prompt":
            for pr in sec.get("prompts", []):
                plan.append(_task(P.prompt_page, prompt=pr, **opts))
        elif t in P.REGISTRY:
            if sec.get("alphabetical"):
                letters = [chr(65 + i // per) for i in range(n) for per in [max(1, n // 26)]][:n]
                letters = [min(l, "Z") for l in letters]
                opts.pop("alphabetical")
                plan += [_task(P.REGISTRY[t], letter=l, **opts) for l in letters]
            else:
                plan += [_task(P.REGISTRY[t], **opts) for _ in range(n)]
        elif t in PUZZLE_TYPES:
            items = []
            for i in range(n):
                title = f"Puzzle {i + 1}"
                if t == "wordsearch":
                    pz = sec.get("puzzles") or []
                    if i >= len(pz):
                        raise ValueError(f"wordsearch needs {n} entries in 'puzzles' (have {len(pz)})")
                    data = puzzles.make_wordsearch(pz[i]["words"], sec.get("size", 15),
                                                   sec.get("difficulty", "medium"), rng)
                    if data["skipped"]:
                        warnings.append(f"wordsearch {i + 1}: skipped words {data['skipped']}")
                    title = pz[i].get("title", title)
                    renderer = P.wordsearch_page
                elif t == "sudoku":
                    data = puzzles.make_sudoku(sec.get("difficulty", "medium"), rng)
                    renderer = P.sudoku_page
                else:
                    data = puzzles.make_maze(sec.get("cols", 22), sec.get("rows", 30), rng)
                    renderer = P.maze_page
                plan.append(_task(renderer, data=data, title=title))
                items.append((title, data))
            if sec.get("solutions", True):
                sol_blocks.append((t, items))
        elif t == "coloring":
            art = base / sec.get("art_dir", "art")
            for i in range(n):
                files = sorted(art.glob(f"{i + 1:03d}.*")) if art.exists() else []
                img = files[0] if files else art / f"{i + 1:03d}.png"
                if not files:
                    warnings.append(f"missing art: {img}")
                plan.append(_task(P.coloring_page, image=str(img), strict=strict, label=f"page {i + 1}"))
                if single:
                    plan.append(_task(P.blank))
        else:
            raise ValueError(f"Unknown section type '{t}'")

    for kind, items in sol_blocks:
        c_, r_ = SOL_PER_PAGE[kind]
        for i in range(0, len(items), c_ * r_):
            plan.append(_task(P.solutions_page, items=items[i:i + c_ * r_], kind=kind, cols=c_, rows=r_))

    target = int(spec.get("page_count") or 0)
    if target and len(plan) > target:
        raise ValueError(f"Content needs {len(plan)} pages but page_count is {target}. "
                         f"Raise page_count or reduce section counts.")
    if not target:
        target = max(24, len(plan))
    if target % 2:
        target += 1
    pad = spec.get("pad_with", "lined")
    while len(plan) < target:
        plan.append(_task(P.REGISTRY[pad], header="Notes") if pad == "lined" else _task(P.REGISTRY[pad]))
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
