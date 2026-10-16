"""Quality lint for NLC specs: catches the generic-template faults that get kids' books rejected.

lint_spec() inspects the spec; lint_plan() inspects the expanded page plan. Both return warning strings.
"""

import re

BARE_HEADER = re.compile(r"^\s*(name|date)\s*[:_/]", re.I)
THIN_STARTERS = re.compile(r"^(my favou?rite|the position i|describe the best|what is your)", re.I)


def _items(sec):
    return [i for i in (sec.get("prompts") or []) + (sec.get("items") or [])]


def lint_spec(spec: dict) -> list[str]:
    w = []
    theme = spec.get("theme")
    audience_kids = bool(theme)
    kinds, n_prompts = [], 0
    for si, sec in enumerate(spec.get("sections", [])):
        t = sec.get("type")
        where = f"section {si + 1} ({t})"
        for key in ("header", "title"):
            if isinstance(sec.get(key), str) and BARE_HEADER.match(sec[key]):
                w.append(f"{where}: bare '{sec[key]}' header - use a themed equivalent (e.g. 'Player: ___ / Match date: ___')")
        if audience_kids and t == "gratitude":
            w.append(f"{where}: gratitude pages read as adult wellness copy - use a 'report' section instead")
        if audience_kids and t in ("lined", "dotted", "grid", "blank") and int(sec.get("count", 1)) > 2:
            w.append(f"{where}: {sec.get('count')} flat '{t}' pages - give each page a directed task (prompt/doodle/notes)")
        if not sec.get("line") and not sec.get("lines") and audience_kids and t not in ("prompt", "doodle", "pages"):
            w.append(f"{where}: no 'line'/'lines' personality copy (theme.lines will be cycled instead)")
        for ii, it in enumerate(_items(sec)):
            d = {"text": it} if isinstance(it, str) else it
            ityp = d.get("type", {"prompt": "prompt", "doodle": "doodle"}.get(t, "notes"))
            text = d.get("text", "")
            if ityp in ("prompt", "prompt_card"):
                n_prompts += 1
                kinds.append(d.get("kind", "opinion"))
                if len(text.split()) < 9 and d.get("kind") not in ("wyr", "ranking"):
                    w.append(f"{where} item {ii + 1}: prompt is thin ({len(text.split())} words) - make it specific and surprising")
                if THIN_STARTERS.match(text):
                    w.append(f"{where} item {ii + 1}: generic opener '{text[:36]}...' - rewrite as a scenario")
                if audience_kids and not d.get("line") and not sec.get("lines") and not sec.get("line"):
                    w.append(f"{where} item {ii + 1}: no personality 'line'")
                if d.get("kind") == "wyr" and len(d.get("options") or []) != 2:
                    w.append(f"{where} item {ii + 1}: 'wyr' needs exactly 2 options")
                if d.get("kind") in ("draw", "design", "fill") and not (d.get("starter") or d.get("art")):
                    w.append(f"{where} item {ii + 1}: '{d['kind']}' page has no printed starter element")
            if ityp == "doodle":
                if not (d.get("starter") or d.get("art")):
                    w.append(f"{where} item {ii + 1}: doodle page has no printed starter (empty canvas)")
                if BARE_HEADER.match(text) or len(text.split()) < 6:
                    w.append(f"{where} item {ii + 1}: doodle challenge is not a directed challenge")
        if t == "wordsearch":
            for pi, pz in enumerate(sec.get("puzzles", [])):
                if len(pz.get("words", [])) < 12:
                    w.append(f"{where} puzzle {pi + 1}: only {len(pz.get('words', []))} words - use 12+ (and mix in tricky ones)")
                if audience_kids and not pz.get("blurb"):
                    w.append(f"{where} puzzle {pi + 1}: no mascot 'blurb'")
                if not pz.get("secret"):
                    w.append(f"{where} puzzle {pi + 1}: no 'secret' word/clue (gives the puzzle a reason to exist)")
    if n_prompts >= 8 and len(set(kinds)) < 6:
        w.append(f"prompts use only {len(set(kinds))} kinds ({', '.join(sorted(set(kinds)))}); vary: "
                 "opinion, story, draw, ranking, wyr, design, rule, fill")
    if theme:
        if not theme.get("mascot", {}).get("name"):
            w.append("theme.mascot.name missing - the host character should talk to the reader")
        if not theme.get("fonts"):
            w.append("theme.fonts not set - pages will use built-in Helvetica (drop OFL .ttf files in ./fonts)")
        if len(theme.get("lines", [])) < 8:
            w.append("theme.lines has <8 lines of fallback personality copy")
    else:
        w.append("no 'theme' block: pages will use the plain template look (fine for utility logs, not for kids' books)")
    return w


def lint_plan(plan: list) -> list[str]:
    w, run, last = [], 0, None
    for i, (fn, kw) in enumerate(plan, 1):
        sig = (fn.__name__, kw.get("kind"))
        run = run + 1 if sig == last else 1
        if run == 4 and fn.__name__ not in ("wordsearch_page", "maze_page", "solutions_page", "notes_page"):
            w.append(f"pages {i - 3}-{i}: four identical '{fn.__name__}' layouts in a row")
        last = sig
    pads = sum(1 for _, kw in plan if kw.get("_pad"))
    if pads > 4:
        w.append(f"{pads} of {len(plan)} pages are padding repeats - add real content or lower page_count "
                 "(KDP only needs 24+ pages)")
    early = [(fn.__name__, kw) for fn, kw in plan[3:12]]
    for name, kw in early:
        d = kw.get("data")
        if name == "wordsearch_page" and d and (d["size"] >= 14 or len(d["placed"]) > 14):
            w.append("an early word search is large/long - the first ~5 pages should be easy wins")
            break
    return w
