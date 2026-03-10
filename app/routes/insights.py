from fastapi import APIRouter, HTTPException
from bson import ObjectId

from app.core.database import get_db
from app.services.irt import performance_summary
from app.services.llm import generate_study_plan
from app.models.schemas import ResponseRecord

router = APIRouter()


@router.get("/insights/{session_id}")
async def get_insights(session_id: str):
    """
    After a session is complete, generate a personalized AI study plan
    using the student's performance data.
    """
    db = get_db()

    if not ObjectId.is_valid(session_id):
        raise HTTPException(status_code=400, detail="Invalid session_id")

    session = await db["sessions"].find_one({"_id": ObjectId(session_id)})
    if not session:
        raise HTTPException(status_code=404, detail="Session not found")

    if not session["is_complete"]:
        raise HTTPException(
            status_code=400,
            detail=f"Session not yet complete. "
                   f"{session['questions_answered']}/{session['max_questions']} questions answered.",
        )

    # Build ResponseRecord objects for summary
    responses = [ResponseRecord(**r) for r in session.get("responses", [])]
    topic_summary = performance_summary(responses)

    # Generate AI study plan
    study_plan = generate_study_plan(
        student_name=session.get("student_name", "Student"),
        final_ability=session["ability_score"],
        topic_summary=topic_summary,
    )

    return {
        "session_id": session_id,
        "student_name": session.get("student_name"),
        "final_ability_score": session["ability_score"],
        "questions_answered": session["questions_answered"],
        "topic_summary": topic_summary,
        "study_plan": study_plan,
    }
