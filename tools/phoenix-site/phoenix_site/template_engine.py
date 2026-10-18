"""A small HTML template engine.

{{ name }} is escaped. {{{ name }}} is inserted as-is.
{{# name }}...{{/ name }} repeats for a list, or renders once for a truthy value.
{{^ name }}...{{/ name }} renders when the value is missing or empty.
{{> partial }} loads templates/partials/<partial>.html.
"""

from __future__ import annotations

import html
import re
from pathlib import Path
from typing import Any

_TOKEN = re.compile(
    r"\{\{\{\s*([A-Za-z0-9_.]+)\s*\}\}\}"
    r"|\{\{([#^>/])\s*([A-Za-z0-9_.-]+)\s*\}\}"
    r"|\{\{\s*([A-Za-z0-9_.]+)\s*\}\}"
)


class TemplateError(Exception):
    pass


def render_file(path: Path, context: dict[str, Any], template_dir: Path) -> str:
    return render_string(path.read_text(encoding="utf-8"), context, template_dir)


def render_string(source: str, context: dict[str, Any], template_dir: Path | None = None) -> str:
    rendered, end = _render(source, 0, context, template_dir or Path("."), [], stop_key=None)
    if end != len(source):
        raise TemplateError("Unexpected template close tag.")
    return rendered


def _lookup(context: dict[str, Any], key: str) -> Any:
    current: Any = context
    for part in key.split("."):
        if isinstance(current, dict) and part in current:
            current = current[part]
        else:
            raise TemplateError(f"Missing template value: {key}")
    return current


def _render(
    source: str,
    start: int,
    context: dict[str, Any],
    template_dir: Path,
    stack: list[str],
    stop_key: str | None,
) -> tuple[str, int]:
    out: list[str] = []
    pos = start
    while True:
        match = _TOKEN.search(source, pos)
        if match is None:
            if stop_key is not None:
                raise TemplateError(f"Unclosed section {stop_key}")
            out.append(source[pos:])
            return "".join(out), len(source)
        out.append(source[pos:match.start()])
        raw_key, sigil, sigil_key, var_key = match.groups()
        if stop_key is not None and sigil == "/" and sigil_key == stop_key:
            return "".join(out), match.end()
        if sigil == "/":
            raise TemplateError(f"Unexpected close tag {sigil_key}")
        if raw_key:
            out.append(str(_lookup(context, raw_key)))
            pos = match.end()
            continue
        if var_key:
            out.append(html.escape(str(_lookup(context, var_key)), quote=True))
            pos = match.end()
            continue
        if sigil == ">":
            partial = template_dir / "partials" / f"{sigil_key}.html"
            if not partial.is_file():
                raise TemplateError(f"Missing partial: {partial}")
            if sigil_key in stack:
                raise TemplateError(f"Partial loop: {sigil_key}")
            rendered, _end = _render(
                partial.read_text(encoding="utf-8"),
                0,
                context,
                template_dir,
                stack + [sigil_key],
                stop_key=None,
            )
            out.append(rendered)
            pos = match.end()
            continue
        if sigil in {"#", "^"}:
            try:
                value = _lookup(context, sigil_key)
            except TemplateError:
                value = None
            truthy = _is_truthy(value)
            if sigil == "^":
                if not truthy:
                    inner, pos = _render(source, match.end(), context, template_dir, stack, sigil_key)
                    out.append(inner)
                else:
                    pos = _skip(source, match.end(), sigil_key)
                continue
            if not truthy:
                pos = _skip(source, match.end(), sigil_key)
                continue
            if isinstance(value, list):
                block_end = None
                for item in value:
                    child = dict(context)
                    if isinstance(item, dict):
                        child.update(item)
                    else:
                        child["value"] = item
                    inner, block_end = _render(source, match.end(), child, template_dir, stack, sigil_key)
                    out.append(inner)
                pos = block_end if block_end is not None else match.end()
            elif isinstance(value, dict):
                child = dict(context)
                child.update(value)
                inner, pos = _render(source, match.end(), child, template_dir, stack, sigil_key)
                out.append(inner)
            else:
                inner, pos = _render(source, match.end(), context, template_dir, stack, sigil_key)
                out.append(inner)
            continue
        raise TemplateError(f"Unknown template tag near {match.group(0)}")


def _skip(source: str, start: int, stop_key: str) -> int:
    """Advance past a section without evaluating its tags."""
    pos = start
    depth = 1
    while True:
        match = _TOKEN.search(source, pos)
        if match is None:
            raise TemplateError(f"Unclosed section {stop_key}")
        _raw, sigil, sigil_key, _var = match.groups()
        pos = match.end()
        if sigil in {"#", "^"} and sigil_key == stop_key:
            depth += 1
        elif sigil == "/" and sigil_key == stop_key:
            depth -= 1
            if depth == 0:
                return pos


def _is_truthy(value: Any) -> bool:
    if value is None or value is False:
        return False
    if value == "" or value == [] or value == {}:
        return False
    return True
