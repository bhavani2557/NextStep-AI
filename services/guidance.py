
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


def local_answer(question: str, profile: dict | None = None) -> str:
    question_lower = question.lower().strip()
    profile = profile or {}

    skills = profile.get("skills", [])
    interests = profile.get("interests", [])
    goal = str(profile.get("goal", "")).lower()

    if isinstance(skills, str):
        skills = [skills]

    if isinstance(interests, str):
        interests = [interests]

    skills = [str(skill).strip() for skill in skills if str(skill).strip()]
    interests = [str(item).strip() for item in interests if str(item).strip()]

    # Identify the career being discussed.
    software_keywords = [
        "software developer", "software development",
        "programmer", "coding", "programming"
    ]
    data_keywords = ["data analyst", "data analytics"]
    ml_keywords = ["machine learning", "ml engineer"]
    devops_keywords = ["devops", "cloud engineer"]

    if any(word in question_lower for word in software_keywords):
        career = "software developer"
    elif any(word in question_lower for word in data_keywords):
        career = "data analyst"
    elif any(word in question_lower for word in ml_keywords):
        career = "machine learning engineer"
    elif any(word in question_lower for word in devops_keywords):
        career = "cloud / DevOps engineer"
    elif any(word in " ".join(interests).lower()
             for word in ["software development", "building applications"]):
        career = "software developer"
    else:
        career = "software developer"

    # Handle personalized skill-gap and learning-order questions directly.
    personal_keywords = [
        "based on my current skills",
        "based on my skills",
        "what should i learn next",
        "what should i learn first",
        "what am i lacking",
        "skills am i missing",
        "skill gap",
        "what do i need to learn",
        "what should i improve",
        "anything i am lacking",
    ]

    if any(keyword in question_lower for keyword in personal_keywords):
        if career == "software developer":
            required_skills = [
                "Python or Java",
                "Data Structures and Algorithms",
                "Problem Solving",
                "Git and GitHub",
                "SQL",
                "REST APIs",
                "Debugging and Testing",
            ]

            skill_lower = {skill.lower() for skill in skills}

            # Match skills the profile explicitly lists.
            known = []
            for required in required_skills:
                if required == "Python or Java":
                    if any(s in skill_lower for s in ["python", "java"]):
                        known.append(required)
                elif required == "Data Structures and Algorithms":
                    if any("data structure" in s or "algorithm" in s
                           for s in skill_lower):
                        known.append(required)
                elif required == "Problem Solving":
                    if any("problem solving" in s for s in skill_lower):
                        known.append(required)
                elif required == "Git and GitHub":
                    if any("git" in s or "github" in s for s in skill_lower):
                        known.append(required)
                elif required == "SQL":
                    if any("sql" in s for s in skill_lower):
                        known.append(required)

            missing = [item for item in required_skills if item not in known]

            response = [
                "Based on your profile, here is your next-step plan for "
                "becoming a Software Developer."
            ]

            response.append(
                "\nSkills listed in your profile: "
                + (", ".join(skills) if skills else "No skills provided yet.")
            )

            response.append(
                "\n\nWhat to learn or strengthen next:\n"
                "1. Problem solving: practice coding problems regularly.\n"
                "2. REST APIs: learn HTTP methods and build CRUD endpoints.\n"
                "3. Debugging and testing: find errors and write basic tests.\n"
                "4. Object-oriented programming: practice classes and objects.\n"
                "5. Projects: build and document an application on GitHub."
            )

            if "java" not in skill_lower:
                response.append(
                    "\n\nOptional next skill: learn Java if it is required "
                    "for your target roles. You do not need to learn several "
                    "programming languages at once."
                )

            response.append(
                "\n\nRecommended order: problem solving → REST APIs → "
                "testing and debugging → one complete portfolio project."
            )

            response.append(
                "\n\nThese are recommendations based on the skills listed "
                "in your profile, not a formal test of your ability."
            )

            return "\n".join(response)

        return (
            f"For {career}, start by comparing your profile skills "
            "with the role's core requirements. Choose one important "
            "missing skill, practice it, and build a small project. "
            "Update your profile with your current skills for more "
            "personalized guidance."
        )

    if any(word in question_lower for word in ["project", "portfolio"]):
        return (
            "Suggested beginner software projects:\n\n"
            "1. Task management application.\n"
            "2. REST API with CRUD operations.\n"
            "3. Database-backed application with input validation.\n\n"
            "Upload your code to GitHub and include a README, setup steps, "
            "technologies, and screenshots."
        )

    if "interview" in question_lower:
        return (
            "For software developer interviews, prepare programming "
            "fundamentals, data structures, algorithms, SQL, debugging, "
            "and explanations of your projects. Practise coding questions "
            "and explain your reasoning aloud."
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
                        "You are a practical career guidance assistant. "
                        "Answer the exact question, use the student's "
                        "profile to personalize advice, and stay focused "
                        "on their target career. Do not invent live jobs "
                        "or guarantee outcomes."
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
