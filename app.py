
import json
import logging

import streamlit as st

from src.assistant import ASSISTANT_MODEL, analyze_resume
from src.judge import (
    JUDGE_MODEL,
    judge_suggestions,
    quote_in_resume,
    verdicts_by_index,
)
from src.pdf_utils import extract_pdf_text
from src.prompts import DEFAULT_PROMPT_VERSION, PROMPTS


# Longest resume or job posting accepted, in characters.
MAX_INPUT_CHARS = 30000

# Verification labels shown with an icon and text, never color alone.
BADGES = {
    "supported": "✅ Supported",
    "exaggerated": "⚠️ Exaggerated",
    "unsupported": "❌ Unsupported",
}
NOT_CHECKED = "❔ Not checked"


# Configure the application page.
st.set_page_config(
    page_title="FitCheck AI",
    page_icon="📄",
    layout="wide"
)


# Store the latest analysis so results remain available after reruns.
if "analysis" not in st.session_state:
    st.session_state.analysis = None


# Collect the resume, job posting, and settings in the sidebar.
with st.sidebar:
    st.title("FitCheck AI")
    st.caption("AI-powered job application assistant")

    st.subheader("Your resume")
    resume_file = st.file_uploader(
        "Upload resume (PDF)",
        type=["pdf"],
        key="resume_upload"
    )
    resume_text = st.text_area(
        "Or paste your resume",
        height=150,
        placeholder="Enter your resume text here..."
    )

    st.subheader("Job posting")
    job_file = st.file_uploader(
        "Upload job posting (PDF)",
        type=["pdf"],
        key="job_upload"
    )
    job_text = st.text_area(
        "Or paste the job description",
        height=150,
        placeholder="Enter the job posting here..."
    )

    st.caption("If you provide both a PDF and pasted text, the PDF is used.")

    # Let reviewers compare prompt versions on the same inputs.
    prompt_versions = list(PROMPTS)
    prompt_version = st.selectbox(
        "Prompt version",
        prompt_versions,
        index=prompt_versions.index(DEFAULT_PROMPT_VERSION),
        help="Switch versions to compare results on the same inputs."
    )

    analyze_clicked = st.button("Analyze application", type="primary")

    st.info(
        "Your resume and the job posting are sent to OpenAI for analysis, "
        "and your resume is also sent to Google Gemini for verification. "
        "This app does not save them. Remove any details you do not want "
        "to share."
    )


# Run the assistant and then the judge when the user submits both inputs.
if analyze_clicked:

    # Clear previous results and review choices before a new analysis.
    st.session_state.analysis = None
    for key in list(st.session_state.keys()):
        if key.startswith(("keep_", "edit_")):
            del st.session_state[key]

    try:
        # Use uploaded PDFs when available, otherwise use pasted text.
        final_resume = (
            extract_pdf_text(resume_file)
            if resume_file is not None
            else resume_text.strip()
        )

        final_job = (
            extract_pdf_text(job_file)
            if job_file is not None
            else job_text.strip()
        )

        # Validate both inputs before calling the OpenAI API.
        if not final_resume or not final_job:
            st.warning("Please provide both a resume and a job posting.")

        elif max(len(final_resume), len(final_job)) > MAX_INPUT_CHARS:
            st.warning(
                f"Each input is limited to {MAX_INPUT_CHARS:,} characters. "
                "Please shorten the text and try again."
            )

        else:
            with st.spinner("Analyzing your application..."):
                result = analyze_resume(
                    final_resume, final_job, prompt_version
                )

            with st.spinner("Checking each suggestion against your resume..."):
                judge_result = judge_suggestions(
                    final_resume, result.resume_suggestions
                )

            # Save everything needed for display and download.
            st.session_state.analysis = {
                "result": result,
                "verdicts": verdicts_by_index(
                    judge_result, len(result.resume_suggestions)
                ),
                "resume": final_resume,
                "prompt_version": prompt_version,
            }

    except ValueError as error:
        # Problems the user can fix, such as an unreadable PDF.
        st.error(str(error))

    except Exception:
        # Keep technical details in the server log, not on the page.
        logging.exception("FitCheck AI analysis failed")
        st.error(
            "Something went wrong while contacting the AI services. "
            "Check your API keys and connection, then try again."
        )


analysis = st.session_state.analysis

# Show an introduction until an analysis has been completed.
if analysis is None:

    st.title("FitCheck AI")
    st.write(
        "Compare your resume against a job posting to identify skill gaps, "
        "improve your resume bullet points, and prepare for interviews."
    )
    st.write(
        "Every suggested bullet is checked against your resume by a second "
        "AI model, which flags claims that are exaggerated or unsupported "
        "so you can review them before use."
    )
    st.write("Add your resume and a job posting in the sidebar to begin.")

# Display the most recent completed analysis.
else:

    result = analysis["result"]
    verdicts = analysis["verdicts"]
    resume = analysis["resume"]
    suggestions = result.resume_suggestions

    # Only bullets labeled "supported" are kept by default, so the user
    # must opt in to anything the judge flagged or did not check.
    def default_keep(index: int) -> bool:
        verdict = verdicts.get(index)
        return verdict is not None and verdict.label == "supported"

    labels = [
        verdicts[index].label if index in verdicts else None
        for index in range(len(suggestions))
    ]
    kept_count = sum(
        st.session_state.get(f"keep_{index}", default_keep(index))
        for index in range(len(suggestions))
    )

    st.title("Review your suggestions")
    st.write(
        "Each suggested bullet was checked against your resume. "
        "Decide what to keep."
    )

    # Summarize the verification results.
    col1, col2, col3, col4 = st.columns(4)
    col1.metric("Supported", labels.count("supported"))
    col2.metric("Exaggerated", labels.count("exaggerated"))
    col3.metric("Unsupported", labels.count("unsupported"))
    col4.metric("Kept by you", f"{kept_count} of {len(suggestions)}")

    st.markdown(
        f"**Overall fit: {result.overall_fit} match.** {result.fit_summary}"
    )

    tab_gaps, tab_bullets, tab_questions = st.tabs([
        f"Skill gaps ({len(result.skill_gaps)})",
        f"Resume bullets ({len(suggestions)})",
        f"Interview questions ({len(result.interview_questions)})",
    ])

    # Display skills the job requires that the resume does not show.
    with tab_gaps:
        if result.skill_gaps:
            for gap in result.skill_gaps:
                st.subheader(gap.skill)
                st.write(gap.explanation)
        else:
            st.info("No significant skill gaps were identified.")

    # Display each suggestion with its verification label and evidence.
    with tab_bullets:
        kept_bullets = []
        review = []

        if not suggestions:
            st.info("No resume improvements were suggested.")

        for index, suggestion in enumerate(suggestions):
            verdict = verdicts.get(index)
            badge = BADGES[verdict.label] if verdict else NOT_CHECKED

            with st.container(border=True):
                st.markdown(f"**Suggestion {index + 1}** · {badge}")

                left, right = st.columns(2)

                with left:
                    st.caption("Original")
                    st.write(suggestion.original_text)

                    # Check the assistant's quote with code, not an LLM.
                    if not quote_in_resume(suggestion.original_text, resume):
                        st.warning(
                            "This original text was not found word for word "
                            "in your resume."
                        )

                with right:
                    st.caption("Suggested (you can edit this)")
                    edited_text = st.text_area(
                        "Suggested bullet",
                        value=suggestion.suggested_text,
                        key=f"edit_{index}",
                        label_visibility="collapsed"
                    )

                if verdict is None:
                    st.warning(
                        "The verification step did not return a result for "
                        "this bullet. Check it against your resume yourself."
                    )
                else:
                    st.info(
                        f"**Why:** {verdict.reason}\n\n"
                        "**Evidence from your resume:** "
                        f"{verdict.evidence or 'none found'}"
                    )

                    # Check the judge's quote with code as well.
                    if verdict.evidence and not quote_in_resume(
                        verdict.evidence, resume
                    ):
                        st.warning(
                            "The quoted evidence was not found word for word "
                            "in your resume, so treat this label with caution."
                        )

                keep = st.checkbox(
                    "Keep this bullet",
                    value=default_keep(index),
                    key=f"keep_{index}"
                )

            if keep:
                kept_bullets.append(edited_text)

            review.append({
                "original_text": suggestion.original_text,
                "suggested_text": suggestion.suggested_text,
                "final_text": edited_text,
                "label": verdict.label if verdict else None,
                "evidence": verdict.evidence if verdict else None,
                "reason": verdict.reason if verdict else None,
                "kept": keep,
            })

        if suggestions:
            st.caption(
                "Edited bullets are not checked again. Make sure your edits "
                "stay true to your experience."
            )

            # Allow users to download only the bullets they chose to keep.
            st.download_button(
                label=f"Download kept bullets ({len(kept_bullets)})",
                data="\n".join(f"- {bullet}" for bullet in kept_bullets),
                file_name="fitcheck_bullets.txt",
                mime="text/plain",
                disabled=not kept_bullets
            )

            # Allow users to download the full structured analysis.
            st.download_button(
                label="Download full analysis (JSON)",
                data=json.dumps(
                    {
                        "prompt_version": analysis["prompt_version"],
                        "assistant_model": ASSISTANT_MODEL,
                        "judge_model": JUDGE_MODEL,
                        "overall_fit": result.overall_fit,
                        "fit_summary": result.fit_summary,
                        "skill_gaps": [
                            gap.model_dump() for gap in result.skill_gaps
                        ],
                        "resume_suggestions": review,
                        "interview_questions": result.interview_questions,
                    },
                    indent=2
                ),
                file_name="fitcheck_analysis.json",
                mime="application/json"
            )

    # Display tailored practice interview questions.
    with tab_questions:
        if result.interview_questions:
            for index, question in enumerate(
                result.interview_questions, start=1
            ):
                st.write(f"**{index}.** {question}")
        else:
            st.info("No interview questions were generated.")


# Display a reminder about reviewing AI-generated content.
st.divider()

st.caption(
    "FitCheck AI generates suggestions and verification labels using "
    "artificial intelligence, and both can be wrong. You are responsible "
    "for the accuracy of your resume."
)
