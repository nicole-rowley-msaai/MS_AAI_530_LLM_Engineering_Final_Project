
import os
import re

from dotenv import load_dotenv
from openai import OpenAI

from src.prompts import JUDGE_PROMPT
from src.schemas import BulletVerdict, JudgeResult, ResumeSuggestion


# Load API credentials and configuration from the .env file.
load_dotenv()


# Use the configured model or the default judge model. A different model
# from the assistant reduces the chance that both share the same blind spots.
JUDGE_MODEL = os.getenv("JUDGE_MODEL", "gpt-4.1")


# Lowercase text and collapse whitespace so PDF line breaks do not matter.
def _normalize(text: str) -> str:
    return re.sub(r"\s+", " ", text).strip().lower()


# Check that a quote really appears in the resume.
# Used to validate the judge's evidence and the assistant's original text.
def quote_in_resume(quote: str, resume: str) -> bool:
    quote = _normalize(quote).strip("\"'“”‘’.… ")

    if not quote:
        return False

    return quote in _normalize(resume)


# Ask the LLM judge to label each suggested bullet against the resume.
# The judge sees only the resume and the suggested bullets, not the
# assistant's "original text", so it checks each claim independently.
def judge_suggestions(
    resume: str,
    suggestions: list[ResumeSuggestion],
) -> JudgeResult:

    if not suggestions:
        return JudgeResult(verdicts=[])

    if not os.getenv("OPENAI_API_KEY"):
        raise ValueError("OPENAI_API_KEY is missing from the .env file.")

    bullets = "\n".join(
        f"[{index}] {suggestion.suggested_text}"
        for index, suggestion in enumerate(suggestions)
    )

    client = OpenAI()

    # Temperature 0 keeps repeated runs as consistent as possible. Remove it
    # if JUDGE_MODEL is set to a model that does not accept temperature.
    response = client.responses.parse(
        model=JUDGE_MODEL,
        instructions=JUDGE_PROMPT,
        input=(
            f"<resume>\n{resume}\n</resume>\n\n"
            f"<bullets>\n{bullets}\n</bullets>"
        ),
        text_format=JudgeResult,
        temperature=0,
        store=False,
    )

    if response.output_parsed is None:
        raise ValueError("The judge did not return a valid structured response.")

    return response.output_parsed


# Map bullet number to verdict. Bullets the judge skipped are left out,
# so callers must handle a missing verdict.
def verdicts_by_index(
    judge_result: JudgeResult,
    bullet_count: int,
) -> dict[int, BulletVerdict]:
    return {
        verdict.index: verdict
        for verdict in judge_result.verdicts
        if 0 <= verdict.index < bullet_count
    }
