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
    if "auth_mode" not in st.session_state:
        st.session_state["auth_mode"] = "Login"  # default mode

    # -- Mode toggle buttons
    st.subheader("🔐 Unlock Your Career Advisor")
    st.caption("Log in or sign up to access personalized AI-powered career guidance.")
    col1, col2 = st.columns(2)
    with col1:
        if st.button("Sign In", use_container_width=True):
            st.session_state["auth_mode"] = "Login"
    with col2:
        if st.button("Create Account", use_container_width=True):
            st.session_state["auth_mode"] = "Sign Up"

    # -- Container for both forms (only one is visible)
    with st.form("auth_form", border=True):
        mode = st.session_state["auth_mode"]
        st.markdown(f"**{mode}** to continue")

        email = st.text_input("Email", key=f"email_{mode}")
        pwd = st.text_input("Password", type="password", key=f"pwd_{mode}")

        submitted = st.form_submit_button("Continue")
        if submitted and email and pwd:
            ok, msg = auth_with_supabase(email, pwd, signup=(mode == "Sign Up"))
            if ok and mode == "Login":
                st.session_state.token = msg
                st.session_state.token_time = datetime.now()
                st.success("Logged in successfully! Taking you to your dashboard...")
                st.rerun()
            elif ok:
                st.success("🎉 Account created! Please check your email to verify and then log in.")
            else:
                # Triangulate common errors
                if "invalid login" in msg.lower() or "user not found" in msg.lower():
                    st.error("Email not found. New here? Try creating an account.")
                elif "password" in msg.lower():
                    st.error("Incorrect password. Please try again or click 'Forgot Password?' if available.")
                elif "already registered" in msg.lower():
                    st.error("Welcome back! An account with this email already exists. Please sign in.")
                else:
                    st.error(f"⚠️ {mode} failed. Error: {msg}")
    st.stop()

# ----------------------------------------------------------------
# 4. ‑‑‑‑ Sidebar (logout)
# ----------------------------------------------------------------
st.sidebar.success("You're logged in!")
if st.sidebar.button("Logout"):
    st.session_state.clear()
    st.rerun()

# ----------------------------------------------------------------
# 5. ‑‑‑‑ Resume upload with safety checks
# ----------------------------------------------------------------
st.header("Upload Your Resume (PDF)")
uploaded_file = st.file_uploader("Select Your PDF Resume", type=["pdf"], help="Max file size: 5MB. Ensure it's a PDF for best results.")
st.caption("Tip: Uploading a new resume replaces the current one. You can always update it here.")

if "resume_uploaded_name" in st.session_state:
    st.info(f"Current resume on file: **{st.session_state['resume_uploaded_name']}**")

def is_pdf(file: io.BytesIO) -> bool:
    mime, _ = mimetypes.guess_type(uploaded_file.name)
    return mime == "application/pdf"

if uploaded_file:
    if uploaded_file.size > MAX_FILE_SIZE:
        st.error("⚠️ File exceeds 5MB limit. Please upload a smaller PDF.")
    elif not is_pdf(uploaded_file):
        st.error("⚠️ Oops! This doesn't seem to be a PDF. Please upload a valid PDF file.")
    else:
        with st.spinner("🚀 Uploading & analyzing your resume..."):
            resp = call_backend(
                "resume/upload",
                files={"file": (uploaded_file.name, uploaded_file.read(), "application/pdf")},
            )
            if resp:
                st.session_state["resume_uploaded_name"] = uploaded_file.name
                st.success("Resume uploaded! You're all set to explore the features below.")

# ----------------------------------------------------------------
# 6. ‑‑‑‑ Feature menu
# ----------------------------------------------------------------
st.header("✨ Explore Our AI Services")
st.caption("Pick a service to get started. Our AI will provide personalized insights based on your resume.")

tab_titles = ["🧭 Career Path Finder", "📝 Resume Reviewer", "💬 Mock Interview Practice"]
tab1, tab2, tab3 = st.tabs(tab_titles)

# 6‑A  •  Career paths ---------------------------------------------------------
with tab1:
    if st.button("🔍 Discover Career Paths"):
        with st.spinner("🧠 Analyzing possibilities with Groq AI..."):
            data = call_backend("career/recommend")
            if data:
                st.session_state["career_suggestions"] = data["recommendations"]

    if suggestions := st.session_state.get("career_suggestions"):
        st.subheader("🎯 Your AI-Powered Career Roadmap")
        st.markdown(suggestions)

# 6‑B  •  Resume feedback ------------------------------------------------------
with tab2:
    if st.button("🛠 Improve Your Resume"):
        with st.spinner("🔎 Reviewing your resume line by line..."):
            data = call_backend("resume_feedback/feedback")
            if data:
                st.session_state["resume_feedback"] = data["feedback"]

    if feedback := st.session_state.get("resume_feedback"):
        st.subheader("📝 Detailed Resume Analysis")
        st.markdown(feedback)

# 6‑C  •  Mock interview -------------------------------------------------------
with tab3:
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
        if st.button("📊 Submit for critique") and answer.strip():
            data = call_backend(
                "interview/critique",
                json={"question": q, "answer": answer},
            )
            if data:
                st.subheader("📝 AI Feedback")
                st.markdown(data["critique"])
                st.success(f"Score: {data['score']} / 10")