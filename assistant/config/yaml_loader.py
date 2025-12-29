from __future__ import annotations

from typing import Any, Tuple


def _coerce_scalar(value: str) -> Any:
    if value.lower() in {"true", "false"}:
        return value.lower() == "true"
    try:
        if "." in value:
            return float(value)
        return int(value)
    except ValueError:
        return value


def _next_non_empty(lines: list[str], start: int) -> tuple[int, str, int] | None:
    for idx in range(start, len(lines)):
        raw = lines[idx]
        stripped = raw.strip()
        if not stripped or stripped.startswith("#"):
            continue
        indent = len(raw) - len(raw.lstrip(" "))
        return idx, stripped, indent
    return None


def _parse_block(lines: list[str], start: int, indent: int) -> tuple[Any, int]:
    data: dict[str, Any] = {}
    i = start
    while i < len(lines):
        raw = lines[i]
        stripped = raw.strip()
        if not stripped or stripped.startswith("#"):
            i += 1
            continue
        current_indent = len(raw) - len(raw.lstrip(" "))
        if current_indent < indent:
            break

        if ":" not in stripped:
            i += 1
            continue

        key, rest = stripped.split(":", 1)
        key = key.strip()
        rest = rest.strip()

        if rest:
            data[key] = _coerce_scalar(rest)
            i += 1
            continue

        lookahead = _next_non_empty(lines, i + 1)
        if lookahead is None:
            data[key] = {}
            i += 1
            continue

        next_idx, next_stripped, next_indent = lookahead
        if next_indent <= current_indent:
            data[key] = {}
            i += 1
            continue

        if next_stripped.startswith("- "):
            items: list[Any] = []
            i = next_idx
            while i < len(lines):
                raw_item = lines[i]
                stripped_item = raw_item.strip()
                item_indent = len(raw_item) - len(raw_item.lstrip(" "))
                if item_indent < next_indent or not stripped_item:
                    break
                if not stripped_item.startswith("- "):
                    break
                value_str = stripped_item[2:].strip()
                if value_str:
                    items.append(_coerce_scalar(value_str))
                    i += 1
                else:
                    nested_obj, new_i = _parse_block(lines, i + 1, item_indent + 2)
                    items.append(nested_obj)
                    i = new_i
            data[key] = items
        else:
            nested_obj, new_i = _parse_block(lines, i + 1, current_indent + 2)
            data[key] = nested_obj
            i = new_i
            continue
    return data, i


def load_yaml_text(text: str) -> Any:
    lines = text.splitlines()
    result, _ = _parse_block(lines, 0, 0)
    return result
