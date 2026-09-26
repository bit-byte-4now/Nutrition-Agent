"""
The multi-agent system. Each function is one agent from the problem statement.
Every agent is just: (1) a distinct system prompt defining its role, and
(2) a call to GPT with whatever context it needs. Orchestration between them
happens in app.py, which calls these in sequence and passes each agent's
output into the next.
"""
import os
from openai import OpenAI

from . import rag

client = OpenAI(api_key=os.environ.get("OPENAI_API_KEY"))
MODEL = "gpt-4o-mini"  # fast + cheap, swap for "gpt-4o" if you want higher quality


def _call_llm(system_prompt, user_content):
    response = client.chat.completions.create(
        model=MODEL,
        messages=[
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": user_content},
        ],
        temperature=0.4,
    )
    return response.choices[0].message.content


# ---- Agent 1: Nutrition Knowledge Agent -----------------------------------
def nutrition_knowledge_agent(food_names):
    """Retrieves nutrition facts (via RAG) and summarizes them in plain language."""
    facts = []
    for name in food_names:
        facts.extend(rag.get_nutrition_info(name))

    system_prompt = (
        "You are the Nutrition Knowledge Agent. You are given raw nutrition data "
        "(calories, macros) for some foods. Summarize it clearly and briefly, "
        "in plain language a non-expert can follow. Do not invent numbers that "
        "aren't in the data."
    )
    user_content = f"Raw nutrition data:\n{facts}"
    summary = _call_llm(system_prompt, user_content)
    return {"raw_data": facts, "summary": summary}


# ---- Agent 2: Diet Recommendation Agent -----------------------------------
def diet_recommendation_agent(profile, nutrition_context):
    """Generates a personalized meal plan from the user's profile + retrieved facts."""
    system_prompt = (
        "You are the Diet Recommendation Agent. Using the user's profile "
        "(age, health conditions, allergies, cultural preferences, fitness goals) "
        "and the nutrition data provided, propose a one-day meal plan "
        "(breakfast, lunch, dinner, one snack). Respect allergies strictly. "
        "Keep it practical and culturally appropriate. Be concise."
    )
    user_content = f"User profile: {profile}\n\nAvailable nutrition data: {nutrition_context}"
    return _call_llm(system_prompt, user_content)


# ---- Agent 3: Health Advisory Agent ----------------------------------------
def health_advisory_agent(profile, diet_plan):
    """Reviews a diet plan against any stated health conditions and flags concerns."""
    system_prompt = (
        "You are the Health Advisory Agent. You review a proposed meal plan "
        "against the user's stated health conditions (e.g. diabetes, "
        "hypertension, heart disease) and flag anything risky, and suggest "
        "specific swaps if needed. If no conditions were stated, just give one "
        "general preventive-health tip. Be concise and non-alarmist."
    )
    user_content = f"User profile: {profile}\n\nProposed plan: {diet_plan}"
    return _call_llm(system_prompt, user_content)


# ---- Agent 4: Food Log & Feedback Agent ------------------------------------
def food_log_agent(profile, logged_meal_text):
    """Analyzes a meal the user logged (as free text) and gives instant feedback."""
    # crude but effective for a demo: ask GPT to pull out food item names first
    extraction_prompt = (
        "Extract just the distinct food item names mentioned in this meal "
        "description, as a comma-separated list, nothing else."
    )
    items_raw = _call_llm(extraction_prompt, logged_meal_text)
    items = [item.strip() for item in items_raw.split(",") if item.strip()]

    nutrition = nutrition_knowledge_agent(items)

    system_prompt = (
        "You are the Food Log & Feedback Agent. The user just logged a meal. "
        "Using the retrieved nutrition data, estimate total calories and macros "
        "for the meal, compare it briefly to what a balanced meal should look "
        "like for this user's profile, and give one actionable piece of feedback."
    )
    user_content = (
        f"User profile: {profile}\n"
        f"Logged meal: {logged_meal_text}\n"
        f"Retrieved nutrition data: {nutrition['raw_data']}"
    )
    feedback = _call_llm(system_prompt, user_content)
    return {"items": items, "nutrition_data": nutrition["raw_data"], "feedback": feedback}
