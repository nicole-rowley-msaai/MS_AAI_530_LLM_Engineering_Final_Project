
from typing import Literal

from pydantic import BaseModel, Field


# Defines a skill or qualification missing from the resume.
class SkillGap(BaseModel):
    skill: str = Field(
        description="Skill or qualification missing from the resume"
    )
    explanation: str = Field(
        description="Why this skill matters for the job"
    )


# Stores the original resume text and the suggested improvement.
class ResumeSuggestion(BaseModel):
    original_text: str = Field(
        description="Relevant text from the original resume"
    )
    suggested_text: str = Field(
        description="Improved resume bullet grounded in the original resume"
    )


# Defines the structured JSON output returned by the main LLM assistant.
class FitCheckResult(BaseModel):
    overall_fit: Literal["strong", "partial", "weak"] = Field(
        description="How well the resume matches the job posting overall"
    )
    fit_summary: str = Field(
        description="One or two sentences explaining the overall fit"
    )
    skill_gaps: list[SkillGap] = Field(
        description="Skills required by the job but not evidenced in the resume"
    )
    resume_suggestions: list[ResumeSuggestion] = Field(
        description="Suggested resume improvements"
    )
    interview_questions: list[str] = Field(
        description="Practice interview questions tailored to the job"
    )


# Stores the judge's decision about one suggested resume bullet.
class BulletVerdict(BaseModel):
    index: int = Field(
        description="Number of the bullet being judged, as given in the input"
    )
    label: Literal["supported", "exaggerated", "unsupported"] = Field(
        description="Whether the resume supports the bullet"
    )
    evidence: str = Field(
        description=(
            "Exact text copied from the resume that the decision relies on, "
            "or an empty string if there is none"
        )
    )
    reason: str = Field(
        description="One sentence explaining the label"
    )


# Defines the structured JSON output returned by the LLM judge.
class JudgeResult(BaseModel):
    verdicts: list[BulletVerdict] = Field(
        description="One verdict for each suggested bullet"
    )
