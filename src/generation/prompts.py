"""
Prompt templates and schema definitions for LLM-based question generation.
"""

from typing import Optional
from schema.enums import Board, ClassGrade, Subject, QuestionType, Difficulty


class PromptBuilder:
    """
    Constructs pedagogically sound prompts and strict JSON instructions for Gemini.
    """

    SYSTEM_INSTRUCTION = (
        "You are a senior educational assessment specialist and curriculum expert for Indian school boards "
        "(CBSE and ICSE). Your task is to generate high-quality, syllabus-aligned questions. "
        "You must return ONLY raw, valid JSON matching the exact schema specified. "
        "Do not include markdown backticks (like ```json), explanations, or conversational preamble."
    )

    @classmethod
    def build_mcq_prompt(
        cls,
        board: Board = Board.CBSE,
        class_grade: ClassGrade = ClassGrade.CLASS_9,
        subject: Subject = Subject.HISTORY,
        chapter: str = "The French Revolution",
        topic: Optional[str] = None,
        difficulty: Difficulty = Difficulty.MEDIUM,
    ) -> str:
        """
        Builds a prompt requesting a single MCQ in strict JSON format.
        """
        topic_clause = f" specifically on the topic '{topic}'" if topic else ""
        return f"""Generate a high-quality Multiple Choice Question (MCQ) for:
- Board: {board.value}
- Grade: {class_grade.value}
- Subject: {subject.value}
- Chapter: {chapter}{topic_clause}
- Difficulty: {difficulty.value}
- Maximum Marks: 1.0

CRITICAL REQUIREMENTS:
1. Provide exactly four (4) options.
2. Every option must be unique, non-empty, and historically plausible.
3. The 'correct_answer' field MUST exactly match one of the four options verbatim.
4. Include a detailed, factual explanation explaining why the correct answer is right.
5. Return ONLY a single JSON object with the following structure:
{{
  "question_text": "Clear and unambiguous question stem",
  "options": [
    "Option 1",
    "Option 2",
    "Option 3",
    "Option 4"
  ],
  "correct_answer": "Option matching one of the above",
  "explanation": "Detailed explanation of historical facts and context",
  "difficulty": "{difficulty.value}",
  "maximum_marks": 1.0,
  "chapter": "{chapter}",
  "topic": "{topic or ''}"
}}"""

    @classmethod
    def build_subjective_prompt(
        cls,
        board: Board = Board.CBSE,
        class_grade: ClassGrade = ClassGrade.CLASS_9,
        subject: Subject = Subject.HISTORY,
        chapter: str = "The French Revolution",
        topic: Optional[str] = None,
        question_type: QuestionType = QuestionType.SHORT_ANSWER,
        difficulty: Difficulty = Difficulty.MEDIUM,
        maximum_marks: float = 3.0,
    ) -> str:
        """
        Builds a prompt requesting a Subjective question with a structured marking rubric.
        """
        topic_clause = f" specifically focusing on '{topic}'" if topic else ""
        num_points = int(maximum_marks) if maximum_marks.is_integer() else 3
        return f"""Generate a high-quality subjective assessment question for:
- Board: {board.value}
- Grade: {class_grade.value}
- Subject: {subject.value}
- Chapter: {chapter}{topic_clause}
- Question Type: {question_type.value}
- Difficulty: {difficulty.value}
- Maximum Marks: {maximum_marks}

CRITICAL REQUIREMENTS:
1. Formulate a clear, standard exam question suitable for {board.value} {class_grade.value}.
2. Provide a comprehensive 'expected_answer' (model answer) demonstrating historical depth.
3. Provide a structured 'marking_rubric' containing distinct marking points.
4. The sum of 'allocated_marks' in the rubric MUST EXACTLY EQUAL {maximum_marks}.
5. For each marking point, define:
   - 'point': The core historical concept, cause, event, date, or consequence.
   - 'allocated_marks': Number of marks for this point (e.g. 1.0 or 0.5).
   - 'acceptable_alternatives': Alternative valid historical explanations.
   - 'common_misconceptions': Known student errors or confusions.
6. Return ONLY a single JSON object with this exact structure:
{{
  "question_text": "Question statement",
  "expected_answer": "Comprehensive model answer containing key historical facts, dates, and reasoning.",
  "marking_rubric": [
    {{
      "point": "Specific historical fact/argument 1",
      "allocated_marks": 1.0,
      "description": "Guidance on what constitutes full credit",
      "acceptable_alternatives": ["Acceptable alternative wording"],
      "common_misconceptions": ["Common incorrect student belief"]
    }}
  ],
  "difficulty": "{difficulty.value}",
  "maximum_marks": {maximum_marks},
  "chapter": "{chapter}",
  "topic": "{topic or ''}"
}}"""
