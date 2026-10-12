"""
Data models and strict validation schemas for answer evaluation results.
"""

from enum import Enum
import math
from typing import List, Optional
from uuid import uuid4
from pydantic import BaseModel, Field, model_validator, ConfigDict


class EvaluationStatus(str, Enum):
    EVALUATED = "EVALUATED"
    PROVISIONAL = "PROVISIONAL"
    NEEDS_TEACHER_REVIEW = "NEEDS_TEACHER_REVIEW"
    BLANK_ANSWER = "BLANK_ANSWER"
    ERROR = "ERROR"


class FactualError(BaseModel):
    """
    Identifies a specific incorrect claim made by the student and its historical correction.
    """
    model_config = ConfigDict(extra="ignore")

    student_claim: str = Field(..., description="The inaccurate or unsupported claim in student answer")
    correction: str = Field(..., description="The historically accurate fact and correction")


class CriterionEvaluation(BaseModel):
    """
    Itemized evaluation of a single rubric criterion.
    """
    model_config = ConfigDict(extra="ignore")

    criterion_id: Optional[str] = None
    criterion: str = Field(..., description="The specific marking point / concept from rubric")
    maximum_marks: float = Field(..., gt=0, description="Maximum marks for this criterion")
    awarded_marks: float = Field(..., ge=0, description="Marks awarded to student for this criterion")
    evidence: str = Field(default="", description="Relevant sentence or thought from student answer")
    feedback: str = Field(default="", description="Explanation of why marks were awarded or deducted")

    @model_validator(mode="after")
    def validate_marks_within_criterion_limit(self) -> "CriterionEvaluation":
        if self.awarded_marks > self.maximum_marks + 1e-4:
            raise ValueError(
                f"Awarded marks ({self.awarded_marks}) cannot exceed criterion maximum ({self.maximum_marks})."
            )
        return self


class AnswerEvaluationResult(BaseModel):
    """
    Validated outcome of a subjective answer evaluation.
    """
    model_config = ConfigDict(extra="ignore")

    evaluation_id: str = Field(default_factory=lambda: f"eval_{uuid4().hex[:8]}")
    question_id: str = Field(..., description="ID of the evaluated question")
    question_text: str = Field(..., description="Original question text")
    maximum_marks: float = Field(..., gt=0, description="Question's official maximum marks")
    student_submitted_answer: str = Field(..., description="Original response submitted by the student")
    awarded_marks: float = Field(..., ge=0, description="Total validated marks awarded")
    
    correct_concepts_identified: List[str] = Field(default_factory=list)
    missing_concepts: List[str] = Field(default_factory=list)
    factual_errors: List[FactualError] = Field(default_factory=list)
    criterion_wise_marks: List[CriterionEvaluation] = Field(default_factory=list)
    
    feedback: str = Field(..., min_length=5, description="Constructive evaluation feedback")
    improvement_suggestions: List[str] = Field(default_factory=list)
    model_answer: Optional[str] = Field(default=None, description="Verified or approved reference answer")
    
    evaluation_status: EvaluationStatus = Field(default=EvaluationStatus.EVALUATED)
    teacher_review_required: bool = Field(default=False)
    review_reason: Optional[str] = Field(default=None)
    confidence_score: float = Field(default=0.85, ge=0.0, le=1.0)

    @model_validator(mode="after")
    def validate_score_boundaries(self) -> "AnswerEvaluationResult":
        # 1. Total marks cannot exceed question maximum marks
        if self.awarded_marks > self.maximum_marks + 1e-3:
            raise ValueError(
                f"Awarded marks ({self.awarded_marks}) cannot exceed question maximum marks ({self.maximum_marks})."
            )
        
        # 2. Check consistency with criterion_wise_marks if present
        if self.criterion_wise_marks:
            criteria_sum = sum(c.awarded_marks for c in self.criterion_wise_marks)
            if not math.isclose(criteria_sum, self.awarded_marks, rel_tol=1e-2, abs_tol=0.1):
                raise ValueError(
                    f"Awarded marks ({self.awarded_marks}) do not match sum of criteria marks ({criteria_sum:.2f})."
                )
        return self


class EvaluationRequest(BaseModel):
    """
    Request payload submitted by a student or interface.
    """
    model_config = ConfigDict(extra="forbid")

    question_id: str
    student_answer: str
    student_id: Optional[str] = "student_001"
