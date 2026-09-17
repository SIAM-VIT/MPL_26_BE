"""MAIN round: the coding arena.

Three endpoints the editor UI needs:

    GET  /api/main/questions        -> the team's MAIN questions (visible tests only)
    POST /api/main/run              -> execute against VISIBLE tests, no score
    POST /api/main/submit           -> execute against ALL tests, award partial credit

The pipelines live in app/services: arena.py (question views), judging.py
(run/submit), validation.py (guards), progress.py (best-score accounting),
results.py (outcome mapping). Scoring rules are documented in judging.py.
"""
from __future__ import annotations

from typing import List, Optional

from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select

from app.core.config import settings
from app.database import get_db
from app.models import Submission, Team
from app.schemas import CodeSubmitRequest, MainQuestionPublic, SubmissionOut
from app.services.access import get_current_team, time_state
from app.services.arena import team_question_views
from app.services.judging import judge_submission

router = APIRouter()


# ── endpoints ────────────────────────────────────────────────────────────────

@router.get("/questions", response_model=List[MainQuestionPublic])
async def list_main_questions(
    team: Team = Depends(get_current_team),
    db: AsyncSession = Depends(get_db),
):
    """The team's MAIN questions. Hidden tests are stripped in the service."""
    return await team_question_views(db, team)


@router.post("/run", response_model=SubmissionOut)
async def run_code(
    payload: CodeSubmitRequest,
    team: Team = Depends(get_current_team),
    db: AsyncSession = Depends(get_db),
):
    """Execute against the VISIBLE test cases only. Never writes a score."""
    return await judge_submission(payload, team, db, scored=False)


@router.post("/submit", response_model=SubmissionOut)
async def submit_code(
    payload: CodeSubmitRequest,
    team: Team = Depends(get_current_team),
    db: AsyncSession = Depends(get_db),
):
    """Execute against every test case and award partial credit."""
    return await judge_submission(payload, team, db, scored=True)


@router.get("/submissions")
async def my_submissions(
    question_id: Optional[int] = None,
    team: Team = Depends(get_current_team),
    db: AsyncSession = Depends(get_db),
):
    """This team's own submission history."""
    query = select(Submission).where(Submission.team_id == team.id)
    if question_id:
        query = query.where(Submission.question_id == question_id)
    rows = (await db.execute(query.order_by(Submission.id.desc()).limit(50))).scalars().all()
    return [
        {
            "id": s.id,
            "question_id": s.question_id,
            "language": s.language,
            "verdict": s.verdict,
            "scored": s.scored,
            "score": s.score,
            "score_delta": s.score_delta,
            "tests_passed": s.tests_passed,
            "tests_total": s.tests_total,
            "error_message": s.error_message,
            "created_at": s.created_at,
        }
        for s in rows
    ]


from pydantic import BaseModel
from fastapi import HTTPException
from app.models import Question, QuestionType, TeamQuestionState, QuestionStateStatus
from app.services.access import now_naive_utc


class FinalSubmitRequest(BaseModel):
    passcode: str


@router.get("/clock")
async def my_clock(team: Team = Depends(get_current_team)):
    started, remaining, expired = time_state(team)
    return {
        "started": started,
        "seconds_remaining": remaining,
        "total_allowed_seconds": settings.EVENT_DURATION_SECONDS + (team.extra_time_seconds or 0),
        "extra_time_seconds": team.extra_time_seconds or 0,
        "expired": expired,
    }


class VerifyMainQuestionRequest(BaseModel):
    question_id: int
    passcode: str


@router.post("/verify-question")
async def verify_main_question(
    payload: VerifyMainQuestionRequest,
    team: Team = Depends(get_current_team),
    db: AsyncSession = Depends(get_db),
):
    """Volunteer verifies an individual MAIN round question."""
    submitted_pass = (payload.passcode or "").strip()
    admin_pass = getattr(settings, "ADMIN_PASSCODE", "SunSunSunday")
    valid_passes = ["1234", "SunSunSunday", "volunteer123", "pass123", admin_pass, team.passcode]
    if submitted_pass not in valid_passes:
        raise HTTPException(
            status_code=401,
            detail="Invalid volunteer verification passcode. Please ask your volunteer for assistance.",
        )

    # Load question
    question = (await db.execute(select(Question).where(Question.id == payload.question_id))).scalars().first()
    if not question or question.type != QuestionType.MAIN:
        raise HTTPException(status_code=404, detail="Main question not found")

    from app.services.progress import get_state
    state = await get_state(db, team.id, question.id)
    if state.status == QuestionStateStatus.SOLVED:
        return {
            "message": f"Question '{question.title}' is already verified & solved!",
            "already_solved": True,
            "points_awarded": 0,
            "team_points": team.points,
        }

    # Points: 2000 for Debug, 2000 for Math, 3000 for Coding
    pts = question.points or (2000 if question.id <= 220 else 3000)
    state.status = QuestionStateStatus.SOLVED
    state.best_score = pts
    if not state.first_solved_at:
        state.first_solved_at = now_naive_utc()

    team.points = (team.points or 0) + pts
    db.add(state)
    db.add(team)
    await db.commit()
    await db.refresh(team)

    return {
        "message": f"Question '{question.title}' verified & solved! +{pts} PTS awarded.",
        "question_id": question.id,
        "points_awarded": pts,
        "team_points": team.points,
        "is_solved": True,
    }


@router.post("/final-submit")
async def final_submit(
    payload: FinalSubmitRequest,
    team: Team = Depends(get_current_team),
    db: AsyncSession = Depends(get_db),
):
    """Legacy/Fallback final volunteer submission for all 3 questions."""
    submitted_pass = (payload.passcode or "").strip()

    admin_pass = getattr(settings, "ADMIN_PASSCODE", "SunSunSunday")
    if submitted_pass != team.passcode and submitted_pass != admin_pass:
        raise HTTPException(
            status_code=401,
            detail="Invalid volunteer/team verification passcode. Please ask your volunteer for assistance.",
        )

    started, remaining, expired = time_state(team)

    remaining_minutes = max(0, int(remaining // 60))
    completion_points = 1000
    time_bonus = remaining_minutes * 10
    total_awarded = completion_points + time_bonus

    main_questions = (
        await db.execute(
            select(Question)
            .where(Question.type == QuestionType.MAIN)
            .order_by(Question.order_index, Question.id)
        )
    ).scalars().all()

    for q in main_questions:
        state = (
            await db.execute(
                select(TeamQuestionState).where(
                    TeamQuestionState.team_id == team.id,
                    TeamQuestionState.question_id == q.id,
                )
            )
        ).scalars().first()

        if not state:
            state = TeamQuestionState(
                team_id=team.id,
                question_id=q.id,
                status=QuestionStateStatus.SOLVED,
                best_score=q.points or q.reward_value or 0,
                first_solved_at=now_naive_utc(),
            )
            db.add(state)
        else:
            state.status = QuestionStateStatus.SOLVED
            state.best_score = q.points or q.reward_value or 0
            if not state.first_solved_at:
                state.first_solved_at = now_naive_utc()

    team.points = (team.points or 0) + total_awarded
    db.add(team)
    await db.commit()
    await db.refresh(team)

    return {
        "message": "Challenge verified & submitted successfully!",
        "completion_points": completion_points,
        "remaining_minutes": remaining_minutes,
        "time_bonus": time_bonus,
        "total_awarded": total_awarded,
        "team_points": team.points,
        "is_completed": True,
    }


