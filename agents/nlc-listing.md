# No/Low-Content KDP Listing Writer

> **Usage:** After the build. Ask Claude: "Write the KDP listing for my NLC book". Output: `output/{project-name}/nlc_listing.md`.

## Dependencies

- `output/{project-name}/nlc_niche_researcher.md`, `nlc_spec.json`, `kdp_specs.md`

## Deliver

1. **Title (≤ 200 chars) and subtitle** — keyword-rich but readable, matching the cover
2. **Description** — HTML (`<b>`, `<br>`, `<ul>`) listing concrete interior features, size, page count, who and what it's for; no false claims
3. **7 backend keywords** (≤ 50 chars each)
4. **2 categories** (+ browse-path suggestions) and recommended list price using the research royalty estimate
5. **Series/bundle ideas**: 3 follow-up books reusing the same builder with different presets/themes
6. **Launch checklist**: KDP previewer, proof copy order, low-content ISBN choice, A+ content, ads starter keywords

Use the actual trim, page count and features from `nlc_spec.json`/`kdp_specs.md`. Never imply the book is a content-rich guide.

## Output

Save to `output/{project-name}/nlc_listing.md`.
