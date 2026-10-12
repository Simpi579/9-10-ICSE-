"""
Validation Pipeline coordinating structural and semantic validation stages.
Enforces programmatic overrides for source_type and validation_status.
"""

from typing import Any, Dict, Optional
from schema.enums import QuestionType, SourceType, ValidationStatus
from schema.models import ValidationResult, Question
from .structural import StructuralValidator
from .semantic import SemanticValidator


class ValidationPipeline:
    """
    Coordinates structural and semantic validation in strict decoupled order.
    Enforces programmatic security constraints (e.g. source_type and validation_status).
    """

    def __init__(self, semantic_validator: Optional[SemanticValidator] = None):
        self.structural_validator = StructuralValidator()
        self.semantic_validator = semantic_validator or SemanticValidator(strict_syllabus=True)

    def process(
        self,
        raw_data: Dict[str, Any],
        question_type: Optional[QuestionType] = None,
        force_source_type: SourceType = SourceType.LLM_GENERATED,
    ) -> ValidationResult:
        """
        Processes raw input dictionary through:
        1. Structural / schema validation.
        2. Programmatic enforcement of source_type = LLM_GENERATED.
        3. Semantic and syllabus validation.
        4. Programmatic assignment of validation_status.
        """
        # Step 1: Structural Validation
        struct_res = self.structural_validator.validate(raw_data, question_type)
        if not struct_res.is_valid or not struct_res.validated_question:
            # Cannot proceed to semantic validation if structural validation failed
            return struct_res

        question: Question = struct_res.validated_question

        # Step 2: PROGRAMMATIC ENFORCEMENT: Enforce source_type in Python
        # Do not trust the LLM or raw input to set this field correctly.
        question.source_type = force_source_type

        # Step 3: Semantic and Syllabus Validation
        semantic_res = self.semantic_validator.validate(question)

        # Step 4: PROGRAMMATIC ASSIGNMENT: validation_status
        all_errors = list(struct_res.errors) + list(semantic_res.errors)
        all_warnings = list(struct_res.warnings) + list(semantic_res.warnings)

        if all_errors:
            question.validation_status = ValidationStatus.INVALID
            final_status = ValidationStatus.INVALID
            is_valid = False
        elif all_warnings:
            question.validation_status = ValidationStatus.NEEDS_REVIEW
            final_status = ValidationStatus.NEEDS_REVIEW
            is_valid = True
        else:
            question.validation_status = ValidationStatus.VALID
            final_status = ValidationStatus.VALID
            is_valid = True

        question.validation_errors = all_errors

        return ValidationResult(
            is_valid=is_valid,
            status=final_status,
            errors=all_errors,
            warnings=all_warnings,
            validated_question=question,
        )
