#!/usr/bin/env python3
"""Generate GitHub-compatible project-card SVGs + README gallery from config/projects.json.

Standard-library only: runs locally or in GitHub Actions without pip dependencies.
The generated section is delimited with FEATURED_PROJECTS markers; everything
outside that section is preserved verbatim.
"""

from __future__ import annotations

import argparse
import html
import json
import re
import sys
from pathlib import Path
from urllib.parse import urlparse

ROOT = Path(__file__).resolve().parents[1]
CONFIG = ROOT / "config" / "projects.json"
README = ROOT / "README.md"
ASSETS = ROOT / "assets"
START = "<!-- FEATURED_PROJECTS:START -->"
END = "<!-- FEATURED_PROJECTS:END -->"

PALETTE = {
    "cyan": "#40E7E1",
    "violet": "#AD9AFF",
    "blue": "#67B7FF",
    "teal": "#49DEC1",
    "amber": "#F5BC6D",
}


def xml(text: str) -> str:
    return html.escape(text, quote=True)


def validate(data: dict) -> list[tuple[str, dict]]:
    if not isinstance(data, dict):
        raise ValueError("Expected a JSON object")
    catalog, featured = data.get("catalog"), data.get("featured")
    if not isinstance(catalog, dict) or not isinstance(featured, list):
        raise ValueError("Provide 'catalog' (object) and 'featured' (array)")
    if not 2 <= len(featured) <= 8:
        raise ValueError("Feature between 2 and 8 projects")
    if len(set(featured)) != len(featured):
        raise ValueError("The featured list cannot contain duplicate project ids")
    result = []
    for key in featured:
        if not isinstance(key, str) or not re.fullmatch(r"[a-z0-9][a-z0-9_-]{0,38}", key):
            raise ValueError(f"Invalid project id: {key!r}")
        if key not in catalog:
            raise ValueError(f"Featured project {key!r} is absent from catalog")
        item = catalog[key]
        for field in ("title", "url", "category", "subtitle", "description", "color"):
            if not isinstance(item.get(field), str) or not item[field].strip():
                raise ValueError(f"{key}: field {field!r} must be non-empty text")
        for field in ("title", "category", "subtitle", "description"):
            if len(item[field]) > {"title": 65, "category": 65, "subtitle": 105, "description": 350}[field]:
                raise ValueError(f"{key}: {field} is too long")
        parsed = urlparse(item["url"])
        if parsed.scheme != "https" or not parsed.netloc or parsed.username or parsed.password:
            raise ValueError(f"{key}: URL must be a valid HTTPS URL")
        if item["color"] not in PALETTE:
            raise ValueError(f"{key}: color must be one of {', '.join(PALETTE)}")
        if not (isinstance(item.get("flow"), list) and len(item["flow"]) == 3
                and all(isinstance(v, str) and 1 <= len(v) <= 18 for v in item["flow"])):
            raise ValueError(f"{key}: flow must be three short node names (max 18 characters)")
        if not (isinstance(item.get("tags"), list) and 1 <= len(item["tags"]) <= 4
                and all(isinstance(v, str) and 1 <= len(v) <= 22 for v in item["tags"])):
            raise ValueError(f"{key}: tags must contain 1-4 short values")
        result.append((key, item))
    return result


def svg_card(item: dict, position: int) -> str:
    accent = PALETTE[item["color"]]
    title = item["title"]
    title_size = 30 if len(title) <= 29 else 26 if len(title) <= 37 else 22
    # Limit subtitle/caption width at small GitHub column sizes.
    subtitle = item["subtitle"]
    if len(subtitle) > 47:
        subtitle = subtitle[:44].rstrip() + "…"
    tags = "   ·   ".join(item["tags"])
    if len(tags) > 71:
        tags = tags[:68].rstrip() + "…"
    boxes = []
    for idx, node in enumerate(item["flow"]):
        x = 24 + idx * 193
        txtsize = 16 if len(node) <= 13 else 14
        boxes.append(f'<rect x="{x}" y="160" width="174" height="55" rx="10" fill="#15364B" stroke="{accent}" stroke-opacity="0.7"/>')
        boxes.append(f'<text x="{x + 87}" y="194" text-anchor="middle" font-family="Arial, Helvetica, sans-serif" font-size="{txtsize}" font-weight="700" fill="#F1F8FF">{xml(node)}</text>')
        if idx < 2:
            xx=x+174
            boxes.append(f'<path d="M{xx} 187 H{xx + 18} m-6 -5 l6 5 -6 5" fill="none" stroke="{accent}" stroke-width="2.4"/>')
    return f'''<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 610 266" width="610" height="266" role="img" aria-label="Project diagram: {xml(title)}">
  <defs>
    <linearGradient id="card-bg" x1="0" y1="0" x2="1" y2="1"><stop stop-color="#112A40"/><stop offset="1" stop-color="#081728"/></linearGradient>
    <pattern id="grid" width="28" height="28" patternUnits="userSpaceOnUse"><path d="M28 0 H0 V28" fill="none" stroke="#35576C" stroke-opacity="0.35" stroke-width="1"/></pattern>
  </defs>
  <rect width="610" height="266" rx="16" fill="url(#card-bg)"/>
  <rect width="610" height="266" rx="16" fill="url(#grid)"/>
  <rect x="1" y="1" width="608" height="264" rx="15" fill="none" stroke="#3E637C" stroke-width="1.5"/>
  <path d="M24 1 H172" fill="none" stroke="{accent}" stroke-width="4"/>
  <text x="24" y="34" font-family="Arial, Helvetica, sans-serif" font-size="13.5" font-weight="700" fill="{accent}">{position:02d} / {xml(item['category'])}</text>
  <text x="24" y="79" font-family="Arial, Helvetica, sans-serif" font-size="{title_size}" font-weight="700" fill="#F3F8FF">{xml(title)}</text>
  <text x="24" y="110" font-family="Arial, Helvetica, sans-serif" font-size="17" fill="#D1E2F5">{xml(subtitle)}</text>
  <circle cx="573" cy="32" r="5" fill="{accent}"/>
  {''.join(boxes)}
  <text x="24" y="245" font-family="Arial, Helvetica, sans-serif" font-size="14.3" font-weight="700" fill="#BFD9ED">{xml(tags)}</text>
</svg>
'''


def card_markup(item: dict, position: int) -> str:
    link = xml(item["url"])
    title = xml(item["title"])
    description = xml(item["description"])
    return (
        '<td width="50%" valign="top">\n'
        f'  <a href="{link}"><img src="./assets/featured-{position}.svg" width="100%" alt="Diagram card for {title}" /></a>\n'
        f'  <br /><b><a href="{link}">{title}</a></b><br />\n'
        f'  <sub>{description}</sub>\n'
        '</td>'
    )


def gallery(items: list[tuple[str, dict]]) -> str:
    lines = ['<table>']
    for start in range(0, len(items), 2):
        lines.append('<tr>')
        lines.append(card_markup(items[start][1], start + 1))
        if start + 1 < len(items):
            lines.append(card_markup(items[start + 1][1], start + 2))
        else:
            lines.append('<td width="50%"></td>')
        lines.append('</tr>')
    lines.append('</table>')
    return "\n".join(lines)


def build(check: bool = False) -> bool:
    data = json.loads(CONFIG.read_text(encoding="utf-8"))
    items = validate(data)
    source = README.read_text(encoding="utf-8")
    if source.count(START) != 1 or source.count(END) != 1:
        raise ValueError("README.md must contain exactly one pair of FEATURED_PROJECTS markers")
    a, b = source.split(START, 1)
    _old, c = b.split(END, 1)
    updated_readme = a + START + "\n\n" + gallery(items) + "\n\n" + END + c
    desired = {f"featured-{idx}.svg": svg_card(item, idx) for idx, (_, item) in enumerate(items, 1)}
    current = {f.name: f.read_text(encoding="utf-8") for f in ASSETS.glob("featured-*.svg")}
    changed = updated_readme != source or desired != current
    if check:
        if changed:
            print("Generated project gallery is out of date. Run python scripts/generate_featured.py")
        return changed
    README.write_text(updated_readme, encoding="utf-8") if updated_readme != source else None
    ASSETS.mkdir(parents=True, exist_ok=True)
    for path in ASSETS.glob("featured-*.svg"):
        if path.name not in desired:
            path.unlink()
    for filename, content in desired.items():
        path = ASSETS / filename
        if not path.exists() or path.read_text(encoding="utf-8") != content:
            path.write_text(content, encoding="utf-8")
    print(f"Generated {len(items)} featured project cards from {CONFIG.relative_to(ROOT)}")
    return changed


def main() -> int:
    parser = argparse.ArgumentParser(description="Generate README featured project gallery from a JSON catalog")
    parser.add_argument("--check", action="store_true", help="Return failure if gallery needs rebuilding")
    args = parser.parse_args()
    try:
        return 1 if build(args.check) and args.check else 0
    except (ValueError, OSError, json.JSONDecodeError) as exc:
        print(f"Error: {exc}", file=sys.stderr)
        return 2


if __name__ == "__main__":
    raise SystemExit(main())
