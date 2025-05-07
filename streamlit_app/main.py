# streamlit_app.py
from __future__ import annotations

import hashlib
import io
import mimetypes
import time
from datetime import datetime, timedelta

import requests
import streamlit as st
from supabase import create_client, Client

# ════════════════ 1.  CONFIG  ══════════════════
from config import API_BASE, SUPABASE_URL, SUPABASE_KEY

MAX_FILE_SIZE = 5 * 1024 * 1024  # 5 MB

supabase: Client = create_client(SUPABASE_URL, SUPABASE_KEY)

st.set_page_config(page_title="Generative AI Job Advisor", layout="centered")
st.title("🧠 Generative AI Job Advisor")

# ════════════════ 2.  AUTH HELPERS ═════════════
def auth_with_supabase(email: str, password: str, signup: bool) -> tuple[bool, str | None]:
    try:
        if signup:
            supabase.auth.sign_up({"email": email, "password": password})
            return True, "Sign‑up successful! Verify your email before login."
        else:
            data = supabase.auth.sign_in_with_password({"email": email, "password": password})
            return True, data.session.access_token
    except Exception as exc:
        return False, str(exc)

def refresh_token_if_needed() -> None:
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

# ════════════════ 3.  BACKEND CALL WRAPPER ═════
def call_backend(path: str, method: str = "POST", **kwargs):
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

# ════════════════ 4.  LOGIN  ═══════════════════
if "token" not in st.session_state:
    if "auth_mode" not in st.session_state:
        st.session_state["auth_mode"] = "Login"

    st.subheader("🔐 Unlock Your Career Advisor")
    st.caption("Log in or sign up to access personalized AI‑powered career guidance.")
    col1, col2 = st.columns(2)
    with col1:
        if st.button("Sign In", use_container_width=True):
            st.session_state["auth_mode"] = "Login"
    with col2:
        if st.button("Create Account", use_container_width=True):
            st.session_state["auth_mode"] = "Sign Up"

    with st.form("auth_form", border=True):
        mode = st.session_state["auth_mode"]
        st.markdown(f"**{mode}** to continue")

        email = st.text_input("Email", key="email")
        pwd = st.text_input("Password", type="password", key="pwd")

        submitted = st.form_submit_button("Continue")
        if submitted and email and pwd:
            ok, msg = auth_with_supabase(email, pwd, signup=(mode == "Sign Up"))
            if ok and mode == "Login":
                st.session_state.token = msg
                st.session_state.token_time = datetime.now()
                st.toast("Logged in successfully! Taking you to your dashboard...")
                st.rerun()
            elif ok:
                st.toast("🎉 Account created! Please check your email to verify and then log in.")
            else:
                if "invalid login" in msg.lower() or "user not found" in msg.lower():
                    st.error("Email not found. New here? Try creating an account.")
                elif "password" in msg.lower():
                    st.error("Incorrect password. Please try again or click 'Forgot Password?' if available.")
                elif "already registered" in msg.lower():
                    st.error("Welcome back! An account with this email already exists. Please sign in.")
                else:
                    st.error(f"⚠️ {mode} failed. Error: {msg}")
    st.stop()

# ════════════════ 5.  LOGOUT (SIDEBAR) ═════════
st.sidebar.success("You're logged in!")
if st.sidebar.button("Logout"):
    st.session_state.clear()
    st.rerun()

# ════════════════ 6.  RESUME HELPERS ═══════════
def get_checksum(b: bytes) -> str:
    return hashlib.sha256(b).hexdigest()

def parse_and_upload(file_bytes: bytes, filename: str):
    """One‑shot heavy call – used only inside the callback."""
    with st.spinner("🚀 Uploading & analysing your resume…"):
        resp = call_backend(
            "resume/upload",
            files={"file": (filename, file_bytes, "application/pdf")},
        )
    return resp

# ════════════════ 7.  CALLBACK  ════════════════
def handle_resume_upload():
    file: io.BytesIO | None = st.session_state["resume_file"]
    if file is None:
        return

    # --- safety checks ---
    if file.size > MAX_FILE_SIZE:
        st.error("⚠️ File exceeds 5 MB limit.")
        st.session_state["resume_file"] = None
        return
    if mimetypes.guess_type(file.name)[0] != "application/pdf":
        st.error("⚠️ Please upload a PDF.")
        st.session_state["resume_file"] = None
        return

    bytes_data = file.read()
    checksum = get_checksum(bytes_data)

    # --- only parse NEW files ---
    if checksum != st.session_state.get("resume_checksum"):
        st.session_state["resume_checksum"] = checksum
        st.session_state["resume_data"] = parse_and_upload(bytes_data, file.name)
        st.session_state["resume_uploaded_name"] = file.name
        st.toast("Resume uploaded & parsed! 🎉")

# ════════════════ 8.  RESUME UPLOAD WIDGET ═════
st.header("Upload Your Resume (PDF)")
st.file_uploader(
    "Select PDF (max 5 MB)",
    type=["pdf"],
    key="resume_file",
    help="Max file size: 5 MB. Uploading a new file replaces the current one.",
    on_change=handle_resume_upload,
)

if "resume_uploaded_name" in st.session_state:
    st.info(f"Current resume on file: **{st.session_state['resume_uploaded_name']}**")

# ════════════════ 9.  FEATURE MENU ═════════════
st.header("✨ Explore Our AI Services")
st.caption("Pick a service to get started. Our AI will provide personalized insights based on your resume.")

tab_titles = ["🧭 Career Path Finder", "📝 Resume Reviewer", "💬 Mock Interview Practice"]
tab1, tab2, tab3 = st.tabs(tab_titles)

# ---- 9‑A Career paths ----
with tab1:
    if st.button("🔍 Discover Career Paths"):
        if "resume_data" not in st.session_state:
            st.warning("Upload a resume first! ☝️")
        else:
            progress = st.progress(0, text="🧠 Analyzing possibilities with Groq AI...")
            for i in range(3):
                time.sleep(0.35)
                progress.progress((i + 1) / 3)
            data = call_backend(
                "career/recommend",
                json={"parsed_resume": st.session_state["resume_data"]},
            )
            progress.empty()
            if data:
                st.session_state["career_suggestions"] = data["recommendations"]

    if suggestions := st.session_state.get("career_suggestions"):
        st.subheader("🎯 Your AI‑Powered Career Roadmap")
        st.markdown(suggestions)

# ---- 9‑B Resume feedback ----
with tab2:
    if st.button("🛠 Improve Your Resume"):
        if "resume_data" not in st.session_state:
            st.warning("Upload a resume first! ☝️")
        else:
            progress = st.progress(0, text="🔎 Reviewing your resume line by line...")
            for i in range(3):
                time.sleep(0.35)
                progress.progress((i + 1) / 3)
            data = call_backend(
                "resume_feedback/feedback",
                json={"parsed_resume": st.session_state["resume_data"]},
            )
            progress.empty()
            if data:
                st.session_state["resume_feedback"] = data["feedback"]

    if feedback := st.session_state.get("resume_feedback"):
        st.subheader("📝 Detailed Resume Analysis")
        st.markdown(feedback)

# ---- 9‑C Mock interview ----
with tab3:
    st.subheader("🎤 Practice an Interview")
    job_title = st.text_input("Target role (e.g. Data Scientist)")
    if st.button("🎤 Generate Question") and job_title.strip():
        data = call_backend(
            "interview/question",
            method="GET",
            params={"job_title": job_title},
        )
        if data:
            st.session_state["interview_q"] = data["question"]
            st.session_state["interview_a"] = ""

    if q := st.session_state.get("interview_q"):
        st.markdown(f"**🗨️ Interview Question:** {q}")
        answer = st.text_area("Your answer", value=st.session_state.get("interview_a", ""))
        st.session_state["interview_a"] = answer
        if st.button("📊 Submit for critique") and answer.strip():
            progress = st.progress(0, text="🧠 Reviewing your answer...")
            for i in range(3):
                time.sleep(0.35)
                progress.progress((i + 1) / 3)
            data = call_backend(
                "interview/critique",
                json={"question": q, "answer": answer},
            )
            progress.empty()
            if data:
                st.subheader("📝 AI Feedback")
                st.markdown(data["critique"])
                st.success(f"Score: {data['score']} / 10")
