"""
Enumerations for Question Bank and Assessment Schema.
"""

from enum import Enum


class Board(str, Enum):
    CBSE = "CBSE"
    ICSE = "ICSE"
    STATE_BOARD = "State Board"
    OTHER = "Other"


class ClassGrade(str, Enum):
    CLASS_9 = "Class 9"
    CLASS_10 = "Class 10"
    CLASS_11 = "Class 11"
    CLASS_12 = "Class 12"


class Subject(str, Enum):
    HISTORY = "History"
    COMPUTER_APPLICATIONS = "Computer Applications"
    SCIENCE = "Science"
    MATHEMATICS = "Mathematics"
    ENGLISH = "English"


class QuestionType(str, Enum):
    MCQ = "MCQ"
    SHORT_ANSWER = "Short Answer"
    LONG_ANSWER = "Long Answer"
    SOURCE_BASED = "Source Based"
    DESCRIPTIVE = "Descriptive"


class Difficulty(str, Enum):
    EASY = "Easy"
    MEDIUM = "Medium"
    HARD = "Hard"


class SourceType(str, Enum):
    LLM_GENERATED = "LLM_GENERATED"
    QUESTION_PAPER = "QUESTION_PAPER"
    TEXTBOOK = "TEXTBOOK"
    TEACHER_CREATED = "TEACHER_CREATED"


class ValidationStatus(str, Enum):
    VALID = "VALID"
    INVALID = "INVALID"
    NEEDS_REVIEW = "NEEDS_REVIEW"
    PENDING_REVIEW = "PENDING_REVIEW"


class RubricVerificationStatus(str, Enum):
    VERIFIED = "VERIFIED"
    UNVERIFIED = "UNVERIFIED"
    NEEDS_PREPARATION = "NEEDS_PREPARATION"
