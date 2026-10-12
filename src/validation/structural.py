"""
Structural and Schema Validator.
Implements strict deterministic rules for MCQ options, answers, marks, and rubrics.
"""

import math
from typing import Any, Dict, List, Optional, Union
from pydantic import ValidationError

from schema.enums import QuestionType, ValidationStatus, SourceType
from schema.models import (
    MCQQuestion,
    SubjectiveQuestion,
    Question,
    ValidationResult,
    RubricCriterion,
)


class StructuralValidator:
    """
    Performs purely structural, deterministic validation on questions.
    Checks option count, uniqueness, correct answer matching, rubric math, and score ranges.
    """

    @staticmethod
    def validate_mcq_data(data: Dict[str, Any]) -> ValidationResult:
        """
        Validates raw data for a Multiple Choice Question.
        """
        errors: List[str] = []
        warnings: List[str] = []

        # 1. Basic question text check
        q_text = str(data.get("question_text", "")).strip()
        if len(q_text) < 5:
            errors.append("Question text is missing or shorter than 5 characters.")

        # 2. Options validation (exactly 4 non-empty unique options)
        options = data.get("options")
        if not isinstance(options, list):
            errors.append("Options must be provided as a list.")
        else:
            if len(options) != 4:
                errors.append(f"MCQ must have exactly 4 options. Found {len(options)}.")
            
            cleaned_options = []
            for idx, opt in enumerate(options):
                if not isinstance(opt, str) or not opt.strip():
                    errors.append(f"Option at index {idx} cannot be empty or non-string.")
                else:
                    cleaned_options.append(opt.strip())

            if len(cleaned_options) == 4:
                lowered_set = {opt.lower() for opt in cleaned_options}
                if len(lowered_set) != 4:
                    errors.append(f"MCQ options must be unique. Found duplicates in: {cleaned_options}")

                # 3. Correct answer matching
                correct_ans = str(data.get("correct_answer", "")).strip()
                if not correct_ans:
                    errors.append("Correct answer cannot be empty.")
                else:
                    matches = [opt for opt in cleaned_options if opt.lower() == correct_ans.lower()]
                    if not matches:
                        errors.append(
                            f"Correct answer '{correct_ans}' does not match any of the 4 options: {cleaned_options}"
                        )

        # 4. Maximum marks check
        max_marks = data.get("maximum_marks", 1.0)
        try:
            max_marks_float = float(max_marks)
            if max_marks_float <= 0:
                errors.append(f"Maximum marks must be greater than zero. Received: {max_marks}")
        except (ValueError, TypeError):
            errors.append(f"Invalid maximum marks value: {max_marks}")

        # 5. Explanation check
        explanation = str(data.get("explanation", "")).strip()
        if len(explanation) < 5:
            errors.append("Explanation is missing or too short (minimum 5 characters).")

        # If deterministic checks fail, return immediately
        if errors:
            return ValidationResult(
                is_valid=False,
                status=ValidationStatus.INVALID,
                errors=errors,
                warnings=warnings,
                validated_question=None,
            )

        # Attempt Pydantic model construction
        try:
            validated_q = MCQQuestion(**data)
            return ValidationResult(
                is_valid=True,
                status=ValidationStatus.VALID,
                errors=[],
                warnings=warnings,
                validated_question=validated_q,
            )
        except ValidationError as e:
            for err in e.errors():
                loc = " -> ".join(str(l) for l in err.get("loc", []))
                errors.append(f"Pydantic validation error at '{loc}': {err.get('msg')}")
            return ValidationResult(
                is_valid=False,
                status=ValidationStatus.INVALID,
                errors=errors,
                warnings=warnings,
                validated_question=None,
            )

    @staticmethod
    def validate_subjective_data(data: Dict[str, Any]) -> ValidationResult:
        """
        Validates raw data for a Subjective Question (Short/Long Answer, Source-Based, Descriptive).
        """
        errors: List[str] = []
        warnings: List[str] = []

        # 1. Question text
        q_text = str(data.get("question_text", "")).strip()
        if len(q_text) < 5:
            errors.append("Question text is missing or shorter than 5 characters.")

        # 2. Maximum marks
        max_marks_val = data.get("maximum_marks")
        max_marks_float = 0.0
        try:
            max_marks_float = float(max_marks_val)
            if max_marks_float <= 0:
                errors.append(f"Maximum marks must be greater than 0. Received: {max_marks_val}")
        except (ValueError, TypeError):
            errors.append(f"Invalid maximum marks value: {max_marks_val}")

        # 3. Model / Expected answer
        expected_ans = str(data.get("expected_answer", "")).strip()
        if len(expected_ans) < 10:
            errors.append("Expected answer must be provided with at least 10 characters.")

        # 4. Marking rubric checks
        rubric_data = data.get("marking_rubric")
        if not isinstance(rubric_data, list) or len(rubric_data) == 0:
            errors.append("Subjective questions require a non-empty 'marking_rubric' list.")
        else:
            total_rubric_marks = 0.0
            for idx, item in enumerate(rubric_data):
                if not isinstance(item, dict):
                    errors.append(f"Rubric point at index {idx} must be a dictionary.")
                    continue
                point_text = str(item.get("point", "")).strip()
                if len(point_text) < 3:
                    errors.append(f"Rubric point at index {idx} must specify a descriptive concept.")
                alloc_marks = item.get("allocated_marks")
                try:
                    alloc_float = float(alloc_marks)
                    if alloc_float <= 0:
                        errors.append(f"Rubric point at index {idx} marks must be > 0. Received: {alloc_marks}")
                    else:
                        total_rubric_marks += alloc_float
                except (ValueError, TypeError):
                    errors.append(f"Rubric point at index {idx} has invalid marks: {alloc_marks}")

            if max_marks_float > 0 and not errors:
                if not math.isclose(total_rubric_marks, max_marks_float, rel_tol=1e-3, abs_tol=1e-3):
                    errors.append(
                        f"Sum of rubric marks ({total_rubric_marks:.2f}) does not match question maximum_marks ({max_marks_float:.2f})."
                    )

        if errors:
            return ValidationResult(
                is_valid=False,
                status=ValidationStatus.INVALID,
                errors=errors,
                warnings=warnings,
                validated_question=None,
            )

        # Attempt Pydantic model construction
        try:
            validated_q = SubjectiveQuestion(**data)
            return ValidationResult(
                is_valid=True,
                status=ValidationStatus.VALID,
                errors=[],
                warnings=warnings,
                validated_question=validated_q,
            )
        except ValidationError as e:
            for err in e.errors():
                loc = " -> ".join(str(l) for l in err.get("loc", []))
                errors.append(f"Pydantic validation error at '{loc}': {err.get('msg')}")
            return ValidationResult(
                is_valid=False,
                status=ValidationStatus.INVALID,
                errors=errors,
                warnings=warnings,
                validated_question=None,
            )

    @classmethod
    def validate(cls, data: Dict[str, Any], question_type: Optional[QuestionType] = None) -> ValidationResult:
        """
        Dispatches validation to MCQ or Subjective validator based on question_type.
        """
        q_type_raw = question_type or data.get("question_type")
        if isinstance(q_type_raw, str):
            try:
                q_type = QuestionType(q_type_raw)
            except ValueError:
                # Check case-insensitive match
                matches = [t for t in QuestionType if t.value.lower() == q_type_raw.lower()]
                if matches:
                    q_type = matches[0]
                else:
                    return ValidationResult(
                        is_valid=False,
                        status=ValidationStatus.INVALID,
                        errors=[f"Unsupported question_type: '{q_type_raw}'."],
                    )
        elif isinstance(q_type_raw, QuestionType):
            q_type = q_type_raw
        else:
            return ValidationResult(
                is_valid=False,
                status=ValidationStatus.INVALID,
                errors=["Missing 'question_type' field in data."],
            )

        if q_type == QuestionType.MCQ:
            return cls.validate_mcq_data(data)
        else:
            return cls.validate_subjective_data(data)
