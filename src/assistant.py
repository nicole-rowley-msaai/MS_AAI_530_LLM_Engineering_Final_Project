
import os

from dotenv import load_dotenv
from openai import OpenAI

from src.prompts import DEFAULT_PROMPT_VERSION, PROMPTS
from src.schemas import FitCheckResult


# Load API credentials and configuration from the .env file.
load_dotenv()


# Use the configured model or the default assistant model.
ASSISTANT_MODEL = os.getenv("ASSISTANT_MODEL", "gpt-4.1-mini")


# Analyze a resume against a job posting using the OpenAI API.
def analyze_resume(
    resume: str,
    job: str,
    prompt_version: str = DEFAULT_PROMPT_VERSION,
) -> FitCheckResult:

    if not resume.strip() or not job.strip():
        raise ValueError("Both a resume and job posting are required.")

    if prompt_version not in PROMPTS:
        raise ValueError(f"Unknown prompt version: {prompt_version}")

    if not os.getenv("OPENAI_API_KEY"):
        raise ValueError("OPENAI_API_KEY is missing from the .env file.")

    client = OpenAI()

    # Send the tagged resume and job posting with the selected system prompt.
    # Temperature 0 keeps repeated runs as consistent as possible. Remove it
    # if ASSISTANT_MODEL is set to a model that does not accept temperature.
    response = client.responses.parse(
        model=ASSISTANT_MODEL,
        instructions=PROMPTS[prompt_version],
        input=(
            f"<resume>\n{resume}\n</resume>\n\n"
            f"<job_posting>\n{job}\n</job_posting>"
        ),
        text_format=FitCheckResult,
        temperature=0,
        store=False,
    )

    # Return the validated structured output.
    if response.output_parsed is None:
        raise ValueError("The model did not return a valid structured response.")

    return response.output_parsed
