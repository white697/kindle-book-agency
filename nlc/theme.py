"""Visual system for themed (kids / character-led) interiors.

A spec with a top-level "theme" block gets, on every page that has a chrome dict:
  * a themed header (display font + phase tag), a frame, an original vector mascot,
    a speech-bubble "personality line" and a page-number badge.
Pages draw into the inset content box, so renderers need no knowledge of the chrome.

Fonts: pass OFL .ttf files in theme.fonts (paths relative to the project folder or ./fonts).
Anything missing falls back to built-in Helvetica faces, so a build never fails on fonts.
"""

import math
from pathlib import Path

from reportlab.lib.utils import ImageReader, simpleSplit
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont

HEADER_H = 44.0
FOOTER_H = 62.0
PAD = 12.0

FALLBACK = {"display": "Helvetica-Bold", "body": "Helvetica", "body_bold": "Helvetica-Bold",
            "body_italic": "Helvetica-Oblique"}


def _hex(value, default):
    value = (value or default).lstrip("#")
    return tuple(int(value[i:i + 2], 16) / 255 for i in (0, 2, 4))


class Theme:
    def __init__(self, cfg: dict, base: Path):
        self.cfg = cfg
        pal = cfg.get("palette", {})
        self.ink = _hex(pal.get("ink"), "#1c1c1c")
        self.tone = _hex(pal.get("tone"), "#dcdcdc")
        self.mid = tuple((a + b) / 2 for a, b in zip(self.ink, self.tone))
        self.frame = cfg.get("frame", "stitched")
        self.icon = cfg.get("icon", "star")
        m = cfg.get("mascot", {})
        self.mascot_name = m.get("name", "")
        self.mascot_style = m.get("style", "ball_buddy")
        self.mascot_image = None
        if m.get("image") and (base / m["image"]).exists():
            self.mascot_image = str(base / m["image"])
        self.default_lines = cfg.get("lines", [])
        self.kind_labels = {"opinion": "HOT TAKE", "story": "STORY STARTER", "draw": "DRAW IT",
                            "ranking": "RANK 'EM", "wyr": "WOULD YOU RATHER", "design": "DESIGN LAB",
                            "rule": "INVENT A RULE", "fill": "FILL THE GAPS", **cfg.get("kind_labels", {})}
        self.headers = {"opinion": "Hot Take", "story": "Story Time", "draw": "Draw It!", "ranking": "Rank 'Em!",
                        "wyr": "Would You Rather?", "design": "Design Lab", "rule": "Rule Maker",
                        "fill": "Fill the Gaps", **cfg.get("headers", {})}
        self.fonts = dict(FALLBACK)
        self.missing_fonts = []
        for i, (role, name) in enumerate(cfg.get("fonts", {}).items()):
            if role not in FALLBACK or not name:
                continue
            path = next((p for p in (base / name, base / "fonts" / name,
                                     Path(__file__).resolve().parent.parent / "fonts" / name) if p.exists()), None)
            if path is None:
                self.missing_fonts.append(name)
                continue
            reg = f"NLC-{role}-{path.stem}"
            if reg not in pdfmetrics.getRegisteredFontNames():
                pdfmetrics.registerFont(TTFont(reg, str(path)))
            self.fonts[role] = reg
        # Bold/italic body fall back to the regular body font when only that one is supplied
        if "body" in cfg.get("fonts", {}) and self.fonts["body"] != FALLBACK["body"]:
            for r in ("body_bold", "body_italic"):
                if self.fonts[r] == FALLBACK[r]:
                    self.fonts[r] = self.fonts["body"]

    # ── convenience ───────────────────────────────────────────────────────
    @property
    def display(self): return self.fonts["display"]
    @property
    def body(self): return self.fonts["body"]
    @property
    def bold(self): return self.fonts["body_bold"]
    @property
    def italic(self): return self.fonts["body_italic"]

    def line_for(self, n: int) -> str:
        return self.default_lines[n % len(self.default_lines)] if self.default_lines else ""


class ThemedGeometry:
    """Wraps Geometry so renderers draw inside the chrome (header above, footer below)."""
    themed = True

    def __init__(self, g):
        self._g = g

    def __getattr__(self, k):
        return getattr(self._g, k)

    def box(self, page_no):
        x0, y0, x1, y1 = self._g.box(page_no)
        return x0 + PAD, y0 + FOOTER_H, x1 - PAD, y1 - HEADER_H


# ── primitives ────────────────────────────────────────────────────────────

def stroke(c, rgb, w=1.0):
    c.setStrokeColorRGB(*rgb)
    c.setLineWidth(w)


def fill(c, rgb):
    c.setFillColorRGB(*rgb)


def wrap(text, font, size, width):
    out = []
    for para in str(text).split("\n"):
        out += simpleSplit(para, font, size, width) if para.strip() else [""]
    return out


def sticker_text(c, theme, x, y, text, size, align="left"):
    """Display text with a offset tone shadow so it reads like a printed sticker."""
    draw = {"left": c.drawString, "center": c.drawCentredString, "right": c.drawRightString}[align]
    c.setFont(theme.display, size)
    fill(c, theme.tone)
    draw(x + size * 0.07, y - size * 0.07, text)
    fill(c, theme.ink)
    draw(x, y, text)


def bubble(c, theme, x0, y0, x1, y1, tail=None, r=9, fillc=(1, 1, 1)):
    """Rounded speech bubble; tail=(tx, ty) puts a pointer toward that point on the left/bottom edge."""
    stroke(c, theme.ink, 1.2)
    fill(c, fillc)
    if tail:
        tx, ty = tail
        ym = min(max(ty, y0 + r + 4), y1 - r - 4)
        p = c.beginPath()
        p.moveTo(x0 + 1, ym + 6)
        p.lineTo(tx, ty)
        p.lineTo(x0 + 1, ym - 6)
        p.close()
        c.drawPath(p, stroke=1, fill=1)
    c.roundRect(x0, y0, x1 - x0, y1 - y0, r, stroke=1, fill=1)
    if tail:
        stroke(c, fillc, 2.6)
        c.line(x0, ym - 5, x0, ym + 5)


def pill(c, theme, x, y, text, size=8.5, align="left", dark=False):
    w = c.stringWidth(text, theme.bold, size) + 14
    x0 = x if align == "left" else x - w
    stroke(c, theme.ink, 1.0)
    fill(c, theme.ink if dark else theme.tone)
    c.roundRect(x0, y - 4, w, size + 8, (size + 8) / 2, stroke=1, fill=1)
    fill(c, (1, 1, 1) if dark else theme.ink)
    c.setFont(theme.bold, size)
    c.drawString(x0 + 7, y + 1, text)
    return w


def _pentagon(c, cx, cy, r, rot=-math.pi / 2):
    p = c.beginPath()
    for k in range(5):
        a = rot + k * 2 * math.pi / 5
        (p.moveTo if k == 0 else p.lineTo)(cx + r * math.cos(a), cy + r * math.sin(a))
    p.close()
    return p


def icon(c, theme, kind, cx, cy, r, filled=True):
    stroke(c, theme.ink, 1.1)
    if kind == "star":
        p = c.beginPath()
        for k in range(10):
            a = -math.pi / 2 + k * math.pi / 5
            rr = r if k % 2 == 0 else r * 0.46
            (p.moveTo if k == 0 else p.lineTo)(cx + rr * math.cos(a), cy + rr * math.sin(a))
        p.close()
        fill(c, theme.ink if filled else (1, 1, 1))
        c.drawPath(p, stroke=1, fill=1)
    else:  # ball
        fill(c, (1, 1, 1))
        c.circle(cx, cy, r, stroke=1, fill=1)
        fill(c, theme.ink if filled else theme.tone)
        c.drawPath(_pentagon(c, cx, cy, r * 0.42), stroke=0, fill=1)


def draw_ball(c, theme, cx, cy, r):
    c.saveState()
    fill(c, (1, 1, 1))
    stroke(c, theme.ink, max(1.2, r * 0.07))
    c.circle(cx, cy, r, stroke=1, fill=1)
    clip = c.beginPath()
    clip.circle(cx, cy, r)
    c.clipPath(clip, stroke=0, fill=0)
    fill(c, theme.ink)
    c.drawPath(_pentagon(c, cx, cy, r * 0.34), stroke=0, fill=1)
    for k in range(5):
        a = -math.pi / 2 + k * 2 * math.pi / 5
        px, py = cx + r * 0.62 * math.cos(a), cy + r * 0.62 * math.sin(a)
        stroke(c, theme.ink, max(0.8, r * 0.05))
        c.line(cx + r * 0.34 * math.cos(a), cy + r * 0.34 * math.sin(a), px, py)
        c.drawPath(_pentagon(c, cx + r * 1.0 * math.cos(a), cy + r * 1.0 * math.sin(a), r * 0.3, a + math.pi),
                   stroke=0, fill=1)
    c.restoreState()


def draw_mascot(c, theme, cx, cy, r, mood="happy"):
    """Original vector mascot: a ball-bodied buddy with headband, boots and a face.
    A PNG at theme.mascot.image (e.g. from Ideogram) replaces it."""
    if theme.mascot_image:
        c.drawImage(ImageReader(theme.mascot_image), cx - r * 1.25, cy - r * 1.3, r * 2.5, r * 2.6,
                    preserveAspectRatio=True, mask="auto")
        return
    ink = theme.ink
    stroke(c, ink, max(1.2, r * 0.08))
    fill(c, (1, 1, 1))
    # legs + boots
    for sx in (-1, 1):
        c.line(cx + sx * r * 0.35, cy - r * 0.95, cx + sx * r * 0.4, cy - r * 1.28)
        fill(c, ink)
        c.ellipse(cx + sx * r * 0.4 - r * 0.28 + sx * r * 0.08, cy - r * 1.44,
                  cx + sx * r * 0.4 + r * 0.28 + sx * r * 0.08, cy - r * 1.2, stroke=1, fill=1)
    # arms
    up = mood == "cheer"
    for sx in (-1, 1):
        p = c.beginPath()
        p.moveTo(cx + sx * r * 0.95, cy - r * 0.05)
        if up:
            p.curveTo(cx + sx * r * 1.4, cy + r * 0.2, cx + sx * r * 1.5, cy + r * 0.6, cx + sx * r * 1.35, cy + r * 1.0)
        else:
            p.curveTo(cx + sx * r * 1.35, cy - r * 0.1, cx + sx * r * 1.5, cy - r * 0.3, cx + sx * r * 1.4, cy - r * 0.55)
        c.drawPath(p, stroke=1, fill=0)
    draw_ball(c, theme, cx, cy, r)
    # headband
    c.saveState()
    clip = c.beginPath()
    clip.circle(cx, cy, r)
    c.clipPath(clip, stroke=0, fill=0)
    fill(c, theme.tone)
    stroke(c, ink, max(1, r * 0.05))
    c.rect(cx - r, cy + r * 0.28, 2 * r, r * 0.2, stroke=1, fill=1)
    c.restoreState()
    # face
    fill(c, (1, 1, 1))
    stroke(c, ink, max(1, r * 0.05))
    c.ellipse(cx - r * 0.62, cy - r * 0.5, cx + r * 0.62, cy + r * 0.24, stroke=0, fill=1)
    fill(c, ink)
    ey = cy - r * 0.02
    for sx in (-1, 1):
        ex = cx + sx * r * 0.27
        if mood == "wink" and sx == 1:
            stroke(c, ink, max(1.2, r * 0.07))
            c.line(ex - r * 0.1, ey, ex + r * 0.1, ey)
        elif mood == "cheer":
            stroke(c, ink, max(1.2, r * 0.07))
            c.arc(ex - r * 0.12, ey - r * 0.06, ex + r * 0.12, ey + r * 0.2, 20, 140)
        else:
            c.circle(ex, ey, r * 0.075, stroke=0, fill=1)
        if mood == "tough":
            stroke(c, ink, max(1.2, r * 0.07))
            c.line(ex - sx * r * 0.14, ey + r * 0.2, ex + sx * r * 0.1, ey + r * 0.12)
    stroke(c, ink, max(1.2, r * 0.07))
    if mood == "cheer":
        c.arc(cx - r * 0.24, cy - r * 0.48, cx + r * 0.24, cy - r * 0.04, 200, 140)
    elif mood == "tough":
        c.line(cx - r * 0.18, cy - r * 0.28, cx + r * 0.18, cy - r * 0.28)
    else:
        c.arc(cx - r * 0.22, cy - r * 0.42, cx + r * 0.22, cy - r * 0.1, 205, 130)


def kid_lines(c, theme, x0, x1, y_top, y_bottom, spacing=30.0):
    """Handwriting lines for ages 6-10: solid baseline + dotted mid-line. Returns line count."""
    y, n = y_top - spacing, 0
    while y >= y_bottom:
        stroke(c, theme.mid, 0.9)
        c.line(x0, y, x1, y)
        stroke(c, theme.tone, 0.8)
        c.setDash(1, 3)
        c.line(x0, y + spacing * 0.45, x1, y + spacing * 0.45)
        c.setDash()
        y -= spacing
        n += 1
    return n


# ── chrome ────────────────────────────────────────────────────────────────

def draw_frame(c, theme, x0, y0, x1, y1):
    kind = theme.frame
    if kind == "double":
        stroke(c, theme.ink, 2.4)
        c.rect(x0, y0, x1 - x0, y1 - y0)
        stroke(c, theme.mid, 0.7)
        c.rect(x0 + 4, y0 + 4, x1 - x0 - 8, y1 - y0 - 8)
    elif kind == "corner_arcs":
        stroke(c, theme.ink, 1.6)
        c.rect(x0, y0, x1 - x0, y1 - y0)
        stroke(c, theme.mid, 1.0)
        r = 20
        c.arc(x0 - r, y0 - r, x0 + r, y0 + r, 0, 90)
        c.arc(x1 - r, y0 - r, x1 + r, y0 + r, 90, 90)
        c.arc(x1 - r, y1 - r, x1 + r, y1 + r, 180, 90)
        c.arc(x0 - r, y1 - r, x0 + r, y1 + r, 270, 90)
    else:  # stitched
        stroke(c, theme.ink, 1.8)
        c.roundRect(x0, y0, x1 - x0, y1 - y0, 14)
        stroke(c, theme.mid, 0.9)
        c.setDash(3, 3)
        c.roundRect(x0 + 5, y0 + 5, x1 - x0 - 10, y1 - y0 - 10, 10)
        c.setDash()


def draw_chrome(c, g, p, theme: Theme, header="", phase="", line="", mood="happy"):
    """Frame, header, phase tag, mascot + speech bubble and page badge for one page."""
    x0, y0, x1, y1 = g._g.box(p) if getattr(g, "themed", False) else g.box(p)
    draw_frame(c, theme, x0, y0, x1, y1)
    # header
    top = y1 - 30
    tag_w = 0
    if phase:
        tag_w = pill(c, theme, x1 - 12, top - 1, phase.upper(), 8.5, "right", dark=True) + 16
    size = 22.0
    maxw = (x1 - x0) - 28 - tag_w
    while size > 11 and c.stringWidth(header, theme.display, size) > maxw:
        size -= 1
    if header:
        sticker_text(c, theme, x0 + 14, top, header, size)
    stroke(c, theme.tone, 4)
    c.line(x0 + 12, y1 - HEADER_H + 4, x1 - 12, y1 - HEADER_H + 4)
    stroke(c, theme.ink, 0.8)
    c.line(x0 + 12, y1 - HEADER_H + 1, x1 - 12, y1 - HEADER_H + 1)
    # footer: mascot + bubble + page badge
    r = 17
    mx, my = x0 + 16 + r + 8, y0 + FOOTER_H / 2 - 2
    draw_mascot(c, theme, mx, my, r, mood)
    bx0, bx1 = mx + r + 22, x1 - 48
    by0, by1 = y0 + 12, y0 + FOOTER_H - 12
    if line:
        fs = 10.5
        lines = wrap(line, theme.italic, fs, bx1 - bx0 - 16)
        while len(lines) > 2 and fs > 8:
            fs -= 0.5
            lines = wrap(line, theme.italic, fs, bx1 - bx0 - 16)
        bubble(c, theme, bx0, by0, bx1, by1, tail=(bx0 - 8, my + 2))
        fill(c, theme.ink)
        c.setFont(theme.italic, fs)
        ty = (by0 + by1) / 2 + (len(lines) - 1) * fs * 0.6 - fs * 0.3
        for ln in lines[:2]:
            c.drawCentredString((bx0 + bx1) / 2, ty, ln)
            ty -= fs * 1.2
    icon(c, theme, "ball", x1 - 26, my, 13, True)
    fill(c, theme.ink)
    c.setFont(theme.bold, 8.5)
    c.setFillColorRGB(1, 1, 1)
    c.roundRect(x1 - 36, my - 6, 20, 12, 5, stroke=0, fill=1)
    fill(c, theme.ink)
    c.drawCentredString(x1 - 26, my - 3, str(p))
