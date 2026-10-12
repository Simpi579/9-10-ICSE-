"""
Pydantic data models for educational questions, rubrics, and validation.
"""

from typing import List, Optional, Union, Literal
from uuid import uuid4
from pydantic import BaseModel, Field, model_validator, field_validator, ConfigDict
import math

from .enums import (
    Board,
    ClassGrade,
    Subject,
    QuestionType,
    Difficulty,
    SourceType,
    ValidationStatus,
    RubricVerificationStatus,
)


class RubricCriterion(BaseModel):
    """
    An individual marking point in a subjective rubric.
    """
    model_config = ConfigDict(extra="forbid")

    criterion_id: str = Field(default_factory=lambda: f"crit_{uuid4().hex[:6]}")
    point: str = Field(..., min_length=3, description="Specific historical concept or point required")
    allocated_marks: float = Field(..., gt=0, description="Marks allocated for this specific point")
    description: Optional[str] = Field(default=None, description="Detailed guidance for awarding marks")
    acceptable_alternatives: List[str] = Field(
        default_factory=list,
        description="Alternative phrasings or historical explanations acceptable for credit",
    )
    common_misconceptions: List[str] = Field(
        default_factory=list,
        description="Frequent misconceptions or errors students make on this point",
    )


class QuestionBase(BaseModel):
    """
    Base model for all educational assessment questions.
    """
    model_config = ConfigDict(extra="forbid")

    question_id: str = Field(default_factory=lambda: f"q_{uuid4().hex[:8]}")
    board: Board = Field(default=Board.CBSE)
    class_grade: ClassGrade = Field(default=ClassGrade.CLASS_9)
    subject: Subject = Field(default=Subject.HISTORY)
    chapter: str = Field(..., min_length=2)
    topic: Optional[str] = Field(default=None)
    question_text: str = Field(..., min_length=5)
    difficulty: Difficulty = Field(default=Difficulty.MEDIUM)
    maximum_marks: float = Field(..., gt=0)
    source_reference: Optional[str] = Field(default=None)
    
    # Programmatically enforced fields - never trusted directly from LLM
    source_type: SourceType = Field(default=SourceType.LLM_GENERATED)
    validation_status: ValidationStatus = Field(default=ValidationStatus.PENDING_REVIEW)
    validation_errors: List[str] = Field(default_factory=list)

    @field_validator("question_text")
    @classmethod
    def validate_question_text_not_empty(cls, v: str) -> str:
        stripped = v.strip()
        if len(stripped) < 5:
            raise ValueError("Question text must be at least 5 characters long and non-whitespace.")
        return stripped


class MCQQuestion(QuestionBase):
    """
    Multiple-Choice Question with strict 4 unique options and matching answer.
    """
    question_type: Literal[QuestionType.MCQ] = QuestionType.MCQ
    maximum_marks: float = Field(default=1.0, gt=0)
    options: List[str] = Field(..., description="Exactly four unique options")
    correct_answer: str = Field(..., description="The correct answer matching one option")
    explanation: str = Field(..., min_length=5, description="Explanation why the answer is correct")

    @field_validator("options")
    @classmethod
    def validate_options(cls, options: List[str]) -> List[str]:
        if len(options) != 4:
            raise ValueError(f"MCQ must have exactly 4 options, found {len(options)}.")
        
        cleaned_options = [opt.strip() for opt in options]
        for idx, opt in enumerate(cleaned_options):
            if not opt:
                raise ValueError(f"Option {idx + 1} cannot be empty or whitespace.")

        # Check uniqueness case-insensitively
        lowered = [opt.lower() for opt in cleaned_options]
        if len(set(lowered)) != 4:
            raise ValueError(f"MCQ options must be unique. Found duplicates in: {cleaned_options}")

        return cleaned_options

    @model_validator(mode="after")
    def validate_correct_answer_matches_option(self) -> "MCQQuestion":
        cleaned_answer = self.correct_answer.strip()
        cleaned_options = [opt.strip() for opt in self.options]

        # Case-insensitive match check
        matching = [opt for opt in cleaned_options if opt.lower() == cleaned_answer.lower()]
        if not matching:
            raise ValueError(
                f"Correct answer '{cleaned_answer}' does not match any of the provided options: {cleaned_options}"
            )
        # Normalize correct_answer to the exact string in options
        self.correct_answer = matching[0]
        return self


class SubjectiveQuestion(QuestionBase):
    """
    Subjective question (Short Answer, Long Answer, Source Based, Descriptive)
    with structured marking rubric and expected model answer.
    """
    question_type: QuestionType = Field(..., description="Subjective question type")
    expected_answer: str = Field(default="", description="Model answer or expected response")
    marking_rubric: List[RubricCriterion] = Field(
        default_factory=list,
        description="Structured rubric points whose marks sum up to maximum_marks",
    )
    rubric_status: RubricVerificationStatus = Field(default=RubricVerificationStatus.UNVERIFIED)

    @field_validator("question_type")
    @classmethod
    def validate_not_mcq(cls, v: QuestionType) -> QuestionType:
        if v == QuestionType.MCQ:
            raise ValueError("SubjectiveQuestion question_type cannot be MCQ.")
        return v

    @model_validator(mode="after")
    def validate_rubric_sum(self) -> "SubjectiveQuestion":
        if self.rubric_status == RubricVerificationStatus.VERIFIED:
            if not self.expected_answer or len(self.expected_answer.strip()) < 10:
                raise ValueError("Verified subjective question must have an expected_answer with at least 10 characters.")
            if not self.marking_rubric:
                raise ValueError("Verified subjective question must have at least one marking rubric point.")
            
            total_allocated = sum(criterion.allocated_marks for criterion in self.marking_rubric)
            if not math.isclose(total_allocated, self.maximum_marks, rel_tol=1e-3, abs_tol=1e-3):
                raise ValueError(
                    f"Sum of rubric marks ({total_allocated}) does not match maximum_marks ({self.maximum_marks})."
                )
        elif self.marking_rubric:
            # If rubric is present even though unverified, verify mark sum consistency
            total_allocated = sum(criterion.allocated_marks for criterion in self.marking_rubric)
            if not math.isclose(total_allocated, self.maximum_marks, rel_tol=1e-3, abs_tol=1e-3):
                raise ValueError(
                    f"Sum of rubric marks ({total_allocated}) does not match maximum_marks ({self.maximum_marks})."
                )
        return self


# Union of question types
Question = Union[MCQQuestion, SubjectiveQuestion]


class RawMCQPayload(BaseModel):
    """
    Raw payload schema expected from LLM generation for MCQ questions.
    Notice this model does NOT contain source_type or validation_status.
    """
    model_config = ConfigDict(extra="ignore")

    question_text: str
    options: List[str]
    correct_answer: str
    explanation: str
    difficulty: Difficulty = Difficulty.MEDIUM
    maximum_marks: float = 1.0
    chapter: Optional[str] = None
    topic: Optional[str] = None


class RawRubricCriterion(BaseModel):
    model_config = ConfigDict(extra="ignore")

    point: str
    allocated_marks: float
    description: Optional[str] = None
    acceptable_alternatives: List[str] = Field(default_factory=list)
    common_misconceptions: List[str] = Field(default_factory=list)


class RawSubjectivePayload(BaseModel):
    """
    Raw payload schema expected from LLM generation for Subjective questions.
    Notice this model does NOT contain source_type or validation_status.
    """
    model_config = ConfigDict(extra="ignore")

    question_text: str
    expected_answer: str
    marking_rubric: List[RawRubricCriterion]
    difficulty: Difficulty = Difficulty.MEDIUM
    maximum_marks: float = 3.0
    chapter: Optional[str] = None
    topic: Optional[str] = None


class ValidationResult(BaseModel):
    """
    Structured outcome of deterministic validation.
    """
    model_config = ConfigDict(extra="forbid")

    is_valid: bool
    status: ValidationStatus
    errors: List[str] = Field(default_factory=list)
    warnings: List[str] = Field(default_factory=list)
    validated_question: Optional[Question] = None
