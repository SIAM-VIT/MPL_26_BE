"""Admin question management: create and patch questions."""
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select

from app.database import get_db
from app.models import Question
from app.schemas import QuestionCreate
from app.routes.admin.deps import verify_admin

router = APIRouter()


@router.get("/questions")
async def list_questions(db: AsyncSession = Depends(get_db), _: None = Depends(verify_admin)):
    result = await db.execute(select(Question).order_by(Question.order_index, Question.id))
    questions = result.scalars().all()
    return [
        {
            "id": q.id,
            "title": q.title,
            "description": q.description,
            "type": q.type.value if q.type else None,
            "difficulty": q.difficulty.value if q.difficulty else None,
            "reward_value": q.reward_value,
            "sub_type": q.sub_type.value if q.sub_type else None,
            "points": q.points,
            "compare_mode": q.compare_mode.value if q.compare_mode else None,
            "starter_code": q.starter_code,
            "allowed_languages": q.allowed_languages,
            "order_index": q.order_index,
        }
        for q in questions
    ]


@router.post("/questions")
async def create_question(question: QuestionCreate, db: AsyncSession = Depends(get_db), _: None = Depends(verify_admin)):
    new_question = Question(**question.model_dump())
    db.add(new_question)
    await db.commit()
    return {"message": "Question created", "id": new_question.id}


@router.patch("/questions/{question_id}")
async def update_question(
    question_id: int,
    payload: dict,
    db: AsyncSession = Depends(get_db),
    _: None = Depends(verify_admin),
):
    question = (await db.execute(select(Question).where(Question.id == question_id))).scalars().first()
    if not question:
        raise HTTPException(status_code=404, detail="Question not found")
    allowed = {c.name for c in Question.__table__.columns} - {"id"}
    for key, value in payload.items():
        if key in allowed:
            setattr(question, key, value)
    return {"message": "Question updated", "id": question.id}


# ── Question Sets Management ─────────────────────────────────────────────────

@router.get("/question-sets")
async def list_question_sets(db: AsyncSession = Depends(get_db), _: None = Depends(verify_admin)):
    from app.models import QuestionSet
    result = await db.execute(select(QuestionSet).order_by(QuestionSet.id))
    sets = result.scalars().all()
    return [
        {
            "id": s.id,
            "name": s.name,
            "is_allocated": s.is_allocated,
            "allocated_team_id": s.allocated_team_id,
            "allocated_at": s.allocated_at,
            "debug_question": {"id": s.debug_question.id, "title": s.debug_question.title} if s.debug_question else None,
            "math_question": {"id": s.math_question.id, "title": s.math_question.title} if s.math_question else None,
            "leetcode_question": {"id": s.leetcode_question.id, "title": s.leetcode_question.title} if s.leetcode_question else None,
        }
        for s in sets
    ]


@router.post("/question-sets")
async def create_question_set(payload: dict, db: AsyncSession = Depends(get_db), _: None = Depends(verify_admin)):
    from app.models import QuestionSet
    new_set = QuestionSet(
        name=payload.get("name"),
        debug_question_id=payload.get("debug_question_id"),
        math_question_id=payload.get("math_question_id"),
        leetcode_question_id=payload.get("leetcode_question_id"),
    )
    db.add(new_set)
    await db.commit()
    await db.refresh(new_set)
    return {"message": "Question set created", "id": new_set.id}

