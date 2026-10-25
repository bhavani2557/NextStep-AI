import os

from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import cosine_similarity

from services.recommender import CAREERS


KNOWLEDGE = [
    "Software development requires programming, data structures, "
    "problem solving, Git, SQL, APIs, debugging, testing, and projects.",
    "Data analytics requires SQL, spreadsheets, statistics, Python, "
    "data analysis, and visualization.",
    "Machine learning requires Python, statistics, data preparation, "
    "Pandas, NumPy, and model evaluation.",
    "DevOps requires Linux, Git, scripting, CI/CD, Docker, cloud "
    "fundamentals, monitoring, and secure configuration.",
    "A portfolio project should include a README, setup instructions, "
    "technologies used, and screenshots or a demo.",
    "Software developer interviews cover programming fundamentals, "
    "data structures, algorithms, SQL, debugging, and project explanations.",
]


CAREER_REQUIREMENTS = {
    "software developer": [
        ("Programming language", ["python", "java", "javascript", "c++", "c#"]),
        ("Data Structures and Algorithms", ["data structures", "data structure", "algorithms", "algorithm", "dsa"]),
        ("Problem solving", ["problem solving", "problem-solving", "competitive programming"]),
        ("Git and GitHub", ["git", "github", "version control"]),
        ("SQL and databases", ["sql", "mysql", "postgresql", "mongodb", "database", "dbms"]),
        ("REST APIs", ["rest api", "rest apis", "api", "apis", "fastapi", "express"]),
        ("Debugging and testing", ["debugging", "debug", "testing", "unit test", "pytest"]),
        ("Object-oriented programming", ["oop", "object-oriented", "object oriented"]),
    ],
    "data analyst": [
        ("SQL and databases", ["sql", "mysql", "postgresql", "database", "dbms"]),
        ("Spreadsheets", ["excel", "spreadsheet", "google sheets"]),
        ("Python for data analysis", ["python", "pandas", "numpy"]),
        ("Statistics", ["statistics", "statistical"]),
        ("Data visualization", ["visualization", "visualisation", "power bi", "tableau", "matplotlib"]),
        ("Data cleaning and analysis", ["data analysis", "data cleaning", "data analytics"]),
        ("Portfolio project", ["project", "portfolio"]),
    ],
    "machine learning engineer": [
        ("Python", ["python"]),
        ("Statistics and mathematics", ["statistics", "probability", "linear algebra", "mathematics", "math"]),
        ("Pandas and NumPy", ["pandas", "numpy"]),
        ("Data preparation", ["data preparation", "data preprocessing", "data cleaning"]),
        ("Machine learning fundamentals", ["machine learning", "scikit-learn", "sklearn", "ml"]),
        ("Model evaluation", ["model evaluation", "evaluation", "metrics"]),
        ("Portfolio project", ["project", "portfolio"]),
    ],
    "cloud / DevOps engineer": [
        ("Linux fundamentals", ["linux", "ubuntu", "bash", "shell"]),
        ("Git and GitHub", ["git", "github", "version control"]),
        ("Scripting", ["python", "bash", "shell scripting", "powershell"]),
        ("CI/CD", ["ci/cd", "continuous integration", "continuous delivery", "jenkins", "github actions"]),
        ("Containers", ["docker", "container", "kubernetes"]),
        ("Cloud fundamentals", ["aws", "azure", "gcp", "cloud"]),
        ("Monitoring and security", ["monitoring", "logging", "security", "secure configuration"]),
    ],
}


def _as_list(value):
    if value is None:
        return []
    if isinstance(value, str):
        value = [value]
    if not isinstance(value, (list, tuple, set)):
        value = [value]
    return [str(item).strip() for item in value if str(item).strip()]


def _choose_career(question_lower: str, interests: list[str], goal: str) -> str:
    combined = " ".join([question_lower, " ".join(interests), goal]).lower()

    if any(word in combined for word in [
        "data analyst", "data analytics", "data analysis", "business intelligence"
    ]):
        return "data analyst"
    if any(word in combined for word in [
        "machine learning", "ml engineer", "artificial intelligence", " ai "
    ]):
        return "machine learning engineer"
    if any(word in combined for word in [
        "devops", "cloud engineer", "cloud computing", "site reliability"
    ]):
        return "cloud / DevOps engineer"
    return "software developer"


def _has_skill(skill_text: str, aliases: list[str]) -> bool:
    text = skill_text.lower()
    return any(alias in text for alias in aliases)


def _personalized_skill_plan(career: str, skills: list[str], interests: list[str]) -> str:
    requirements = CAREER_REQUIREMENTS[career]
    profile_text = " ".join(skills).lower()
    known = []
    missing = []

    for label, aliases in requirements:
        if _has_skill(profile_text, aliases):
            known.append(label)
        else:
            missing.append(label)

    # Keep the next steps realistic and avoid telling the student to learn everything at once.
    strengthen = known[:2]
    next_to_learn = missing[:3]
    project = {
        "software developer": "Build a small full-stack CRUD app with a database, input validation, and a README; push it to GitHub.",
        "data analyst": "Analyse a small public dataset using SQL or Python, create clear charts, and explain three findings in a README.",
        "machine learning engineer": "Train and evaluate one beginner model on a clean dataset, compare it with a baseline, and document the results.",
        "cloud / DevOps engineer": "Containerize a small application with Docker and document how to run it; add a basic CI workflow if ready.",
    }[career]

    lines = [
        f"## Your next-step plan: {career.title()}",
        "",
        f"**Skills in your profile:** {', '.join(skills) if skills else 'No skills listed yet.'}",
    ]

    if interests:
        lines.append(f"**Interests in your profile:** {', '.join(interests)}")

    lines.extend(["", "### Skills you already list"])
    lines.append(
        ", ".join(known) if known
        else "Your profile does not yet list any of this role's core skills. That does not mean you lack them—add the skills you have practised."
    )

    lines.extend(["", "### Skills to strengthen"])
    lines.append(
        ", ".join(strengthen) if strengthen
        else "Choose one foundation you have studied and practise it with small exercises."
    )

    lines.extend(["", "### Good next skills to learn"])
    lines.append(
        ", ".join(next_to_learn) if next_to_learn
        else "Your listed skills cover the core items in this demo checklist. Focus on applying them in a project and reviewing job descriptions for your target role."
    )

    lines.extend([
        "",
        "### Practical project",
        project,
        "",
        "### Suggested order",
    ])

    order = []
    if missing:
        order.extend(missing[:2])
    if "Portfolio project" not in order:
        order.append("a portfolio project")
    lines.append(" → ".join(order) if order else "Build a portfolio project and prepare to explain your decisions.")

    lines.extend([
        "",
        "This is a first-pass comparison against a small demo checklist, not a test of your actual ability. If you already know a skill, add it to your profile so the plan can account for it."
    ])
    return "\n".join(lines)


def local_answer(question: str, profile: dict | None = None) -> str:
    question_lower = question.lower().strip()
    profile = profile or {}

    skills = _as_list(profile.get("skills", []))
    interests = _as_list(profile.get("interests", []))
    goal = str(profile.get("goal", "")).strip()

    career = _choose_career(question_lower, interests, goal)

    # Explicitly compare both paths when the student asks about both careers.
    asks_software = any(term in question_lower for term in [
        "software developer", "software development", "software engineer"
    ])
    asks_analyst = any(term in question_lower for term in [
        "data analyst", "data analytics", "data analysis"
    ])
    asks_compare = any(term in question_lower for term in [
        "compare", "both", "each career", "each role", "requirements for"
    ])

    if asks_software and asks_analyst and asks_compare:
        software_plan = _personalized_skill_plan("software developer", skills, interests)
        analyst_plan = _personalized_skill_plan("data analyst", skills, interests)
        return (
            "I compared both paths using the skills listed in your profile. "
            "A skill not listed is not necessarily a skill you do not know.\\n\\n"
            + software_plan
            + "\\n\\n---\\n\\n"
            + analyst_plan
            + "\\n\\n### How to choose\\n"
            "If you enjoy building applications and solving programming problems, "
            "explore Software Developer first. If you enjoy working with datasets, "
            "finding patterns, and explaining insights, explore Data Analyst. "
            "You can try one small project in each before deciding."
        )

    personal_keywords = [
        "based on my current skills", "based on my skills",
        "what should i learn next", "what should i learn first",
        "what am i lacking", "skills am i missing", "skill gap",
        "what do i need to learn", "what should i improve",
        "anything i am lacking", "next step", "learning plan",
        "roadmap", "personalized", "personalised",
    ]

    if any(keyword in question_lower for keyword in personal_keywords):
        return _personalized_skill_plan(career, skills, interests)

    if any(word in question_lower for word in ["project", "portfolio"]):
        projects = {
            "software developer": (
                "1. Task management app with CRUD operations.\n"
                "2. REST API connected to a database.\n"
                "3. Full-stack application with validation and error handling."
            ),
            "data analyst": (
                "1. SQL analysis of a public dataset.\n"
                "2. Excel dashboard with a short insight summary.\n"
                "3. Python data-cleaning and visualisation notebook."
            ),
            "machine learning engineer": (
                "1. Classification model with a simple baseline.\n"
                "2. Data-cleaning and exploratory-analysis notebook.\n"
                "3. Model comparison with documented evaluation metrics."
            ),
            "cloud / DevOps engineer": (
                "1. Dockerize a small web application.\n"
                "2. Create a basic CI workflow for tests.\n"
                "3. Deploy a small app and document its configuration."
            ),
        }
        return (
            f"Project ideas for a {career} path:\n\n{projects[career]}\n\n"
            "For any project, add a README with the problem, features, setup steps, "
            "technologies used, and screenshots or a demo. Do not include passwords or API keys."
        )

    if "interview" in question_lower:
        interview_topics = {
            "software developer": "programming fundamentals, data structures, algorithms, SQL, debugging, and explaining your projects",
            "data analyst": "SQL queries, spreadsheets, statistics basics, data cleaning, visualisation choices, and explaining insights",
            "machine learning engineer": "Python, statistics, data preparation, model evaluation, overfitting, and explaining project trade-offs",
            "cloud / DevOps engineer": "Linux, Git, networking basics, CI/CD, Docker, cloud fundamentals, logs, and troubleshooting",
        }
        return (
            f"For {career} interviews, prepare {interview_topics[career]}. "
            "Practise explaining your reasoning and what you personally built."
        )

    documents = KNOWLEDGE + [
        f"{item['title']}: {item['description']} "
        f"Skills: {', '.join(item['skills'])}. "
        f"Projects: {', '.join(item['projects'])}."
        for item in CAREERS
    ]

    vectorizer = TfidfVectorizer(stop_words="english")
    matrix = vectorizer.fit_transform(documents + [question])
    scores = cosine_similarity(matrix[-1], matrix[:-1]).flatten()
    top_indices = scores.argsort()[::-1][:3]

    selected = [
        documents[int(index)]
        for index in top_indices
        if scores[index] > 0
    ]

    if not selected:
        return (
            "I can help with career options, skill gaps, learning roadmaps, "
            "projects, and interview preparation. Tell me your target role "
            "and current skills."
        )

    return (
        "Here is guidance based on the career knowledge included in this demo:\n\n"
        + "\n\n".join(selected)
        + "\n\nNote: this demo uses a limited local knowledge base. "
        "Verify current jobs, salaries, and course details with official sources."
    )


def answer(question: str, profile: dict | None = None) -> str:
    # Route explicit multi-career comparisons through the deterministic local
    # comparison handler, even when an OpenAI API key is configured.
    question_lower = question.lower()
    asks_software = any(term in question_lower for term in [
        "software developer", "software development", "software engineer"
    ])
    asks_analyst = any(term in question_lower for term in [
        "data analyst", "data analytics", "data analysis"
    ])
    asks_compare = any(term in question_lower for term in [
        "compare", "both", "each career", "each role", "requirements for"
    ])
    if asks_software and asks_analyst and asks_compare:
        return local_answer(question, profile)

    api_key = os.getenv("OPENAI_API_KEY", "").strip()

    if not api_key:
        return local_answer(question, profile)

    try:
        from openai import OpenAI

        client = OpenAI(api_key=api_key)
        response = client.chat.completions.create(
            model=os.getenv("OPENAI_MODEL", "gpt-4o-mini"),
            messages=[
                {
                    "role": "system",
                    "content": (
                        "You are a practical career guidance assistant. Answer the exact "
                        "question and personalize advice using the student's profile. "
                        "When discussing skill gaps, separate skills the profile already "
                        "lists from skills to strengthen and skills to learn. Never claim "
                        "that an unlisted skill is definitely unknown; say it is not listed. "
                        "Give a short ordered plan and one practical project. Do not invent "
                        "live jobs, salaries, credentials, or guarantee outcomes. Be clear "
                        "when advice is based on a limited profile."
                    ),
                },
                {
                    "role": "user",
                    "content": (
                        f"Student profile: {profile or {}}\n"
                        f"Question: {question}"
                    ),
                },
            ],
            temperature=0.4,
        )

        result = response.choices[0].message.content
        return result or local_answer(question, profile)

    except Exception:
        return local_answer(question, profile)
