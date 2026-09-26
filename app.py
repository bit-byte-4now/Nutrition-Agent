"""
Nutrition Agent - Flask backend.

Routes:
  GET  /                -> serves the single-page UI
  POST /api/profile     -> save the user's profile, generate + return a diet plan
  POST /api/log         -> log a meal (text), return instant nutrition feedback
  GET  /api/dashboard   -> today's running totals, for the chart

State is kept in the Flask session (server-side signed cookie) so this needs
no database for a demo - restart the server and it resets, which is fine here.
"""
import os
from datetime import date

from dotenv import load_dotenv
from flask import Flask, jsonify, render_template, request, session

load_dotenv()

from rag_and_agents import agents  # noqa: E402 (must load env vars first)

app = Flask(__name__)
app.secret_key = os.environ.get("FLASK_SECRET_KEY", "dev-only-change-me")


def _today_key():
    return str(date.today())


@app.route("/")
def index():
    return render_template("index.html")


@app.route("/api/profile", methods=["POST"])
def save_profile():
    profile = request.json or {}
    session["profile"] = profile
    session.setdefault("logs", {})

    # Agent 1 fetches supporting nutrition data for one or two staple foods
    # mentioned in the user's cultural preference, if any, to ground the plan.
    seed_foods = profile.get("cultural_preference_foods", ["roti", "dal", "rice"])
    nutrition = agents.nutrition_knowledge_agent(seed_foods)

    # Agent 2 builds the plan, Agent 3 reviews it
    plan = agents.diet_recommendation_agent(profile, nutrition["summary"])
    advisory = agents.health_advisory_agent(profile, plan)

    session["latest_plan"] = plan
    return jsonify({"plan": plan, "advisory": advisory})


@app.route("/api/log", methods=["POST"])
def log_meal():
    profile = session.get("profile", {})
    meal_text = (request.json or {}).get("meal_text", "")
    if not meal_text.strip():
        return jsonify({"error": "meal_text is required"}), 400

    result = agents.food_log_agent(profile, meal_text)

    # running daily totals for the dashboard - sum whatever numeric fields
    # came back from the RAG data (skips any items with missing values)
    logs = session.get("logs", {})
    today = logs.setdefault(_today_key(), {"calories": 0, "protein_g": 0, "carbs_g": 0, "fat_g": 0, "meals": []})
    for item in result["nutrition_data"]:
        for field in ("calories", "protein_g", "carbs_g", "fat_g"):
            value = item.get(field)
            if isinstance(value, (int, float)):
                today[field] += value
    today["meals"].append(meal_text)
    session["logs"] = logs

    return jsonify({"feedback": result["feedback"], "items": result["items"], "totals_today": today})


@app.route("/api/dashboard")
def dashboard():
    logs = session.get("logs", {})
    today = logs.get(_today_key(), {"calories": 0, "protein_g": 0, "carbs_g": 0, "fat_g": 0, "meals": []})
    return jsonify(today)


if __name__ == "__main__":
    app.run(debug=True, port=5000)
