from fastapi import APIRouter, HTTPException
from app.core.database import get_db

router = APIRouter()


@router.get("/questions")
async def list_questions(topic: str = None, limit: int = 20):
    """List all questions (admin/debug use)."""
    db = get_db()
    query = {}
    if topic:
        query["topic"] = topic
    cursor = db["questions"].find(query).limit(limit)
    questions = []
    async for q in cursor:
        q["_id"] = str(q["_id"])
        q.pop("correct_answer", None)  # Don't expose answer
        questions.append(q)
    return {"count": len(questions), "questions": questions}


@router.get("/next-question/{session_id}")
async def get_next_question(session_id: str):
    """
    Convenience endpoint: returns the next question for a session
    without requiring a submission (useful for resuming).
    """
    from bson import ObjectId
    db = get_db()

    if not ObjectId.is_valid(session_id):
        raise HTTPException(status_code=400, detail="Invalid session_id")

    session = await db["sessions"].find_one({"_id": ObjectId(session_id)})
    if not session:
        raise HTTPException(status_code=404, detail="Session not found")
    if session["is_complete"]:
        raise HTTPException(status_code=400, detail="Session complete. Fetch insights instead.")

    answered_ids = session.get("answered_ids", [])
    object_ids = [ObjectId(i) for i in answered_ids if ObjectId.is_valid(i)]

    ability = session["ability_score"]
    from app.services.irt import select_next_difficulty
    target = select_next_difficulty(ability, answered_ids)

    question = await db["questions"].find_one(
        {
            "_id": {"$nin": object_ids},
            "difficulty": {"$gte": max(0.1, target - 0.25), "$lte": min(1.0, target + 0.25)},
        }
    )
    if not question:
        question = await db["questions"].find_one({"_id": {"$nin": object_ids}})
    if not question:
        raise HTTPException(status_code=404, detail="No more questions available")

    question["_id"] = str(question["_id"])
    question.pop("correct_answer", None)
    return question
