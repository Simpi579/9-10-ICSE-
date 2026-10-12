"""
Question Generation module supporting MCQ and Rubric-Based Subjective question synthesis.
"""

from .prompts import PromptBuilder
from .generator import QuestionGenerator

__all__ = ["PromptBuilder", "QuestionGenerator"]
