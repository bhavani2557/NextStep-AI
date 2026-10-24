# Personalized Career Recommendation Agent (Streamlit Full Stack)

A student-focused career guidance prototype based on the uploaded project abstract. It includes a Streamlit UI, FastAPI backend, Scikit-learn TF-IDF career matching, skill-gap analysis, a learning roadmap, a career chatbot (optional LLM API with local fallback), MongoDB persistence (optional), and PDF resume keyword analysis.

## Features
- Student profile: education, branch, skills, interests, experience, and goal
- ML-based career similarity ranking using TF-IDF + cosine similarity
- Skill gaps for each suggested career
- Suggested courses, certifications, portfolio projects, and role titles
- Career guidance chatbot: optional OpenAI API; local retrieval-style fallback when no key is configured
- Optional MongoDB persistence for profiles and chat history
- Resume PDF text extraction and simple skill keyword detection
- FastAPI endpoints for health, career catalogue, recommendations, profile saving, and chat
- Downloadable learning roadmap JSON

## Stack
- Frontend: Streamlit
- Backend: FastAPI + Pydantic
- ML/NLP: Scikit-learn TF-IDF and cosine similarity
- Generative AI: OpenAI-compatible API when configured; otherwise local fallback
- Database: MongoDB (optional; app still works without it)

## 1. Requirements
Install Python 3.11 or 3.12, then open a terminal in this project folder.

### Windows PowerShell
```powershell
py -3.11 -m venv .venv
.\.venv\Scripts\Activate.ps1
python -m pip install --upgrade pip
pip install -r requirements.txt
Copy-Item .env.example .env
```
If PowerShell blocks activation, run `Set-ExecutionPolicy -Scope Process -ExecutionPolicy Bypass` in that terminal and activate again, or use `\.venv\Scripts\python.exe -m pip install -r requirements.txt`.

### macOS/Linux
```bash
python3.11 -m venv .venv
source .venv/bin/activate
python -m pip install --upgrade pip
pip install -r requirements.txt
cp .env.example .env
```

## 2. Run the app
Open **two terminals** in the project folder and activate the virtual environment in each.

Terminal 1 — API:
```bash
uvicorn backend.main:app --reload --port 8000
```
API docs: http://127.0.0.1:8000/docs

Terminal 2 — Streamlit frontend:
```bash
streamlit run app.py
```
Streamlit normally opens http://localhost:8501.

The Streamlit app currently runs its recommendation/chat logic locally for responsiveness. The FastAPI service exposes the corresponding endpoints for API testing and future integration.

## 3. Optional MongoDB
Set `MONGODB_URI` and `MONGODB_DATABASE` in `.env`. A local MongoDB instance or MongoDB Atlas connection can be used. If MongoDB is not set up or reachable, the app continues to work; saving to the database is skipped and a message is shown. Never commit database credentials.

## 4. Optional LLM chatbot
Set `OPENAI_API_KEY` and optionally `OPENAI_MODEL` in `.env`. Keep the key private and never place it in source code or GitHub. Without the key, the chatbot uses a small local TF-IDF retrieval knowledge base.

## API examples
```bash
curl http://127.0.0.1:8000/health
curl -X POST http://127.0.0.1:8000/recommend -H "Content-Type: application/json" -d '{"name":"Student","education":"B.Tech","degree":"Computer Science","skills":["Python","Git"],"interests":["software development"],"experience":"Student projects","goal":"Become a software developer"}'
```

## Project structure
```text
career_agent_project/
├── app.py
├── backend/
│   ├── __init__.py
│   └── main.py
├── data/
│   └── careers.json
├── services/
│   ├── database.py
│   ├── guidance.py
│   └── recommender.py
├── .env.example
├── .gitignore
├── requirements.txt
└── README.md
```

## Important limitations / next steps
- The included career catalogue is a small illustrative dataset, not a trained model on a large real-world dataset. Scores mean text similarity, not probability of getting hired.
- Job and internship suggestions are role categories and links to job-search websites, not live verified listings. Integrate official job APIs or a trusted data provider if live jobs are required.
- Resume analysis uses PDF text extraction and exact keyword matching; scanned PDFs need OCR and a stronger parser.
- The local chatbot knowledge base is limited. The optional LLM gives more flexible responses but requires an API key and may incur cost.
- Before production use, add authentication, user consent, privacy policy, input limits, secure deployment, logging controls, tests, and a larger reviewed career/course dataset.
