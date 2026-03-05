"""
Prompt Builder Service
Builds structured prompts for question generation, refinement, and evaluation.
"""

from app.services.bloom_taxonomy import get_bloom_descriptor, BloomLevel


def build_question_generation_prompt(
    topic: str,
    bloom_level: BloomLevel,
    difficulty: str,
    num_questions: int,
    marks_per_question: int,
) -> str:
    """Build a prompt for generating Bloom-aligned exam questions."""
    desc = get_bloom_descriptor(bloom_level)
    verbs = ", ".join(desc["verbs"])

    return f"""You are an expert exam question designer. Generate {num_questions} descriptive exam question(s) on the topic: "{topic}".

Requirements:
- Bloom's Taxonomy Level: {bloom_level.value} — {desc['description']}
- Use action verbs appropriate for this level: {verbs}
- Difficulty: {difficulty}
- Each question should be worth {marks_per_question} marks
- Include sub-questions where appropriate (label them (a), (b), etc.)
- Distribute marks across sub-questions if present
- Provide a model answer for each question

Return ONLY valid JSON in this format:
{{
  "questions": [
    {{
      "question_text": "Main question text",
      "sub_questions": [
        {{"label": "(a)", "text": "Sub-question text", "marks": 2, "model_answer": "..."}},
        {{"label": "(b)", "text": "Sub-question text", "marks": 3, "model_answer": "..."}}
      ],
      "marks": {marks_per_question},
      "model_answer": "Complete model answer for the main question"
    }}
  ]
}}

If there are no sub-questions, set "sub_questions" to an empty list.
"""


def build_refinement_prompt(
    original_question: str,
    feedback: str,
    bloom_level: BloomLevel,
) -> str:
    """Build a prompt for refining a question based on HITL feedback."""
    desc = get_bloom_descriptor(bloom_level)
    verbs = ", ".join(desc["verbs"])

    return f"""You are an expert exam question editor. A teacher has reviewed the following question and requested changes.

Original Question:
{original_question}

Teacher Feedback:
{feedback}

Requirements:
- Maintain Bloom's level: {bloom_level.value} — {desc['description']}
- Use appropriate action verbs: {verbs}
- Preserve the original marks allocation
- Address ALL feedback points
- Provide an updated model answer

Return ONLY valid JSON:
{{
  "question_text": "Refined question text",
  "sub_questions": [...],
  "marks": <same marks>,
  "model_answer": "Updated model answer"
}}
"""


def build_evaluation_prompt(
    question_text: str,
    model_answer: str,
    student_answer: str,
    max_marks: int,
    bloom_level: str,
) -> str:
    """Build a prompt for evaluating a student's descriptive answer."""
    return f"""You are an expert exam evaluator. Evaluate the student's answer against the model answer using rubric-based scoring.

Question ({max_marks} marks, Bloom Level: {bloom_level}):
{question_text}

Model Answer:
{model_answer}

Student Answer:
{student_answer}

Evaluate using these criteria:
1. **Semantic Similarity** (0.0-1.0): How closely does the student's answer match the meaning of the model answer?
2. **Completeness** (0.0-1.0): How many key points from the model answer are covered?
3. **Bloom Alignment** (0.0-1.0): Does the answer demonstrate the expected cognitive level ({bloom_level})?
4. **Logic & Reasoning** (0.0-1.0): Is the answer well-structured and logically sound?

Return ONLY valid JSON:
{{
  "awarded_marks": <float between 0 and {max_marks}>,
  "semantic_similarity": <float 0-1>,
  "completeness": <float 0-1>,
  "bloom_alignment": <float 0-1>,
  "reasoning": "Brief explanation of scoring rationale",
  "feedback": "Constructive feedback for the student"
}}
"""
