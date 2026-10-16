# No/Low-Content Interior Planner

> **Usage:** After NLC niche research. Ask Claude: "Plan the interior for my NLC book". It writes `output/{project-name}/nlc_spec.json`, which `python build_nlc.py output/{project-name}` turns into `interior.pdf`, `cover.pdf` and `kdp_specs.md`.

## Dependencies

- `output/{project-name}/nlc_niche_researcher.md`

## Your Role

You design the book's interior and write the build spec. You also write ALL creative content the builder needs: title, subtitle, cover copy, prompts, themed word lists, art prompts.

## Process

1. Run `python build_nlc.py --init output/{project-name} --type <preset> --title "<title>"` (presets: `python build_nlc.py --list-types`).
2. Edit the generated `nlc_spec.json` to match the research — title, subtitle, author, trim, paper, page_count, cover colors/copy, sections.
3. Run `python build_nlc.py output/{project-name}` and fix any errors/warnings.

## Spec schema

Top level: `title`, `subtitle`, `author`, `publisher`, `copyright_year`, `trim` (5x8, 5.25x8, 5.5x8.5, 6x9, 7x10, 8x10, 8.5x8.5, 8.5x11), `paper` (white, cream, color_standard, color_premium), `bleed` (bool; needed only if art touches the page edge), `page_count` (24–828; builder pads with `pad_with` pages, errors if content exceeds it), `pad_with` (`lined`, `dotted`, `grid`, `blank`), `seed`, `front_matter` (list of `title`, `copyright`, `belongs_to`, `blank`), `single_sided` (coloring: blank page behind each image), `cover` {`bg`, `fg`, `accent` hex colors; `image` path relative to the project folder; `tagline`; `back_description`}, `coloring_prompts` (list of strings), `sections`.

Each section is `{"type": ..., "count": N, ...options}`:

| type | options |
|------|---------|
| `lined`, `dotted`, `grid` | `spacing` (in), `header` |
| `blank`, `gratitude`, `daily_planner`, `weekly_planner`, `monthly_calendar` | — |
| `password`, `address` | `alphabetical` (true = pages spread across A–Z tabs; use `count` of 26, 52 or 104) |
| `meal_planner`, `grocery_list`, `recipe`, `budget` | — |
| `habit_tracker` | `habits` (columns, default 7) |
| `prompt` | `prompts`: list of strings (one page each; `count` ignored) |
| `log_table` | `title`, `columns`, `widths` (relative), `rows` |
| `wordsearch` | `size` (default 15), `difficulty` easy/medium/hard, `puzzles`: `[{ "title", "words": [...] }]` — exactly `count` entries, `solutions` |
| `sudoku` | `difficulty` easy/medium/hard/expert, `solutions` |
| `maze` | `cols`, `rows`, `solutions` |
| `coloring` | `art_dir` (default `art`); images named `001.png`, `002.png`, … |

Puzzle solutions are appended automatically at the back of the book.

## Rules

- Write original content only: word lists themed to the niche (8–20 words each, max length = grid size), prompts, and art prompts. Never copy existing books' lists, prompts or art.
- Coloring books: write one detailed art prompt per page in `coloring_prompts` (simple bold outlines, no shading, white background). The builder writes `coloring_prompts.md`; art must be generated/licensed separately and saved to `art/`. Until it exists, pages show placeholders; build with `--strict` before final upload.
- Keep a sensible page mix: front matter + content + a few notes pages at the back.
- Cover text must match the listing title and make no unverifiable claims ("#1 bestseller").

## Output

`output/{project-name}/nlc_spec.json` plus the built `interior.pdf`, `cover.pdf`, `kdp_specs.md`.
