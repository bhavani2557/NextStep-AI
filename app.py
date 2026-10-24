import os
import json
import requests
import streamlit as st
from dotenv import load_dotenv
from pypdf import PdfReader
from services.recommender import recommend, get_careers
from services.guidance import answer
from services.database import save_profile, save_chat

load_dotenv()
st.set_page_config(page_title="CareerGuide AI", page_icon="🎯", layout="wide", initial_sidebar_state="expanded")

st.markdown("""
<style>
.block-container {padding-top: 1.8rem; padding-bottom: 2rem; max-width: 1250px;}
[data-testid="stSidebar"] {background: #101d38;}
[data-testid="stSidebar"] * {color: #f4f7ff;}
.hero {padding: 1.5rem 1.7rem; border-radius: 18px; background: linear-gradient(115deg,#142b50,#2463a8); color: white; margin-bottom: 1.1rem;}
.hero h1 {margin-bottom: .35rem; color: white;} .hero p {color:#e5efff; margin-bottom:0;}
.small-muted {color: #64748b; font-size:.9rem;}
</style>
""", unsafe_allow_html=True)

if "profile" not in st.session_state:
    st.session_state.profile = None
if "recommendations" not in st.session_state:
    st.session_state.recommendations = []
if "messages" not in st.session_state:
    st.session_state.messages = []

with st.sidebar:
    st.markdown("# 🎯 CareerGuide AI")
    st.caption("Your personalized career companion")
    page = st.radio("Navigate", ["Dashboard", "My Profile", "Recommendations", "Skill Gap & Roadmap", "Jobs & Internships", "Career Chatbot", "Resume Analysis"], label_visibility="collapsed")
    st.divider()
    st.caption("AI + ML career guidance demo")


def profile_form():
    old = st.session_state.profile or {}
    with st.form("profile_form"):
        name = st.text_input("Your name", old.get("name", "Student"))
        c1, c2 = st.columns(2)
        with c1:
            education = st.selectbox("Education", ["B.Tech", "B.E.", "BCA", "MCA", "B.Sc.", "BBA", "B.Com", "M.Tech", "Other"], index=["B.Tech", "B.E.", "BCA", "MCA", "B.Sc.", "BBA", "B.Com", "M.Tech", "Other"].index(old.get("education", "B.Tech")) if old.get("education", "B.Tech") in ["B.Tech", "B.E.", "BCA", "MCA", "B.Sc.", "BBA", "B.Com", "M.Tech", "Other"] else 0)
            degree = st.text_input("Branch / degree", old.get("degree", "Computer Science"))
            experience = st.selectbox("Experience level", ["Beginner", "Student projects", "Internship experience", "Experienced"], index=["Beginner", "Student projects", "Internship experience", "Experienced"].index(old.get("experience", "Beginner")) if old.get("experience", "Beginner") in ["Beginner", "Student projects", "Internship experience", "Experienced"] else 0)
        with c2:
            skill_options = ["Python", "Java", "C/C++", "Data Structures", "SQL", "Excel", "Statistics", "Data Visualization", "Machine Learning", "Pandas", "NumPy", "Networking", "Linux", "Security Fundamentals", "Git", "Docker", "CI/CD", "Cloud Fundamentals", "Figma", "Wireframing", "Prototyping", "User Research", "Communication", "Problem Solving", "Requirements Analysis"]
            skills = st.multiselect("Skills you currently have", skill_options, default=[x for x in old.get("skills", []) if x in skill_options])
            interest_options = ["software development", "problem solving", "building applications", "data", "analytics", "statistics", "artificial intelligence", "machine learning", "cybersecurity", "networks", "automation", "cloud", "deployment", "design", "creativity", "user experience", "business", "research", "product strategy"]
            interests = st.multiselect("Interests", interest_options, default=[x for x in old.get("interests", []) if x in interest_options])
        goal = st.text_area("Career goal", old.get("goal", "Find a suitable entry-level role and internship"), placeholder="Example: I want to become a software developer and build projects.")
        submitted = st.form_submit_button("Save profile & generate recommendations", type="primary", use_container_width=True)
    if submitted:
        profile = {"name": name.strip() or "Student", "education": education, "degree": degree.strip(), "experience": experience, "skills": skills, "interests": interests, "goal": goal.strip()}
        st.session_state.profile = profile
        st.session_state.recommendations = recommend(profile)
        result = save_profile(profile)
        st.success("Profile saved for this session. " + result.get("message", ""))
        st.rerun()


def show_recommendations():
    if not st.session_state.profile:
        st.info("Complete **My Profile** first to receive personalized recommendations.")
        return
    results = st.session_state.recommendations or recommend(st.session_state.profile)
    if not results:
        st.warning("Add some skills, interests, or a career goal in My Profile.")
        return
    st.caption("Match percentages are similarity scores from the demo's TF-IDF model, not a guarantee of job suitability.")
    for i, career in enumerate(results, 1):
        with st.container(border=True):
            left, right = st.columns([4, 1])
            with left:
                st.subheader(f"{i}. {career['title']}")
                st.write(career["description"])
                st.write("**Core skills:** " + ", ".join(career["skills"]))
                if career.get("matched_skills"):
                    st.write("**Skills you already have:** " + ", ".join(career["matched_skills"]))
            with right:
                st.metric("Profile similarity", f"{career['match_score']}%")
                if st.button("View roadmap", key=f"roadmap_{i}"):
                    st.session_state.selected_career = career["title"]
                    st.session_state["jump_to_roadmap"] = True
            st.progress(min(max(career["match_score"] / 100, 0.0), 1.0))

if page == "Dashboard":
    p = st.session_state.profile
    st.markdown('<div class="hero"><h1>Find a career path that fits you.</h1><p>Understand your strengths, discover possible roles, and turn skill gaps into a practical learning plan.</p></div>', unsafe_allow_html=True)
    if p:
        st.subheader(f"Welcome back, {p.get('name', 'Student')} 👋")
        a,b,c,d = st.columns(4)
        a.metric("Career matches", len(st.session_state.recommendations))
        b.metric("Skills entered", len(p.get("skills", [])))
        c.metric("Interests selected", len(p.get("interests", [])))
        d.metric("Experience", p.get("experience", "Beginner"))
        st.subheader("Your top career matches")
        show_recommendations()
    else:
        st.write("### Get started in three steps")
        a,b,c = st.columns(3)
        a.markdown("**1. Build your profile**\n\nAdd your education, skills, interests, experience, and goal.")
        b.markdown("**2. Explore career matches**\n\nSee roles ranked using a machine-learning similarity model.")
        c.markdown("**3. Follow a roadmap**\n\nFind skill gaps, projects, learning topics, and entry-level role ideas.")
        if st.button("Create my profile", type="primary"):
            st.session_state.page_hint = "My Profile"
            st.info("Choose **My Profile** from the sidebar to begin.")
    st.divider()
    st.caption("Prototype notice: sample career catalogue and sample role suggestions are included. Job and internship listings are not live feeds.")

elif page == "My Profile":
    st.title("👤 My Profile")
    st.write("Your profile powers recommendations, skill-gap analysis, and personalized chat responses.")
    profile_form()
    if st.session_state.profile:
        with st.expander("Current profile data"):
            st.json(st.session_state.profile)

elif page == "Recommendations":
    st.title("🧭 Career Recommendations")
    show_recommendations()

elif page == "Skill Gap & Roadmap":
    st.title("🗺️ Skill Gap Analysis & Learning Roadmap")
    p = st.session_state.profile
    results = st.session_state.recommendations or (recommend(p) if p else [])
    if not p or not results:
        st.info("Create your profile first.")
    else:
        choices = [c["title"] for c in results]
        default = st.session_state.get("selected_career", choices[0])
        selected = st.selectbox("Choose a career path", choices, index=choices.index(default) if default in choices else 0)
        career = next(c for c in results if c["title"] == selected)
        st.write(career["description"])
        have, need = st.columns(2)
        with have:
            st.markdown("#### ✅ Skills you have")
            if career["matched_skills"]:
                for s in career["matched_skills"]: st.write(f"- {s}")
            else: st.write("No listed core skills matched yet. This is a starting point, not a judgement of your ability.")
        with need:
            st.markdown("#### 🎯 Skills to develop")
            for s in career["skill_gaps"]: st.write(f"- {s}")
        st.divider()
        st.subheader("Suggested learning roadmap")
        stages = [("Stage 1 · Foundations", career["courses"][:2]), ("Stage 2 · Practice", career["projects"][:2]), ("Stage 3 · Portfolio", career["projects"][2:]), ("Stage 4 · Apply", ["Prepare a role-specific resume", "Practice interview questions", "Check official company career pages for current openings"])]
        for title, items in stages:
            with st.container(border=True):
                st.markdown(f"**{title}**")
                for item in items: st.write(f"- {item}")
        st.download_button("Download roadmap as JSON", json.dumps({"career": career, "roadmap": stages}, indent=2), file_name="career_roadmap.json", mime="application/json")

elif page == "Jobs & Internships":
    st.title("💼 Job & Internship Suggestions")
    st.warning("This starter version provides relevant role titles, not verified live vacancies. Always check official employer pages for current openings and deadlines.")
    p = st.session_state.profile
    results = st.session_state.recommendations or (recommend(p) if p else [])
    if not results:
        st.info("Create your profile first.")
    else:
        for career in results[:5]:
            with st.container(border=True):
                st.subheader(career["title"])
                st.write("**Suggested entry-level roles:** " + ", ".join(career["roles"]))
                st.write("**Portfolio ideas:** " + "; ".join(career["projects"]))
                st.link_button("Search roles on LinkedIn", "https://www.linkedin.com/jobs/")
                st.link_button("Search internships on Internshala", "https://internshala.com/internships/")

elif page == "Career Chatbot":
    st.title("💬 Career Guidance Assistant")
    st.write("Ask about career options, learning order, projects, interviews, or skill development.")
    for m in st.session_state.messages:
        with st.chat_message(m["role"]): st.markdown(m["content"])
    prompt = st.chat_input("What would you like guidance on?")
    if prompt:
        st.session_state.messages.append({"role":"user", "content":prompt})
        with st.chat_message("user"): st.markdown(prompt)
        with st.chat_message("assistant"):
            with st.spinner("Thinking..."):
                reply = answer(prompt, st.session_state.profile)
                st.markdown(reply)
        st.session_state.messages.append({"role":"assistant", "content":reply})
        save_chat(prompt, reply)
        st.rerun()

elif page == "Resume Analysis":
    st.title("📄 Resume Analysis")
    st.write("Upload a PDF resume to extract text and compare mentioned skills with the career catalogue. Text extraction is local to this app session.")
    uploaded = st.file_uploader("Upload resume (PDF)", type=["pdf"])
    if uploaded:
        try:
            reader = PdfReader(uploaded)
            text = "\n".join(page.extract_text() or "" for page in reader.pages)
            if not text.strip():
                st.warning("No selectable text found. The PDF may be scanned; OCR is not included in this starter version.")
            else:
                st.subheader("Extracted resume text")
                st.text_area("Review extracted text", text, height=220)
                catalogue_skills = sorted({s for c in get_careers() for s in c["skills"]}, key=str.lower)
                text_lower = text.lower()
                found = [s for s in catalogue_skills if s.lower() in text_lower]
                missing = [s for s in catalogue_skills if s.lower() not in text_lower]
                st.subheader("Skills detected")
                st.write(", ".join(found) if found else "No catalogue skills detected by exact keyword matching.")
                st.subheader("Other skills to consider (catalogue-wide)")
                st.write(", ".join(missing[:15]) if missing else "All catalogue skills were detected.")
                st.caption("This is keyword matching, not a professional resume score. Review results for context and accuracy.")
        except Exception as e:
            st.error(f"Could not read this PDF: {type(e).__name__}")
