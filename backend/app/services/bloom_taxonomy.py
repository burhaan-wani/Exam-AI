"""
Bloom's Taxonomy Controller
Maps topics to cognitive levels and provides difficulty-based constraints.
"""

from app.models.schemas import BloomLevel

# Bloom level descriptions for prompt injection
BLOOM_DESCRIPTORS: dict[str, dict] = {
    BloomLevel.REMEMBER: {
        "verbs": ["define", "list", "recall", "state", "identify", "name"],
        "description": "Recall facts and basic concepts",
        "cognitive_depth": "surface",
        "mark_weight": 1.0,
    },
    BloomLevel.UNDERSTAND: {
        "verbs": ["explain", "describe", "summarize", "interpret", "classify"],
        "description": "Explain ideas or concepts in own words",
        "cognitive_depth": "shallow",
        "mark_weight": 1.2,
    },
    BloomLevel.APPLY: {
        "verbs": ["solve", "use", "demonstrate", "implement", "calculate"],
        "description": "Use information in new situations",
        "cognitive_depth": "moderate",
        "mark_weight": 1.5,
    },
    BloomLevel.ANALYZE: {
        "verbs": ["differentiate", "compare", "contrast", "examine", "categorize"],
        "description": "Draw connections among ideas; break into parts",
        "cognitive_depth": "deep",
        "mark_weight": 1.8,
    },
    BloomLevel.EVALUATE: {
        "verbs": ["justify", "critique", "assess", "argue", "defend"],
        "description": "Justify a stand or decision; make judgments",
        "cognitive_depth": "deep",
        "mark_weight": 2.0,
    },
    BloomLevel.CREATE: {
        "verbs": ["design", "construct", "develop", "formulate", "propose"],
        "description": "Produce new or original work",
        "cognitive_depth": "synthesis",
        "mark_weight": 2.5,
    },
}

DIFFICULTY_MULTIPLIERS = {
    "easy": 0.8,
    "medium": 1.0,
    "hard": 1.3,
}


def get_bloom_descriptor(level: BloomLevel) -> dict:
    return BLOOM_DESCRIPTORS.get(level, BLOOM_DESCRIPTORS[BloomLevel.REMEMBER])


def get_bloom_verbs(level: BloomLevel) -> list[str]:
    return get_bloom_descriptor(level)["verbs"]


def get_mark_weight(level: BloomLevel, difficulty: str = "medium") -> float:
    """Calculate mark weight based on Bloom level and difficulty."""
    base = get_bloom_descriptor(level)["mark_weight"]
    mult = DIFFICULTY_MULTIPLIERS.get(difficulty, 1.0)
    return round(base * mult, 2)


def compute_marks(base_marks: int, level: BloomLevel, difficulty: str = "medium") -> int:
    """Compute allocated marks for a question given base marks, Bloom level, and difficulty."""
    weight = get_mark_weight(level, difficulty)
    return max(1, round(base_marks * weight))
