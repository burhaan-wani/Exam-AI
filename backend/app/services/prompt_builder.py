"""
Prompt Builder Service
Builds structured prompts for answer evaluation.
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
1. Semantic Similarity (0.0-1.0): How closely does the student's answer match the meaning of the model answer?
2. Completeness (0.0-1.0): How many key points from the model answer are covered?
3. Bloom Alignment (0.0-1.0): Does the answer demonstrate the expected cognitive level ({bloom_level})?
4. Logic & Reasoning (0.0-1.0): Is the answer well-structured and logically sound?

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
