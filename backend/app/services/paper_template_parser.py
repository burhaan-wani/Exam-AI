import asyncio
import json
import logging
import os
import re

from openai import OpenAI

from app.config import get_settings, get_text_model, get_vision_model
from app.models.schemas import (
    PaperTemplateBlueprint,
    PaperTemplateValidationIssue,
    PaperTemplateValidationResult,
)

logger = logging.getLogger(__name__)
settings = get_settings()


def _get_openai_client() -> tuple[OpenAI, str]:
    os.environ["OPENAI_API_KEY"] = settings.openrouter_api_key
    os.environ["OPENAI_BASE_URL"] = "https://openrouter.ai/api/v1"
    model_name = get_vision_model(settings)
    return OpenAI(base_url="https://openrouter.ai/api/v1", api_key=settings.openrouter_api_key), model_name


TEXT_TEMPLATE_ANALYST_INSTRUCTIONS = """Analyze the following exam paper template and extract its structural blueprint.

Known syllabus units:
{unit_names}

Requirements:
- Capture the overall paper title if present.
- Capture total marks and duration if present.
- Extract every main numbered question group in order.
- Count every numbered question group shown in the template. Do not merge separate question numbers.
- If the template shows `Question 1 ... (OR) ... Question 2`, keep Question 1 and Question 2 as separate groups and set `"or_with_next": true` on Question 1.
- Use `"alternative"` only when the OR is inside the same numbered question group.
- For each question group, infer the unit if possible from ordering or topic hints.
- Capture the total marks for the question group.
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
      "or_with_next": true,
      "primary": {{
        "subparts": [
          {{"label": "a", "marks": 8}},
          {{"label": "b", "marks": 8}},
          {{"label": "c", "marks": 4}}
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
"""


PAGE_TEMPLATE_ANALYST_INSTRUCTIONS = """Analyze this single exam paper page and extract only the numbered question groups visible on this page.

Known syllabus units:
{unit_names}

Requirements:
- This is only one page of a larger template.
- Extract every numbered main question group visible on this page.
- Do not merge separate question numbers.
- If the OR is between Question N and Question N+1, set `"or_with_next": true` on Question N.
- Use `"alternative"` only when the OR is inside the same numbered question group.
- Preserve sub-part counts and marks exactly when visible.
- If a question is a single full question, represent it as one subpart with an empty label and the full marks.
- Return only the visible groups from this page, in order.
- If title, duration, or total marks are visible on this page, include them; otherwise use 0 or an empty title.

Return ONLY valid JSON in this exact format:
{{
  "title": "Exam title or empty string",
  "total_marks": 0,
  "duration_minutes": 0,
  "question_groups": [
    {{
      "question_number": 1,
      "unit_hint": "Unit 1",
      "marks": 20,
      "or_with_next": true,
      "primary": {{
        "subparts": [
          {{"label": "a", "marks": 8}},
          {{"label": "b", "marks": 8}},
          {{"label": "c", "marks": 4}}
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


COMBINED_TEMPLATE_ANALYST_INSTRUCTIONS = """Analyze all uploaded exam paper pages together and extract the full paper blueprint.

Known syllabus units:
{unit_names}

Requirements:
- Extract every numbered main question group across all pages.
- Count every numbered question group shown in the template. Do not merge separate question numbers.
- If the OR is between Question N and Question N+1, keep both numbered questions and set `"or_with_next": true` on Question N.
- Use `"alternative"` only when the OR is inside the same numbered question group.
- Preserve question order, sub-part counts, and marks exactly when visible.
- If a question is a single full question, represent it as one subpart with an empty label and the full marks.
- Capture the paper title, duration, and total marks if visible.
- Return only structure, not full question text.

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
      "or_with_next": true,
      "primary": {{
        "subparts": [
          {{"label": "a", "marks": 8}},
          {{"label": "b", "marks": 8}},
          {{"label": "c", "marks": 4}}
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


def _parse_json_payload(raw: str) -> dict:
    content = _clean_json_content(raw)
    try:
        return json.loads(content)
    except json.JSONDecodeError:
        start = content.find("{")
        end = content.rfind("}")
        if start != -1 and end != -1 and end > start:
            return json.loads(content[start:end + 1])
        raise


def _extract_question_number(group: dict, fallback_number: int) -> int:
    raw_value = str(group.get("question_number", "") or "").strip()
    if raw_value.isdigit():
        return int(raw_value)
    match = re.search(r"\d+", raw_value)
    if match:
        return int(match.group(0))
    return fallback_number


def _normalize_subparts(subparts: list[dict], fallback_marks: int) -> list[dict]:
    normalized: list[dict] = []
    for subpart in subparts or []:
        normalized.append(
            {
                "label": str(subpart.get("label", "") or "").strip(),
                "marks": int(subpart.get("marks", 0) or 0),
            }
        )

    if not normalized:
        return [{"label": "", "marks": fallback_marks}]

    if sum(item["marks"] for item in normalized) <= 0 and fallback_marks > 0:
        if len(normalized) == 1:
            normalized[0]["marks"] = fallback_marks
        else:
            remaining = fallback_marks
            for idx, item in enumerate(normalized):
                share = remaining if idx == len(normalized) - 1 else fallback_marks // len(normalized)
                item["marks"] = share
                remaining -= share

    return normalized


def _normalize_question_group(group: dict, fallback_number: int) -> dict:
    question_number = _extract_question_number(group, fallback_number)
    group_marks = int(group.get("marks", 0) or 0)
    unit_hint = str(group.get("unit_hint", "") or "").strip()

    primary = group.get("primary", {}) or {}
    primary_subparts = _normalize_subparts(primary.get("subparts", []), group_marks)
    if group_marks <= 0:
        group_marks = sum(item["marks"] for item in primary_subparts)
    if group_marks <= 0:
        group_marks = 20
    primary_subparts = _normalize_subparts(primary_subparts, group_marks)

    normalized = {
        "question_number": question_number,
        "unit_hint": unit_hint,
        "marks": group_marks,
        "primary": {"subparts": primary_subparts},
        "or_with_next": bool(group.get("or_with_next", False)),
    }

    alternative = group.get("alternative")
    if alternative:
        normalized["alternative"] = {
            "subparts": _normalize_subparts((alternative or {}).get("subparts", []), group_marks)
        }

    return normalized


def _normalize_blueprint_data(data: dict) -> dict:
    raw_groups = data.get("question_groups", []) or []
    ordered_groups: list[dict] = []
    seen_numbers: set[int] = set()

    for index, group in enumerate(raw_groups, start=1):
        normalized = _normalize_question_group(group, index)
        if normalized["question_number"] in seen_numbers:
            normalized["question_number"] = max(seen_numbers) + 1
        seen_numbers.add(normalized["question_number"])
        ordered_groups.append(normalized)

    ordered_groups.sort(key=lambda item: item["question_number"])

    total_marks = int(data.get("total_marks", 0) or 0)
    if total_marks <= 0:
        total_marks = sum(group["marks"] for group in ordered_groups)

    duration_minutes = int(data.get("duration_minutes", 0) or 0)
    if duration_minutes <= 0:
        duration_minutes = 180

    return {
        "title": str(data.get("title", "") or "").strip() or "Examination",
        "total_marks": total_marks,
        "duration_minutes": duration_minutes,
        "question_groups": ordered_groups,
    }


def _validate_blueprint_data(data: dict) -> PaperTemplateBlueprint:
    try:
        blueprint = PaperTemplateBlueprint.model_validate(_normalize_blueprint_data(data))
    except Exception as error:
        logger.error("Failed to parse paper template blueprint: %s", error)
        raise ValueError("Could not extract a usable paper blueprint from the uploaded template.")

    if not blueprint.question_groups:
        raise ValueError("The uploaded template did not contain any recognizable question groups.")
    return blueprint


def validate_paper_template_blueprint(blueprint: PaperTemplateBlueprint) -> PaperTemplateValidationResult:
    issues: list[PaperTemplateValidationIssue] = []
    question_numbers = [group.question_number for group in blueprint.question_groups]

    if not blueprint.question_groups:
        issues.append(PaperTemplateValidationIssue(message="Template does not contain any question groups.", field="question_groups"))
        return PaperTemplateValidationResult(is_valid=False, issues=issues)

    expected_numbers = list(range(1, len(question_numbers) + 1))
    if sorted(question_numbers) != expected_numbers:
        issues.append(
            PaperTemplateValidationIssue(
                message="Question numbers should be continuous starting from 1.",
                field="question_number",
            )
        )

    total_from_groups = 0
    answerable_total_marks = 0
    for index, group in enumerate(blueprint.question_groups):
        primary_total = sum(part.marks for part in group.primary.subparts)
        if primary_total != group.marks:
            issues.append(
                PaperTemplateValidationIssue(
                    message=f"Primary subpart marks sum to {primary_total}, expected {group.marks}.",
                    question_number=group.question_number,
                    field="primary.subparts",
                )
            )

        if group.alternative:
            alternative_total = sum(part.marks for part in group.alternative.subparts)
            if alternative_total != group.marks:
                issues.append(
                    PaperTemplateValidationIssue(
                        message=f"Alternative subpart marks sum to {alternative_total}, expected {group.marks}.",
                        question_number=group.question_number,
                        field="alternative.subparts",
                    )
                )

        if group.or_with_next:
            if index == len(blueprint.question_groups) - 1:
                issues.append(
                    PaperTemplateValidationIssue(
                        message="The last question cannot be marked as OR with next question.",
                        question_number=group.question_number,
                        field="or_with_next",
                    )
                )
            elif group.alternative:
                issues.append(
                    PaperTemplateValidationIssue(
                        message="Use either OR with next question or an internal alternative, not both.",
                        question_number=group.question_number,
                        field="or_with_next",
                    )
                )

        total_from_groups += group.marks
        if group.or_with_next:
            answerable_total_marks += group.marks
        elif index > 0 and blueprint.question_groups[index - 1].or_with_next:
            continue
        else:
            answerable_total_marks += group.marks

    if blueprint.total_marks > 0 and answerable_total_marks != blueprint.total_marks:
        issues.append(
            PaperTemplateValidationIssue(
                message=f"Answerable question marks sum to {answerable_total_marks}, but total marks is {blueprint.total_marks}.",
                field="total_marks",
            )
        )

    return PaperTemplateValidationResult(is_valid=len(issues) == 0, issues=issues)


def _validate_blueprint(raw: str) -> PaperTemplateBlueprint:
    data = _parse_json_payload(raw)
    return _validate_blueprint_data(data)


async def _run_structured_completion(messages: list[dict]) -> str:
    client, model_name = _get_openai_client()

    def _run() -> str:
        response = client.chat.completions.create(
            model=model_name,
            messages=messages,
            temperature=0.1,
        )
        return response.choices[0].message.content or ""

    return await asyncio.to_thread(_run)


async def _parse_from_text(template_text: str, unit_names: list[str]) -> PaperTemplateBlueprint:
    client = OpenAI(base_url="https://openrouter.ai/api/v1", api_key=settings.openrouter_api_key)
    model_name = get_text_model(settings)

    def _run() -> str:
        response = client.chat.completions.create(
            model=model_name,
            messages=[
                {
                    "role": "user",
                    "content": (
                        "You are an academic exam-template analyst. "
                        "Extract only structure from the paper and return only valid JSON.\n\n"
                        + TEXT_TEMPLATE_ANALYST_INSTRUCTIONS.format(
                            unit_names="\n".join(f"- {unit}" for unit in unit_names) or "- Unknown",
                            template_text=template_text[:20000],
                        )
                    ),
                },
            ],
            temperature=0.1,
        )
        return response.choices[0].message.content or ""

    raw = await asyncio.to_thread(_run)
    return _validate_blueprint(raw)


async def _analyze_single_page(page_number: int, image_url: str, unit_names: list[str]) -> dict:
    raw = await _run_structured_completion(
        [
            {
                "role": "user",
                "content": [
                    {
                        "type": "text",
                        "text": (
                            f"You are analyzing page {page_number} of an exam paper template. "
                            "Return only valid JSON.\n\n"
                            + PAGE_TEMPLATE_ANALYST_INSTRUCTIONS.format(
                                unit_names="\n".join(f"- {unit}" for unit in unit_names) or "- Unknown",
                            )
                        ),
                    },
                    {
                        "type": "image_url",
                        "image_url": {"url": image_url},
                    },
                ],
            },
        ]
    )
    return _parse_json_payload(raw)


async def _analyze_all_pages(page_images: list[str], unit_names: list[str]) -> dict:
    content: list[dict] = [
        {
            "type": "text",
            "text": COMBINED_TEMPLATE_ANALYST_INSTRUCTIONS.format(
                unit_names="\n".join(f"- {unit}" for unit in unit_names) or "- Unknown",
            ),
        }
    ]
    for image_url in page_images:
        content.append(
            {
                "type": "image_url",
                "image_url": {"url": image_url},
            }
        )

    raw = await _run_structured_completion(
        [
            {
                "role": "user",
                "content": [
                    {
                        "type": "text",
                        "text": "You are analyzing a multi-page exam paper template. Return only valid JSON.",
                    },
                    *content,
                ],
            },
        ]
    )
    return _parse_json_payload(raw)


async def _parse_from_images(page_images: list[str], unit_names: list[str]) -> PaperTemplateBlueprint:
    if not page_images:
        raise ValueError("The uploaded template did not contain any recognizable question groups.")

    page_results: list[dict] = []
    page_errors: list[str] = []
    for page_number, image_url in enumerate(page_images, start=1):
        try:
            page_results.append(await _analyze_single_page(page_number, image_url, unit_names))
        except Exception as error:
            logger.error("Vision template parsing failed for page %d: %s", page_number, error)
            page_errors.append(f"page {page_number}: {error}")

    merged_groups: list[dict] = []
    title = ""
    total_marks = 0
    duration_minutes = 0

    for page_result in page_results:
        if not title and page_result.get("title"):
            title = str(page_result.get("title") or "").strip()
        if total_marks <= 0:
            total_marks = int(page_result.get("total_marks", 0) or 0)
        if duration_minutes <= 0:
            duration_minutes = int(page_result.get("duration_minutes", 0) or 0)
        merged_groups.extend(page_result.get("question_groups", []) or [])

    if not merged_groups:
        try:
            combined_result = await _analyze_all_pages(page_images, unit_names)
            merged_groups = combined_result.get("question_groups", []) or []
            if combined_result.get("title"):
                title = str(combined_result.get("title") or "").strip()
            if total_marks <= 0:
                total_marks = int(combined_result.get("total_marks", 0) or 0)
            if duration_minutes <= 0:
                duration_minutes = int(combined_result.get("duration_minutes", 0) or 0)
        except Exception as error:
            logger.error("Combined vision template parsing failed: %s", error)
            if page_errors:
                logger.error("Per-page template parsing errors: %s", "; ".join(page_errors))
            raise ValueError(
                "Could not analyze the scanned template images into a usable paper structure. "
                "Try a clearer PDF, a text-based PDF, or a stronger vision-capable model."
            )

    return _validate_blueprint_data(
        {
            "title": title or "Examination",
            "total_marks": total_marks,
            "duration_minutes": duration_minutes,
            "question_groups": merged_groups,
        }
    )


async def parse_paper_template_blueprint(
    template_text: str,
    unit_names: list[str],
    page_images: list[str] | None = None,
) -> PaperTemplateBlueprint:
    normalized_text = (template_text or "").strip()

    if normalized_text and len(normalized_text) >= 120:
        try:
            return await _parse_from_text(normalized_text, unit_names)
        except ValueError:
            if not page_images:
                raise

    if page_images:
        return await _parse_from_images(page_images, unit_names)

    if normalized_text:
        return await _parse_from_text(normalized_text, unit_names)

    raise ValueError("Could not extract readable text from the uploaded template. Try a clearer PDF or image-based OCR path.")
