"""Static catalog metadata for the render-to-image agent skill.

This module is intentionally dependency-free so a skill loader can import it
without installing the renderer's runtime dependencies.
"""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path


@dataclass(frozen=True, slots=True)
class SkillCatalogEntry:
    name: str
    description: str
    skill_dir: Path
    supported_inputs: tuple[str, ...]
    output_format: str
    entrypoint: Path


SKILL_DIR = Path(__file__).resolve().parent

ENTRY = SkillCatalogEntry(
    name="render-to-image",
    description=(
        "Render standalone HTML, HTM, or Mermaid MMD files into PNG images "
        "for visual inspection."
    ),
    skill_dir=SKILL_DIR,
    supported_inputs=(".html", ".htm", ".mmd"),
    output_format="png",
    entrypoint=SKILL_DIR / "scripts" / "render.py",
)


def get_catalog_entry() -> SkillCatalogEntry:
    """Return the immutable catalog entry for this skill."""

    return ENTRY


if __name__ == "__main__":
    print(f"{ENTRY.name}: {ENTRY.description}")
    print(f"inputs={', '.join(ENTRY.supported_inputs)} output={ENTRY.output_format}")
    print(f"entrypoint={ENTRY.entrypoint}")
