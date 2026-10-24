from fastapi import FastAPI, HTTPException
from pydantic import BaseModel, Field
from typing import List, Optional
from services.recommender import recommend, get_careers
from services.guidance import answer
from services.database import save_profile

app = FastAPI(title="Personalized Career Recommendation Agent API", version="1.0.0")

class StudentProfile(BaseModel):
    name: str = "Student"
    education: str = "B.Tech"
    degree: str = "Computer Science"
    skills: List[str] = Field(default_factory=list)
    interests: List[str] = Field(default_factory=list)
    experience: str = "Beginner"
    goal: str = "Explore career options"

class ChatRequest(BaseModel):
    question: str = Field(min_length=1, max_length=4000)
    profile: Optional[dict] = None

@app.get("/")
def root():
    return {"message": "Career Recommendation API is running", "docs": "/docs"}

@app.get("/health")
def health():
    return {"status": "ok"}

@app.get("/careers")
def careers():
    return get_careers()

@app.post("/recommend")
def recommendations(profile: StudentProfile):
    results = recommend(profile.model_dump())
    if not results:
        raise HTTPException(status_code=400, detail="Provide at least some skills, interests, education, or a career goal.")
    return {"recommendations": results}

@app.post("/profile")
def create_profile(profile: StudentProfile):
    return save_profile(profile.model_dump())

@app.post("/chat")
def chat(request: ChatRequest):
    return {"answer": answer(request.question, request.profile)}
