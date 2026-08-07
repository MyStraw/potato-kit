#!/usr/bin/env python3
"""Install potato-kit guidance as native Codex skills and custom agents."""

from __future__ import annotations

import argparse
import json
import re
import shutil
import time
from pathlib import Path


START_MARK = "<!-- potato-kit:start -->"
END_MARK = "<!-- potato-kit:end -->"
LEGACY_MARK = "<!-- potato-kit -->"


CODEX_STATUSLINE_SKILL = """---
name: potato-statusline
description: Codex CLI 하단 상태줄과 사용량 표시를 설정한다. 사용자가 "상태줄 켜줘", "컨텍스트나 사용량 보이게 해줘", "상태줄 바꿔줘"라고 요청할 때 사용한다.
---

# potato-statusline — Codex 상태줄

Codex CLI에는 내장 상태줄 설정이 있다. Claude Code용 스크립트나
`settings.json`을 설치하지 않는다.

## 설정

1. 대화형 Codex CLI라면 사용자에게 `/statusline`을 실행하도록 안내한다.
2. 선택기에서 모델, 추론 수준, 남은 컨텍스트, 사용량 제한, Git 브랜치,
   토큰 수, 현재 디렉터리 등 원하는 항목을 선택하고 순서를 정한다.
3. 현재 사용량만 확인하려면 `/usage`, 전체 세션 설정은 `/status`를 안내한다.

설정은 Codex가 `config.toml`의 `tui.status_line`에 저장한다. 사용자 요청 없이
`config.toml`의 다른 항목을 변경하지 않는다.
"""


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser()
    parser.add_argument("--kit-dir", required=True, type=Path)
    parser.add_argument("--codex-home", required=True, type=Path)
    parser.add_argument("--skills-home", required=True, type=Path)
    return parser.parse_args()


def read_frontmatter(text: str) -> tuple[dict[str, str], str]:
    match = re.match(r"\A---\r?\n(.*?)\r?\n---\r?\n?", text, re.DOTALL)
    if not match:
        raise ValueError("missing YAML frontmatter")
    metadata: dict[str, str] = {}
    for line in match.group(1).splitlines():
        if ":" not in line:
            continue
        key, value = line.split(":", 1)
        metadata[key.strip()] = value.strip().strip('"').strip("'")
    return metadata, text[match.end() :]


def convert_text(text: str, potato_dir: Path) -> str:
    packs_path = (potato_dir / "packs").as_posix()
    rules_path = (potato_dir / "rules.md").as_posix()
    replacements = (
        ("~/.claude/potato-kit-rules.md", rules_path),
        ("~/.claude/packs", packs_path),
        ("./.claude/packs", packs_path),
        ("CLAUDE.md", "AGENTS.md"),
        ("claude mcp add -s user", "codex mcp add"),
        ("claude mcp", "codex mcp"),
        ("WebSearch", "웹 검색"),
        ("WebFetch", "웹 페이지 조회"),
    )
    for old, new in replacements:
        text = text.replace(old, new)
    # Rewrite command-style invocations without corrupting paths such as
    # ~/.codex/potato-kit. A command is not immediately preceded by a path-ish
    # character.
    text = re.sub(r"(?<![A-Za-z0-9_.~-])/potato-(?=[a-z])", "$potato-", text)
    return text


def install_skills(kit_dir: Path, skills_home: Path, potato_dir: Path) -> int:
    source = kit_dir / ".claude" / "skills"
    count = 0
    skills_home.mkdir(parents=True, exist_ok=True)
    for skill_dir in sorted(path for path in source.iterdir() if path.is_dir()):
        target = skills_home / skill_dir.name
        if target.exists():
            shutil.rmtree(target)
        shutil.copytree(skill_dir, target)
        skill_file = target / "SKILL.md"
        if skill_dir.name == "potato-statusline":
            skill_file.write_text(CODEX_STATUSLINE_SKILL, encoding="utf-8")
        else:
            converted = convert_text(skill_file.read_text(encoding="utf-8"), potato_dir)
            skill_file.write_text(converted, encoding="utf-8")
        count += 1
    return count


def install_agents(kit_dir: Path, agent_dir: Path, potato_dir: Path) -> int:
    source = kit_dir / ".claude" / "agents"
    agent_dir.mkdir(parents=True, exist_ok=True)
    count = 0
    for agent_file in sorted(source.glob("*.md")):
        raw = agent_file.read_text(encoding="utf-8")
        metadata, body = read_frontmatter(raw)
        name = metadata.get("name", agent_file.stem)
        description = metadata.get("description", f"potato-kit {name} agent")
        body = convert_text(body.strip() + "\n", potato_dir)
        fields = [
            f"name = {json.dumps(name, ensure_ascii=False)}",
            f"description = {json.dumps(description, ensure_ascii=False)}",
        ]
        if name == "methods-reviewer":
            fields.append('sandbox_mode = "read-only"')
            fields.append('model_reasoning_effort = "high"')
        fields.append(
            "developer_instructions = " + json.dumps(body, ensure_ascii=False)
        )
        (agent_dir / f"{name}.toml").write_text(
            "\n".join(fields) + "\n", encoding="utf-8"
        )
        count += 1
    return count


def managed_agents_block(kit_dir: Path, potato_dir: Path) -> str:
    rules = (kit_dir / "CLAUDE.md").read_text(encoding="utf-8")
    rules = re.sub(r"\A# .*?\r?\n", "", rules, count=1)
    rules = convert_text(rules.strip(), potato_dir)
    return f"""{START_MARK}
# potato-kit — 연구 작업 지침 (Codex)

potato-kit은 Codex의 네이티브 스킬과 사용자 정의 에이전트로 설치되어 있다.

- 연구 요청과 일치하는 `potato-*` 스킬을 먼저 읽고 그 절차를 따른다.
- 문헌 조사, 데이터 분석, 방법론 감사, 보고서 작성이 독립적으로 나뉠 때는
  설치된 전용 에이전트에 위임할 수 있다.
- 방법론 감사는 가능하면 `methods-reviewer` 에이전트에 맡겨 구현 맥락과 분리한다.
- 전공 팩 정의는 `{(potato_dir / 'packs').as_posix()}`에 있다.

## 공통 연구 운영 규칙

{rules}
{END_MARK}"""


def update_global_agents(path: Path, block: str) -> tuple[bool, Path | None]:
    path.parent.mkdir(parents=True, exist_ok=True)
    original = path.read_text(encoding="utf-8") if path.exists() else ""
    updated = original

    managed_pattern = re.compile(
        re.escape(START_MARK) + r".*?" + re.escape(END_MARK), re.DOTALL
    )
    if managed_pattern.search(updated):
        updated = managed_pattern.sub(block, updated, count=1)
    elif LEGACY_MARK in updated:
        prefix = updated.split(LEGACY_MARK, 1)[0].rstrip()
        updated = f"{prefix}\n\n{block}\n" if prefix else f"{block}\n"
    else:
        prefix = updated.rstrip()
        updated = f"{prefix}\n\n{block}\n" if prefix else f"{block}\n"

    if updated == original:
        return False, None

    backup = None
    if path.exists():
        backup = path.with_name(f"{path.name}.bak.{int(time.time())}")
        shutil.copy2(path, backup)
    path.write_text(updated, encoding="utf-8")
    return True, backup


def main() -> int:
    args = parse_args()
    kit_dir = args.kit_dir.resolve()
    codex_home = args.codex_home.expanduser().resolve()
    skills_home = args.skills_home.expanduser().resolve()
    potato_dir = codex_home / "potato-kit"

    if not (kit_dir / "CLAUDE.md").is_file():
        raise SystemExit(f"invalid kit directory: {kit_dir}")

    potato_dir.mkdir(parents=True, exist_ok=True)
    shutil.copy2(kit_dir / "CLAUDE.md", potato_dir / "rules.md")
    packs_target = potato_dir / "packs"
    if packs_target.exists():
        shutil.rmtree(packs_target)
    shutil.copytree(kit_dir / ".claude" / "packs", packs_target)

    skill_count = install_skills(kit_dir, skills_home, potato_dir)
    agent_count = install_agents(kit_dir, codex_home / "agents", potato_dir)
    changed, backup = update_global_agents(
        codex_home / "AGENTS.md", managed_agents_block(kit_dir, potato_dir)
    )

    result = {
        "skills": skill_count,
        "agents": agent_count,
        "skills_home": str(skills_home),
        "agents_home": str(codex_home / "agents"),
        "global_agents_updated": changed,
        "global_agents_backup": str(backup) if backup else None,
    }
    print(json.dumps(result, ensure_ascii=False))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
