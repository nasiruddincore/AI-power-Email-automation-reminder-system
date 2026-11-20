from string import Formatter


class SafeDict(dict):
    """Keeps missing placeholders visible instead of crashing with KeyError."""

    def __missing__(self, key: str) -> str:
        return f"{{{key}}}"


def find_missing_keys(template_str: str, context: dict[str, str]) -> list[str]:
    formatter = Formatter()
    missing: list[str] = []
    for _, field_name, _, _ in formatter.parse(template_str):
        if field_name and field_name not in context and field_name not in missing:
            missing.append(field_name)
    return missing


def render_message(
    subject_tmpl: str,
    body_tmpl: str,
    context: dict[str, str],
) -> tuple[str, str, list[str]]:
    safe_ctx = SafeDict({k: ("" if v is None else str(v)) for k, v in context.items()})
    missing_subj = find_missing_keys(subject_tmpl, safe_ctx)
    missing_body = find_missing_keys(body_tmpl, safe_ctx)
    missing_all = list(dict.fromkeys(missing_subj + missing_body))

    rendered_subject = subject_tmpl.format_map(safe_ctx).strip()
    rendered_body = body_tmpl.format_map(safe_ctx).strip()
    return rendered_subject, rendered_body, missing_all