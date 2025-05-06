import streamlit as st
import requests
import os

# --- Config ---
API_BASE = "http://localhost:8000"
SUPABASE_URL = os.getenv("SUPABASE_URL")
SUPABASE_KEY = os.getenv("SUPABASE_KEY")

st.set_page_config(page_title="Generative AI Job Advisor", layout="centered")
st.title("🧠 Generative AI Job Advisor")

# --- Supabase Auth Logic ---
def supabase_login(email, password):
    url = f"{SUPABASE_URL}/auth/v1/token?grant_type=password"
    headers = {"apikey": SUPABASE_KEY, "Content-Type": "application/json"}
    data = {"email": email, "password": password}
    return requests.post(url, headers=headers, json=data)

def supabase_signup(email, password):
    url = f"{SUPABASE_URL}/auth/v1/signup"
    headers = {"apikey": SUPABASE_KEY, "Content-Type": "application/json"}
    data = {"email": email, "password": password}
    return requests.post(url, headers=headers, json=data)

# --- Login/Signup UI ---
if "user" not in st.session_state:
    st.subheader("🔐 Access Your Advisor")

    auth_mode = st.radio("Choose mode", ["Login", "Sign Up"], horizontal=True)
    email = st.text_input("Email")
    password = st.text_input("Password", type="password")

    if st.button("Submit"):
        with st.spinner("Authenticating..."):
            if auth_mode == "Login":
                res = supabase_login(email, password)
            else:
                # Step 1: Sign up
                res = supabase_signup(email, password)

                if res.status_code == 200:
                    st.success("Sign-up successful! Please check your email and verify your address before logging in.")
                    st.stop()

            if res.status_code == 200:
                data = res.json()
                st.session_state.user = data.get("user", {})
                st.session_state.token = data.get("access_token")
                st.success(f"{auth_mode} successful! Logged in.")
                st.rerun()
            else:
                st.error(f"{auth_mode} failed: {res.text}")
    st.stop()

# --- Sidebar Info ---
st.sidebar.success(f"Logged in as {st.session_state.user['email']}")
if st.sidebar.button("Logout"):
    st.session_state.clear()
    st.rerun()

# --- Auth Headers ---
headers = {
    "Authorization": f"Bearer {st.session_state.token}"
}

# --- Upload Resume ---
st.header("Step 1: Upload Your Resume (PDF)")
uploaded_file = st.file_uploader("Choose a resume PDF", type=["pdf"])
st.caption("Note: Uploading a new resume will overwrite your previous one.")

if uploaded_file:
    with st.spinner("Uploading and parsing resume..."):
        response = requests.post(
            f"{API_BASE}/resume/upload",
            files={"file": (uploaded_file.name, uploaded_file.read())},
            headers=headers
        )
        if response.ok:
            st.success("Resume uploaded successfully! This will replace your previous one.")
        else:
            st.error("Upload failed: " + response.text)

# --- Feature Menu ---
if st.session_state.user:
    st.header("Step 2: Choose a Service")
    choice = st.radio("What would you like help with?", [
        "Career Path Recommendation",
        "Resume Feedback",
        "Mock Interview Q&A"
    ])

    if choice == "Career Path Recommendation":
        if st.button("🔍 Get Career Suggestions"):
            with st.spinner("Consulting Groq AI..."):
                response = requests.post(f"{API_BASE}/career/recommend", headers=headers)
                if response.ok:
                    suggestions = response.json()["recommendations"]
                    st.subheader("🎯 AI Suggested Career Paths:")
                    for line in suggestions.split("\n"):
                        if line.strip():
                            st.markdown(f"{line.strip()}")
                else:
                    try:
                        error_message = response.json().get("error")
                        if error_message:
                            st.error("Error: " + error_message)
                        else:
                            st.error("Unexpected error: " + response.text)
                    except Exception:
                        st.error("Error: " + response.text)

    elif choice == "Resume Feedback":
        if st.button("🛠 Get Resume Feedback"):
            with st.spinner("Reviewing your resume..."):
                response = requests.post(f"{API_BASE}/resume/feedback", headers=headers)
                if response.ok:
                    feedback = response.json()["feedback"]
                    st.subheader("📝 Line-by-Line Feedback:")
                    st.markdown(feedback)
                else:
                    try:
                        error_message = response.json().get("error")
                        if error_message:
                            st.error("Error: " + error_message)
                        else:
                            st.error("Unexpected error: " + response.text)
                    except Exception:
                        st.error("Error: " + response.text)

    elif choice == "Mock Interview Q&A":
        job_title = st.text_input("Enter a target role (e.g. Data Scientist)")

        if st.button("🎤 Generate Question") and job_title:
            response = requests.post(
                f"{API_BASE}/interview/question",
                params={"job_title": job_title},
                headers=headers
            )
            if response.ok:
                question = response.json()["question"]
                st.session_state["interview_q"] = question
                st.markdown(f"**🗨️ Interview Question:** {question}")
            else:
                st.error("Failed to generate question.")

        if "interview_q" in st.session_state:
            answer = st.text_area("Your Answer")

            if st.button("📊 Submit for Critique") and answer:
                response = requests.post(
                    f"{API_BASE}/interview/critique",
                    json={"question": st.session_state["interview_q"], "answer": answer},
                    headers=headers
                )
                if response.ok:
                    result = response.json()
                    st.subheader("📝 AI Feedback")
                    st.markdown(result["critique"])
                    st.success(f"Score: {result['score']} / 10")
                else:
                    st.error("Failed to evaluate answer.")
