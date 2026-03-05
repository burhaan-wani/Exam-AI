"""
Automated Mark Allocation Service
Distributes marks based on Bloom level, difficulty, and sub-question structure.
"""

import logging
from app.models.schemas import BloomLevel
from app.services.bloom_taxonomy import get_mark_weight

logger = logging.getLogger(__name__)


def allocate_marks(
    total_marks: int,
    bloom_configs: list[dict],
) -> list[dict]:
    """
    Distribute total marks across bloom configs proportionally.
    Each config: {topic, bloom_level, num_questions, difficulty}
    Returns configs with computed marks_per_question.
    """
    # Compute raw weights
    weighted = []
    total_weight = 0.0
    for cfg in bloom_configs:
        level = BloomLevel(cfg["bloom_level"])
        difficulty = cfg.get("difficulty", "medium")
        n = cfg.get("num_questions", 1)
        w = get_mark_weight(level, difficulty) * n
        weighted.append((cfg, w))
        total_weight += w

    # Distribute marks proportionally
    result = []
    allocated = 0
    for i, (cfg, w) in enumerate(weighted):
        n = cfg.get("num_questions", 1)
        share = round(total_marks * (w / total_weight)) if total_weight > 0 else total_marks // len(bloom_configs)
        per_q = max(1, share // n)
        allocated += per_q * n
        result.append({**cfg, "marks_per_question": per_q})

    # Adjust rounding errors on last config
    if result and allocated != total_marks:
        diff = total_marks - allocated
        last = result[-1]
        last["marks_per_question"] = max(1, last["marks_per_question"] + diff // last.get("num_questions", 1))

    logger.info(f"Mark allocation complete: total_target={total_marks}, configs={len(result)}")
    return result


def distribute_sub_marks(total_q_marks: int, num_parts: int) -> list[int]:
    """Distribute marks across sub-questions as evenly as possible."""
    if num_parts <= 0:
        return []
    base = total_q_marks // num_parts
    remainder = total_q_marks % num_parts
    marks = [base + (1 if i < remainder else 0) for i in range(num_parts)]
    return marks
