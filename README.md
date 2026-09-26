# Nutrition Agent - starter project

A working skeleton for the "Nutrition Agent" problem statement: 4 GPT-backed
agents (Nutrition Knowledge, Diet Recommendation, Health Advisory, Food Log &
Feedback), a small FAISS-based RAG layer with a live USDA API fallback, and a
simple dashboard - all in a Flask app, matching the file list your mentor's
template asks for (app.py, requirements.txt, style.css, .env, index.html).

## 1. Get IBM Bob running (optional, for the "IBM Bob" mandatory stack line)

- Trial sign-up: https://bob.ibm.com/trial
- Open this project folder inside Bob and use its chat panel to extend or
  modify any file below - e.g. "add a 5th agent that suggests recipes" or
  "make the dashboard show a weekly view instead of just today."
- Screenshot Bob's chat panel (your prompt + its response) for slides 11-13
  of your deck, which explicitly ask for "IBM Bob output screenshots with
  2-3 prompts."

## 2. Get your API keys

- **OpenAI key** (required): https://platform.openai.com/api-keys
  Free-tier accounts get a small starting credit; gpt-4o-mini calls are cheap
  enough that a demo costs well under $1. If your credit has expired, you'll
  need to add a small amount of billing (even $5 covers a lot of demo usage)
  at platform.openai.com/settings/organization/billing.
- **USDA FoodData Central key** (optional): https://api.data.gov/signup/
  Takes 30 seconds, arrives by email instantly. Without it, the app falls
  back to the public `DEMO_KEY`, which is rate-limited but works fine for a
  demo.

Copy `.env.example` to `.env` and fill both in:

```bash
cp .env.example .env
# then edit .env with a text editor
```

## 3. Install and run

```bash
python -m venv venv
source venv/bin/activate        # Windows: venv\Scripts\activate
pip install -r requirements.txt
python app.py
```

Open http://127.0.0.1:5000 in your browser.

## 4. How the pieces map to the problem statement

| Problem statement requirement | Where it lives |
|---|---|
| Nutrition Knowledge Agent | `rag_and_agents/agents.py` -> `nutrition_knowledge_agent` |
| Diet Recommendation Agent | `rag_and_agents/agents.py` -> `diet_recommendation_agent` |
| Health Advisory Agent | `rag_and_agents/agents.py` -> `health_advisory_agent` |
| Food Log & Feedback Agent | `rag_and_agents/agents.py` -> `food_log_agent` |
| Food Data RAG Retrieval | `rag_and_agents/rag.py` (FAISS + USDA API) |
| Visualization Dashboard | `templates/index.html` chart section + `/api/dashboard` |
| Personalized diet plans | Profile form -> `/api/profile` route |
| Diet tracking & feedback | Meal log form -> `/api/log` route |

## 5. What's simplified for the demo (say this out loud to judges, don't hide it)

- **Storage**: user profile and today's logged meals live in the Flask
  session (a signed cookie), not a database. Fine for a live demo, restarts
  on server restart. If you have time, swap in SQLite - a few lines change.
- **Multi-modal logging**: only text logging is wired up. To add image
  logging, send the photo to GPT-4o's vision endpoint instead of text (same
  `food_log_agent` function, different input) - see
  https://platform.openai.com/docs/guides/vision
- **Voice logging**: transcribe with Whisper first
  (https://platform.openai.com/docs/guides/speech-to-text), then feed the
  transcript into the existing `food_log_agent`.

## 6. Next: push to GitHub

1. Create a **public** repo, tick "Add a README" (your template asks for this).
2. Upload this whole folder, your problem-statement PDF, and your final
   `.pptx`.
3. Paste the working GitHub URL into slide 15 of your deck.

## 7. Extending with watsonx.ai / Granite instead of (or alongside) GPT

If your program provides free watsonx.ai credits and you want to show that
stack too, `agents.py`'s `_call_llm` function is the only place that talks to
an LLM - swap the OpenAI client there for IBM's `ibm-watsonx-ai` SDK
(https://ibm.github.io/watsonx-ai-python-sdk/) and point it at a Granite
model (e.g. `ibm/granite-3-2-8b-instruct`). Everything else - the agent
roles, the RAG layer, the Flask routes, the UI - stays the same.
