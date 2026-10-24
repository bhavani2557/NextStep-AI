import json
from pathlib import Path
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import cosine_similarity

CAREERS_PATH = Path(__file__).resolve().parents[1] / "data" / "careers.json"
CAREERS = json.loads(CAREERS_PATH.read_text(encoding="utf-8"))

def _profile_text(profile: dict) -> str:
    fields = [profile.get("education", ""), profile.get("degree", ""), profile.get("experience", ""), profile.get("goal", "")]
    fields += profile.get("skills", [])
    fields += profile.get("interests", [])
    return " ".join(str(x) for x in fields if x)

def _career_text(career: dict) -> str:
    return " ".join([career["title"], career["description"], *career["skills"], *career["interests"], *career["keywords"]])

def recommend(profile: dict, top_k: int = 5) -> list[dict]:
    profile_text = _profile_text(profile).strip()
    if not profile_text:
        return []
    documents = [_career_text(c) for c in CAREERS] + [profile_text]
    matrix = TfidfVectorizer(stop_words="english").fit_transform(documents)
    scores = cosine_similarity(matrix[-1], matrix[:-1]).flatten()
    ranked = scores.argsort()[::-1][:top_k]
    output = []
    user_skills = {s.lower() for s in profile.get("skills", [])}
    for idx in ranked:
        career = dict(CAREERS[int(idx)])
        matched = [s for s in career["skills"] if s.lower() in user_skills]
        gaps = [s for s in career["skills"] if s.lower() not in user_skills]
        career["match_score"] = round(float(scores[idx]) * 100, 1)
        career["matched_skills"] = matched
        career["skill_gaps"] = gaps
        output.append(career)
    return output

def get_careers() -> list[dict]:
    return CAREERS
