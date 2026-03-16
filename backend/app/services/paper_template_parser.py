import asyncio
import json
import logging
import os

from langchain.prompts import ChatPromptTemplate
from langchain_core.messages import HumanMessage, SystemMessage
from langchain_openai import ChatOpenAI

from app.config import get_settings
from app.models.schemas import PaperTemplateBlueprint

logger = logging.getLogger(__name__)
settings = get_settings()


def _get_chat_model() -> ChatOpenAI:
    os.environ["OPENAI_API_KEY"] = settings.openrouter_api_key
    os.environ["OPENAI_BASE_URL"] = "https://openrouter.ai/api/v1"
    return ChatOpenAI(model=settings.openrouter_model, temperature=0.1)


TEMPLATE_BLUEPRINT_PROMPT = ChatPromptTemplate.from_messages(
    [
        (
            "system",
            "You are an academic exam-template analyst. Extract only structure from the paper and return ONLY valid JSON.",
        ),
        (
            "human",
            """Analyze the following exam paper template and extract its structural blueprint.

Known syllabus units:
{unit_names}

Requirements:
- Capture the overall paper title if present.
- Capture total marks and duration if present.
- Extract each main question group.
- For each question group, infer the unit if possible from ordering or topic hints.
- Capture the total marks for the question group.
- Capture whether the question has an OR alternative.
- Capture sub-part labels and marks for both the primary and alternative options.
- If a question is a single full question, represent it as one subpart with an empty label and the full marks.
- Do not copy full question text into the output. We only need the paper structure.

Return ONLY valid JSON in this exact format:
{{
  "title": "Exam title",
  "total_marks": 100,
  "duration_minutes": 180,
  "question_groups": [
    {{
      "question_number": 1,
      "unit_hint": "Unit 1",
      "marks": 20,
      "primary": {{
        "subparts": [
          {{"label": "a", "marks": 8}},
          {{"label": "b", "marks": 6}},
          {{"label": "c", "marks": 6}}
        ]
      }},
      "alternative": {{
        "subparts": [
          {{"label": "a", "marks": 10}},
          {{"label": "b", "marks": 10}}
        ]
      }}
    }}
  ]
}}

Template text:
{template_text}
""",
        ),
    ]
)


VISION_TEMPLATE_ANALYST_INSTRUCTIONS = """Analyze the uploaded exam paper images and extract only the structural blueprint.

Known syllabus units:
{unit_names}

Requirements:
- Capture the overall paper title if present.
- Capture total marks and duration if present.
- Extract each main question group in order.
- For each question group, infer the unit if possible from ordering or topic hints.
- Capture the total marks for the question group.
- Capture whether the question has an OR alternative.
- Capture sub-part labels and marks for both the primary and alternative options.
- If a question is a single full question, represent it as one subpart with an empty label and the full marks.
- Do not copy full question text into the output. We only need the paper structure.
- If some text is unclear, infer the structure conservatively from visible numbering, OR separators, and marks.

Return ONLY valid JSON in this exact format:
{{
  "title": "Exam title",
  "total_marks": 100,
  "duration_minutes": 180,
  "question_groups": [
    {{
      "question_number": 1,
      "unit_hint": "Unit 1",
      "marks": 20,
      "primary": {{
        "subparts": [
          {{"label": "a", "marks": 8}},
          {{"label": "b", "marks": 6}},
          {{"label": "c", "marks": 6}}
        ]
      }},
      "alternative": {{
        "subparts": [
          {{"label": "a", "marks": 10}},
          {{"label": "b", "marks": 10}}
        ]
      }}
    }}
  ]
}}
"""


def _clean_json_content(raw: str) -> str:
    content = (raw or "").strip()
    if content.startswith("```"):
        content = content.split("\n", 1)[1]
        content = content.rsplit("```", 1)[0]
    return content


def _validate_blueprint(raw: str) -> PaperTemplateBlueprint:
    try:
        data = json.loads(_clean_json_content(raw))
        blueprint = PaperTemplateBlueprint.model_validate(data)
    except Exception as error:
        logger.error("Failed to parse paper template blueprint: %s", error)
        raise ValueError("Could not extract a usable paper blueprint from the uploaded template.")

    if not blueprint.question_groups:
        raise ValueError("The uploaded template did not contain any recognizable question groups.")
    return blueprint


async def _parse_from_text(llm: ChatOpenAI, template_text: str, unit_names: list[str]) -> PaperTemplateBlueprint:
    messages = TEMPLATE_BLUEPRINT_PROMPT.format_messages(
        unit_names="\n".join(f"- {unit}" for unit in unit_names) or "- Unknown",
        template_text=template_text[:14000],
    )

    def _run() -> str:
        response = llm.invoke(messages)
        return response.content or ""

    raw = await asyncio.to_thread(_run)
    return _validate_blueprint(raw)


async def _parse_from_images(llm: ChatOpenAI, page_images: list[str], unit_names: list[str]) -> PaperTemplateBlueprint:
    if not page_images:
        raise ValueError("The uploaded template did not contain any recognizable question groups.")

    content: list[dict] = [
        {
            "type": "text",
            "text": VISION_TEMPLATE_ANALYST_INSTRUCTIONS.format(
                unit_names="\n".join(f"- {unit}" for unit in unit_names) or "- Unknown",
            ),
        }
    ]
    for image_url in page_images[:6]:
        content.append(
            {
                "type": "image_url",
                "image_url": {"url": image_url},
            }
        )

    messages = [
        SystemMessage(content="You are an academic exam-template analyst. Return only valid JSON."),
        HumanMessage(content=content),
    ]

    def _run() -> str:
        response = llm.invoke(messages)
        return response.content or ""

    try:
        raw = await asyncio.to_thread(_run)
    except Exception as error:
        logger.error("Vision template parsing failed: %s", error)
        raise ValueError(
            "This template appears to be a scanned image PDF. The current model could not analyze the page images."
        )

    return _validate_blueprint(raw)


async def parse_paper_template_blueprint(
    template_text: str,
    unit_names: list[str],
    page_images: list[str] | None = None,
) -> PaperTemplateBlueprint:
    llm = _get_chat_model()
    normalized_text = (template_text or "").strip()

    if normalized_text and len(normalized_text) >= 120:
        try:
            return await _parse_from_text(llm, normalized_text, unit_names)
        except ValueError:
            if not page_images:
                raise

    if page_images:
        return await _parse_from_images(llm, page_images, unit_names)

    if normalized_text:
        return await _parse_from_text(llm, normalized_text, unit_names)

    raise ValueError("Could not extract readable text from the uploaded template. Try a clearer PDF or image-based OCR path.")
