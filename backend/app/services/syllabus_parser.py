import logging
from typing import List

from app.utils.file_parser import extract_text
from app.services.syllabus_processor import extract_topics

logger = logging.getLogger(__name__)


async def parse_syllabus_units(file_bytes: bytes, filename: str) -> tuple[str, List[str]]:
    """
    High-level helper used by the new pipeline:
    - Extract raw text from the uploaded syllabus file
    - Use the existing LLM-based topic extractor to get structured topics
    - Return raw_text and a simple list of unit names.
    """
    raw_text = extract_text(file_bytes, filename)
    topics = await extract_topics(raw_text)

    # Derive unit names (fall back to topic names if unit is empty)
    units: list[str] = []
    for t in topics:
        unit = t.get("unit") or t.get("name")
        if unit and unit not in units:
            units.append(unit)

    logger.info("Parsed %d units from syllabus '%s'", len(units), filename)
    return raw_text, units

