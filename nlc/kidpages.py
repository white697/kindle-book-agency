"""Themed page renderers for kids' activity books (prompt cards, directed doodles, reports...).

All renderers are drawn inside the chrome's content box (see nlc.theme) and need a `theme`.
"""

import math
from pathlib import Path

from reportlab.lib.utils import ImageReader

from nlc.theme import (bubble, draw_ball, draw_mascot, fill, icon, kid_lines, pill, sticker_text, stroke, wrap)

LINE_GAP = 30.0   # handwriting line spacing in points (~0.42in) for ages 6-10


def _theme(theme):
    if theme is None:
        raise ValueError("themed page used without a top-level 'theme' block in nlc_spec.json")
    return theme


def _banner(c, theme, x0, x1, ytop, text, label="", size=15):
    """Dark task banner with a tone label tab. Returns y of the banner's bottom edge."""
    lines = wrap(text, theme.bold, size, x1 - x0 - 28)
    h = len(lines) * (size + 5) + 22
    fill(c, theme.ink)
    stroke(c, theme.ink, 1.2)
    c.roundRect(x0, ytop - h, x1 - x0, h, 10, stroke=1, fill=1)
    fill(c, (1, 1, 1))
    c.setFont(theme.bold, size)
    y = ytop - 18 - size * 0.4
    for ln in lines:
        c.drawString(x0 + 14, y, ln)
        y -= size + 5
    if label:
        pill(c, theme, x0 + 14, ytop - 1, label, 8.5)
    return ytop - h


def _write_in(c, theme, x, y, w, label, size=11):
    c.setFont(theme.bold, size)
    fill(c, theme.ink)
    c.drawString(x, y + 3, label)
    lw = c.stringWidth(label, theme.bold, size) + 6
    stroke(c, theme.mid, 0.9)
    c.line(x + lw, y, x + w, y)


def _art_or(c, art, x, y, w, h):
    """Draw an Ideogram/other PNG into a box if it exists. Returns True if drawn."""
    if art and Path(art).exists():
        img = ImageReader(str(art))
        iw, ih = img.getSize()
        s = min(w / iw, h / ih)
        c.drawImage(img, x + (w - iw * s) / 2, y + (h - ih * s) / 2, iw * s, ih * s, mask="auto")
        return True
    return False


# ── Starter art: light outlines already printed in the doodle box ─────────

def _s_boot(c, t):
    p = c.beginPath()
    for i, (x, y) in enumerate([(-46, -14), (-46, 26), (-34, 38), (-8, 38), (-8, 14), (22, 6), (44, -2), (48, -14)]):
        (p.moveTo if i == 0 else p.lineTo)(x, y)
    p.close()
    c.drawPath(p, stroke=1, fill=0)
    c.line(-46, -22, 48, -22)
    c.line(-46, -14, -46, -22)
    c.line(48, -14, 48, -22)
    for sx in (-36, -14, 12, 34):
        c.rect(sx, -30, 7, 8)
    for k in range(3):
        c.line(-8, 30 - k * 8, 6, 26 - k * 8)


def _s_ball(c, t):
    c.circle(0, 0, 36)
    p = c.beginPath()
    for k in range(5):
        a = -math.pi / 2 + k * 2 * math.pi / 5
        (p.moveTo if k == 0 else p.lineTo)(13 * math.cos(a), 13 * math.sin(a))
    p.close()
    c.drawPath(p, stroke=1, fill=0)


def _s_goal(c, t):
    c.rect(-48, -26, 96, 52)
    for x in range(-40, 48, 12):
        c.line(x, -26, x, 26)
    for y in range(-14, 26, 12):
        c.line(-48, y, 48, y)
    c.line(-60, -26, 60, -26)


def _s_stadium(c, t):
    c.ellipse(-46, -34, 46, -12)
    c.arc(-60, -26, 60, 50, 0, 180)
    c.arc(-48, -20, 48, 38, 0, 180)
    for sx in (-52, 52):
        c.line(sx, -4, sx, 40)
        c.rect(sx - 5, 40, 10, 6)
    c.line(-46, -23, 46, -23)


def _s_shirt(c, t):
    p = c.beginPath()
    pts = [(-18, 42), (-44, 30), (-56, 6), (-40, -2), (-30, 8), (-30, -44), (30, -44), (30, 8), (40, -2), (56, 6), (44, 30), (18, 42)]
    for i, (x, y) in enumerate(pts):
        (p.moveTo if i == 0 else p.lineTo)(x, y)
    c.drawPath(p, stroke=1, fill=0)
    c.arc(-18, 30, 18, 54, 180, 180)


def _s_trophy(c, t):
    p = c.beginPath()
    p.moveTo(-24, 40)
    p.curveTo(-24, 0, -10, -8, -4, -14)
    p.lineTo(4, -14)
    p.curveTo(10, -8, 24, 0, 24, 40)
    p.close()
    c.drawPath(p, stroke=1, fill=0)
    c.arc(-44, 14, -16, 38, 90, 180)
    c.arc(16, 14, 44, 38, -90, 180)
    c.rect(-4, -30, 8, 16)
    c.rect(-20, -40, 40, 10)


def _s_pitch(c, t):
    c.rect(-56, -36, 112, 72)
    c.line(0, -36, 0, 36)
    c.circle(0, 0, 12)
    c.rect(-56, -16, 16, 32)
    c.rect(40, -16, 16, 32)


def _s_panels(c, t):
    for (x, y) in ((-54, 2), (2, 2), (-54, -36), (2, -36)):
        c.rect(x, y, 52, 34)
    c.setFont("Helvetica-Bold", 7)
    for i, (x, y) in enumerate(((-52, 28), (4, 28), (-52, -10), (4, -10)), 1):
        c.drawString(x, y, str(i))


def _s_badge(c, t):
    p = c.beginPath()
    p.moveTo(-34, 40)
    p.lineTo(34, 40)
    p.lineTo(34, -4)
    p.curveTo(34, -26, 12, -36, 0, -44)
    p.curveTo(-12, -36, -34, -26, -34, -4)
    p.close()
    c.drawPath(p, stroke=1, fill=0)
    c.line(-34, 26, 34, 26)


def _s_scoreboard(c, t):
    c.rect(-56, -10, 112, 44)
    c.line(0, -10, 0, 34)
    c.rect(-50, 0, 36, 22)
    c.rect(14, 0, 36, 22)
    c.line(-8, -10, -8, -26)
    c.line(8, -10, 8, -26)


def _s_face(c, t):
    c.circle(0, 4, 32)
    c.ellipse(-38, -2, -30, 14)
    c.ellipse(30, -2, 38, 14)
    c.line(-10, -28, -10, -42)
    c.line(10, -28, 10, -42)


STARTERS = {"boot": _s_boot, "ball": _s_ball, "goal": _s_goal, "stadium": _s_stadium, "shirt": _s_shirt,
            "trophy": _s_trophy, "pitch": _s_pitch, "panels": _s_panels, "badge": _s_badge,
            "scoreboard": _s_scoreboard, "face": _s_face}


def draw_starter(c, theme, name, x, y, w, h):
    """Printed starting element, centred in (x,y,w,h); drawn in a light tone so kids can draw over it."""
    fn = STARTERS.get(name)
    if not fn:
        return
    c.saveState()
    c.translate(x + w / 2, y + h / 2)
    s = min(w, h) / 120.0
    c.scale(s, s)
    stroke(c, theme.mid, 1.8 / s)
    c.setDash(*(( 5, 3) if name in ("panels",) else (1, 0)))
    fn(c, theme)
    c.restoreState()


def _canvas(c, theme, x0, y0, x1, y1, starter=None, art=None):
    stroke(c, theme.ink, 1.4)
    c.setDash(5, 4)
    fill(c, (1, 1, 1))
    c.roundRect(x0, y0, x1 - x0, y1 - y0, 12, stroke=1, fill=0)
    c.setDash()
    if not _art_or(c, art, x0 + 10, y0 + 10, x1 - x0 - 20, y1 - y0 - 20):
        if starter:
            draw_starter(c, theme, starter, x0, y0, x1 - x0, y1 - y0)


# ── Prompt cards ──────────────────────────────────────────────────────────

def prompt_card(c, g, p, theme=None, kind="opinion", text="", hint="", options=None, slots=None,
                labels=None, starter=None, art=None, items=5, **_):
    t = _theme(theme)
    x0, y0, x1, y1 = g.box(p)
    label = t.kind_labels.get(kind, kind.upper())
    y = y1
    if kind == "story":
        # notebook: tab, spiral holes, margin rule, starter sentence leading into the lines
        pill(c, t, x0 + 6, y - 6, label, 9, dark=True)
        top = y - 22
        fill(c, (1, 1, 1))
        stroke(c, t.ink, 1.4)
        c.roundRect(x0, y0, x1 - x0, top - y0, 10, stroke=1, fill=1)
        for k in range(int((top - y0 - 30) // 34)):
            hy = top - 24 - k * 34
            fill(c, t.tone)
            stroke(c, t.ink, 0.9)
            c.circle(x0 + 12, hy, 4.2, stroke=1, fill=1)
        stroke(c, t.mid, 1.0)
        c.line(x0 + 34, y0 + 6, x0 + 34, top - 6)
        fill(c, t.ink)
        c.setFont(t.italic, 15)
        ty = top - 24
        for ln in wrap(text, t.italic, 15, x1 - x0 - 58):
            c.drawString(x0 + 44, ty, ln)
            ty -= 21
        kid_lines(c, t, x0 + 40, x1 - 14, ty + 12, y0 + 12, LINE_GAP)
        return

    y = _banner(c, t, x0, x1, y - 8, text, label)
    if hint:
        c.setFont(t.italic, 10.5)
        fill(c, t.mid)
        c.drawString(x0 + 6, y - 15, hint)
        y -= 20
    y -= 14

    if kind == "ranking":
        n = int(items)
        slots = slots or [""] * n
        rh = min(64.0, (y - y0 - 150) / n)
        for i in range(n):
            ry = y - (i + 1) * rh + 8
            fill(c, t.tone if i else t.ink)
            stroke(c, t.ink, 1.2)
            c.circle(x0 + 22, ry + rh / 2 - 4, 17, stroke=1, fill=1)
            fill(c, (1, 1, 1) if i == 0 else t.ink)
            c.setFont(t.display, 20)
            c.drawCentredString(x0 + 22, ry + rh / 2 - 11, str(i + 1))
            stroke(c, t.mid, 1.0)
            c.line(x0 + 50, ry + 6, x1, ry + 6)
            if slots[i % len(slots)]:
                fill(c, t.mid)
                c.setFont(t.italic, 9.5)
                c.drawString(x0 + 54, ry + 10, slots[i % len(slots)])
        wy = y - n * rh - 8
        fill(c, t.ink)
        c.setFont(t.display, 13)
        c.drawString(x0, wy - 6, "Why is number 1 the winner?")
        kid_lines(c, t, x0, x1, wy - 10, y0 + 6, LINE_GAP)
    elif kind == "wyr":
        opts = options or ["Option A", "Option B"]
        gap = 46
        bw = (x1 - x0 - gap) / 2
        for i, o in enumerate(opts[:2]):
            bx = x0 + i * (bw + gap)
            stroke(c, t.ink, 1.4)
            fill(c, (1, 1, 1))
            c.roundRect(bx, y0, bw, y - y0, 12, stroke=1, fill=1)
            fill(c, t.tone)
            c.roundRect(bx, y - 74, bw, 74, 12, stroke=1, fill=1)
            fill(c, t.ink)
            ly = y - 24
            for ln in wrap(o, t.bold, 12.5, bw - 20)[:3]:
                c.setFont(t.bold, 12.5)
                c.drawCentredString(bx + bw / 2, ly, ln)
                ly -= 16
            c.setFont(t.italic, 10)
            fill(c, t.mid)
            c.drawString(bx + 10, y - 92, "Because...")
            kid_lines(c, t, bx + 10, bx + bw - 10, y - 96, y0 + 40, LINE_GAP)
            pill(c, t, bx + bw / 2 - 28, y0 + 14, "I PICK THIS", 8.5)
        cx, cy = x0 + bw + gap / 2, y - 37
        fill(c, t.ink)
        c.circle(cx, cy, 18, stroke=0, fill=1)
        fill(c, (1, 1, 1))
        c.setFont(t.display, 14)
        c.drawCentredString(cx, cy - 5, "OR")
    elif kind in ("draw", "design"):
        lab = labels or (["Name it:", "Superpower:", "Costs:"] if kind == "design" else [])
        side = 150 if lab else 0
        cap_h = 74 if kind == "draw" else 6
        _canvas(c, t, x0, y0 + cap_h, x1 - (side + 12 if side else 0), y, starter, art)
        if lab:
            ly = y - 30
            for lb in lab:
                _write_in(c, t, x1 - side, ly, side, lb, 10.5)
                ly -= 54
        if kind == "draw":
            _write_in(c, t, x0, y0 + 40, x1 - x0, "Name your masterpiece:", 12)
            _write_in(c, t, x0, y0 + 8, x1 - x0, "Artist's signature:", 12)
    elif kind == "rule":
        stroke(c, t.ink, 1.4)
        fill(c, (1, 1, 1))
        c.roundRect(x0, y0, x1 - x0, y - y0, 12, stroke=1, fill=1)
        fields = labels or ["Rule name", "How it works", "Why it makes the game better", "Penalty if you break it"]
        cy = y - 24
        per = (y - y0 - 20) / len(fields)
        for i, fl in enumerate(fields):
            fill(c, t.ink)
            c.setFont(t.display, 13)
            c.drawString(x0 + 14, cy, f"{i + 1}. {fl}")
            kid_lines(c, t, x0 + 14, x1 - 14, cy - 6, cy - per + 12, LINE_GAP) if per > 60 else None
            cy -= per
    elif kind == "fill":
        fill(c, t.ink)
        ty = y - 10
        for ln in wrap(text_blank(options), t.body, 16, x1 - x0 - 12):
            c.setFont(t.body, 16)
            c.drawString(x0 + 6, ty, ln)
            ty -= 34
        _canvas(c, t, x0, y0, x1, min(ty - 6, y0 + (y - y0) * 0.55), starter, art)
        pill(c, t, x0 + 14, y0 + 8, "DRAW THE SCENE", 8.5)
    else:  # opinion and anything else: a verdict box + big writing lines
        kid_lines(c, t, x0, x1, y, y0 + 70, LINE_GAP)
        stroke(c, t.ink, 1.3)
        fill(c, t.tone)
        c.roundRect(x0, y0 + 4, x1 - x0, 52, 10, stroke=1, fill=1)
        fill(c, t.ink)
        c.setFont(t.bold, 11)
        c.drawString(x0 + 12, y0 + 36, "How sure are you?")
        for k in range(5):
            icon(c, t, t.icon, x0 + 150 + k * 30, y0 + 40, 11, False)
        fill(c, t.ink)
        c.setFont(t.italic, 9.5)
        c.drawString(x0 + 12, y0 + 16, "Colour in one icon for each point of certainty.")


def text_blank(options):
    """For kind 'fill': the sentence(s) with ____ gaps live in options[0]."""
    return (options or ["Fill in: ______"])[0]


# ── Directed doodle ───────────────────────────────────────────────────────

def doodle(c, g, p, theme=None, text="", starter=None, art=None, caption="Name your creation:", **_):
    t = _theme(theme)
    x0, y0, x1, y1 = g.box(p)
    y = _banner(c, t, x0, x1, y1 - 8, text, "DOODLE CHALLENGE")
    _canvas(c, t, x0, y0 + 46, x1, y - 14, starter, art)
    _write_in(c, t, x0, y0 + 12, x1 - x0, caption, 12)


# ── Post-match report (replaces adult gratitude pages) ────────────────────

def report(c, g, p, theme=None, title="PLAYER REPORT", fields=None, ratings=None, thank="Today I want to thank",
           **_):
    t = _theme(theme)
    x0, y0, x1, y1 = g.box(p)
    fields = fields or ["We played:", "Match date:"]
    ratings = ratings or ["Effort", "Teamwork", "Fun", "Skills"]
    y = y1 - 6
    fw = (x1 - x0 - 20) / len(fields)
    for i, f in enumerate(fields):
        _write_in(c, t, x0 + i * (fw + 20), y - 8, fw, f, 12)
    y -= 38
    # score row
    stroke(c, t.ink, 1.6)
    fill(c, t.ink)
    c.roundRect(x0, y - 52, x1 - x0, 52, 12, stroke=1, fill=1)
    fill(c, (1, 1, 1))
    c.setFont(t.display, 16)
    c.drawString(x0 + 18, y - 32, "US")
    c.drawRightString(x1 - 18, y - 32, "THEM")
    cx = (x0 + x1) / 2
    for dx in (-62, 22):
        fill(c, (1, 1, 1))
        c.roundRect(cx + dx, y - 44, 40, 36, 6, stroke=0, fill=1)
    c.setFont(t.display, 22)
    fill(c, (1, 1, 1))
    c.drawCentredString(cx, y - 34, "-")
    y -= 70
    # ratings
    fill(c, t.ink)
    c.setFont(t.display, 14)
    c.drawString(x0, y - 4, "RATE YOUR PERFORMANCE")
    y -= 14
    for i, rname in enumerate(ratings):
        ry = y - 8 - i * 30
        c.setFont(t.bold, 12)
        fill(c, t.ink)
        c.drawString(x0 + 4, ry - 4, rname)
        for k in range(5):
            icon(c, t, t.icon, x0 + 150 + k * 34, ry, 12, False)
    y -= 8 + len(ratings) * 30 + 6
    # best moment
    box_h = max(70.0, (y - y0) - 84)
    stroke(c, t.ink, 1.4)
    c.setDash(5, 4)
    c.roundRect(x0, y - box_h, x1 - x0, box_h, 12, stroke=1, fill=0)
    c.setDash()
    pill(c, t, x0 + 14, y - 2, "MY BEST MOMENT (WRITE OR DRAW IT)", 8.5, dark=True)
    y -= box_h + 28
    _write_in(c, t, x0, y, x1 - x0, thank, 12)
    y -= 34
    _write_in(c, t, x0, y, x1 - x0, "Next match I will try to:", 12)


# ── Front matter & notes ──────────────────────────────────────────────────

def title_page_themed(c, g, p, theme=None, title="", subtitle="", author="", **_):
    from nlc.theme import draw_frame
    t = _theme(theme)
    x0, y0, x1, y1 = g.box(p)
    draw_frame(c, t, x0, y0, x1, y1)
    cx = (x0 + x1) / 2
    y = y1 - 80
    size = 40
    lines = wrap(title.upper(), t.display, size, x1 - x0 - 60)
    while len(lines) > 3 and size > 24:
        size -= 2
        lines = wrap(title.upper(), t.display, size, x1 - x0 - 60)
    for ln in lines:
        sticker_text(c, t, cx, y, ln, size, "center")
        y -= size * 1.15
    y -= 6
    fill(c, t.ink)
    for ln in wrap(subtitle, t.body, 13, x1 - x0 - 90):
        c.setFont(t.body, 13)
        c.drawCentredString(cx, y, ln)
        y -= 17
    my = (y + y0) / 2 + 20
    draw_mascot(c, t, cx, my, 82, "cheer")
    if t.mascot_name:
        bubble(c, t, cx + 98, my + 70, x1 - 26, my + 128, tail=(cx + 92, my + 60))
        fill(c, t.ink)
        c.setFont(t.italic, 11)
        c.drawCentredString((cx + 98 + x1 - 26) / 2, my + 94, f"I'm {t.mascot_name}!")
        c.drawCentredString((cx + 98 + x1 - 26) / 2, my + 80, "Let's play.")
    for k in range(7):
        icon(c, t, t.icon, cx - 90 + k * 30, y0 + 70, 9, k % 2 == 0)
    if author:
        c.setFont(t.bold, 13)
        c.drawCentredString(cx, y0 + 32, f"by {author}")


def belongs_themed(c, g, p, theme=None, fields=None, **_):
    t = _theme(theme)
    x0, y0, x1, y1 = g.box(p)
    fields = fields or ["Player name:", "Shirt number:", "Favourite team:", "My secret skill:"]
    cw, ch = x1 - x0 - 20, 330
    cy1 = y1 - 40
    cx0 = x0 + 10
    stroke(c, t.ink, 1.8)
    fill(c, (1, 1, 1))
    c.roundRect(cx0, cy1 - ch, cw, ch, 16, stroke=1, fill=1)
    fill(c, t.ink)
    c.roundRect(cx0, cy1 - 44, cw, 44, 16, stroke=0, fill=1)
    c.rect(cx0, cy1 - 44, cw, 16, stroke=0, fill=1)
    fill(c, (1, 1, 1))
    c.setFont(t.display, 20)
    c.drawString(cx0 + 18, cy1 - 30, "OFFICIAL PLAYER CARD")
    # photo box: draw yourself
    px, py, pw, ph = cx0 + 18, cy1 - ch + 22, 120, 150
    stroke(c, t.mid, 1.2)
    c.setDash(4, 3)
    fill(c, (1, 1, 1))
    c.rect(px, py, pw, ph, stroke=1, fill=0)
    c.setDash()
    fill(c, t.mid)
    c.setFont(t.italic, 9)
    c.drawCentredString(px + pw / 2, py + ph / 2 + 4, "Draw yourself")
    c.drawCentredString(px + pw / 2, py + ph / 2 - 8, "in your kit!")
    fy = cy1 - 82
    for f in fields:
        _write_in(c, t, px + pw + 24, fy, cw - pw - 60, f, 12)
        fy -= 44
    if t.mascot_name:
        draw_mascot(c, t, x1 - 70, y0 + 150, 26, "wink")
        bubble(c, t, x1 - 190, y0 + 138, x1 - 106, y0 + 176, tail=(x1 - 98, y0 + 154))
        fill(c, t.ink)
        c.setFont(t.italic, 9)
        c.drawCentredString(x1 - 148, y0 + 160, f"{t.mascot_name} says:")
        c.drawCentredString(x1 - 148, y0 + 149, "good luck!")


def notes_page(c, g, p, theme=None, text="", starter=None, **_):
    t = _theme(theme)
    x0, y0, x1, y1 = g.box(p)
    y = y1
    if text:
        y = _banner(c, t, x0, x1, y - 6, text, "SCOUT REPORT", 13) - 14
    kid_lines(c, t, x0, x1, y, y0 + 10, LINE_GAP)
