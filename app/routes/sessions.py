from fastapi import APIRouter, HTTPException
from bson import ObjectId
from datetime import datetime

from app.core.database import get_db
from app.models.schemas import (
    UserSession,
    SubmitAnswerRequest,
    SubmitAnswerResponse,
    QuestionResponse,
    ResponseRecord,
)
from app.services.irt import update_ability, select_next_difficulty

router = APIRouter()


def _fmt_question(q: dict) -> QuestionResponse:
    return QuestionResponse(
        id=str(q["_id"]),
        text=q["text"],
        options=q["options"],
        difficulty=q["difficulty"],
        topic=q["topic"],
        tags=q.get("tags", []),
    )


async def _get_next_question(db, ability: float, answered_ids: list) -> dict | None:
    target = select_next_difficulty(ability, answered_ids)
    object_ids = [ObjectId(i) for i in answered_ids if ObjectId.is_valid(i)]

    # Find closest unanswered question by difficulty
    question = await db["questions"].find_one(
        {
            "_id": {"$nin": object_ids},
            "difficulty": {"$gte": max(0.1, target - 0.25), "$lte": min(1.0, target + 0.25)},
        }
    )

    # Widen search if nothing found in band
    if not question:
        question = await db["questions"].find_one({"_id": {"$nin": object_ids}})

    return question


# ─── Start Session ────────────────────────────────────────────────────────────

@router.post("/session/start", response_model=dict)
async def start_session(student_name: str = "Anonymous"):
    db = get_db()

    # First question at baseline difficulty 0.5
    first_q = await db["questions"].find_one(
        {"difficulty": {"$gte": 0.45, "$lte": 0.55}}
    )
    if not first_q:
        first_q = await db["questions"].find_one()
    if not first_q:
        raise HTTPException(status_code=404, detail="No questions in database. Run seed script first.")

    session = {
        "student_name": student_name,
        "ability_score": 0.5,
        "questions_answered": 0,
        "max_questions": 10,
        "is_complete": False,
        "responses": [],
        "current_question_id": str(first_q["_id"]),
        "answered_ids": [str(first_q["_id"])],
        "created_at": datetime.utcnow(),
    }

    result = await db["sessions"].insert_one(session)
    session_id = str(result.inserted_id)

    return {
        "session_id": session_id,
        "student_name": student_name,
        "ability_score": 0.5,
        "first_question": _fmt_question(first_q),
        "message": f"Session started! Answer {session['max_questions']} questions to get your personalized study plan.",
    }


# ─── Submit Answer ─────────────────────────────────────────────────────────

@router.post("/submit-answer", response_model=SubmitAnswerResponse)
async def submit_answer(payload: SubmitAnswerRequest):
    db = get_db()

    if not ObjectId.is_valid(payload.session_id):
        raise HTTPException(status_code=400, detail="Invalid session_id")
    if not ObjectId.is_valid(payload.question_id):
        raise HTTPException(status_code=400, detail="Invalid question_id")

    session = await db["sessions"].find_one({"_id": ObjectId(payload.session_id)})
    if not session:
        raise HTTPException(status_code=404, detail="Session not found")
    if session["is_complete"]:
        raise HTTPException(status_code=400, detail="Session is already complete")

    question = await db["questions"].find_one({"_id": ObjectId(payload.question_id)})
    if not question:
        raise HTTPException(status_code=404, detail="Question not found")

    # Grade the answer
    is_correct = payload.answer.strip().upper() == question["correct_answer"].strip().upper()

    # Rasch model update
    new_ability = update_ability(
        current_ability=session["ability_score"],
        difficulty=question["difficulty"],
        is_correct=is_correct,
    )

    # Record response
    response_record = {
        "question_id": payload.question_id,
        "topic": question["topic"],
        "difficulty": question["difficulty"],
        "is_correct": is_correct,
        "timestamp": datetime.utcnow(),
    }

    questions_answered = session["questions_answered"] + 1
    is_complete = questions_answered >= session["max_questions"]

    answered_ids = session.get("answered_ids", []) + [payload.question_id]

    # Get next question if not done
    next_q = None
    next_q_formatted = None
    if not is_complete:
        next_q = await _get_next_question(db, new_ability, answered_ids)
        if next_q:
            next_q_formatted = _fmt_question(next_q)
            answered_ids.append(str(next_q["_id"]))

    # Update session in DB
    await db["sessions"].update_one(
        {"_id": ObjectId(payload.session_id)},
        {
            "$set": {
                "ability_score": new_ability,
                "questions_answered": questions_answered,
                "is_complete": is_complete,
                "answered_ids": answered_ids,
            },
            "$push": {"responses": response_record},
        },
    )

    return SubmitAnswerResponse(
        is_correct=is_correct,
        correct_answer=question["correct_answer"],
        updated_ability_score=new_ability,
        questions_answered=questions_answered,
        is_complete=is_complete,
        next_question=next_q_formatted,
        message=(
            "Test complete! Call GET /api/insights/{session_id} for your study plan."
            if is_complete
            else f"{'Correct! Moving up.' if is_correct else 'Incorrect. Adjusting difficulty.'} Ability: {new_ability:.2f}"
        ),
    )


# ─── Get Session ─────────────────────────────────────────────────────────────

@router.get("/session/{session_id}")
async def get_session(session_id: str):
    db = get_db()
    if not ObjectId.is_valid(session_id):
        raise HTTPException(status_code=400, detail="Invalid session_id")
    session = await db["sessions"].find_one({"_id": ObjectId(session_id)})
    if not session:
        raise HTTPException(status_code=404, detail="Session not found")
    session["_id"] = str(session["_id"])
    return session
