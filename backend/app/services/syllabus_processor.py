import json
import logging
from langchain_openrouter import ChatOpenRouter
from langchain.prompts import ChatPromptTemplate
from app.config import get_settings

logger = logging.getLogger(__name__)
settings = get_settings()


TOPIC_EXTRACTION_PROMPT = ChatPromptTemplate.from_messages([
    ("system", "You are an expert academic syllabus analyzer. Extract structured topics from the given syllabus text."),
    ("human", """Analyze the following syllabus text and extract a structured list of topics.

For each topic, provide:
- name: the main topic name
- unit: the unit or module it belongs to (if identifiable)
- subtopics: a list of subtopics under it

Return ONLY valid JSON in this exact format:
{{
  "topics": [
    {{
      "name": "Topic Name",
      "unit": "Unit 1",
      "subtopics": ["Subtopic A", "Subtopic B"]
    }}
  ]
}}

Syllabus text:
{syllabus_text}
""")
])


async def extract_topics(syllabus_text: str) -> list[dict]:
    """Use LLM to extract topics from syllabus text."""
    logger.info("Extracting topics from syllabus text via LLM")
    llm = ChatOpenRouter(
      model=settings.openrouter_model,
      api_key=settings.openrouter_api_key,
        temperature=0.2,
    )
    chain = TOPIC_EXTRACTION_PROMPT | llm
    result = await chain.ainvoke({"syllabus_text": syllabus_text[:8000]})

    try:
        content = result.content.strip()
        # Strip markdown code fences if present
        if content.startswith("```"):
            content = content.split("\n", 1)[1]
            content = content.rsplit("```", 1)[0]
        data = json.loads(content)
        return data.get("topics", [])
    except (json.JSONDecodeError, AttributeError) as e:
        logger.error(f"Failed to parse LLM topic extraction: {e}")
        # Fallback: split by lines as rough topics
        lines = [l.strip() for l in syllabus_text.split("\n") if l.strip() and len(l.strip()) > 5]
        return [{"name": line, "unit": "", "subtopics": []} for line in lines[:20]]
