import os
import json
import secrets
import requests
import streamlit as st
from dotenv import load_dotenv
from pypdf import PdfReader
from services.recommender import recommend, get_careers
from services.guidance import answer
from services.database import save_profile, load_profile, save_chat

load_dotenv()
st.set_page_config(page_title="NextStep AI", page_icon="↗️", layout="wide", initial_sidebar_state="expanded")

# Keep a random profile ID in the URL so the same browser link can restore its profile.
# Treat this link like a private link: anyone who has it can access that profile.
if "profile_id" not in st.session_state:
    profile_id = st.query_params.get("pid", "")
    if not profile_id:
        profile_id = secrets.token_urlsafe(32)
        st.query_params["pid"] = profile_id
    st.session_state.profile_id = profile_id

if "theme_mode" not in st.session_state:
    st.session_state.theme_mode = "Light"

st.markdown("""
<style>
:root { color-scheme: dark; }
.stApp { background: #0b1220; color: #e6edf7; }
.block-container { padding-top: 1.25rem; padding-bottom: 2.2rem; max-width: 1500px; }
[data-testid="stHeader"] { background: rgba(11,18,32,.94); }
[data-testid="stToolbar"] { right: 1rem; }
[data-testid="stSidebar"] { background: linear-gradient(180deg,#101b31 0%,#0a1222 100%); border-right: 1px solid #26344d; }
[data-testid="stSidebar"] * { color: #e8f0ff; }
[data-testid="stSidebar"] [data-testid="stRadio"] label { padding: .48rem .62rem; border-radius: 10px; margin: .12rem 0; }
[data-testid="stSidebar"] [data-testid="stRadio"] label:hover { background: #1b2b45; }
[data-testid="stSidebar"] [data-testid="stMarkdownContainer"] h1 { font-size: 1.25rem; white-space: nowrap; }
.nextstep-brand { display:flex; flex-direction:column; align-items:flex-start; gap:.18rem; padding:.25rem 0 .65rem; }
.nextstep-logo { width:54px; height:54px; display:block; border-radius:14px; margin-bottom:.35rem; }
.nextstep-brand-name { color:#e8f0ff; font-size:1.28rem; font-weight:800; letter-spacing:-.025em; line-height:1.2; }
.nextstep-brand-tagline { color:#9fb7d5; font-size:.76rem; line-height:1.4; }
[data-testid="stSidebar"] [aria-checked="true"] { background: #123b42; border-radius: 10px; }
[data-testid="stMarkdownContainer"] h1, [data-testid="stMarkdownContainer"] h2, [data-testid="stMarkdownContainer"] h3, [data-testid="stMarkdownContainer"] h4 { color: #f1f6ff; }
[data-testid="stMarkdownContainer"] p, [data-testid="stMarkdownContainer"] li { color: #d2dced; }
.hero { padding: 1.45rem 1.6rem; border-radius: 18px; background: linear-gradient(115deg,#132a3e 0%,#173b4a 58%,#174e52 100%); border: 1px solid #28535c; color: #f3fbff; margin: .25rem 0 1.15rem; box-shadow: 0 12px 30px rgba(0,0,0,.18); }
.hero h1 { margin: 0 0 .35rem; color: #f6fbff; font-size: 1.75rem; }
.hero p { color: #c4e2e8; margin: 0; font-size: .98rem; }
.topline { color:#7dd3c7; font-size:.8rem; font-weight:700; letter-spacing:.06em; padding:.1rem 0 .7rem; }
.metric-card { min-height: 112px; padding: 1rem 1.05rem; border-radius: 15px; border: 1px solid #2a3b54; background: #131f32 !important; box-shadow: 0 5px 18px rgba(0,0,0,.14); }
.metric-card h4 { font-size:.8rem; font-weight:650; margin:0 0 .5rem; color:#a9bdd4; }
.metric-card .number { font-size:1.85rem; line-height:1.15; font-weight:800; color:#71e0d0; }
.metric-card .sub { font-size:.75rem; color:#9cafc5; margin-top:.32rem; }
.card-title { font-size:1.04rem; font-weight:750; color:#e7f1ff; margin:.2rem 0 .7rem; }
.career-card, .roadmap-step, .profile-strip { background:#121e30; border:1px solid #293b54; border-radius:13px; padding:.9rem 1rem; margin-bottom:.6rem; }
.career-card .career-name { font-weight:750; color:#eaf4ff; font-size:.94rem; }
.career-card .career-desc { color:#a9bad0; font-size:.8rem; margin:.3rem 0 .55rem; }
.pill { display:inline-block; border-radius:20px; background:#173d43; border:1px solid #28615f; color:#8ce5d7; padding:.2rem .55rem; margin:.1rem .18rem .1rem 0; font-size:.7rem; }
.roadmap-step strong { color:#e4f4ff; font-size:.84rem; }
div[data-testid="stMetric"] { background:#121e30; border:1px solid #293b54; border-radius:12px; padding:.7rem; }
div[data-testid="stMetric"] label { color:#b5c6dc !important; }
div[data-testid="stMetric"] [data-testid="stMetricValue"] { color:#72e1d1 !important; }
/* Consistent readable labels and dark form controls */
[data-testid="stWidgetLabel"], [data-testid="stWidgetLabel"] p, [data-testid="stWidgetLabel"] label,
[data-testid="stTextInput"] label, [data-testid="stTextArea"] label,
[data-testid="stSelectbox"] label, [data-testid="stMultiSelect"] label,
[data-testid="stNumberInput"] label, [data-testid="stFileUploader"] label { color:#dbe7f7 !important; opacity:1 !important; }
[data-testid="stTextInput"] input, [data-testid="stTextArea"] textarea,
[data-testid="stNumberInput"] input, [data-baseweb="select"] > div,
[data-baseweb="input"] > div { background:#172438 !important; color:#f0f6ff !important; border:1px solid #3a4b65 !important; border-radius:10px !important; }
[data-testid="stTextInput"] input::placeholder, [data-testid="stTextArea"] textarea::placeholder { color:#8fa4bd !important; }
[data-baseweb="select"] *, [data-baseweb="popover"] *, [role="listbox"] *, [role="option"] { color:#edf5ff !important; }
[data-baseweb="popover"], [role="listbox"] { background:#172438 !important; }
[data-baseweb="tag"] { background:#12665f !important; border:1px solid #2aa99a !important; }
[data-baseweb="tag"] * { color:#ffffff !important; }
[data-testid="stForm"] { background:#101b2b; border:1px solid #273950; border-radius:16px; padding:1.05rem; }
.stButton button, .stFormSubmitButton button, .stLinkButton a, [data-testid="stDownloadButton"] button { border-radius:10px; font-weight:650; min-height:2.6rem; border:1px solid #2daba0 !important; background:#147d78 !important; color:#ffffff !important; }
.stButton button:hover, .stFormSubmitButton button:hover, .stLinkButton a:hover, [data-testid="stDownloadButton"] button:hover { background:#18978e !important; border-color:#66e0d1 !important; color:#ffffff !important; }
.stButton button[kind="secondary"] { background:#1b2940 !important; color:#e5efff !important; border-color:#3a4b65 !important; }
[data-testid="stProgressBar"] > div { background:#25364d; }
[data-testid="stProgressBar"] > div > div { background:#35c6b4; }
[data-testid="stAlert"] { border-radius:12px; }
[data-testid="stExpander"] { background:#121e30; border:1px solid #293b54; border-radius:12px; }
[data-testid="stExpander"] summary, [data-testid="stExpander"] summary p { color:#e6edf7 !important; }
[data-testid="stChatMessage"] { background:#121e30; border:1px solid #293b54; border-radius:12px; }
[data-testid="stChatInput"] textarea { background:#172438 !important; color:#f0f6ff !important; }
hr { border-color:#2a3b54; }
small, .small-muted { color:#9cafc5; }
/* Keep the chat composer visually consistent with the selected theme. */
[data-testid="stBottom"], [data-testid="stBottomBlockContainer"] { background: transparent !important; }
[data-testid="stChatInput"] { background: transparent !important; }
[data-testid="stChatInput"] > div { border-radius: 14px !important; box-shadow: 0 4px 18px rgba(20,45,75,.08) !important; }
[data-testid="stChatInput"] textarea::placeholder { color:#8192a8 !important; opacity:1 !important; }
[data-testid="stChatInput"] textarea { min-height: 46px !important; }
[data-testid="stChatInputSubmitButton"] { color:#ffffff !important; }
@media (max-width: 900px) { .hero h1 { font-size:1.45rem; } .metric-card { min-height:100px; } }
</style>
""", unsafe_allow_html=True)

# Light mode overrides the dark palette above. The selection is controlled by the user.
if st.session_state.theme_mode == "Light":
    st.markdown("""
    <style>
    :root { color-scheme: light; }
    .stApp { background:#f5f8fc !important; color:#1d2b42 !important; }
    [data-testid="stHeader"] { background:rgba(245,248,252,.96) !important; }
    [data-testid="stSidebar"] { background:linear-gradient(180deg,#edf4fb 0%,#e4eef8 100%) !important; border-right:1px solid #d5e1ef !important; }
    [data-testid="stSidebar"] *, [data-testid="stSidebar"] [data-testid="stMarkdownContainer"] p { color:#1e3553 !important; }
    [data-testid="stSidebar"] .nextstep-brand-name { color:#17345a !important; }
    [data-testid="stSidebar"] .nextstep-brand-tagline { color:#526b88 !important; }
    [data-testid="stSidebar"] [data-testid="stRadio"] label:hover { background:#d9e9f7 !important; }
    [data-testid="stSidebar"] [aria-checked="true"] { background:#c9e8e3 !important; }
    [data-testid="stMarkdownContainer"] h1, [data-testid="stMarkdownContainer"] h2, [data-testid="stMarkdownContainer"] h3, [data-testid="stMarkdownContainer"] h4 { color:#172b49 !important; }
    [data-testid="stMarkdownContainer"] p, [data-testid="stMarkdownContainer"] li { color:#344a66 !important; }
    .hero { background:linear-gradient(115deg,#e3efff 0%,#e1f5f2 100%) !important; border:1px solid #cbdff0 !important; box-shadow:0 8px 24px rgba(38,72,112,.07) !important; }
    .hero h1 { color:#17345a !important; }
    .hero p { color:#45627f !important; }
    .topline { color:#167c78 !important; }
    .metric-card { background:#ffffff !important; border-color:#dce6f1 !important; box-shadow:0 5px 18px rgba(31,67,110,.06) !important; }
    .metric-card h4 { color:#536a85 !important; }
    .metric-card .number { color:#167f78 !important; }
    .metric-card .sub { color:#71839a !important; }
    .card-title { color:#203a5c !important; }
    .career-card, .roadmap-step, .profile-strip { background:#ffffff !important; border-color:#dce6f1 !important; }
    .career-card .career-name, .roadmap-step strong { color:#203a5c !important; }
    .career-card .career-desc { color:#61758e !important; }
    .pill { background:#e2f4f1 !important; border-color:#b8e4dc !important; color:#176b66 !important; }
    div[data-testid="stMetric"] { background:#ffffff !important; border-color:#dce6f1 !important; }
    div[data-testid="stMetric"] label { color:#536a85 !important; }
    div[data-testid="stMetric"] [data-testid="stMetricValue"] { color:#167f78 !important; }
    [data-testid="stWidgetLabel"], [data-testid="stWidgetLabel"] p, [data-testid="stWidgetLabel"] label,
    [data-testid="stTextInput"] label, [data-testid="stTextArea"] label, [data-testid="stSelectbox"] label,
    [data-testid="stMultiSelect"] label, [data-testid="stNumberInput"] label, [data-testid="stFileUploader"] label { color:#263e5b !important; opacity:1 !important; }
    [data-testid="stTextInput"] input, [data-testid="stTextArea"] textarea, [data-testid="stNumberInput"] input,
    [data-baseweb="select"] > div, [data-baseweb="input"] > div, [data-testid="stChatInput"] textarea {
      background:#ffffff !important; color:#203650 !important; border:1px solid #cbd8e7 !important; border-radius:10px !important;
    }
    [data-testid="stTextInput"] input::placeholder, [data-testid="stTextArea"] textarea::placeholder { color:#7b8da3 !important; }
    [data-baseweb="select"] *, [data-baseweb="popover"] *, [role="listbox"] *, [role="option"] { color:#203650 !important; }
    [data-baseweb="popover"], [role="listbox"] { background:#ffffff !important; }
    [data-baseweb="tag"] { background:#d8f0eb !important; border:1px solid #a8dcd2 !important; }
    [data-baseweb="tag"] * { color:#155e59 !important; }
    [data-testid="stForm"] { background:#ffffff !important; border:1px solid #dce6f1 !important; }
    /* High-contrast primary/green controls across EVERY page, including nested labels. */
    .stButton button, .stButton button *,
    .stFormSubmitButton button, .stFormSubmitButton button *,
    .stLinkButton a, .stLinkButton a *,
    [data-testid="stDownloadButton"] button, [data-testid="stDownloadButton"] button *,
    [data-testid="stBaseButton-primary"], [data-testid="stBaseButton-primary"] * {
      background-color:#126b66 !important; border-color:#126b66 !important;
      color:#ffffff !important; -webkit-text-fill-color:#ffffff !important;
      font-weight:700 !important; text-shadow:none !important; opacity:1 !important;
    }
    .stButton button:hover, .stButton button:hover *,
    .stFormSubmitButton button:hover, .stFormSubmitButton button:hover *,
    .stLinkButton a:hover, .stLinkButton a:hover *,
    [data-testid="stDownloadButton"] button:hover, [data-testid="stDownloadButton"] button:hover * {
      background-color:#0b5753 !important; border-color:#0b5753 !important;
      color:#ffffff !important; -webkit-text-fill-color:#ffffff !important;
    }
    /* Secondary controls remain light with dark readable text. */
    .stButton button[kind="secondary"], .stButton button[kind="secondary"] *,
    [data-testid="stBaseButton-secondary"], [data-testid="stBaseButton-secondary"] * {
      background-color:#edf3f9 !important; color:#263e5b !important;
      -webkit-text-fill-color:#263e5b !important; border-color:#cbd8e7 !important;
    }
    .stButton button:focus-visible, .stFormSubmitButton button:focus-visible,
    .stLinkButton a:focus-visible { outline:3px solid #42cfc1 !important; outline-offset:2px !important; }
    [data-testid="stProgressBar"] > div { background:#e0e9f3 !important; }
    [data-testid="stProgressBar"] > div > div { background:#23a99b !important; }
    [data-testid="stExpander"] { background:#ffffff !important; border-color:#dce6f1 !important; }
    [data-testid="stExpander"] summary, [data-testid="stExpander"] summary p { color:#263e5b !important; }
    [data-testid="stChatMessage"] { background:#ffffff !important; border-color:#dce6f1 !important; }
    [data-testid="stBottom"], [data-testid="stBottomBlockContainer"] { background:transparent !important; }
    [data-testid="stChatInput"] > div { background:#ffffff !important; border:1px solid #cbd8e7 !important; box-shadow:0 4px 18px rgba(20,45,75,.08) !important; }
    [data-testid="stChatInput"] textarea { color:#203650 !important; }
    [data-testid="stChatInput"] textarea::placeholder { color:#7b8da3 !important; opacity:1 !important; }
    hr { border-color:#dce6f1 !important; }
    small, .small-muted { color:#71839a !important; }
    </style>
    """, unsafe_allow_html=True)

if "profile" not in st.session_state:
    st.session_state.profile = None
if "recommendations" not in st.session_state:
    st.session_state.recommendations = []
if "messages" not in st.session_state:
    st.session_state.messages = []

# Load the saved profile once when a new Streamlit session starts.
if "profile_loaded" not in st.session_state:
    st.session_state.profile_loaded = True
    saved_profile = load_profile(st.session_state.profile_id)
    if saved_profile:
        st.session_state.profile = saved_profile
        try:
            st.session_state.recommendations = recommend(saved_profile) or []
        except Exception:
            st.session_state.recommendations = []

# Navigation requests are applied before the sidebar radio is created.
def go_to_profile():
    st.session_state.nav_selection = "Profile"

if "nav_selection" not in st.session_state:
    st.session_state.nav_selection = "Home"
requested_page = st.session_state.pop("navigate_after_save", None)
if requested_page in ["Recommendations", "Learning Roadmap", "Profile", "Home"]:
    st.session_state.nav_selection = requested_page

with st.sidebar:
    st.radio("Appearance", ["Light", "Dark"], key="theme_mode", horizontal=True)
    st.divider()
    st.markdown("""
    <div class="nextstep-brand">
      <svg class="nextstep-logo" viewBox="0 0 64 64" role="img" aria-label="NextStep AI geometric N logo">
        <rect x="1" y="1" width="62" height="62" rx="15" fill="#071b3a"/>
        <path d="M16 48 V16 H23 L48 41 V48 H41 L24 31 V48 Z" fill="#27d5ed"/>
        <path d="M29 16 H48 V35 Z" fill="#27d5ed"/>
      </svg>
      <div class="nextstep-brand-name">NextStep AI</div>
      <div class="nextstep-brand-tagline">Your Next Step Starts Here.</div>
    </div>
    """, unsafe_allow_html=True)
    page_label = st.radio("Navigate", ["Home", "Profile", "Recommendations", "Learning Roadmap", "Skill Gap Analysis", "Job Opportunities", "Chat Assistant", "Resume Analysis"], key="nav_selection", label_visibility="collapsed")
    page = {"Home":"Dashboard", "Profile":"My Profile", "Recommendations":"Recommendations", "Learning Roadmap":"Learning Roadmap", "Skill Gap Analysis":"Skill Gap Analysis", "Job Opportunities":"Jobs & Internships", "Chat Assistant":"Career Chatbot", "Resume Analysis":"Resume Analysis"}[page_label]
    st.divider()
    st.markdown("**DREAM · PLAN · ACHIEVE**")
    st.caption("Your career journey starts here.")


def profile_form():
    old = st.session_state.profile or {}
    education_options = ["B.Tech", "B.E.", "BCA", "MCA", "B.Sc.", "BBA", "B.Com", "M.Tech", "Other"]
    experience_options = ["Beginner", "Student projects", "Internship experience", "Experienced"]
    skill_options = ["Python", "Java", "C/C++", "Data Structures", "SQL", "Excel", "Statistics", "Data Visualization", "Machine Learning", "Pandas", "NumPy", "Networking", "Linux", "Security Fundamentals", "Git", "Docker", "CI/CD", "Cloud Fundamentals", "Figma", "Wireframing", "Prototyping", "User Research", "Communication", "Problem Solving", "Requirements Analysis"]
    interest_options = ["software development", "problem solving", "building applications", "data", "analytics", "statistics", "artificial intelligence", "machine learning", "cybersecurity", "networks", "automation", "cloud", "deployment", "design", "creativity", "user experience", "business", "research", "product strategy"]

    # Keep inputs outside st.form so submission is a direct, visible button action.
    name = st.text_input("Your name", value=old.get("name", "Student"), key="profile_name_input")
    c1, c2 = st.columns(2)
    with c1:
        old_education = old.get("education", "B.Tech")
        education = st.selectbox("Education", education_options, index=education_options.index(old_education) if old_education in education_options else 0, key="profile_education_input")
        degree = st.text_input("Branch / degree", value=old.get("degree", "Computer Science"), key="profile_degree_input")
        old_experience = old.get("experience", "Beginner")
        experience = st.selectbox("Experience level", experience_options, index=experience_options.index(old_experience) if old_experience in experience_options else 0, key="profile_experience_input")
    with c2:
        skills = st.multiselect("Skills you currently have", skill_options, default=[x for x in old.get("skills", []) if x in skill_options], key="profile_skills_input")
        interests = st.multiselect("Interests", interest_options, default=[x for x in old.get("interests", []) if x in interest_options], key="profile_interests_input")
    goal = st.text_area("Career goal", value=old.get("goal", "Find a suitable entry-level role and internship"), placeholder="Example: I want to become a software developer and build projects.", key="profile_goal_input")

    submitted = st.button("Save profile & generate recommendations", type="primary", use_container_width=True, key="save_profile_generate_button")
    if not submitted:
        return

    profile = {
        "name": name.strip() or "Student",
        "education": education,
        "degree": degree.strip(),
        "experience": experience,
        "skills": skills,
        "interests": interests,
        "goal": goal.strip(),
    }
    st.session_state.profile = profile
    st.info("Profile received. Generating your recommendations…")

    try:
        recommendations = recommend(profile) or []
        st.session_state.recommendations = recommendations
    except Exception as exc:
        print(f"Recommendation generation error: {type(exc).__name__}: {exc}")
        st.error(f"Profile was received, but recommendations failed ({type(exc).__name__}). Check the app logs for details.")
        return

    try:
        result = save_profile(profile, st.session_state.profile_id)
        message = result.get("message", "") if isinstance(result, dict) else ""
        notice = "Profile processed successfully for this session."
        if message:
            notice += " " + str(message)
    except Exception as exc:
        print(f"Profile save error: {type(exc).__name__}: {exc}")
        notice = f"Recommendations generated, but database saving failed ({type(exc).__name__})."

    st.session_state.profile_save_notice = notice
    # Set the sidebar radio's state before rerunning; the navigation block above
    # consumes this request before the radio widget is created.
    st.session_state.navigate_after_save = "Recommendations"
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
                    st.session_state.navigate_after_save = "Learning Roadmap"
                    st.rerun()
            st.progress(min(max(career["match_score"] / 100, 0.0), 1.0))

if page == "Dashboard":
    p = st.session_state.profile or {}
    results = st.session_state.recommendations or (recommend(p) if p else [])
    st.markdown('<div class="topline">Your Skills　 +　 Your Interests　 +　 AI Intelligence　 =　 A Brighter Future</div>', unsafe_allow_html=True)
    greeting = f"Hello, {p.get('name', 'Student')}!" if p else "Hello, future professional!"
    subtitle = "Here are your personalized career recommendations based on your profile." if p else "Build your profile to discover career paths, skill gaps, and your next steps."
    st.markdown(f'<div class="hero"><h1>👋 {greeting}</h1><p>{subtitle}</p></div>', unsafe_allow_html=True)

    careers_count = len(results) if results else len(get_careers())
    roles_count = sum(len(c.get("roles", [])) for c in results) if results else sum(len(c.get("roles", [])) for c in get_careers())
    resource_count = sum(len(c.get("courses", [])) for c in results) if results else sum(len(c.get("courses", [])) for c in get_careers())
    gaps_count = len(results[0].get("skill_gaps", [])) if results else 0
    metric_cols = st.columns(4)
    cards = [
        ("🧳 Recommended Career Paths", careers_count, "suitable career options", "#e9f3ff"),
        ("👥 Recommended Job Roles", roles_count, "role ideas across your matches", "#e9faf3"),
        ("📚 Learning Resources", resource_count, "topics in the career catalogue", "#f1edff"),
        ("🎯 Skill Gaps Identified", gaps_count if p else "—", "skills to develop for top match", "#fff5e4"),
    ]
    for col, (label, number, detail, bg) in zip(metric_cols, cards):
        with col:
            st.markdown(f'<div class="metric-card" style="background:{bg}"><h4>{label}</h4><div class="number">{number}</div><div class="sub">{detail}</div></div>', unsafe_allow_html=True)

    left, right = st.columns([1.22, .88], gap="medium")
    with left:
        st.markdown('<div class="card-title">⭐ Top Career Recommendations</div>', unsafe_allow_html=True)
        if p and results:
            st.caption("Similarity scores are demo-model estimates, not guarantees of job suitability.")
            for i, career in enumerate(results[:5], 1):
                score = career.get("match_score", 0)
                matched = career.get("matched_skills", [])
                tags = matched[:3] if matched else career.get("skills", [])[:3]
                tag_html = "".join(f'<span class="pill">{tag}</span>' for tag in tags)
                st.markdown(f'<div class="career-card"><div class="career-name">{i}. {career["title"]} <span style="float:right;color:#258b70;font-size:.72rem">{score}% match</span></div><div class="career-desc">{career["description"]}</div>{tag_html}</div>', unsafe_allow_html=True)
                if st.button("View details / roadmap", key=f"dashboard_career_{i}"):
                    st.session_state.selected_career = career["title"]
                    st.session_state.navigate_after_save = "Learning Roadmap"
                    st.rerun()
        else:
            st.markdown('<div class="career-card"><div class="career-name">Your recommendations will appear here</div><div class="career-desc">Complete your profile with skills, interests, and a career goal to personalize these results.</div></div>', unsafe_allow_html=True)
            st.button(
                "Create my profile",
                type="primary",
                use_container_width=True,
                on_click=go_to_profile,
                key="create_profile_from_home",
            )

    with right:
        st.markdown('<div class="card-title">📘 Your Learning Roadmap</div>', unsafe_allow_html=True)
        if p and results:
            career = results[0]
            stages = [
                ("1", "Build Strong Fundamentals", "Python programming · Data Structures & Algorithms", "1–2 months", "#2878d4"),
                ("2", "Learn Core Technologies", "Focus on the core skills listed for your selected career", "2–3 months", "#7b61d1"),
                ("3", "Gain Practical Experience", "; ".join(career.get("projects", [])[:2]) or "Build a small portfolio project", "2–3 months", "#25a77a"),
                ("4", "Prepare to Apply", "Resume · Interview practice · Official career pages", "1–2 months", "#ed9824"),
            ]
            for num, title, detail, duration, color in stages:
                st.markdown(f'<div class="roadmap-step"><strong><span style="color:{color}">● {num}</span>　{title}</strong><div style="font-size:.75rem;color:#71839a;margin:.3rem 0">{detail}</div><span style="font-size:.68rem;color:#7d8da2">Suggested duration: {duration}</span></div>', unsafe_allow_html=True)
            if st.button("Open full learning roadmap", use_container_width=True):
                st.info("Choose **Learning Roadmap** from the sidebar.")
        else:
            for title, detail in [("1 · Build your profile", "Add your current skills and interests."), ("2 · Explore career paths", "Compare roles suggested by the demo model."), ("3 · Build practical skills", "Turn skill gaps into projects and learning steps.")]:
                st.markdown(f'<div class="roadmap-step"><strong>{title}</strong><div style="font-size:.75rem;color:#71839a;margin-top:.3rem">{detail}</div></div>', unsafe_allow_html=True)

        st.markdown('<div class="card-title" style="margin-top:1rem">💬 Career Guidance Assistant</div>', unsafe_allow_html=True)
        st.caption("Ask about career choices, skills, or learning order.")
        if "dashboard_chat_input" not in st.session_state:
            st.session_state.dashboard_chat_input = ""
        with st.form("dashboard_quick_chat", clear_on_submit=True):
            quick_question = st.text_input("Ask your career assistant", placeholder="How can I improve my skills?", label_visibility="collapsed")
            ask = st.form_submit_button("Ask assistant", use_container_width=True)
        if ask and quick_question.strip():
            reply = answer(quick_question.strip(), p or None)
            st.session_state.messages.append({"role":"user", "content":quick_question.strip()})
            st.session_state.messages.append({"role":"assistant", "content":reply})
            save_chat(quick_question.strip(), reply)
            st.success(reply)
            st.caption("You can continue the conversation in Chat Assistant.")

    st.markdown('<div class="card-title" style="margin-top:.8rem">👤 Your Profile Summary</div>', unsafe_allow_html=True)
    if p:
        prof_cols = st.columns(4)
        prof_items = [("🎓 Education", f"{p.get('education','—')} · {p.get('degree','') or 'Degree not specified'}"), ("⚙️ Skills", ", ".join(p.get("skills", [])[:5]) or "Not added yet"), ("♥ Interests", ", ".join(p.get("interests", [])[:3]) or "Not added yet"), ("◎ Career Goal", p.get("goal", "Not added yet"))]
        for col, (label, value) in zip(prof_cols, prof_items):
            with col:
                st.markdown(f'<div class="profile-strip"><div style="font-size:.73rem;color:#71849b;font-weight:700">{label}</div><div style="font-size:.8rem;color:#263e5f;margin-top:.35rem">{value}</div></div>', unsafe_allow_html=True)
        st.caption("Profile and recommendation data are based on the information entered in this session. MongoDB saving depends on your database configuration.")
    else:
        st.info("Your profile summary will appear here after you save your profile.")
    st.divider()
    st.caption("Prototype notice: career matches use the local TF-IDF similarity model. Job suggestions are role ideas, not verified live vacancies.")

elif page == "My Profile":
    st.title("👤 My Profile")
    st.write("Your profile powers recommendations, skill-gap analysis, and personalized chat responses.")
    profile_form()
    if st.session_state.profile:
        with st.expander("Current profile data"):
            st.json(st.session_state.profile)

elif page == "Recommendations":
    st.title("🧭 Career Recommendations")
    notice = st.session_state.pop("profile_save_notice", None)
    if notice:
        st.success(notice)
    show_recommendations()

elif page == "Skill Gap Analysis":
    st.title("🎯 Skill Gap Analysis")
    st.write("Compare the skills listed for a recommended career with the skills in your profile.")
    p = st.session_state.profile
    results = st.session_state.recommendations or (recommend(p) if p else [])
    if not p or not results:
        st.info("Create and save your profile first to see your personalized skill gaps.")
    else:
        choices = [c["title"] for c in results]
        default = st.session_state.get("selected_career", choices[0])
        selected = st.selectbox("Career to analyze", choices, index=choices.index(default) if default in choices else 0, key="skill_gap_career")
        career = next(c for c in results if c["title"] == selected)
        st.markdown(f"### {career['title']}")
        st.write(career["description"])
        st.caption("This is a guidance estimate based on the profile and career catalogue, not a formal assessment.")
        have, need = st.columns(2)
        with have:
            st.markdown("#### ✅ Skills you have")
            matched = career.get("matched_skills", [])
            if matched:
                for skill in matched: st.success(skill)
            else:
                st.info("No catalogue skills matched your profile for this career yet. You can still add skills you know in My Profile.")
        with need:
            st.markdown("#### 📌 Skills to develop")
            gaps = career.get("skill_gaps", [])
            if gaps:
                for skill in gaps: st.warning(skill)
            else:
                st.success("No additional skills listed as gaps for this match.")
        st.markdown("#### Suggested next steps")
        st.write("1. Pick one skill to focus on first.")
        st.write("2. Practice it through a small project.")
        st.write("3. Update your profile as you gain experience.")
        if st.button("Open learning roadmap for this career", type="primary"):
            st.session_state.selected_career = selected
            st.session_state.navigate_after_save = "Learning Roadmap"
            st.rerun()

elif page == "Learning Roadmap":
    st.title("🗺️ Learning Roadmap")
    st.write("Turn your target career into a practical learning sequence.")
    p = st.session_state.profile
    results = st.session_state.recommendations or (recommend(p) if p else [])
    if not p or not results:
        st.info("Create and save your profile first to generate a roadmap.")
    else:
        choices = [c["title"] for c in results]
        default = st.session_state.get("selected_career", choices[0])
        selected = st.selectbox("Choose a career path", choices, index=choices.index(default) if default in choices else 0, key="roadmap_career")
        career = next(c for c in results if c["title"] == selected)
        st.markdown(f"### {career['title']} learning plan")
        st.write(career["description"])
        stages = [
            ("Stage 1 · Foundations", career.get("courses", [])[:2] or ["Review core concepts for this role"]),
            ("Stage 2 · Guided practice", career.get("courses", [])[2:4] or ["Complete beginner exercises and tutorials"]),
            ("Stage 3 · Build projects", career.get("projects", [])[:2] or ["Build a small portfolio project related to this role"]),
            ("Stage 4 · Portfolio and applications", career.get("projects", [])[2:] or ["Polish one project", "Prepare a role-specific resume", "Practice interview questions"]),
        ]
        for idx, (stage_title, items) in enumerate(stages, 1):
            with st.container(border=True):
                st.markdown(f"#### {idx}. {stage_title}")
                for item in items: st.write(f"- {item}")
        st.download_button("Download roadmap as JSON", json.dumps({"career": career, "roadmap": stages}, indent=2), file_name="nextstep_ai_learning_roadmap.json", mime="application/json")

elif page == "Jobs & Internships":
    from urllib.parse import quote_plus
    st.title("💼 Job & Internship Opportunities")
    st.write("Explore relevant role ideas and open job platforms to check current vacancies.")
    st.info("These are links to job-search platforms, not live vacancy results. Check each listing's details, eligibility, and deadline on the employer or platform website.")
    p = st.session_state.profile
    results = st.session_state.recommendations or (recommend(p) if p else [])
    if not results:
        st.info("Create and save your profile first to get career-specific role suggestions.")
    else:
        platforms = [
            ("LinkedIn Jobs", "https://www.linkedin.com/jobs/", "Professional roles and internships"),
            ("Naukri", "https://www.naukri.com/", "India-focused job listings"),
            ("Indeed", "https://in.indeed.com/", "Jobs across industries"),
            ("Internshala", "https://internshala.com/", "Internships and fresher opportunities"),
            ("Foundit", "https://www.foundit.in/", "Jobs for freshers and experienced candidates"),
            ("Wellfound", "https://wellfound.com/jobs", "Startup roles and opportunities"),
        ]
        st.markdown("### Job search platforms")
        platform_cols = st.columns(3)
        for col, (name, url, detail) in zip(platform_cols * 2, platforms):
            with col:
                with st.container(border=True):
                    st.markdown(f"**{name}**")
                    st.caption(detail)
                    st.link_button(f"Open {name}", url, use_container_width=True)
        st.divider()
        st.markdown("### Suggested roles based on your profile")
        for i, career in enumerate(results[:5], 1):
            title = career.get("title", "Suggested career")
            roles = career.get("roles", [])
            with st.container(border=True):
                left, right = st.columns([3, 1])
                with left:
                    st.subheader(f"{i}. {title}")
                    st.write(career.get("description", "Explore entry-level opportunities in this area."))
                    st.write("**Role ideas:** " + (", ".join(roles) if roles else title))
                    st.write("**Portfolio ideas:** " + ("; ".join(career.get("projects", [])[:3]) or "Build a small project related to this role"))
                with right:
                    st.metric("Profile similarity", f"{career.get('match_score', 0)}%")
                search_role = roles[0] if roles else title
                query = quote_plus(search_role + " fresher internship")
                links = st.columns(3)
                links[0].link_button("Search LinkedIn", f"https://www.linkedin.com/jobs/search/?keywords={query}", use_container_width=True)
                links[1].link_button("Search Naukri", f"https://www.naukri.com/{quote_plus(search_role.lower()).replace('+','-')}-jobs", use_container_width=True)
                links[2].link_button("Search Indeed", f"https://in.indeed.com/jobs?q={query}", use_container_width=True)

elif page == "Career Chatbot":
    st.title("💬 Career Guidance Assistant")
    st.write("Ask about career options, learning order, projects, interviews, or skill development.")
    p = st.session_state.profile
    with st.container(border=True):
        st.markdown("**How can I help?**")
        st.caption("Try asking: Which skills should I learn first? · Suggest a project for my target role · How should I prepare for internships?")
    if st.session_state.messages:
        for m in st.session_state.messages:
            with st.chat_message(m["role"]):
                st.markdown(m["content"])
    else:
        st.info("Your conversation will appear here. Ask a question below to get started.")
    with st.form("career_chat_form", clear_on_submit=True):
        prompt = st.text_input("Your question", placeholder="e.g., How can I prepare for a software developer internship?")
        send = st.form_submit_button("Send message", type="primary", use_container_width=True)
    if send and prompt.strip():
        st.session_state.messages.append({"role":"user", "content":prompt.strip()})
        try:
            reply = answer(prompt.strip(), p)
            st.session_state.messages.append({"role":"assistant", "content":reply})
            try:
                save_chat(prompt.strip(), reply)
            except Exception:
                pass
        except Exception as exc:
            st.error(f"The assistant couldn't answer right now ({type(exc).__name__}). Please try again.")
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
