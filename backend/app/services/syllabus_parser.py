import logging
import re
from typing import Any

from app.utils.file_parser import extract_text

logger = logging.getLogger(__name__)

_UNIT_PATTERN = re.compile(r"^\s*unit\s*[-:]?\s*(\d+)\s*$", re.IGNORECASE)
_IGNORED_LINE_PREFIXES = (
    "course objective",
    "course objectives",
    "course outcome",
    "course outcomes",
    "prerequisite",
    "prerequisites",
    "hands-on",
    "text book",
    "text books",
    "reference book",
    "reference books",
    "references",
)
_TERMINAL_SECTION_PREFIXES = (
    "text book",
    "text books",
    "reference book",
    "reference books",
    "e-learning",
    "f-learning",
    "co-po",
    "co po",
    "co-pso",
    "course po",
    "course outcomes",
)


def _normalize_line(line: str) -> str:
    line = line.replace("\u2013", "-").replace("\u2014", "-")
    return re.sub(r"\s+", " ", line).strip(" \t-:|")


def _is_unit_heading(line: str) -> re.Match[str] | None:
    return _UNIT_PATTERN.match(_normalize_line(line))


def _should_skip_line(line: str) -> bool:
    normalized = _normalize_line(line)
    lowered = normalized.lower()

    if not normalized:
        return True
    if lowered in {"contents", "hours", "cos", "&"}:
        return True
    if lowered.startswith(_IGNORED_LINE_PREFIXES):
        return True
    if lowered.startswith("co") and len(lowered) <= 4:
        return True
    if lowered.startswith("http"):
        return True
    if normalized.startswith('"'):
        return True
    if re.fullmatch(r"[\d\s.]+", normalized):
        return True
    return False


def _is_terminal_section_heading(line: str) -> bool:
    normalized = _normalize_line(line).lower()
    return normalized.startswith(_TERMINAL_SECTION_PREFIXES)


def _dedupe_keep_order(items: list[str]) -> list[str]:
    seen: set[str] = set()
    ordered: list[str] = []
    for item in items:
        key = item.lower()
        if key in seen:
            continue
        seen.add(key)
        ordered.append(item)
    return ordered


def _extract_topics_from_line(line: str) -> list[str]:
    normalized = _normalize_line(line)
    if _should_skip_line(normalized):
        return []

    topics: list[str] = []
    if ":" in normalized:
        heading, remainder = normalized.split(":", 1)
        heading = _normalize_line(heading)
        remainder = _normalize_line(remainder)
        if heading and not _should_skip_line(heading):
            topics.append(heading)
        if remainder:
            for part in re.split(r",|/|;", remainder):
                cleaned = _normalize_line(part)
                if cleaned and not _should_skip_line(cleaned):
                    topics.append(cleaned)
    else:
        topics.append(normalized)

    return _dedupe_keep_order(topics)


def _build_unit_record(unit_number: str, lines: list[str]) -> dict[str, Any]:
    extracted_topics: list[str] = []
    for line in lines:
        extracted_topics.extend(_extract_topics_from_line(line))

    extracted_topics = _dedupe_keep_order(extracted_topics)
    if not extracted_topics:
        raise ValueError(f"Unit {unit_number} does not contain any parseable topics")

    title = extracted_topics[0]
    unit_name = f"Unit {unit_number}: {title}"
    return {
        "name": unit_name,
        "unit": unit_name,
        "subtopics": extracted_topics,
    }


async def parse_syllabus_units(file_bytes: bytes, filename: str) -> tuple[str, list[dict[str, Any]]]:
    """
    Extract syllabus units and topics with strict filtering.
    Course objectives, outcomes, prerequisites, references, and hands-on lines
    are intentionally ignored.
    """
    raw_text = extract_text(file_bytes, filename)
    lines = [_normalize_line(line) for line in raw_text.splitlines()]

    parsed_units: list[dict[str, Any]] = []
    current_unit_number: str | None = None
    current_unit_lines: list[str] = []

    for line in lines:
        if not line:
            continue

        if current_unit_number and _is_terminal_section_heading(line):
            if current_unit_lines:
                parsed_units.append(_build_unit_record(current_unit_number, current_unit_lines))
            current_unit_number = None
            current_unit_lines = []
            break

        unit_match = _is_unit_heading(line)
        if unit_match:
            if current_unit_number and current_unit_lines:
                parsed_units.append(_build_unit_record(current_unit_number, current_unit_lines))
            current_unit_number = unit_match.group(1)
            current_unit_lines = []
            continue

        if current_unit_number:
            current_unit_lines.append(line)

    if current_unit_number and current_unit_lines:
        parsed_units.append(_build_unit_record(current_unit_number, current_unit_lines))

    if not parsed_units:
        raise ValueError(
            "Could not identify any syllabus units. Make sure the file contains headings like 'Unit 1' or 'Unit - 1'."
        )

    logger.info("Parsed %d units from syllabus '%s'", len(parsed_units), filename)
    return raw_text, parsed_units

