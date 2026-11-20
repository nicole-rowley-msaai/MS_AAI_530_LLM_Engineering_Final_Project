
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
    skill_gaps: list[SkillGap] = Field(
        description="Skills required by the job but not demonstrated in the resume"
    )
    resume_suggestions: list[ResumeSuggestion] = Field(
        description="Suggested resume improvements"
    )
    interview_questions: list[str] = Field(
        description="Practice interview questions tailored to the job"
    )

