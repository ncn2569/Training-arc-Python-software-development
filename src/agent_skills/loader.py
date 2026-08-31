"""Skill discovery + loading cho agent.

Agent skills nằm trong `agent_skills/`. Mỗi skill là MỘT thư mục con chứa `SKILL.md`
(frontmatter `name` + `description`) và tùy chọn `references/` (tài liệu bổ trợ) và
`scripts/` (entrypoint thực thi).

Cách dùng (progressive disclosure, giống Claude Code):
- Startup: `render_skills_index()` quét mọi skill, chỉ bơm name + description vào
  system prompt để agent BIẾT có những skill nào.
- Khi cần dùng: agent gọi tool `load_skill(name)` -> nạp TOÀN BỘ hướng dẫn
  (body của SKILL.md + nội dung references + đường dẫn scripts) vào context rồi làm theo.
"""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path

SKILLS_ROOT = Path(__file__).resolve().parent


@dataclass(frozen=True, slots=True)
class Skill:
    name: str
    description: str
    skill_dir: Path
    body: str
    references: tuple[Path, ...]
    scripts: tuple[Path, ...]


def _parse_frontmatter(text: str) -> tuple[dict, str]:
    """Tách frontmatter `--- ... ---` khỏi body. Trả về (meta, body)."""
    lines = text.splitlines()
    if not lines or lines[0].strip() != "---":
        return {}, text

    end = None
    for i in range(1, len(lines)):
        if lines[i].strip() == "---":
            end = i
            break
    if end is None:
        return {}, text

    meta: dict = {}
    for raw in lines[1:end]:
        if ":" not in raw:
            continue
        key, _, value = raw.partition(":")
        meta[key.strip().lower()] = value.strip()

    body = "\n".join(lines[end + 1:]).strip()
    return meta, body


def _iter_files(directory: Path) -> tuple[Path, ...]:
    if not directory.is_dir():
        return ()
    return tuple(
        sorted(p for p in directory.iterdir() if p.is_file() and p.name != "__pycache__")
    )


def discover_skills(root: Path = SKILLS_ROOT) -> list[Skill]:
    """Quét các thư mục con chứa SKILL.md, trả về danh sách skill đã parse."""
    skills: list[Skill] = []
    if not root.is_dir():
        return skills

    for skill_dir in sorted(root.iterdir()):
        if not skill_dir.is_dir():
            continue
        skill_md = skill_dir / "SKILL.md"
        if not skill_md.is_file():
            continue

        text = skill_md.read_text(encoding="utf-8")
        meta, body = _parse_frontmatter(text)

        skills.append(
            Skill(
                name=meta.get("name") or skill_dir.name,
                description=meta.get("description", ""),
                skill_dir=skill_dir,
                body=body,
                references=_iter_files(skill_dir / "references"),
                scripts=_iter_files(skill_dir / "scripts"),
            )
        )

    return skills


def get_skill(name: str) -> Skill | None:
    """Tìm skill theo `name` (frontmatter) hoặc theo tên thư mục."""
    for skill in discover_skills():
        if skill.name == name or skill.skill_dir.name == name:
            return skill
    return None


def render_skills_index(skills: list[Skill] | None = None) -> str:
    """Render danh sách skill (name + description) để bơm vào system prompt."""
    skills = skills if skills is not None else discover_skills()
    if not skills:
        return ""

    lines = ["## AGENT SKILLS (có sẵn)", ""]
    for skill in skills:
        lines.append(f"- **{skill.name}**: {skill.description}")
    lines.append("")
    lines.append(
        "Khi nhiệm vụ liên quan tới một skill ở trên, hãy gọi tool `load_skill(name)` "
        "để nạp toàn bộ hướng dẫn của skill đó vào context rồi làm đúng theo nó."
    )
    return "\n".join(lines)


def build_system_prompt(base: str, skills: list[Skill] | None = None) -> str:
    """Ghép skills index vào sau system prompt gốc."""
    index = render_skills_index(skills)
    if not index:
        return base
    return f"{base}\n\n{index}"


def load_skill(name: str) -> dict:
    """Handler cho tool `load_skill`.

    Trả về toàn bộ nội dung skill để bơm vào context: instructions (body SKILL.md),
    references (đã inline nội dung) và scripts (đường dẫn tuyệt đối).
    """
    skill = get_skill(name)
    if skill is None:
        available = ", ".join(s.name for s in discover_skills()) or "(không có)"
        return {
            "success": False,
            "error": (
                f"Không tìm thấy skill '{name}'. Skill hiện có: {available}. "
                "Dùng đúng tên trong danh sách AGENT SKILLS ở system prompt."
            ),
        }

    return {
        "success": True,
        "name": skill.name,
        "description": skill.description,
        "skill_dir": str(skill.skill_dir),
        "instructions": skill.body,
        "references": {
            str(p.relative_to(skill.skill_dir)): p.read_text(encoding="utf-8")
            for p in skill.references
        },
        "scripts": {
            str(p.relative_to(skill.skill_dir)): str(p) for p in skill.scripts
        },
        "hint": (
            "Chạy script bằng run_terminal với đường dẫn tuyệt đối trong 'scripts'. "
            "Nội dung references đã được in đầy đủ phía trên."
        ),
    }


if __name__ == "__main__":
    for s in discover_skills():
        print(f"[{s.name}] {s.description}")
        print(f"  dir={s.skill_dir}")
        print(f"  refs={[str(r.name) for r in s.references]}")
        print(f"  scripts={[str(p.name) for p in s.scripts]}")
