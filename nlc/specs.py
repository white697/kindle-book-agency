"""KDP paperback geometry: trim sizes, gutter margins, spine width, cover dimensions.

Values follow Amazon KDP's published paperback guidelines. KDP revises these
occasionally — confirm final numbers with KDP's cover calculator before upload.
"""

from dataclasses import dataclass

PT = 72.0  # points per inch

TRIMS = {
    "5x8": (5.0, 8.0),
    "5.25x8": (5.25, 8.0),
    "5.5x8.5": (5.5, 8.5),
    "6x9": (6.0, 9.0),
    "7x10": (7.0, 10.0),
    "8x10": (8.0, 10.0),
    "8.5x8.5": (8.5, 8.5),
    "8.5x11": (8.5, 11.0),
}

# Paper thickness in inches per page
PAPER = {
    "white": 0.002252,         # black ink, white paper
    "cream": 0.0025,           # black ink, cream paper
    "color_standard": 0.002252,
    "color_premium": 0.002347,
}

BLEED = 0.125
MIN_PAGES = 24
MAX_PAGES = 828
COVER_SPINE_TEXT_MIN_PAGES = 79


def gutter_inches(pages: int) -> float:
    """Minimum inside (gutter) margin by page count (KDP table)."""
    for limit, g in ((150, 0.375), (300, 0.5), (500, 0.625), (700, 0.75), (828, 0.875)):
        if pages <= limit:
            return g
    raise ValueError(f"KDP paperbacks max out at {MAX_PAGES} pages (got {pages})")


def spine_inches(pages: int, paper: str) -> float:
    return round(pages * PAPER[paper], 4)


@dataclass
class Geometry:
    """Page geometry in points for a given trim/bleed/page count."""
    trim_w: float
    trim_h: float
    pages: int
    bleed: bool = False
    outer: float = 0.5   # inches, outside/top/bottom safe margin
    gutter: float = 0.0  # inches; filled from page count

    def __post_init__(self):
        if not self.gutter:
            self.gutter = gutter_inches(self.pages)
        self.b = BLEED * PT if self.bleed else 0.0
        self.page_w = self.trim_w * PT + self.b          # bleed on outside edge only
        self.page_h = self.trim_h * PT + 2 * self.b      # top and bottom

    def box(self, page_no: int) -> tuple[float, float, float, float]:
        """Safe content box (x0, y0, x1, y1) for 1-indexed page; odd pages are recto."""
        o, g = self.outer * PT, self.gutter * PT
        if page_no % 2 == 1:   # recto: gutter on the left, bleed on the right
            x0, x1 = g, self.page_w - o - self.b
        else:                  # verso: bleed on the left, gutter on the right
            x0, x1 = self.b + o, self.page_w - g
        return x0, self.b + o, x1, self.page_h - self.b - o


def cover_dims(trim: tuple[float, float], pages: int, paper: str) -> dict:
    """Full-wrap cover size in inches (includes 0.125in bleed on all sides)."""
    tw, th = trim
    spine = spine_inches(pages, paper)
    return {
        "spine": spine,
        "width": round(2 * tw + spine + 2 * BLEED, 4),
        "height": round(th + 2 * BLEED, 4),
    }


def validate(trim_key: str, paper: str, pages: int):
    if trim_key not in TRIMS:
        raise ValueError(f"Unknown trim '{trim_key}'. Options: {', '.join(TRIMS)}")
    if paper not in PAPER:
        raise ValueError(f"Unknown paper '{paper}'. Options: {', '.join(PAPER)}")
    if not MIN_PAGES <= pages <= MAX_PAGES:
        raise ValueError(f"Page count must be {MIN_PAGES}-{MAX_PAGES} (got {pages})")
