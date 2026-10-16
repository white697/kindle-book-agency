"""Interior page renderers. Every renderer: fn(c, g, page_no, **opts) draws one page on canvas `c`."""

from pathlib import Path

from reportlab.lib.utils import ImageReader, simpleSplit

from nlc import puzzles
from nlc.specs import PT

GREY = (0.62, 0.62, 0.62)
LIGHT = (0.8, 0.8, 0.8)
BLACK = (0, 0, 0)
FONT, BOLD = "Helvetica", "Helvetica-Bold"


def _stroke(c, rgb, w=0.5):
    c.setStrokeColorRGB(*rgb)
    c.setLineWidth(w)


def _heading(c, g, p, text, size=18):
    x0, y0, x1, y1 = g.box(p)
    c.setFillColorRGB(*BLACK)
    c.setFont(BOLD, size)
    c.drawString(x0, y1 - size, text)
    return y1 - size - 10


def _centered(c, g, p, text, y, font=FONT, size=12):
    x0, _, x1, _ = g.box(p)
    c.setFont(font, size)
    c.drawCentredString((x0 + x1) / 2, y, text)


# ── Front matter ──────────────────────────────────────────────────────────

def title_page(c, g, p, title="", subtitle="", author="", **_):
    x0, y0, x1, y1 = g.box(p)
    c.setFillColorRGB(*BLACK)
    cy = y0 + (y1 - y0) * 0.6
    for i, line in enumerate(simpleSplit(title, BOLD, 30, x1 - x0)):
        _centered(c, g, p, line, cy - i * 36, BOLD, 30)
    cy -= 36 * len(simpleSplit(title, BOLD, 30, x1 - x0)) + 6
    for i, line in enumerate(simpleSplit(subtitle, FONT, 14, x1 - x0)):
        _centered(c, g, p, line, cy - i * 18, FONT, 14)
    if author:
        _centered(c, g, p, author, y0 + 60, FONT, 13)


def copyright_page(c, g, p, title="", author="", year="", publisher="", **_):
    x0, y0, x1, y1 = g.box(p)
    c.setFont(FONT, 9)
    y = y0 + 90
    for line in (f"Copyright © {year} {author or publisher}", "All rights reserved.",
                 "No part of this publication may be reproduced without written permission.",
                 f"Published by {publisher}" if publisher else ""):
        if line:
            c.drawString(x0, y, line)
            y -= 13


def belongs_to(c, g, p, **_):
    x0, y0, x1, y1 = g.box(p)
    _centered(c, g, p, "This book belongs to", y0 + (y1 - y0) * 0.55, BOLD, 18)
    _stroke(c, BLACK, 0.8)
    c.line(x0 + 40, y0 + (y1 - y0) * 0.45, x1 - 40, y0 + (y1 - y0) * 0.45)


def blank(c, g, p, **_):
    pass


# ── Writing surfaces ──────────────────────────────────────────────────────

def lined(c, g, p, spacing=0.3, header="", **_):
    x0, y0, x1, y1 = g.box(p)
    top = _heading(c, g, p, header, 16) if header else y1
    _stroke(c, LIGHT, 0.6)
    y = top - spacing * PT
    while y >= y0:
        c.line(x0, y, x1, y)
        y -= spacing * PT


def dotted(c, g, p, spacing=0.25, header="", **_):
    x0, y0, x1, y1 = g.box(p)
    top = _heading(c, g, p, header, 16) if header else y1
    c.setFillColorRGB(*GREY)
    s = spacing * PT
    y = top - s
    while y >= y0:
        x = x0
        while x <= x1 + 0.1:
            c.circle(x, y, 0.6, stroke=0, fill=1)
            x += s
        y -= s


def grid_page(c, g, p, spacing=0.25, header="", **_):
    x0, y0, x1, y1 = g.box(p)
    top = _heading(c, g, p, header, 16) if header else y1
    s = spacing * PT
    cols, rows = int((x1 - x0) / s), int((top - y0) / s)
    _stroke(c, LIGHT, 0.5)
    for i in range(cols + 1):
        c.line(x0 + i * s, top, x0 + i * s, top - rows * s)
    for j in range(rows + 1):
        c.line(x0, top - j * s, x0 + cols * s, top - j * s)


def prompt_page(c, g, p, prompt="", spacing=0.32, **_):
    x0, y0, x1, y1 = g.box(p)
    c.setFont(BOLD, 13)
    y = y1 - 14
    for line in simpleSplit(prompt, BOLD, 13, x1 - x0):
        c.drawString(x0, y, line)
        y -= 17
    _stroke(c, LIGHT, 0.6)
    y -= 8
    while y >= y0:
        c.line(x0, y, x1, y)
        y -= spacing * PT


# ── Planners & logs ───────────────────────────────────────────────────────

def _field(c, x, y, w, label, size=9):
    c.setFont(FONT, size)
    c.setFillColorRGB(*BLACK)
    c.drawString(x, y + 3, label)
    _stroke(c, GREY, 0.6)
    lw = c.stringWidth(label, FONT, size) + 6
    c.line(x + lw, y, x + w, y)


def _checkboxes(c, x, y, w, n, step=22):
    _stroke(c, GREY, 0.6)
    for i in range(n):
        yy = y - i * step
        c.rect(x, yy - 3, 9, 9)
        c.line(x + 16, yy - 3, x + w, yy - 3)


def daily_planner(c, g, p, **_):
    x0, y0, x1, y1 = g.box(p)
    top = _heading(c, g, p, "Daily Planner", 18)
    _field(c, x0, top - 6, 150, "Date:")
    _field(c, x1 - 150, top - 6, 150, "Weather/Mood:")
    mid = x0 + (x1 - x0) * 0.52
    y = top - 36
    c.setFont(BOLD, 10)
    c.drawString(x0, y, "Schedule")
    y -= 14
    hours = 16
    step = max(14, (y - y0) / hours)
    _stroke(c, LIGHT, 0.6)
    for i in range(hours):
        hh = 6 + i
        label = f"{(hh - 1) % 12 + 1}{'am' if hh < 12 else 'pm'}"
        c.setFont(FONT, 8)
        c.drawString(x0, y - i * step + 3, label)
        c.line(x0 + 24, y - i * step, mid - 14, y - i * step)
    c.setFont(BOLD, 10)
    c.drawString(mid, top - 36, "Top Priorities")
    _checkboxes(c, mid, top - 56, x1 - mid, 3, 22)
    c.setFont(BOLD, 10)
    c.drawString(mid, top - 140, "To-Do")
    _checkboxes(c, mid, top - 160, x1 - mid, 8, 22)
    c.setFont(BOLD, 10)
    c.drawString(mid, y0 + 100, "Notes")
    _stroke(c, LIGHT, 0.6)
    for i in range(4):
        c.line(mid, y0 + 80 - i * 20, x1, y0 + 80 - i * 20)


def weekly_planner(c, g, p, **_):
    x0, y0, x1, y1 = g.box(p)
    top = _heading(c, g, p, "Weekly Planner", 18)
    _field(c, x0, top - 6, 170, "Week of:")
    days = ["Monday", "Tuesday", "Wednesday", "Thursday", "Friday", "Saturday / Sunday"]
    top -= 26
    rows = len(days)
    h = (top - y0) / rows
    _stroke(c, GREY, 0.7)
    for i, d in enumerate(days):
        yy = top - (i + 1) * h
        c.rect(x0, yy, x1 - x0, h)
        c.setFont(BOLD, 10)
        c.drawString(x0 + 6, yy + h - 14, d)
        _stroke(c, LIGHT, 0.5)
        for k in range(1, int((h - 20) // 18) + 1):
            c.line(x0 + 6, yy + h - 18 - k * 16, x1 - 6, yy + h - 18 - k * 16)
        _stroke(c, GREY, 0.7)


def monthly_calendar(c, g, p, **_):
    x0, y0, x1, y1 = g.box(p)
    top = _heading(c, g, p, "Month: ______________   Year: ________", 15)
    top -= 4
    cw = (x1 - x0) / 7
    c.setFont(BOLD, 9)
    for i, d in enumerate(("SUN", "MON", "TUE", "WED", "THU", "FRI", "SAT")):
        c.drawCentredString(x0 + cw * (i + .5), top - 10, d)
    top -= 16
    ch = (top - y0) / 6
    _stroke(c, GREY, 0.7)
    for r in range(6):
        for col in range(7):
            c.rect(x0 + col * cw, top - (r + 1) * ch, cw, ch)


def habit_tracker(c, g, p, habits=7, **_):
    """Days run down the page (31 rows); one column per habit, with a write-in name box on top."""
    x0, y0, x1, y1 = g.box(p)
    top = _heading(c, g, p, "Habit Tracker", 18)
    _field(c, x0, top - 6, 170, "Month:")
    top -= 24
    day_w = 22
    cw = (x1 - x0 - day_w) / habits
    head_h = 46
    rh = (top - head_h - y0) / 31
    _stroke(c, GREY, 0.6)
    c.setFont(FONT, 7)
    c.setFillColorRGB(*BLACK)
    c.drawString(x0 + 3, top - head_h + 4, "Day")
    for h in range(habits):
        c.rect(x0 + day_w + h * cw, top - head_h, cw, head_h)
    for d in range(31):
        yy = top - head_h - (d + 1) * rh
        c.setFont(FONT, 7)
        c.drawString(x0 + 5, yy + rh * 0.3, str(d + 1))
        c.rect(x0, yy, day_w, rh)
        for h in range(habits):
            c.rect(x0 + day_w + h * cw, yy, cw, rh)


def gratitude(c, g, p, **_):
    x0, y0, x1, y1 = g.box(p)
    top = _heading(c, g, p, "Daily Gratitude", 18)
    _field(c, x0, top - 6, 170, "Date:")
    y = top - 40
    blocks = ["I am grateful for...", "What would make today great?", "Daily affirmation", "Highlights of the day"]
    h = (y - y0) / len(blocks)
    for b in blocks:
        c.setFont(BOLD, 11)
        c.drawString(x0, y, b)
        _stroke(c, LIGHT, 0.6)
        for k in range(1, int((h - 22) // 22) + 1):
            c.line(x0, y - 6 - k * 22, x1, y - 6 - k * 22)
        y -= h


def log_table(c, g, p, title="Log", columns=("Date", "Notes"), widths=None, rows=None, **_):
    x0, y0, x1, y1 = g.box(p)
    top = _heading(c, g, p, title, 18) - 4
    widths = widths or [1] * len(columns)
    tot = sum(widths)
    xs = [x0]
    for w in widths:
        xs.append(xs[-1] + (x1 - x0) * w / tot)
    hh = 22
    _stroke(c, GREY, 0.8)
    c.setFont(BOLD, 9)
    for i, col in enumerate(columns):
        c.rect(xs[i], top - hh, xs[i + 1] - xs[i], hh)
        c.drawString(xs[i] + 4, top - hh + 7, col)
    rh = 24 if rows is None else (top - hh - y0) / rows
    n = int((top - hh - y0) // rh)
    for r in range(n):
        for i in range(len(columns)):
            c.rect(xs[i], top - hh - (r + 1) * rh, xs[i + 1] - xs[i], rh)



# ── Password / address / meal / recipe / budget ───────────────────────────

def _letter_tab(c, g, p, letter):
    if not letter:
        return
    x0, y0, x1, y1 = g.box(p)
    c.setFillColorRGB(*BLACK)
    c.setFont(BOLD, 28)
    c.drawRightString(x1, y1 - 24, letter)


def _entry_cards(c, g, p, title, fields, letter="", per_page=5, field_gap=18):
    x0, y0, x1, y1 = g.box(p)
    top = _heading(c, g, p, title, 16) - 4
    _letter_tab(c, g, p, letter)
    h = (top - y0) / per_page
    for i in range(per_page):
        ytop = top - i * h
        _stroke(c, LIGHT, 0.8)
        c.roundRect(x0, ytop - h + 4, x1 - x0, h - 8, 4)
        for k, f in enumerate(fields):
            yy = ytop - 18 - k * field_gap
            _field(c, x0 + 6, yy, x1 - x0 - 12, f, 8)


def password_page(c, g, p, letter="", **_):
    _entry_cards(c, g, p, "Passwords", ["Website:", "Username / Email:", "Password:", "Notes:"], letter, 5, 17)


def address_page(c, g, p, letter="", **_):
    _entry_cards(c, g, p, "Address Book", ["Name:", "Address:", "Phone:", "Email:", "Birthday:"], letter, 6, 14)


def meal_planner(c, g, p, **_):
    x0, y0, x1, y1 = g.box(p)
    top = _heading(c, g, p, "Weekly Meal Planner", 18)
    _field(c, x0, top - 6, 170, "Week of:")
    top -= 26
    cols = ["Day", "Breakfast", "Lunch", "Dinner", "Snacks"]
    ws = [0.9, 1.3, 1.3, 1.3, 1.0]
    tot = sum(ws)
    xs = [x0]
    for w in ws:
        xs.append(xs[-1] + (x1 - x0) * w / tot)
    _stroke(c, GREY, 0.7)
    c.setFillColorRGB(*BLACK)
    c.setFont(BOLD, 8)
    for i, col in enumerate(cols):
        c.rect(xs[i], top - 18, xs[i + 1] - xs[i], 18)
        c.drawCentredString((xs[i] + xs[i + 1]) / 2, top - 12, col)
    notes_h = 110
    rh = (top - 18 - y0 - notes_h) / 7
    for r, day in enumerate(("Mon", "Tue", "Wed", "Thu", "Fri", "Sat", "Sun")):
        yy = top - 18 - (r + 1) * rh
        for i in range(5):
            c.rect(xs[i], yy, xs[i + 1] - xs[i], rh)
        c.setFont(BOLD, 9)
        c.drawString(xs[0] + 4, yy + rh / 2 - 3, day)
    c.setFont(BOLD, 10)
    c.drawString(x0, y0 + notes_h - 14, "Notes / Prep")
    _stroke(c, LIGHT, 0.6)
    for k in range(1, 5):
        c.line(x0, y0 + notes_h - 14 - k * 18, x1, y0 + notes_h - 14 - k * 18)


def grocery_list(c, g, p, **_):
    x0, y0, x1, y1 = g.box(p)
    top = _heading(c, g, p, "Grocery List", 18)
    _field(c, x0, top - 6, 150, "Store/Date:")
    top -= 24
    cats = ["Produce", "Dairy & Eggs", "Meat & Fish", "Pantry", "Frozen", "Other"]
    gap = 14
    cw, ch = (x1 - x0 - gap) / 2, (top - y0) / 3
    for i, cat in enumerate(cats):
        bx, by = x0 + (i % 2) * (cw + gap), top - (i // 2 + 1) * ch
        c.setFillColorRGB(*BLACK)
        c.setFont(BOLD, 10)
        c.drawString(bx, by + ch - 14, cat)
        _checkboxes(c, bx, by + ch - 32, cw, int((ch - 34) // 19), 19)


def recipe_page(c, g, p, **_):
    x0, y0, x1, y1 = g.box(p)
    top = _heading(c, g, p, "Recipe", 18)
    _field(c, x0, top - 8, x1 - x0, "Name:", 10)
    third = (x1 - x0) / 3
    for i, lab in enumerate(("Prep:", "Cook:", "Serves:")):
        _field(c, x0 + i * third, top - 30, third - 8, lab, 9)
    top -= 46
    lw = (x1 - x0) * 0.4
    c.setFillColorRGB(*BLACK)
    c.setFont(BOLD, 10)
    c.drawString(x0, top - 6, "Ingredients")
    c.drawString(x0 + lw + 10, top - 6, "Instructions")
    _stroke(c, LIGHT, 0.6)
    y = top - 26
    while y > y0 + 70:
        c.line(x0, y, x0 + lw, y)
        c.line(x0 + lw + 10, y, x1, y)
        y -= 20
    c.setFont(BOLD, 10)
    c.drawString(x0, y0 + 56, "Notes")
    for k in range(3):
        c.line(x0, y0 + 38 - k * 18, x1, y0 + 38 - k * 18)


def budget_page(c, g, p, **_):
    x0, y0, x1, y1 = g.box(p)
    top = _heading(c, g, p, "Monthly Budget", 18)
    _field(c, x0, top - 6, 170, "Month:")
    top -= 26
    half = (x1 - x0 - 12) / 2

    def table(x, y, w, title, cols, rows):
        c.setFillColorRGB(*BLACK)
        c.setFont(BOLD, 10)
        c.drawString(x, y - 10, title)
        y -= 16
        cw = w / len(cols)
        _stroke(c, GREY, 0.6)
        c.setFont(BOLD, 7.5)
        for i, col in enumerate(cols):
            c.rect(x + i * cw, y - 16, cw, 16)
            c.drawCentredString(x + (i + .5) * cw, y - 11, col)
        for r in range(rows):
            for i in range(len(cols)):
                c.rect(x + i * cw, y - 16 - (r + 1) * 17, cw, 17)
        return y - 16 - rows * 17

    table(x0, top, half, "Income", ["Source", "Amount"], 5)
    table(x0 + half + 12, top, half, "Savings & Goals", ["Goal", "Amount"], 5)
    bottom = top - 16 - 16 - 5 * 17 - 14
    rows = int((bottom - y0 - 34) // 17)
    table(x0, bottom, x1 - x0, "Expenses / Bills", ["Category", "Due", "Budget", "Actual", "Paid"], rows)


# ── Puzzles ───────────────────────────────────────────────────────────────

def _draw_wordsearch(c, x, y, w, h, data, solution=False, title="", with_words=True):
    """Draw grid in box (x,y)-(x+w,y+h) (y = bottom)."""
    size = data["size"]
    words = [pw["word"] for pw in data["placed"]]
    words_h = 0
    if with_words and not solution:
        words_h = h * 0.26
    gw = min(w, h - words_h - (24 if title else 0))
    cell = gw / size
    gx = x + (w - gw) / 2
    gy = y + h - (24 if title else 0) - gw
    fs = max(4, cell * 0.55)
    if title:
        c.setFillColorRGB(*BLACK)
        c.setFont(BOLD, 14 if not solution else 8)
        c.drawCentredString(x + w / 2, y + h - (14 if not solution else 8), title)
    if solution:
        c.setFillColorRGB(0.85, 0.85, 0.85)
        for pw in data["placed"]:
            for (r, col) in pw["cells"]:
                c.rect(gx + col * cell, gy + (size - 1 - r) * cell, cell, cell, stroke=0, fill=1)
    c.setFillColorRGB(*BLACK)
    c.setFont(FONT, fs)
    for r in range(size):
        for col in range(size):
            c.drawCentredString(gx + (col + .5) * cell, gy + (size - 1 - r) * cell + cell * .25,
                                data["grid"][r][col])
    _stroke(c, GREY, 0.4 if solution else 0.8)
    c.rect(gx, gy, gw, gw)
    if with_words and not solution:
        wfs = 9 if size >= 15 else 13        # bigger word list for small grids (kids' books)
        c.setFont(FONT, wfs)
        words = sorted(words)
        cols = 4 if len(words) > 12 else 3
        per = -(-len(words) // cols)
        colw = w / cols
        for i, wd in enumerate(words):
            cx, cy = x + (i // per) * colw + 4, gy - 16 - (i % per) * wfs * 1.35
            c.drawString(cx, cy, "☐ " + wd) if False else c.drawString(cx, cy, wd)


def wordsearch_page(c, g, p, data=None, title="", **_):
    x0, y0, x1, y1 = g.box(p)
    _draw_wordsearch(c, x0, y0, x1 - x0, y1 - y0, data, False, title)


def _draw_sudoku(c, x, y, w, h, data, solution=False, title=""):
    side = min(w, h - (22 if title else 0))
    s = side / 9
    gx, gy = x + (w - side) / 2, y + h - (22 if title else 0) - side
    if title:
        c.setFillColorRGB(*BLACK)
        c.setFont(BOLD, 14 if not solution else 8)
        c.drawCentredString(x + w / 2, y + h - (14 if not solution else 8), title)
    grid = data["solution"] if solution else data["puzzle"]
    c.setFillColorRGB(*BLACK)
    for r in range(9):
        for col in range(9):
            v = grid[r][col]
            if v:
                given = data["puzzle"][r][col]
                c.setFont(BOLD if (not solution or given) else FONT, s * 0.6)
                if solution and not given:
                    c.setFillColorRGB(0.35, 0.35, 0.35)
                else:
                    c.setFillColorRGB(*BLACK)
                c.drawCentredString(gx + (col + .5) * s, gy + (8 - r) * s + s * 0.25, str(v))
    for i in range(10):
        _stroke(c, BLACK, 2.0 if i % 3 == 0 and not solution else (1.0 if i % 3 == 0 else 0.4))
        c.line(gx, gy + i * s, gx + side, gy + i * s)
        c.line(gx + i * s, gy, gx + i * s, gy + side)


def sudoku_page(c, g, p, data=None, title="", **_):
    x0, y0, x1, y1 = g.box(p)
    _draw_sudoku(c, x0, y0, x1 - x0, y1 - y0, data, False, title)


def _draw_maze(c, x, y, w, h, data, solution=False, title=""):
    cols, rows = data["cols"], data["rows"]
    t = 22 if title else 0
    cell = min(w / cols, (h - t) / rows)
    mw, mh = cell * cols, cell * rows
    mx, my = x + (w - mw) / 2, y + h - t - mh
    if title:
        c.setFillColorRGB(*BLACK)
        c.setFont(BOLD, 14 if not solution else 8)
        c.drawCentredString(x + w / 2, y + h - (14 if not solution else 8), title)
    _stroke(c, BLACK, 0.3 if solution else 1.4)
    c.setLineCap(1)
    op = data["open"]
    for r in range(rows):
        for col in range(cols):
            px, py = mx + col * cell, my + (rows - 1 - r) * cell
            if (r - 1, col) not in op[(r, col)] and not (r == 0 and col == 0):
                c.line(px, py + cell, px + cell, py + cell)       # top
            if (r + 1, col) not in op[(r, col)] and not (r == rows - 1 and col == cols - 1):
                c.line(px, py, px + cell, py)                     # bottom
            if (r, col - 1) not in op[(r, col)]:
                c.line(px, py, px, py + cell)                     # left
            if (r, col + 1) not in op[(r, col)]:
                c.line(px + cell, py, px + cell, py + cell)       # right
    if solution:
        _stroke(c, (0.8, 0.1, 0.1), 1.2 if cell > 6 else 0.6)
        pts = [(mx + (cc + .5) * cell, my + (rows - 1 - rr + .5) * cell) for rr, cc in data["path"]]
        for a, b in zip(pts, pts[1:]):
            c.line(*a, *b)
    else:
        c.setFont(BOLD, 9)
        c.drawString(mx, my + mh + 3, "START")
        c.drawRightString(mx + mw, my - 11, "FINISH")
    c.setLineCap(0)


def maze_page(c, g, p, data=None, title="", **_):
    x0, y0, x1, y1 = g.box(p)
    _draw_maze(c, x0, y0, x1 - x0, y1 - y0 - 6, data, False, title)


def solutions_page(c, g, p, items=None, kind="wordsearch", cols=2, rows=3, **_):
    """items: list of (title, data). Draws a cols x rows grid of small solutions."""
    x0, y0, x1, y1 = g.box(p)
    top = _heading(c, g, p, "Solutions", 16)
    cw, ch = (x1 - x0) / cols, (top - y0) / rows
    draw = {"wordsearch": _draw_wordsearch, "sudoku": _draw_sudoku, "maze": _draw_maze}[kind]
    for i, (t, d) in enumerate(items):
        col, row = i % cols, i // cols
        bx, by = x0 + col * cw + 6, top - (row + 1) * ch + 6
        if kind == "wordsearch":
            draw(c, bx, by, cw - 12, ch - 12, d, True, t, False)
        else:
            draw(c, bx, by, cw - 12, ch - 12, d, True, t)


# ── Coloring ──────────────────────────────────────────────────────────────

def coloring_page(c, g, p, image=None, label="", strict=False, **_):
    x0, y0, x1, y1 = g.box(p)
    if image and Path(image).exists():
        img = ImageReader(str(image))
        iw, ih = img.getSize()
        s = min((x1 - x0) / iw, (y1 - y0) / ih)
        c.drawImage(img, x0 + ((x1 - x0) - iw * s) / 2, y0 + ((y1 - y0) - ih * s) / 2,
                    iw * s, ih * s, mask="auto")
    else:
        if strict:
            raise FileNotFoundError(f"Missing coloring art: {image}")
        _stroke(c, GREY, 1)
        c.setDash(4, 4)
        c.rect(x0, y0, x1 - x0, y1 - y0)
        c.setDash()
        c.setFillColorRGB(*GREY)
        _centered(c, g, p, f"[ART PLACEHOLDER: {Path(str(image)).name if image else label}]",
                  (y0 + y1) / 2, FONT, 10)


REGISTRY = {
    "title": title_page, "copyright": copyright_page, "belongs_to": belongs_to, "blank": blank,
    "lined": lined, "dotted": dotted, "grid": grid_page, "prompt": prompt_page,
    "daily_planner": daily_planner, "weekly_planner": weekly_planner,
    "monthly_calendar": monthly_calendar, "habit_tracker": habit_tracker,
    "gratitude": gratitude, "log_table": log_table,
    "password": password_page, "address": address_page, "meal_planner": meal_planner,
    "grocery_list": grocery_list, "recipe": recipe_page, "budget": budget_page,
}
