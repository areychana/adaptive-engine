"""
LLM Insights Service
Calls Anthropic Claude to generate a personalized 3-step study plan
based on the student's session performance summary.
"""

import os
import anthropic
from typing import Dict
from dotenv import load_dotenv

load_dotenv()

client = anthropic.Anthropic(api_key=os.getenv("ANTHROPIC_API_KEY"))


def build_prompt(
    student_name: str,
    final_ability: float,
    topic_summary: Dict,
) -> str:
    topic_lines = []
    for topic, stats in topic_summary.items():
        accuracy_pct = int(stats["accuracy"] * 100)
        topic_lines.append(
            f"  - {topic}: {accuracy_pct}% accuracy, "
            f"avg difficulty reached = {stats['avg_difficulty_reached']:.2f}/1.0 "
            f"({stats['questions_attempted']} questions)"
        )

    topics_text = "\n".join(topic_lines) if topic_lines else "  - No topic data available"

    return f"""You are an expert GRE tutor and learning coach.

A student named {student_name} just completed an adaptive diagnostic test.

PERFORMANCE SUMMARY:
- Final ability score: {final_ability:.2f} / 1.0  (0 = beginner, 1 = expert)
- Topic breakdown:
{topics_text}

Based on this data, generate a concise, actionable 3-step personalized study plan.

Rules:
1. Each step must be specific and tied to their weakest topics.
2. Recommend concrete resources or practice strategies (not generic advice).
3. Prioritize topics with accuracy below 60% or difficulty below 0.4.
4. Keep each step to 2-3 sentences max.
5. End with one motivational sentence.

Format your response as:
STEP 1: [Title]
[Action]

STEP 2: [Title]
[Action]

STEP 3: [Title]
[Action]

[Motivational closing]"""


def generate_study_plan(
    student_name: str,
    final_ability: float,
    topic_summary: Dict,
) -> str:
    """
    Calls Anthropic Claude and returns a personalized 3-step study plan.
    Falls back gracefully if API key is missing.
    """
    api_key = os.getenv("ANTHROPIC_API_KEY")
    if not api_key:
        return (
            "⚠️  ANTHROPIC_API_KEY not set. "
            "Add it to your .env file to enable AI-powered study plans."
        )

    prompt = build_prompt(student_name, final_ability, topic_summary)

    message = client.messages.create(
        model="claude-opus-4-5",
        max_tokens=600,
        messages=[{"role": "user", "content": prompt}],
    )

    return message.content[0].text
