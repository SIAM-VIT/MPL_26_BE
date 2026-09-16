"""Unchanged legacy endpoints (CHALLENGE / TIME_BOOST - out of scope for now).

These power boost.html and challenge.html: the admin assigns a boost question
or opens a challenge session, and manually marks it solved after reviewing
the team's answer. MAIN questions are graded automatically instead.
"""
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select

from app.database import get_db
from app.models import (
    Team, Question, TeamQuestionState, ChallengeSession, QuestionType,
    QuestionStateStatus, ChallengeStatus,
)
import random
from app.schemas import (
    ChallengeCreate, AssignBoost, ReviewMarkSolved,
    AssignRandomBoostRequest,
)
from app.routes.admin.deps import verify_admin
from app.models.enums import QuestionDifficulty

router = APIRouter()


@router.post("/teams/{team_id}/assign-random-boost")
async def assign_random_boost(
    team_id: int,
    req: AssignRandomBoostRequest = AssignRandomBoostRequest(),
    db: AsyncSession = Depends(get_db),
    _: None = Depends(verify_admin)
):
    team = (await db.execute(select(Team).where(Team.id == team_id))).scalars().first()
    if not team:
        raise HTTPException(status_code=404, detail="Team not found")

    # Fetch IDs of questions already assigned or solved by this team
    existing_states = (
        await db.execute(
            select(TeamQuestionState).where(
                TeamQuestionState.team_id == team_id,
                TeamQuestionState.status.in_([QuestionStateStatus.ASSIGNED, QuestionStateStatus.SOLVED])
            )
        )
    ).scalars().all()
    assigned_qids = {s.question_id for s in existing_states}

    # Query TIME_BOOST questions matching the requested difficulty
    diff_str = (req.difficulty or "MEDIUM").upper()
    try:
        target_diff = QuestionDifficulty(diff_str)
    except ValueError:
        target_diff = QuestionDifficulty.MEDIUM

    query = select(Question).where(
        Question.type == QuestionType.TIME_BOOST,
        Question.difficulty == target_diff
    )
    matching_questions = (await db.execute(query)).scalars().all()

    # Filter out already used ones
    available = [q for q in matching_questions if q.id not in assigned_qids]

    # If all of this difficulty are used, fallback to any unassigned TIME_BOOST question
    if not available:
        all_boost_q = (
            await db.execute(select(Question).where(Question.type == QuestionType.TIME_BOOST))
        ).scalars().all()
        available = [q for q in all_boost_q if q.id not in assigned_qids]

    # If still none or no TIME_BOOST questions seeded, create on the fly
    if not available:
        reward_map = {QuestionDifficulty.EASY: 300, QuestionDifficulty.MEDIUM: 600, QuestionDifficulty.HARD: 900}
        reward = reward_map.get(target_diff, 600)
        fallback_q = Question(
            title=f"Time Boost ({diff_str.capitalize()}): Algorithmic Speed Challenge",
            description=f"Quick {diff_str.capitalize()} Challenge: Write an optimized solution in your local IDE, demonstrate it to your volunteer, and verify with their passcode to earn +{reward // 60} minutes bonus.",
            type=QuestionType.TIME_BOOST,
            difficulty=target_diff,
            reward_value=reward,
            points=reward,
        )
        db.add(fallback_q)
        await db.flush()
        selected_q = fallback_q
    else:
        selected_q = random.choice(available)

    # Cancel any previous currently ASSIGNED boost questions for this team so only 1 active boost exists
    for s in existing_states:
        if s.status == QuestionStateStatus.ASSIGNED:
            s.status = QuestionStateStatus.FAILED
            db.add(s)

    db.add(
        TeamQuestionState(
            team_id=team_id,
            question_id=selected_q.id,
            status=QuestionStateStatus.ASSIGNED,
        )
    )
    await db.commit()

    return {
        "message": "Time boost assigned successfully",
        "question": {
            "id": selected_q.id,
            "title": selected_q.title,
            "description": selected_q.description,
            "difficulty": selected_q.difficulty,
            "reward_seconds": selected_q.reward_value or (300 if selected_q.difficulty == QuestionDifficulty.EASY else 600 if selected_q.difficulty == QuestionDifficulty.MEDIUM else 900),
        }
    }


@router.post("/teams/{team_id}/assign-boost")
async def assign_boost(team_id: int, boost: AssignBoost, db: AsyncSession = Depends(get_db), _: None = Depends(verify_admin)):
    team = (await db.execute(select(Team).where(Team.id == team_id))).scalars().first()
    if not team:
        raise HTTPException(status_code=404, detail="Team not found")
    question = (await db.execute(select(Question).where(Question.id == boost.question_id))).scalars().first()
    if not question:
        raise HTTPException(status_code=404, detail="Question not found")

    existing = (
        await db.execute(
            select(TeamQuestionState).where(
                TeamQuestionState.team_id == team_id,
                TeamQuestionState.question_id == boost.question_id,
            )
        )
    ).scalars().first()
    if existing:
        raise HTTPException(status_code=400, detail="That question is already assigned to this team")

    db.add(
        TeamQuestionState(
            team_id=team_id,
            question_id=boost.question_id,
            status=QuestionStateStatus.ASSIGNED,
        )
    )
    await db.commit()
    return {"message": "Time boost assigned"}


from app.schemas.teams import ResolveChallengeRequest
from seeding.questions import CHALLENGE_QUESTIONS
from app.models.enums import QuestionType, MainSubType, CompareMode, QuestionDifficulty


@router.get("/challenge/questions")
async def list_challenge_questions(
    db: AsyncSession = Depends(get_db),
    _: None = Depends(verify_admin)
):
    """List only questions tagged as CHALLENGE."""
    query = select(Question).where(Question.type == QuestionType.CHALLENGE)
    questions = (await db.execute(query)).scalars().all()

    # If no challenge questions exist in DB, seed them automatically
    if not questions:
        for cq in CHALLENGE_QUESTIONS:
            diff_val = cq.get("difficulty", "HARD")
            diff_enum = QuestionDifficulty[diff_val] if isinstance(diff_val, str) and diff_val in QuestionDifficulty.__members__ else QuestionDifficulty.HARD
            sub_val = cq.get("sub_type", "CODING")
            sub_enum = MainSubType[sub_val] if isinstance(sub_val, str) and sub_val in MainSubType.__members__ else MainSubType.CODING
            comp_val = cq.get("compare_mode", "TRIM")
            comp_enum = CompareMode[comp_val] if isinstance(comp_val, str) and comp_val in CompareMode.__members__ else CompareMode.TRIM

            new_q = Question(
                title=cq["title"],
                description=cq["description"],
                type=QuestionType.CHALLENGE,
                difficulty=diff_enum,
                reward_value=cq.get("reward_value", 100),
                points=cq.get("points", 100),
                sub_type=None,
                starter_code=cq.get("starter_code", "{}"),
                allowed_languages=cq.get("allowed_languages", '["python", "c", "cpp", "java"]'),
                compare_mode=comp_enum,
            )
            db.add(new_q)
        await db.commit()
        questions = (await db.execute(query)).scalars().all()

    return [
        {
            "id": q.id,
            "title": q.title,
            "description": q.description,
            "difficulty": q.difficulty.value if hasattr(q.difficulty, "value") else str(q.difficulty),
            "points": q.points or 100,
            "type": "CHALLENGE",
        }
        for q in questions
    ]


@router.get("/challenge/sessions")
async def list_challenge_sessions(
    db: AsyncSession = Depends(get_db),
    _: None = Depends(verify_admin)
):
    """List all 1v1 and 1v1v1 challenge matches."""
    sessions = (
        await db.execute(
            select(ChallengeSession).order_by(ChallengeSession.id.desc())
        )
    ).scalars().all()

    out = []
    for s in sessions:
        q = (await db.execute(select(Question).where(Question.id == s.question_id))).scalars().first()
        t1 = (await db.execute(select(Team).where(Team.id == s.team1_id))).scalars().first() if s.team1_id else None
        t2 = (await db.execute(select(Team).where(Team.id == s.team2_id))).scalars().first() if s.team2_id else None
        t3 = (await db.execute(select(Team).where(Team.id == s.team3_id))).scalars().first() if s.team3_id else None
        winner = (await db.execute(select(Team).where(Team.id == s.winner_team_id))).scalars().first() if s.winner_team_id else None

        out.append({
            "id": s.id,
            "question_id": s.question_id,
            "question_title": q.title if q else f"Question #{s.question_id}",
            "status": s.status.value if hasattr(s.status, "value") else str(s.status),
            "team1_id": s.team1_id,
            "team1_name": t1.name if t1 else f"Team #{s.team1_id}",
            "team2_id": s.team2_id,
            "team2_name": t2.name if t2 else f"Team #{s.team2_id}",
            "team3_id": s.team3_id,
            "team3_name": t3.name if t3 else None,
            "winner_team_id": s.winner_team_id,
            "winner_name": winner.name if winner else None,
            "stake_points": 100,
            "is_triangular": s.team3_id is not None,
        })
    return out


@router.post("/challenge/create")
async def create_challenge(
    challenge: ChallengeCreate,
    db: AsyncSession = Depends(get_db),
    _: None = Depends(verify_admin)
):
    """Start a 1v1 or 1v1v1 challenge match between teams."""
    team_ids = [challenge.team1_id, challenge.team2_id]
    if challenge.team3_id:
        team_ids.append(challenge.team3_id)

    if len(set(team_ids)) != len(team_ids):
        raise HTTPException(status_code=400, detail="All competing teams in the match must be distinct.")

    teams = []
    for tid in team_ids:
        t = (await db.execute(select(Team).where(Team.id == tid))).scalars().first()
        if not t:
            raise HTTPException(status_code=404, detail=f"Team #{tid} not found.")
        teams.append(t)

    q = (await db.execute(select(Question).where(Question.id == challenge.question_id))).scalars().first()
    if not q:
        raise HTTPException(status_code=404, detail="Question not found.")

    # Close any previous ONGOING challenge session for competing teams
    old_sessions = (
        await db.execute(
            select(ChallengeSession).where(
                ChallengeStatus.ONGOING == ChallengeSession.status,
                (
                    (ChallengeSession.team1_id.in_(team_ids)) |
                    (ChallengeSession.team2_id.in_(team_ids)) |
                    (ChallengeSession.team3_id.in_(team_ids))
                )
            )
        )
    ).scalars().all()
    for os in old_sessions:
        os.status = ChallengeStatus.COMPLETED
        db.add(os)

    new_challenge = ChallengeSession(
        question_id=challenge.question_id,
        team1_id=challenge.team1_id,
        team2_id=challenge.team2_id,
        team3_id=challenge.team3_id,
        status=ChallengeStatus.ONGOING,
    )
    db.add(new_challenge)
    await db.commit()
    await db.refresh(new_challenge)

    match_label = " VS ".join([t.name for t in teams])
    return {
        "message": f"Match started: {match_label} on '{q.title}' (100 pts stake)",
        "id": new_challenge.id,
        "match_label": match_label,
        "question_title": q.title,
    }


@router.post("/challenge/{session_id}/resolve")
async def resolve_challenge(
    session_id: int,
    payload: ResolveChallengeRequest,
    db: AsyncSession = Depends(get_db),
    _: None = Depends(verify_admin)
):
    """Admin manually resolves a 1v1 / 1v1v1 challenge match by declaring the winning team."""
    session = (
        await db.execute(
            select(ChallengeSession).where(ChallengeSession.id == session_id)
        )
    ).scalars().first()
    if not session:
        raise HTTPException(status_code=404, detail="Challenge session not found")

    winner_id = payload.winner_team_id
    competing_ids = [tid for tid in [session.team1_id, session.team2_id, session.team3_id] if tid]
    if winner_id not in competing_ids:
        raise HTTPException(status_code=400, detail="Winning team must be one of the match participants.")

    loser_ids = [tid for tid in competing_ids if tid != winner_id]

    winner_team = (await db.execute(select(Team).where(Team.id == winner_id))).scalars().first()

    # Complete session
    session.winner_team_id = winner_id
    session.status = ChallengeStatus.COMPLETED
    db.add(session)

    stake_points = 100
    # Winner gains +100
    if winner_team:
        winner_team.points = (winner_team.points or 0) + stake_points
        db.add(winner_team)

    # Losers lose 100 each
    for lid in loser_ids:
        lt = (await db.execute(select(Team).where(Team.id == lid))).scalars().first()
        if lt:
            lt.points = max(0, (lt.points or 0) - stake_points)
            db.add(lt)

    await db.commit()

    return {
        "message": f"Match resolved! {winner_team.name if winner_team else winner_id} won 100 points.",
        "winner_name": winner_team.name if winner_team else str(winner_id),
    }



@router.post("/review/mark-solved")
async def mark_solved(review: ReviewMarkSolved, db: AsyncSession = Depends(get_db), _: None = Depends(verify_admin)):
    q_result = await db.execute(select(Question).where(Question.id == review.question_id))
    question = q_result.scalars().first()
    if not question:
        raise HTTPException(status_code=404, detail="Question not found")

    team_result = await db.execute(select(Team).where(Team.id == review.team_id))
    team = team_result.scalars().first()
    if not team:
        raise HTTPException(status_code=404, detail="Team not found")

    if question.type == QuestionType.TIME_BOOST:
        state_result = await db.execute(
            select(TeamQuestionState).where(
                TeamQuestionState.team_id == review.team_id,
                TeamQuestionState.question_id == review.question_id,
                TeamQuestionState.status == QuestionStateStatus.ASSIGNED,
            )
        )
        state = state_result.scalars().first()
        if state:
            state.status = QuestionStateStatus.SOLVED
            team.extra_time_seconds = (team.extra_time_seconds or 0) + question.reward_value
            db.add(state)
            db.add(team)
            await db.commit()
            return {"message": "Time boost solved, time added"}

    elif question.type == QuestionType.CHALLENGE:
        challenge_result = await db.execute(
            select(ChallengeSession).where(
                ChallengeSession.question_id == review.question_id,
                ChallengeSession.status == ChallengeStatus.ONGOING,
                (
                    (ChallengeSession.team1_id == review.team_id)
                    | (ChallengeSession.team2_id == review.team_id)
                ),
            )
        )
        challenge = challenge_result.scalars().first()
        if challenge:
            challenge.status = ChallengeStatus.COMPLETED
            challenge.winner_team_id = review.team_id
            
            # Loser team
            loser_id = challenge.team2_id if challenge.team1_id == review.team_id else challenge.team1_id
            loser_team = (await db.execute(select(Team).where(Team.id == loser_id))).scalars().first() if loser_id else None
            
            # Winner gains 100, loser loses 100
            team.points = (team.points or 0) + 100
            if loser_team:
                loser_team.points = max(0, (loser_team.points or 0) - 100)
                db.add(loser_team)

            db.add(challenge)
            db.add(team)
            await db.commit()
            return {"message": f"1v1 Challenge won by {team.name}! +100 points transferred from {loser_team.name if loser_team else 'opponent'}."}

    if question.type == QuestionType.MAIN:
        return {
            "message": "MAIN questions are graded automatically by the judge. "
                       "Use GET /api/admin/leaderboard to see scores."
        }

    return {"message": "No active assignment found for this question"}

