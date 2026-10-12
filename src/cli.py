"""
Command Line Interface for Generating and Validating Assessment Questions.
Default primary workflow: CBSE Class 9 History.
Configurable for other subjects (e.g. ICSE Class 9 Computer Applications).
"""

import argparse
import json
import os
import sys
from typing import Optional

from schema.enums import Board, ClassGrade, Subject, QuestionType, Difficulty, SourceType
from generation.generator import QuestionGenerator
from llm_module.client import GeminiClient


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="AI-Powered Assessment Question Generator & Validator (CBSE / ICSE)",
        formatter_class=argparse.ArgumentDefaultsHelpFormatter,
    )
    parser.add_argument(
        "--board",
        type=str,
        default="CBSE",
        choices=[b.value for b in Board],
        help="Educational Board",
    )
    parser.add_argument(
        "--grade",
        type=str,
        default="Class 9",
        choices=[g.value for g in ClassGrade],
        help="Academic Class / Grade",
    )
    parser.add_argument(
        "--subject",
        type=str,
        default="History",
        choices=[s.value for s in Subject],
        help="Academic Subject",
    )
    parser.add_argument(
        "--chapter",
        type=str,
        default="The French Revolution",
        help="Chapter Name (from syllabus)",
    )
    parser.add_argument(
        "--topic",
        type=str,
        default=None,
        help="Optional specific topic within the chapter",
    )
    parser.add_argument(
        "--type",
        type=str,
        default="Short Answer",
        choices=[t.value for t in QuestionType],
        help="Question Type (MCQ, Short Answer, Long Answer, Source Based, Descriptive)",
    )
    parser.add_argument(
        "--difficulty",
        type=str,
        default="Medium",
        choices=[d.value for d in Difficulty],
        help="Question Difficulty Level",
    )
    parser.add_argument(
        "--marks",
        type=float,
        default=3.0,
        help="Maximum Marks (MCQ defaults to 1.0)",
    )
    parser.add_argument(
        "--output",
        type=str,
        default=None,
        help="Path to JSON file to save the generated question",
    )
    parser.add_argument(
        "--mock",
        action="store_true",
        help="Run in offline mock mode using pre-generated schema sample",
    )
    return parser


def run_cli(args: Optional[argparse.Namespace] = None):
    if args is None:
        parser = build_parser()
        args = parser.parse_args()

    board = Board(args.board)
    class_grade = ClassGrade(args.grade)
    subject = Subject(args.subject)
    q_type = QuestionType(args.type)
    difficulty = Difficulty(args.difficulty)
    marks = 1.0 if q_type == QuestionType.MCQ else float(args.marks)

    print("\n" + "=" * 60)
    print("AI ASSESSMENT QUESTION GENERATOR & SCHEMA VALIDATOR")
    print("=" * 60)
    print(f"Board:        {board.value}")
    print(f"Class/Grade:  {class_grade.value}")
    print(f"Subject:      {subject.value}")
    print(f"Chapter:      {args.chapter}")
    if args.topic:
        print(f"Topic:        {args.topic}")
    print(f"Type:         {q_type.value}")
    print(f"Difficulty:   {difficulty.value}")
    print(f"Max Marks:    {marks}")
    print("=" * 60 + "\n")

    generator = QuestionGenerator()

    if args.mock:
        print("[INFO] Running in MOCK MODE (offline validation demonstration)...")
        if q_type == QuestionType.MCQ:
            mock_payload = {
                "question_text": "Which fortress-prison was stormed by the people of Paris on 14th July 1789?",
                "options": [
                    "The Bastille",
                    "The Tuileries",
                    "Versailles Palace",
                    "The Louvre",
                ],
                "correct_answer": "The Bastille",
                "explanation": "The storming of the Bastille on 14 July 1789 marked the outbreak of the French Revolution.",
                "difficulty": difficulty.value,
                "maximum_marks": 1.0,
                "chapter": args.chapter,
                "topic": args.topic or "",
            }
        else:
            mock_payload = {
                "question_text": "Describe the main causes that led to the French Revolution of 1789.",
                "expected_answer": (
                    "The French Revolution was caused by social inequality (division into Three Estates), "
                    "economic distress due to bad harvests and feudal taxes, financial bankruptcy under Louis XVI, "
                    "and the spread of Enlightenment ideas advocating liberty and equality."
                ),
                "marking_rubric": [
                    {
                        "point": "Social division: Three Estates system and unfair tax burden on the Third Estate",
                        "allocated_marks": 1.0,
                        "description": "Award 1 mark for mentioning the social structure and unequal taxation",
                        "acceptable_alternatives": ["Third Estate paid all taxes while clergy and nobility enjoyed privileges"],
                        "common_misconceptions": ["Believing all three estates paid taxes equally"],
                    },
                    {
                        "point": "Economic crisis: Subsistence crisis, population rise, and high bread prices",
                        "allocated_marks": 1.0,
                        "description": "Award 1 mark for detailing subsistence crisis or economic bankruptcy",
                        "acceptable_alternatives": ["Empty treasury due to wars and lavish court spending"],
                        "common_misconceptions": ["Ignoring the agricultural failures and food shortage"],
                    },
                    {
                        "point": "Role of Philosophers: Spread of Enlightenment ideas by Rousseau, Voltaire, and Montesquieu",
                        "allocated_marks": 1.0,
                        "description": "Award 1 mark for citing philosopher influence or demands for democratic rights",
                        "acceptable_alternatives": ["Enlightenment thinkers criticizing absolute monarchy"],
                        "common_misconceptions": ["Attributing the revolution solely to foreign invasion"],
                    },
                ],
                "difficulty": difficulty.value,
                "maximum_marks": marks,
                "chapter": args.chapter,
                "topic": args.topic or "",
            }
        result = generator.parse_and_validate(
            raw_response=json.dumps(mock_payload),
            question_type=q_type,
            expected_metadata={
                "board": board,
                "class_grade": class_grade,
                "subject": subject,
                "chapter": args.chapter,
                "topic": args.topic,
                "difficulty": difficulty,
                "maximum_marks": marks,
            },
        )
    else:
        try:
            client = GeminiClient()
            generator.client = client
        except Exception as e:
            print(f"[ERROR] Gemini client could not be initialized: {e}")
            print("Tip: Use --mock to test schema validation offline without an API key.")
            sys.exit(1)

        result = generator.generate(
            board=board,
            class_grade=class_grade,
            subject=subject,
            chapter=args.chapter,
            topic=args.topic,
            question_type=q_type,
            difficulty=difficulty,
            maximum_marks=marks,
        )

    print("[RESULT] Validation Outcome:")
    print(f"  - Is Valid:          {result.is_valid}")
    print(f"  - Validation Status: {result.status.value}")
    if result.errors:
        print(f"  - Errors ({len(result.errors)}):")
        for err in result.errors:
            print(f"      * {err}")
    if result.warnings:
        print(f"  - Warnings ({len(result.warnings)}):")
        for warn in result.warnings:
            print(f"      * {warn}")

    if result.validated_question:
        q = result.validated_question
        print(f"\n[CONFIRMED QUESTION METADATA]")
        print(f"  - Question ID:       {q.question_id}")
        print(f"  - Source Type:       {q.source_type.value} (Programmatically Enforced)")
        print(f"  - Validation Status: {q.validation_status.value} (Programmatically Enforced)")
        print(f"  - Question Text:     {q.question_text}")

        # Save to output file if requested
        if args.output:
            out_path = os.path.abspath(args.output)
            # Check if file exists to prevent accidental overwrite
            if os.path.exists(out_path):
                print(f"[WARNING] File '{args.output}' already exists. Appending to existing collection.")
                try:
                    with open(out_path, "r", encoding="utf-8") as f:
                        existing_data = json.load(f)
                    if not isinstance(existing_data, list):
                        existing_data = [existing_data]
                except Exception:
                    existing_data = []
                existing_data.append(q.model_dump())
                with open(out_path, "w", encoding="utf-8") as f:
                    json.dump(existing_data, f, indent=2)
            else:
                os.makedirs(os.path.dirname(out_path) or ".", exist_ok=True)
                with open(out_path, "w", encoding="utf-8") as f:
                    json.dump([q.model_dump()], f, indent=2)
            print(f"[SUCCESS] Saved validated question to: {args.output}")

    return result


if __name__ == "__main__":
    run_cli()
