from __future__ import annotations

import io
import mimetypes
from datetime import datetime, timedelta

import requests
import streamlit as st
from supabase import create_client, Client
# --- Config ---
from config import API_BASE, SUPABASE_URL, SUPABASE_KEY

MAX_FILE_SIZE = 5 * 1024 * 1024                      # 5 MB

# ── Supabase client (official SDK) ───────────────────────────────
supabase: Client = create_client(SUPABASE_URL, SUPABASE_KEY)

# ── Streamlit page setup ─────────────────────────────────────────
st.set_page_config(page_title="Generative AI Job Advisor", layout="centered")
st.title("🧠 Generative AI Job Advisor")
# ----------------------------------------------------------------
# 1. ‑‑‑‑ Authentication helpers
# ----------------------------------------------------------------

def auth_with_supabase(email: str, password: str, signup: bool) -> tuple[bool, str | None]:
    """
    Returns (success, message_or_token)
    """
    try:
        if signup:
            data = supabase.auth.sign_up({"email": email, "password": password})
            return True, "Sign‑up successful! Verify your email before login."
        else:
            data = supabase.auth.sign_in_with_password({"email": email, "password": password})
            return True, data.session.access_token
    except Exception as exc:
        return False, str(exc)

def refresh_token_if_needed() -> None:
    """
    Refreshes the token when it's about to expire (±55 min).
    Stores new token back into session state.
    """
    if "token_time" not in st.session_state:
        return
    if datetime.now() - st.session_state.token_time < timedelta(minutes=55):
        return

    try:
        new_session = supabase.auth.refresh_session(st.session_state.refresh_token)
        st.session_state.token = new_session.access_token
        st.session_state.refresh_token = new_session.refresh_token
        st.session_state.token_time = datetime.now()
    except Exception:
        st.warning("⚠️ Session expired, please log in again.")
        st.session_state.clear()
        st.rerun()

# ----------------------------------------------------------------
# 2. ‑‑‑‑ Thin wrapper around your FastAPI service
# ----------------------------------------------------------------
def call_backend(path: str, method: str = "POST", **kwargs):
    """
    Centralized HTTP helper: raises for network errors, returns JSON.
    """
    refresh_token_if_needed()
    headers = {"Authorization": f"Bearer {st.session_state.token}"}
    url = f"{API_BASE}/{path.lstrip('/')}"
    try:
        fn = requests.post if method.upper() == "POST" else requests.get
        res = fn(url, headers=headers, timeout=15, **kwargs)
        res.raise_for_status()
        return res.json()
    except requests.exceptions.RequestException as e:
        st.error(f"🌐 Network error: {e}")
        return None

# ----------------------------------------------------------------
# 3. ‑‑‑‑ Login / Sign‑up UI (form = atomic submit)
# ----------------------------------------------------------------
if "token" not in st.session_state:
    with st.form("auth_form"):
        st.subheader("🔐 Access Your Advisor")
        st.caption("Sign up or log in to access personalized career services.")
        auth_mode = st.radio("Choose mode", ["Login", "Sign Up"], horizontal=True, help="Select 'Sign Up' if you don't have an account.")
        email = st.text_input("Email", help="Enter your email address.")
        pwd = st.text_input("Password", type="password", help="Enter your password.")
        submitted = st.form_submit_button("Submit")
        if submitted and email and pwd:
            ok, msg = auth_with_supabase(email, pwd, signup=(auth_mode == "Sign Up"))
            if ok and auth_mode == "Login":
                st.session_state.token = msg
                st.session_state.token_time = datetime.now()
                st.success("Logged in! Redirecting to dashboard...")
                st.rerun()
            elif ok:
                st.success(msg)
            else:
                st.error(f"{auth_mode} failed: {msg}. Please check your credentials or try again.")
    st.stop()

# ----------------------------------------------------------------
# 4. ‑‑‑‑ Sidebar (logout)
# ----------------------------------------------------------------
st.sidebar.success("Logged in")
if st.sidebar.button("Logout"):
    st.session_state.clear()
    st.rerun()

# ----------------------------------------------------------------
# 5. ‑‑‑‑ Resume upload with safety checks
# ----------------------------------------------------------------
st.header("Upload Your Resume (PDF)")
uploaded_file = st.file_uploader("Choose your PDF", type=["pdf"], help="Only PDF files up to 5MB are accepted.")
st.caption("Uploading a new resume will overwrite your previous one. You can view or replace your current resume below.")

if "resume_uploaded_name" in st.session_state:
    st.info(f"Current resume: {st.session_state['resume_uploaded_name']}")

def is_pdf(file: io.BytesIO) -> bool:
    mime, _ = mimetypes.guess_type(uploaded_file.name)
    return mime == "application/pdf"

if uploaded_file:
    if uploaded_file.size > MAX_FILE_SIZE:
        st.error("File too large (> 5 MB).")
    elif not is_pdf(uploaded_file):
        st.error("File doesn’t look like a PDF.")
    else:
        with st.spinner("Uploading & parsing…"):
            resp = call_backend(
                "resume/upload",
                files={"file": (uploaded_file.name, uploaded_file.read(), "application/pdf")},
            )
            if resp:
                st.session_state["resume_uploaded_name"] = uploaded_file.name
                st.success("Resume uploaded successfully! You can now proceed to the next step.")

# ----------------------------------------------------------------
# 6. ‑‑‑‑ Feature menu
# ----------------------------------------------------------------
st.header("Choose a Service")
st.caption("Select a service below and follow the prompts. Each service provides tailored guidance.")
choice = st.radio(
    "How can I help?",
    ["Career Path Recommendation", "Resume Feedback", "Mock Interview Q&A"],
    help="Pick a service to get started."
)

# 6‑A  •  Career paths ---------------------------------------------------------
if choice == "Career Path Recommendation":
    if st.button("🔍 Get Career Suggestions", help="Get AI-powered recommendations based on your resume."):
        with st.spinner("Consulting Groq AI…"):
            data = call_backend("career/recommend")
            if data:
                st.session_state["career_suggestions"] = data["recommendations"]

    if suggestions := st.session_state.get("career_suggestions"):
        st.subheader("🎯 AI‑suggested career paths")
        st.markdown(suggestions)

# 6‑B  •  Resume feedback ------------------------------------------------------
elif choice == "Resume Feedback":
    if st.button("🛠 Get Resume Feedback", help="Receive detailed, line-by-line feedback on your uploaded resume."):
        with st.spinner("Reviewing your resume…"):
            data = call_backend("resume_feedback/feedback")
            if data:
                st.session_state["resume_feedback"] = data["feedback"]

    if feedback := st.session_state.get("resume_feedback"):
        st.subheader("📝 Line‑by‑line feedback")
        st.markdown(feedback)

# 6‑C  •  Mock interview -------------------------------------------------------
else:
    st.subheader("🎤 Practice an Interview")
    job_title = st.text_input("Target role (e.g. Data Scientist)", help="Specify the job title you want to practice for.")
    if st.button("🎤 Generate Question", help="Get a realistic interview question for your chosen role.") and job_title.strip():
        data = call_backend("interview/question", method="GET", params={"job_title": job_title})
        if data:
            st.session_state["interview_q"] = data["question"]
            st.session_state["interview_a"] = ""

    if q := st.session_state.get("interview_q"):
        st.markdown(f"**🗨️ Interview Question:** {q}")
        answer = st.text_area("Your answer", value=st.session_state.get("interview_a", ""), help="Type your answer here for AI critique.")
        st.session_state["interview_a"] = answer
        if st.button("📊 Submit for critique", help="Get instant feedback and a score on your answer.") and answer.strip():
            data = call_backend(
                "interview/critique",
                json={"question": q, "answer": answer},
            )
            if data:
                st.subheader("📝 AI Feedback")
                st.markdown(data["critique"])
                st.success(f"Score: {data['score']} / 10")