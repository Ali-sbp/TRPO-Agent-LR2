import config


def _parse(path):
    text = path.read_text(encoding="utf-8")
    meta, body = {}, text
    if text.startswith("---"):
        _, front, body = text.split("---", 2)
        key = None
        for line in front.strip().splitlines():
            if line.startswith((" ", "\t")) and key:
                meta[key] += " " + line.strip()
            elif ":" in line:
                key, value = line.split(":", 1)
                key = key.strip()
                meta[key] = value.strip()
    return meta, body.strip()


def _all():
    return {p.stem: _parse(p) for p in sorted(config.SKILLS_DIR.glob("*.md"))}


def skill_names():
    return list(_all())


def skills_index():
    # only name + description go into the system prompt, full text via load_skill
    return "\n".join(f"- {name}: {meta.get('description', '')}" for name, (meta, _) in _all().items())


def load_skill(name):
    skills = _all()
    return skills[name][1] if name in skills else None
