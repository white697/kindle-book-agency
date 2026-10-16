#!/usr/bin/env python3
"""
No/low-content KDP paperback builder.

Usage:
  python build_nlc.py --init output/my-journal --type journal --title "Morning Pages"
  python build_nlc.py output/my-journal                 # build interior.pdf + cover.pdf + kdp_specs.md
  python build_nlc.py output/my-journal --strict        # fail if coloring art is missing
  python build_nlc.py --list-types

Reads output/<project>/nlc_spec.json (see agents/nlc-planner.md for the schema).
"""

import argparse
import json
import sys
from pathlib import Path

from nlc.builder import PRESETS, build_cover, build_interior, build_plan, default_spec, kdp_report


def main():
    ap = argparse.ArgumentParser(description="Build print-ready no/low-content KDP books.")
    ap.add_argument("project", nargs="?", help="Project folder, e.g. output/my-journal")
    ap.add_argument("--init", action="store_true", help="Create nlc_spec.json from a preset")
    ap.add_argument("--type", default="journal", help="Preset for --init")
    ap.add_argument("--title", default="Untitled", help="Title for --init")
    ap.add_argument("--strict", action="store_true", help="Fail on missing coloring art")
    ap.add_argument("--list-types", action="store_true")
    a = ap.parse_args()

    if a.list_types:
        print("\n".join(PRESETS))
        return
    if not a.project:
        ap.error("project folder required")
    base = Path(a.project)
    spec_path = base / "nlc_spec.json"

    if a.init:
        base.mkdir(parents=True, exist_ok=True)
        if spec_path.exists():
            sys.exit(f"{spec_path} already exists; edit it instead.")
        spec_path.write_text(json.dumps(default_spec(a.type, a.title), indent=2) + "\n", encoding="utf-8")
        print(f"Created {spec_path}")
        return

    if not spec_path.exists():
        sys.exit(f"{spec_path} not found. Run with --init or have the NLC Planner agent write it.")
    spec = json.loads(spec_path.read_text(encoding="utf-8"))

    try:
        plan, warnings = build_plan(spec, base, strict=a.strict)
        g = build_interior(spec, plan, base / "interior.pdf")
        cover = build_cover(spec, len(plan), base / "cover.pdf", base)
    except (ValueError, KeyError, FileNotFoundError) as e:
        sys.exit(f"Error: {e}")
    (base / "kdp_specs.md").write_text(kdp_report(spec, len(plan), g, cover, warnings), encoding="utf-8")

    prompts = spec.get("coloring_prompts") or []
    if prompts:
        (base / "coloring_prompts.md").write_text(
            "# Coloring page art prompts\n\nSave images as art/001.png, art/002.png, ... "
            "(300 DPI, black line art on white).\n\n"
            + "\n".join(f"{i}. {p}" for i, p in enumerate(prompts, 1)) + "\n", encoding="utf-8")

    print(f"Interior: {base / 'interior.pdf'}  ({len(plan)} pages, {spec['trim']}, {spec['paper']})")
    print(f"Cover:    {base / 'cover.pdf'}  ({cover['width']} x {cover['height']} in, spine {cover['spine']} in)")
    print(f"Specs:    {base / 'kdp_specs.md'}")
    for w in warnings:
        print(f"  warning: {w}")


if __name__ == "__main__":
    main()
