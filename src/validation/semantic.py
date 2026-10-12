"""
Semantic and Syllabus Validator.
Validates academic alignment against standard CBSE/ICSE curricula and inspects question quality.
"""

import difflib
from typing import Dict, List, Optional, Set, Tuple
from schema.enums import Board, ClassGrade, Subject, ValidationStatus
from schema.models import ValidationResult, Question, MCQQuestion, SubjectiveQuestion


# Registry mapping (Board, ClassGrade, Subject) to canonical chapters
SYLLABUS_REGISTRY: Dict[Tuple[Board, ClassGrade, Subject], List[str]] = {
    (Board.CBSE, ClassGrade.CLASS_9, Subject.HISTORY): [
        "The French Revolution",
        "Socialism in Europe and the Russian Revolution",
        "Nazism and the Rise of Hitler",
        "Forest Society and Colonialism",
        "Pastoralists in the Modern World",
    ],
    (Board.ICSE, ClassGrade.CLASS_9, Subject.COMPUTER_APPLICATIONS): [
        "Introduction to Object Oriented Programming Concepts",
        "Elementary Concept of Objects and Classes",
        "Values and Data Types",
        "Operators in Java",
        "Input in Java",
        "Mathematical Library Methods",
        "Conditional Constructs in Java",
        "Iterative Constructs in Java",
    ],
}


class SemanticValidator:
    """
    Validates pedagogical alignment, syllabus compliance, and semantic quality.
    Separated from structural validation to allow independent rule evolution.
    """

    def __init__(self, strict_syllabus: bool = True):
        self.strict_syllabus = strict_syllabus

    def normalize_name(self, text: str) -> str:
        """
        Normalizes chapter names by stripping chapter prefixes and punctuation.
        """
        lowered = text.lower().strip()
        # Remove common prefixes like 'chapter 1: ', 'ch 1 - '
        for prefix in ["chapter", "ch.", "ch", "unit"]:
            if lowered.startswith(prefix):
                parts = lowered.split(":", 1)
                if len(parts) > 1:
                    lowered = parts[1].strip()
                else:
                    parts = lowered.split("-", 1)
                    if len(parts) > 1:
                        lowered = parts[1].strip()
        return " ".join(lowered.split())

    def match_chapter(self, target_chapter: str, allowed_chapters: List[str]) -> Optional[str]:
        """
        Finds the closest canonical chapter matching target_chapter.
        """
        norm_target = self.normalize_name(target_chapter)
        for canonical in allowed_chapters:
            norm_canonical = self.normalize_name(canonical)
            if norm_target == norm_canonical or norm_target in norm_canonical or norm_canonical in norm_target:
                return canonical
        # Fuzzy match
        matches = difflib.get_close_matches(
            norm_target,
            [self.normalize_name(c) for c in allowed_chapters],
            n=1,
            cutoff=0.6,
        )
        if matches:
            idx = [self.normalize_name(c) for c in allowed_chapters].index(matches[0])
            return allowed_chapters[idx]
        return None

    def validate_syllabus(
        self,
        board: Board,
        class_grade: ClassGrade,
        subject: Subject,
        chapter: str,
    ) -> Tuple[bool, List[str], List[str]]:
        """
        Verifies that chapter belongs to the curriculum for (Board, Class, Subject).
        """
        errors: List[str] = []
        warnings: List[str] = []

        key = (board, class_grade, subject)
        if key in SYLLABUS_REGISTRY:
            allowed = SYLLABUS_REGISTRY[key]
            matched = self.match_chapter(chapter, allowed)
            if not matched:
                msg = (
                    f"Chapter '{chapter}' is not recognized for {board.value} {class_grade.value} {subject.value}. "
                    f"Expected one of: {allowed}"
                )
                if self.strict_syllabus:
                    errors.append(msg)
                else:
                    warnings.append(msg)
        else:
            warnings.append(
                f"No pre-configured syllabus registry found for {board.value} {class_grade.value} {subject.value}. "
                "Skipping strict chapter matching."
            )

        return (len(errors) == 0, errors, warnings)

    def validate_quality(self, question: Question) -> Tuple[bool, List[str], List[str]]:
        """
        Performs semantic sanity checks on question content.
        """
        errors: List[str] = []
        warnings: List[str] = []

        q_text = question.question_text.strip().lower()

        # Reject trivial single-phrase questions
        if len(q_text.split()) < 3:
            errors.append("Question text is too brief to form a meaningful assessment question.")

        if isinstance(question, MCQQuestion):
            # Check for generic placeholders
            placeholders = {"option a", "option b", "option c", "option d", "a", "b", "c", "d", "none", "all"}
            for opt in question.options:
                if opt.strip().lower() in placeholders:
                    warnings.append(f"Option '{opt}' appears to be a generic placeholder.")
            
            # Check for tautology (question text == correct answer)
            if q_text == question.correct_answer.strip().lower():
                errors.append("Question text and correct answer are identical (tautology).")

        elif isinstance(question, SubjectiveQuestion):
            # Check that expected answer is substantive
            if len(question.expected_answer.strip().split()) < 5:
                warnings.append("Expected answer is unusually brief for a subjective question.")

            # Check for tautology
            if q_text == question.expected_answer.strip().lower():
                errors.append("Expected answer simply repeats the question text.")

        return (len(errors) == 0, errors, warnings)

    def validate(self, question: Question) -> ValidationResult:
        """
        Validates both curriculum alignment and pedagogical quality.
        """
        all_errors: List[str] = []
        all_warnings: List[str] = []

        syl_ok, syl_errs, syl_warns = self.validate_syllabus(
            question.board,
            question.class_grade,
            question.subject,
            question.chapter,
        )
        all_errors.extend(syl_errs)
        all_warnings.extend(syl_warns)

        qual_ok, qual_errs, qual_warns = self.validate_quality(question)
        all_errors.extend(qual_errs)
        all_warnings.extend(qual_warns)

        is_valid = len(all_errors) == 0
        status = ValidationStatus.VALID if is_valid else ValidationStatus.INVALID
        if is_valid and all_warnings:
            status = ValidationStatus.NEEDS_REVIEW

        return ValidationResult(
            is_valid=is_valid,
            status=status,
            errors=all_errors,
            warnings=all_warnings,
            validated_question=question,
        )
