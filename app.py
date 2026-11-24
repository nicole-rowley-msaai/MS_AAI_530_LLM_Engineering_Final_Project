
import streamlit as st

from src.assistant import analyze_resume
from src.pdf_utils import extract_pdf_text


# Configure the application page.
st.set_page_config(
    page_title="FitCheck AI",
    page_icon="📄",
    layout="wide"
)


# Application title and description.
st.title("FitCheck AI")
st.subheader("AI-Powered Job Application Assistant")

st.write(
    "Compare your resume against a job posting to identify skill gaps, "
    "improve your resume bullet points, and prepare for interviews."
)

st.divider()


# Store the latest analysis so results remain available after reruns.
if "analysis_result" not in st.session_state:
    st.session_state.analysis_result = None


# Create input fields for the resume and job posting.
col1, col2 = st.columns(2)

with col1:
    st.header("Your Resume")

    # Allow users to upload a resume as a PDF.
    resume_file = st.file_uploader(
        "Upload Resume (PDF)",
        type=["pdf"],
        key="resume_upload"
    )

    resume_text = st.text_area(
        "Or paste your resume below:",
        height=250,
        placeholder="Enter your resume text here..."
    )

with col2:
    st.header("Job Posting")

    # Allow users to upload a job posting as a PDF.
    job_file = st.file_uploader(
        "Upload Job Posting (PDF)",
        type=["pdf"],
        key="job_upload"
    )

    job_text = st.text_area(
        "Or paste the job description below:",
        height=250,
        placeholder="Enter the job posting here..."
    )


# Run the LLM assistant when the user submits both inputs.
if st.button("Analyze Application", type="primary", use_container_width=True):

    # Clear previous results before starting another analysis.
    st.session_state.analysis_result = None

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

        else:
            with st.spinner("Analyzing your application..."):
                result = analyze_resume(final_resume, final_job)

            # Save the analysis for display and JSON download.
            st.session_state.analysis_result = result

            st.success("Analysis completed successfully!")

    except Exception as error:
        st.error("An error occurred while analyzing your application.")
        st.exception(error)


# Display the most recent completed analysis.
result = st.session_state.analysis_result

if result is not None:

    st.divider()

    # Display missing or undocumented skills.
    st.header("Skill Gap Analysis")

    if result.skill_gaps:
        for gap in result.skill_gaps:
            st.subheader(gap.skill)
            st.write(gap.explanation)
    else:
        st.info("No significant skill gaps were identified.")

    st.divider()

    # Display suggested improvements to resume bullets.
    st.header("Resume Improvement Suggestions")

    if result.resume_suggestions:
        for index, suggestion in enumerate(
            result.resume_suggestions, start=1
        ):
            st.subheader(f"Suggestion {index}")

            st.write("**Original:**")
            st.write(suggestion.original_text)

            st.write("**Suggested:**")
            st.write(suggestion.suggested_text)
    else:
        st.info("No resume improvements were suggested.")

    st.divider()

    # Display tailored practice interview questions.
    st.header("Practice Interview Questions")

    if result.interview_questions:
        for index, question in enumerate(
            result.interview_questions, start=1
        ):
            st.write(f"**{index}.** {question}")
    else:
        st.info("No interview questions were generated.")

    st.divider()

    # Allow users to download the structured response.
    st.download_button(
        label="Download Analysis (JSON)",
        data=result.model_dump_json(indent=2),
        file_name="fitcheck_analysis.json",
        mime="application/json"
    )


# Display a reminder about reviewing AI-generated content.
st.divider()

st.caption(
    "FitCheck AI generates suggestions using artificial intelligence. "
    "Always review recommendations for accuracy before using them "
    "in a job application."
)
