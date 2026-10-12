#!/usr/bin/env python3
"""
CLI Interactive Answer Evaluator for CBSE Class 9 History.
"""

import os
import sys

# Ensure src is in python path
current_dir = os.path.dirname(os.path.abspath(__file__))
src_dir = os.path.join(current_dir, "src")
if src_dir not in sys.path:
    sys.path.insert(0, src_dir)

from repository.question_repo import QuestionRepository
from evaluation.evaluator import AnswerEvaluationService
from evaluation.models import EvaluationRequest
from evaluation.storage import EvaluationStorage


def main():
    print("=" * 65)
    print("AI-POWERED ANSWER EVALUATION SYSTEM — CBSE CLASS 9 HISTORY")
    print("=" * 65)

    repo = QuestionRepository()
    storage = EvaluationStorage()
    service = AnswerEvaluationService(repository=repo)

    questions = repo.list_all_questions()
    if not questions:
        print("[ERROR] No questions found in question bank.")
        sys.exit(1)

    print("\nSelect an existing question from the CBSE question bank:\n")
    for idx, q in enumerate(questions, 1):
        rubric_flag = " [Verified Rubric]" if getattr(q, 'rubric_status', None) == "VERIFIED" else " [Needs Rubric Review]"
        print(f"[{idx}] {q.question_id} ({q.chapter}) — Max Marks: {q.maximum_marks}{rubric_flag}")
        print(f"    Q: {q.question_text[:90]}...\n")

    choice = input("Enter question number to evaluate [1-" + str(len(questions)) + "] (default 1): ").strip()
    if not choice:
        choice_idx = 0
    else:
        try:
            choice_idx = int(choice) - 1
            if choice_idx < 0 or choice_idx >= len(questions):
                choice_idx = 0
        except ValueError:
            choice_idx = 0

    selected_q = questions[choice_idx]

    print("\n" + "-" * 65)
    print(f"SELECTED QUESTION: {selected_q.question_id}")
    print(f"Chapter:        {selected_q.chapter}")
    print(f"Maximum Marks:  {selected_q.maximum_marks}")
    print(f"Rubric Status:  {getattr(selected_q, 'rubric_status', 'VERIFIED')}")
    print(f"Question Text:  {selected_q.question_text}")
    print("-" * 65)

    print("\nEnter student's answer below (press Enter twice to submit):")
    lines = []
    while True:
        line = input()
        if line == "":
            break
        lines.append(line)
    student_ans = "\n".join(lines).strip()

    if not student_ans:
        print("\n[NOTE] Empty answer detected. Evaluating blank response...")

    print("\n[INFO] Evaluating student answer against marking rubric...")
    req = EvaluationRequest(question_id=selected_q.question_id, student_answer=student_ans)
    result = service.evaluate(req)
    storage.save_result(result)

    print("\n" + "=" * 65)
    print("EVALUATION RESULT")
    print("=" * 65)
    print(f"Evaluation ID:        {result.evaluation_id}")
    print(f"Awarded Marks:        {result.awarded_marks} / {result.maximum_marks}")
    print(f"Status:               {result.evaluation_status.value}")
    if result.teacher_review_required:
        print(f"Teacher Review:       REQUIRED ({result.review_reason})")
    else:
        print(f"Teacher Review:       Not Required")

    print(f"\nFeedback:\n{result.feedback}")

    if result.criterion_wise_marks:
        print("\nCriterion-Wise Marks Breakdown:")
        for idx, crit in enumerate(result.criterion_wise_marks, 1):
            print(f"  [{idx}] {crit.criterion[:55]}...")
            print(f"      Score: {crit.awarded_marks} / {crit.maximum_marks} marks")
            if crit.feedback:
                print(f"      Note:  {crit.feedback}")

    if result.correct_concepts_identified:
        print("\nCorrect Concepts Identified:")
        for cp in result.correct_concepts_identified:
            print(f"  * {cp}")

    if result.missing_concepts:
        print("\nMissing Concepts:")
        for mc in result.missing_concepts:
            print(f"  - {mc}")

    if result.factual_errors:
        print("\nFactual Errors Detected:")
        for fe in result.factual_errors:
            print(f"  ! Claim:      {fe.student_claim}")
            print(f"    Correction: {fe.correction}")

    if result.improvement_suggestions:
        print("\nSuggestions for Improvement:")
        for s in result.improvement_suggestions:
            print(f"  > {s}")

    if result.model_answer:
        print(f"\nOfficial Verified Model Answer:\n{result.model_answer}")
    elif result.evaluation_status == "PROVISIONAL":
        print("\n[INFO] Model answer omitted pending teacher rubric verification.")

    print("\n[SUCCESS] Result safely stored in evaluations database.")
    print("=" * 65 + "\n")


if __name__ == "__main__":
    main()
