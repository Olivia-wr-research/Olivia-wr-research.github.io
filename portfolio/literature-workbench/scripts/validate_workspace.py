#!/usr/bin/env python3
from __future__ import annotations
from pathlib import Path
import re
import sys
import tomllib

ROOT = Path(__file__).resolve().parents[1]

REQUIRED_ROOT = ['README.md','AGENTS.md','.codex/config.toml','.agents/skills','references','templates','scripts','projects']
REQUIRED_AGENT_FIELDS = {'name','description','developer_instructions'}


def parse_frontmatter(path: Path):
    text = path.read_text(encoding='utf-8')
    if not text.startswith('---\n'):
        return None, ['missing YAML frontmatter opening']
    end = text.find('\n---\n', 4)
    if end < 0:
        return None, ['missing YAML frontmatter closing']
    front = text[4:end].splitlines()
    data = {}
    errors = []
    for line in front:
        if not line.strip():
            continue
        if ':' not in line:
            errors.append(f'invalid frontmatter line: {line}')
            continue
        k, v = line.split(':', 1)
        data[k.strip()] = v.strip()
    extra = set(data) - {'name','description'}
    if extra:
        errors.append(f'unexpected frontmatter fields: {sorted(extra)}')
    for k in ('name','description'):
        if not data.get(k):
            errors.append(f'missing {k}')
    return data, errors


def main():
    errors = []
    warnings = []
    for rel in REQUIRED_ROOT:
        if not (ROOT / rel).exists():
            errors.append(f'missing root item: {rel}')

    skills_root = ROOT / '.agents/skills'
    skill_count = 0
    if skills_root.exists():
        for skill_dir in sorted(p for p in skills_root.iterdir() if p.is_dir()):
            skill_count += 1
            sf = skill_dir / 'SKILL.md'
            if not sf.exists():
                errors.append(f'{skill_dir.name}: missing SKILL.md')
                continue
            data, ferr = parse_frontmatter(sf)
            errors.extend(f'{skill_dir.name}: {e}' for e in ferr)
            if data:
                if data['name'] != skill_dir.name:
                    errors.append(f'{skill_dir.name}: frontmatter name mismatch {data["name"]}')
                if not re.fullmatch(r'[a-z0-9-]{1,64}', data['name']):
                    errors.append(f'{skill_dir.name}: invalid skill name')
                if len(data['description']) > 700:
                    warnings.append(f'{skill_dir.name}: long description ({len(data["description"])})')
            oy = skill_dir / 'agents/openai.yaml'
            if not oy.exists():
                warnings.append(f'{skill_dir.name}: no agents/openai.yaml UI metadata')

    agents_root = ROOT / '.codex/agents'
    agent_count = 0
    if agents_root.exists():
        for af in sorted(agents_root.glob('*.toml')):
            agent_count += 1
            try:
                data = tomllib.loads(af.read_text(encoding='utf-8'))
            except Exception as e:
                errors.append(f'{af.name}: TOML parse failed: {e}')
                continue
            missing = REQUIRED_AGENT_FIELDS - set(data)
            if missing:
                errors.append(f'{af.name}: missing fields {sorted(missing)}')

    for script in ('bootstrap_project.py','validate_evidence.py','summarize_project.py'):
        if not (ROOT / 'scripts' / script).exists():
            errors.append(f'missing script {script}')

    print('LITERATURE THEORY WORKBENCH VALIDATION')
    print(f'skills={skill_count} custom_agents={agent_count}')
    for w in warnings:
        print(f'WARN  {w}')
    for e in errors:
        print(f'ERROR {e}')
    if errors:
        print('STATUS=FAIL')
        return 1
    print('STATUS=PASS')
    return 0

if __name__ == '__main__':
    raise SystemExit(main())
