
import os
import re

from dotenv import load_dotenv
from openai import OpenAI

from src.prompts import JUDGE_PROMPT
from src.schemas import BulletVerdict, JudgeResult, ResumeSuggestion


# Load API credentials and configuration from the .env file.
load_dotenv()


# Use the configured model or the default judge model. The judge is a
# Google Gemini model, while the assistant is an OpenAI model, which reduces
# the chance that both share the same blind spots.
JUDGE_MODEL = os.getenv("JUDGE_MODEL", "gemini-3.8-flash")

# Gemini is called through Google's OpenAI-compatible endpoint, so the
# OpenAI library is used with a Gemini API key and this base URL.
GEMINI_BASE_URL = "https://generativelanguage.googleapis.com/v1beta/openai/"


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

    gemini_api_key = os.getenv("GEMINI_API_KEY")

    if not gemini_api_key:
        raise ValueError("GEMINI_API_KEY is missing from the .env file.")

    bullets = "\n".join(
        f"[{index}] {suggestion.suggested_text}"
        for index, suggestion in enumerate(suggestions)
    )

    client = OpenAI(api_key=gemini_api_key, base_url=GEMINI_BASE_URL)

    # Temperature is left at the model default for Gemini. Measure the
    # judge's consistency by repeating runs instead of assuming it.
    completion = client.chat.completions.parse(
        model=JUDGE_MODEL,
        messages=[
            {"role": "system", "content": JUDGE_PROMPT},
            {
                "role": "user",
                "content": (
                    f"<resume>\n{resume}\n</resume>\n\n"
                    f"<bullets>\n{bullets}\n</bullets>"
                ),
            },
        ],
        response_format=JudgeResult,
    )

    judge_result = completion.choices[0].message.parsed

    if judge_result is None:
        raise ValueError("The judge did not return a valid structured response.")

    return judge_result


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
