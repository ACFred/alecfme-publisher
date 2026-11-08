#!/usr/bin/env python3
"""Frontmatter validator — the authoring app's save-time gate (Phase 1+).

Usage (Phase 0, standalone):
    python3 tools/validate_frontmatter.py <path-to-md-file>

Validates and NORMALIZES slugs/categories on both write and read sides.
Exits 0 and prints normalized values when clean; exits 1 with the specific
violations when not. This is the same rule set Astro enforces via zod in
src/content.config.ts — Python side mirrors it so bad frontmatter can never
be *written*, and Astro's build gate catches anything that slips past.
"""

import re
import sys
from pathlib import Path

try:
    import yaml
except ImportError:
    sys.exit("PyYAML required: pip install pyyaml")

SLUG_RE = re.compile(r"^[a-z0-9]+(?:-[a-z0-9]+)*$")
DESCRIPTION_MAX = 180
LAYOUT_VARIANTS = {"classic-serif", "modern-sans", "photo-essay"}
REQUIRED_FIELDS = ["title", "slug", "category", "date", "published"]


def normalize_slug(value: str) -> str:
    """Write/read-side normalization: lowercase, spaces->hyphens, strip junk."""
    value = value.strip().lower()
    value = re.sub(r"[^a-z0-9\s-]", "", value)
    value = re.sub(r"[\s_]+", "-", value)
    value = re.sub(r"-{2,}", "-", value).strip("-")
    return value


def parse_frontmatter(text: str) -> dict:
    if not text.startswith("---"):
        raise ValueError("no frontmatter block found")
    _, fm, _body = text.split("---", 2)
    return yaml.safe_load(fm) or {}


def validate(meta: dict) -> list[str]:
    errors = []

    missing = [f for f in REQUIRED_FIELDS if f not in meta or meta[f] in (None, "")]
    errors += [f"missing required field: {f}" for f in missing]

    for f in ("slug", "category"):
        if isinstance(meta.get(f), str) and not SLUG_RE.match(meta[f]):
            norm = normalize_slug(meta[f])
            if SLUG_RE.match(norm):
                errors.append(
                    f"{f}: '{meta[f]}' not canonical; normalized form is '{norm}' "
                    f"(fix on write)"
                )
            else:
                errors.append(f"{f}: '{meta[f]}' cannot be normalized to a valid slug")

    if isinstance(meta.get("title"), str):
        if len(meta["title"].strip()) < 1:
            errors.append("title: empty")

    if isinstance(meta.get("description"), str):
        if len(meta["description"]) > DESCRIPTION_MAX:
            errors.append(f"description: {len(meta['description'])} chars > {DESCRIPTION_MAX}")

    if meta.get("published") is True:
        if not isinstance(meta.get("description"), str) or not meta["description"].strip():
            errors.append("published article requires a non-empty 'description' (SEO lint)")
        if isinstance(meta.get("excerpt"), str) and not meta["excerpt"].strip():
            errors.append("excerpt present but empty")

    lv = meta.get("layoutVariant")
    if lv is not None and lv not in LAYOUT_VARIANTS:
        errors.append(f"layoutVariant: '{lv}' not in {sorted(LAYOUT_VARIANTS)}")

    if not isinstance(meta.get("tags", []), list):
        errors.append("tags: must be a list")

    return errors


def main() -> int:
    if len(sys.argv) != 2:
        sys.exit("usage: validate_frontmatter.py <file.md>")
    path = Path(sys.argv[1])
    meta = parse_frontmatter(path.read_text(encoding="utf-8"))

    errors = validate(meta)
    if errors:
        print(f"INVALID: {path.name}")
        for e in errors:
            print(f"  - {e}")
        return 1

    print(f"OK: {path.name}  (slug='{meta['slug']}' category='{meta['category']}')")
    return 0


if __name__ == "__main__":
    sys.exit(main())