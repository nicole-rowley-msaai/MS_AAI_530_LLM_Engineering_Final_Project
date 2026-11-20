
import os

from dotenv import load_dotenv
from openai import OpenAI

from src.prompts import SYSTEM_PROMPT
from src.schemas import FitCheckResult


# Load API credentials and configuration from the .env file.
load_dotenv()


# Use the configured model or the default assistant model.
ASSISTANT_MODEL = os.getenv("ASSISTANT_MODEL", "gpt-4.1-mini")


# Analyze a resume against a job posting using the OpenAI API.
def analyze_resume(resume: str, job: str) -> FitCheckResult:

    if not resume.strip() or not job.strip():
        raise ValueError("Both a resume and job posting are required.")

    if not os.getenv("OPENAI_API_KEY"):
        raise ValueError("OPENAI_API_KEY is missing from the .env file.")

    client = OpenAI()

    # Send the resume and job posting with the system prompt.
    response = client.responses.parse(
        model=ASSISTANT_MODEL,
        instructions=SYSTEM_PROMPT,
        input=(
            f"RESUME:\n{resume}\n\n"
            f"JOB POSTING:\n{job}"
        ),
        text_format=FitCheckResult,
        store=False,
    )

    # Return the validated structured output.
    if response.output_parsed is None:
        raise ValueError("The model did not return a valid structured response.")

    return response.output_parsed
