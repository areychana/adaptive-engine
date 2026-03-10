"""
Adaptive Algorithm — Rasch Model (1-Parameter IRT)
====================================================

In the Rasch model, the probability that a student with ability θ (theta)
answers a question of difficulty b correctly is:

    P(correct | θ, b) = exp(θ - b) / (1 + exp(θ - b))

After each response, we update θ using a simplified MLE step:

    θ_new = θ_old + learning_rate * (observed - expected)

Where:
    observed = 1 if correct, 0 if incorrect
    expected = P(correct | θ_old, b)   ← probability from Rasch formula above

We scale both θ and b to [0, 1] for simplicity.
Internally θ lives in [-3, 3] (logit space) and is mapped back to [0, 1].
"""

import math
from typing import List
from app.models.schemas import ResponseRecord


LEARNING_RATE = 0.5     # Controls how fast ability estimate moves
MIN_ABILITY = 0.05      # Floor (maps to logit ≈ -3)
MAX_ABILITY = 0.95      # Ceiling (maps to logit ≈ +3)
DIFFICULTY_BAND = 0.2   # How close next question difficulty should be to θ


def _to_logit(p: float) -> float:
    """Map probability [0,1] → logit space [-∞, +∞]. Clamped for safety."""
    p = max(0.001, min(0.999, p))
    return math.log(p / (1 - p))


def _to_prob(logit: float) -> float:
    """Map logit → probability [0,1]."""
    return math.exp(logit) / (1 + math.exp(logit))


def rasch_probability(ability: float, difficulty: float) -> float:
    """
    P(correct) given ability θ and item difficulty b.
    Both are in [0,1]; convert to logit space first.
    """
    theta = _to_logit(ability)
    b = _to_logit(difficulty)
    return _to_prob(theta - b)


def update_ability(
    current_ability: float,
    difficulty: float,
    is_correct: bool,
) -> float:
    """
    MLE update step for θ after one response.
    Returns updated ability clamped to [MIN_ABILITY, MAX_ABILITY].
    """
    expected = rasch_probability(current_ability, difficulty)
    observed = 1.0 if is_correct else 0.0

    theta = _to_logit(current_ability)
    theta_new = theta + LEARNING_RATE * (observed - expected)

    updated = _to_prob(theta_new)
    return round(max(MIN_ABILITY, min(MAX_ABILITY, updated)), 4)


def select_next_difficulty(
    ability: float,
    answered_ids: List[str],
) -> float:
    """
    Target difficulty = current ability (challenge the student at their edge).
    The route layer will find the closest unanswered question to this target.
    """
    return round(max(0.1, min(1.0, ability)), 2)


def performance_summary(responses: List[ResponseRecord]) -> dict:
    """
    Summarise session results for LLM prompt construction.
    Returns topic-level accuracy and overall stats.
    """
    if not responses:
        return {}

    topic_stats: dict = {}
    for r in responses:
        t = r.topic
        if t not in topic_stats:
            topic_stats[t] = {"correct": 0, "total": 0, "difficulties": []}
        topic_stats[t]["total"] += 1
        topic_stats[t]["difficulties"].append(r.difficulty)
        if r.is_correct:
            topic_stats[t]["correct"] += 1

    summary = {}
    for topic, stats in topic_stats.items():
        accuracy = stats["correct"] / stats["total"]
        avg_diff = sum(stats["difficulties"]) / len(stats["difficulties"])
        summary[topic] = {
            "accuracy": round(accuracy, 2),
            "avg_difficulty_reached": round(avg_diff, 2),
            "questions_attempted": stats["total"],
        }

    return summary
