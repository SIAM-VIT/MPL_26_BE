from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
import random

from app.database import get_db
from app.models import Team, Question, QuestionType, QuestionSet, TeamQuestionState, QuestionStateStatus
from app.schemas import TeamLogin, TeamStatusResponse
from app.services.access import new_session_token, now_naive_utc

router = APIRouter()


@router.post("/login", response_model=TeamStatusResponse)
async def login(login_data: TeamLogin, db: AsyncSession = Depends(get_db)):
    result = await db.execute(select(Team).where(Team.name == login_data.name))
    team = result.scalars().first()

    if not team or team.passcode != login_data.passcode:
        raise HTTPException(status_code=401, detail="Invalid team name or passcode")

    first_login = team.timer_start_time is None
    if first_login:
        team.timer_start_time = now_naive_utc()

    # 1. Check if this team already has an allocated question set
    qs_res = await db.execute(
        select(QuestionSet).where(QuestionSet.allocated_team_id == team.id)
    )
    question_set = qs_res.scalars().first()

    # 2. If not, find an unallocated question set and assign it exclusively
    if not question_set:
        unallocated_res = await db.execute(
            select(QuestionSet)
            .where(QuestionSet.is_allocated == False)
            .order_by(QuestionSet.id)
        )
        question_set = unallocated_res.scalars().first()
        if question_set:
            question_set.is_allocated = True
            question_set.allocated_team_id = team.id
            question_set.allocated_at = now_naive_utc()
            db.add(question_set)

    # 3. Determine the list of questions for this team
    assigned_questions = []
    if question_set:
        assigned_questions = question_set.questions
        if assigned_questions and not team.main_question_id:
            team.main_question_id = assigned_questions[0].id
    else:
        # Fallback if no question set exists
        all_q_res = await db.execute(
            select(Question)
            .where(Question.type == QuestionType.MAIN)
            .order_by(Question.order_index, Question.id)
            .limit(3)
        )
        assigned_questions = all_q_res.scalars().all()
        if assigned_questions and not team.main_question_id:
            team.main_question_id = assigned_questions[0].id

    # 4. Ensure TeamQuestionState exists for each assigned question
    for question in assigned_questions:
        existing = (
            await db.execute(
                select(TeamQuestionState).where(
                    TeamQuestionState.team_id == team.id,
                    TeamQuestionState.question_id == question.id,
                )
            )
        ).scalars().first()
        if not existing:
            db.add(
                TeamQuestionState(
                    team_id=team.id,
                    question_id=question.id,
                    status=QuestionStateStatus.ASSIGNED,
                )
            )

    # Always (re)issue a session token so the team can call /api/main/*.
    team.session_token = new_session_token()

    db.add(team)
    await db.commit()
    await db.refresh(team)
    return team

