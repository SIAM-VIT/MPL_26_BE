"""Builds the team-facing view of the MAIN questions.

Backs GET /api/main/questions. Hidden tests are stripped here: only
non-hidden TestCase rows are ever placed into the response.
"""
from __future__ import annotations

from typing import List

from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select

from app.models import CompareMode, Question, QuestionType, QuestionSet, Team, TestCase, TeamQuestionState, QuestionStateStatus
from app.schemas import MainQuestionPublic, TestCasePublic
from app.services.access import now_naive_utc
from app.services.progress import get_state
from app.services.questions import starter_bundle


async def team_question_views(db: AsyncSession, team: Team) -> List[MainQuestionPublic]:
    """The team's MAIN questions (always exactly 3 in their set). Hidden tests are stripped here."""
    # Check if team has an allocated question set
    qs_res = await db.execute(
        select(QuestionSet).where(QuestionSet.allocated_team_id == team.id)
    )
    question_set = qs_res.scalars().first()

    if question_set and question_set.questions:
        questions = question_set.questions
    else:
        # Auto-allocate an available question set exclusively to this team
        unallocated_res = await db.execute(
            select(QuestionSet)
            .where(QuestionSet.is_allocated == False)
            .order_by(QuestionSet.id)
        )
        unallocated_qs = unallocated_res.scalars().first()
        if unallocated_qs:
            unallocated_qs.is_allocated = True
            unallocated_qs.allocated_team_id = team.id
            unallocated_qs.allocated_at = now_naive_utc()
            db.add(unallocated_qs)
            await db.commit()
            await db.refresh(unallocated_qs)
            questions = unallocated_qs.questions
        else:
            # Fallback to the first question set (3 questions)
            first_qs = (await db.execute(select(QuestionSet).order_by(QuestionSet.id))).scalars().first()
            if first_qs and first_qs.questions:
                questions = first_qs.questions
            else:
                questions = (
                    await db.execute(
                        select(Question)
                        .where(Question.type == QuestionType.MAIN)
                        .order_by(Question.order_index, Question.id)
                        .limit(3)
                    )
                ).scalars().all()


    out: List[MainQuestionPublic] = []
    for question in questions:
        cases = (
            await db.execute(
                select(TestCase)
                .where(TestCase.question_id == question.id)
                .order_by(TestCase.position, TestCase.id)
            )
        ).scalars().all()

        state = await get_state(db, team.id, question.id)
        await db.commit()

        visible = [
            TestCasePublic(
                id=c.id, stdin=c.stdin, expected_output=c.expected_output, position=c.position
            )
            for c in cases
            if not c.is_hidden
        ]

        out.append(
            MainQuestionPublic(
                id=question.id,
                title=question.title,
                description=question.description,
                sub_type=question.sub_type,
                difficulty=question.difficulty,
                points=question.points or question.reward_value or 0,
                compare_mode=question.compare_mode or CompareMode.TRIM,
                starter_code=starter_bundle(question),
                allowed_languages=question.allowed_languages,
                order_index=question.order_index or 0,
                visible_tests=visible,
                attempts=state.attempts or 0,
                best_score=state.best_score or 0,
                status=state.status,
            )
        )
    return out
