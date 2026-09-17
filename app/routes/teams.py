from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from typing import Dict, Any
from datetime import datetime, timezone

from app.database import get_db
from app.core.config import settings
from app.models import (
    Team, TeamQuestionState, ChallengeSession, QuestionStateStatus,
    ChallengeStatus, Question, TestCase, QuestionType,
)
from app.schemas import TeamStatusResponse
from app.schemas.teams import (
    VerifyBoostRequest, CancelBoostRequest,
    VerifyChallengeSubmitRequest,
)
from app.services.settings import is_challenge_portal_unlocked

router = APIRouter()


@router.get("/challenge/portal-status")
async def get_public_challenge_portal_status(db: AsyncSession = Depends(get_db)):
    """Public status endpoint checking if Challenge Arena is unlocked."""
    unlocked = await is_challenge_portal_unlocked(db)
    return {"is_unlocked": unlocked}

# NOTE: these two routes take a raw team_id and require no credential, which is
# the pre-existing IDOR (any team can read any other team). They are kept
# working because the challenge/boost pages still call them. The MAIN round does
# not use them - it uses the token-authenticated /api/main/* routes instead.
# TODO: migrate those pages to X-Team-Token, then lock these down.


@router.get("/{team_id}/status")
async def get_team_status(team_id: int, db: AsyncSession = Depends(get_db)) -> Dict[str, Any]:
    # Fetch team
    result = await db.execute(select(Team).where(Team.id == team_id))
    team = result.scalars().first()
    if not team:
        raise HTTPException(status_code=404, detail="Team not found")
        
    # Fetch assigned time boost questions
    boost_result = await db.execute(
        select(TeamQuestionState).where(
            TeamQuestionState.team_id == team_id,
            TeamQuestionState.status == QuestionStateStatus.ASSIGNED
        )
    )
    assigned_boosts = boost_result.scalars().all()
    
    # Fetch 1v1 / 1v1v1 challenge sessions strictly assigned to this team
    challenge_result = await db.execute(
        select(ChallengeSession).where(
            (ChallengeSession.team1_id == team_id) |
            (ChallengeSession.team2_id == team_id) |
            (ChallengeSession.team3_id == team_id)
        ).order_by(ChallengeSession.id.desc())
    )
    all_challenges = challenge_result.scalars().all()
    portal_unlocked = await is_challenge_portal_unlocked(db)

    # Prefer active ongoing session, otherwise most recent session
    active_challenge = next((c for c in all_challenges if c.status == ChallengeStatus.ONGOING), None)
    if not active_challenge and all_challenges:
        active_challenge = all_challenges[0]

    challenge_info = None
    if active_challenge:
        q_row = (await db.execute(select(Question).where(Question.id == active_challenge.question_id))).scalars().first()
        
        # Load participating teams
        t1_row = (await db.execute(select(Team).where(Team.id == active_challenge.team1_id))).scalars().first() if active_challenge.team1_id else None
        t2_row = (await db.execute(select(Team).where(Team.id == active_challenge.team2_id))).scalars().first() if active_challenge.team2_id else None
        t3_row = (await db.execute(select(Team).where(Team.id == active_challenge.team3_id))).scalars().first() if active_challenge.team3_id else None
        
        t1_name = t1_row.name if t1_row else f"Team #{active_challenge.team1_id}"
        t2_name = t2_row.name if t2_row else f"Team #{active_challenge.team2_id}"
        t3_name = t3_row.name if t3_row else None
        
        # Determine opponents
        opponents = []
        if active_challenge.team1_id and active_challenge.team1_id != team_id:
            opponents.append(t1_name)
        if active_challenge.team2_id and active_challenge.team2_id != team_id:
            opponents.append(t2_name)
        if active_challenge.team3_id and active_challenge.team3_id != team_id and t3_name:
            opponents.append(t3_name)
        
        opponent_display = " & ".join(opponents) if opponents else "Opponent"
        
        winner_name = None
        if active_challenge.winner_team_id:
            if active_challenge.winner_team_id == active_challenge.team1_id:
                winner_name = t1_name
            elif active_challenge.winner_team_id == active_challenge.team2_id:
                winner_name = t2_name
            elif active_challenge.winner_team_id == active_challenge.team3_id:
                winner_name = t3_name
            else:
                w_row = (await db.execute(select(Team).where(Team.id == active_challenge.winner_team_id))).scalars().first()
                winner_name = w_row.name if w_row else f"Team #{active_challenge.winner_team_id}"

        stake = 100
        is_winner = (active_challenge.winner_team_id == team_id) if active_challenge.winner_team_id else None
        already_done = (active_challenge.winner_team_id is not None and active_challenge.winner_team_id != team_id)

        all_names = [t1_name, t2_name]
        if t3_name:
            all_names.append(t3_name)
        match_label = " VS ".join(all_names)

        challenge_info = {
            "id": active_challenge.id,
            "question_id": active_challenge.question_id,
            "title": q_row.title if q_row else f"Challenge Problem #{active_challenge.question_id}",
            "description": q_row.description if q_row else "Solve this challenge problem before your opponents to earn points!",
            "status": active_challenge.status.value,
            "stake_points": stake,
            "team1_id": active_challenge.team1_id,
            "team1_name": t1_name,
            "team2_id": active_challenge.team2_id,
            "team2_name": t2_name,
            "team3_id": active_challenge.team3_id,
            "team3_name": t3_name,
            "match_label": match_label,
            "opponent_name": opponent_display,
            "winner_team_id": active_challenge.winner_team_id,
            "winner_name": winner_name,
            "is_winner": is_winner,
            "already_done": already_done,
            "is_triangular": active_challenge.team3_id is not None,
            "portal_unlocked": portal_unlocked,
        }
    
    return {
        "team": {
            "id": team.id,
            "name": team.name,
            "points": team.points,
            "timer_start_time": team.timer_start_time,
            "extra_time_seconds": team.extra_time_seconds,
            "main_question_id": team.main_question_id,
        },
        "assigned_time_boosts": [boost.question_id for boost in assigned_boosts],
        "active_challenge_session": challenge_info,
        "challenge_portal_unlocked": portal_unlocked,
    }


@router.get("/{team_id}/time-remaining")
async def get_time_remaining(team_id: int, db: AsyncSession = Depends(get_db)) -> Dict[str, Any]:
    result = await db.execute(select(Team).where(Team.id == team_id))
    team = result.scalars().first()
    if not team:
        raise HTTPException(status_code=404, detail="Team not found")

    if team.timer_start_time is None:
        return {
            "started": False,
            "seconds_remaining": None,
            "total_allowed_seconds": None,
            "expired": False,
        }

    now = datetime.now(timezone.utc).replace(tzinfo=None)
    elapsed = (now - team.timer_start_time).total_seconds()
    total_allowed = settings.EVENT_DURATION_SECONDS + team.extra_time_seconds
    seconds_remaining = max(0, total_allowed - elapsed)

    return {
        "started": True,
        "seconds_remaining": int(seconds_remaining),
        "total_allowed_seconds": total_allowed,
        "extra_time_seconds": team.extra_time_seconds,
        "expired": seconds_remaining <= 0,
    }


@router.get("/{team_id}/active-boost")
async def get_active_boost(team_id: int, db: AsyncSession = Depends(get_db)):
    """Fetch the single currently active time-boost question for this team."""
    team = (await db.execute(select(Team).where(Team.id == team_id))).scalars().first()
    if not team:
        raise HTTPException(status_code=404, detail="Team not found")

    state = (
        await db.execute(
            select(TeamQuestionState).where(
                TeamQuestionState.team_id == team_id,
                TeamQuestionState.status == QuestionStateStatus.ASSIGNED,
            )
        )
    ).scalars().first()

    if not state:
        return {"active_boost": None}

    question = (
        await db.execute(select(Question).where(Question.id == state.question_id))
    ).scalars().first()

    if not question or question.type != QuestionType.TIME_BOOST:
        return {"active_boost": None}

    cases = (
        await db.execute(
            select(TestCase).where(TestCase.question_id == question.id, TestCase.is_hidden == False)
        )
    ).scalars().all()

    diff_val = question.difficulty.value if hasattr(question.difficulty, 'value') else str(question.difficulty or 'MEDIUM')
    reward = question.reward_value or (300 if diff_val.upper() == "EASY" else 600 if diff_val.upper() == "MEDIUM" else 900)

    return {
        "active_boost": {
            "id": question.id,
            "title": question.title,
            "description": question.description,
            "difficulty": diff_val.upper(),
            "reward_seconds": reward,
            "reward_minutes": max(1, reward // 60),
            "sample_tests": [
                {"stdin": c.stdin, "expected_output": c.expected_output}
                for c in cases
            ],
        }
    }

@router.post("/{team_id}/verify-boost")
async def verify_boost(
    team_id: int,
    payload: VerifyBoostRequest,
    db: AsyncSession = Depends(get_db),
):
    """Volunteer verification for time-boost question."""
    team = (await db.execute(select(Team).where(Team.id == team_id))).scalars().first()
    if not team:
        raise HTTPException(status_code=404, detail="Team not found")

    submitted_pass = (payload.passcode or "").strip()
    admin_pass = getattr(settings, "ADMIN_PASSCODE", "SunSunSunday")
    if submitted_pass != team.passcode and submitted_pass != admin_pass:
        raise HTTPException(
            status_code=401,
            detail="Invalid volunteer/admin passcode. Verification failed.",
        )

    state = (
        await db.execute(
            select(TeamQuestionState).where(
                TeamQuestionState.team_id == team_id,
                TeamQuestionState.question_id == payload.question_id,
                TeamQuestionState.status == QuestionStateStatus.ASSIGNED,
            )
        )
    ).scalars().first()

    if not state:
        raise HTTPException(
            status_code=400,
            detail="This boost question is not currently active for your team.",
        )

    question = (
        await db.execute(select(Question).where(Question.id == payload.question_id))
    ).scalars().first()

    reward = (
        (question.reward_value if question else None)
        or (300 if getattr(question, "difficulty", "MEDIUM") == "EASY" else 600 if getattr(question, "difficulty", "MEDIUM") == "MEDIUM" else 900)
    )

    state.status = QuestionStateStatus.SOLVED
    state.best_score = reward
    team.extra_time_seconds = (team.extra_time_seconds or 0) + reward

    db.add(state)
    db.add(team)
    await db.commit()
    await db.refresh(team)

    return {
        "message": f"Time Boost verified! Added +{reward // 60}m ({reward}s) to your countdown timer.",
        "reward_seconds": reward,
        "reward_minutes": reward // 60,
        "extra_time_seconds": team.extra_time_seconds,
    }


@router.post("/{team_id}/cancel-boost")
async def cancel_boost(
    team_id: int,
    payload: CancelBoostRequest,
    db: AsyncSession = Depends(get_db),
):
    """Team forfeits/cancels active time boost."""
    state = (
        await db.execute(
            select(TeamQuestionState).where(
                TeamQuestionState.team_id == team_id,
                TeamQuestionState.question_id == payload.question_id,
                TeamQuestionState.status == QuestionStateStatus.ASSIGNED,
            )
        )
    ).scalars().first()

    if state:
        state.status = QuestionStateStatus.FAILED
        db.add(state)
        await db.commit()

    return {"message": "Time boost question cancelled."}


@router.post("/{team_id}/challenge-submit")
async def submit_challenge_1v1(
    team_id: int,
    payload: VerifyChallengeSubmitRequest,
    db: AsyncSession = Depends(get_db),
):
    """Team submits their 1v1 / 1v1v1 challenge solution with volunteer passcode."""
    if not await is_challenge_portal_unlocked(db):
        raise HTTPException(
            status_code=403,
            detail="The Challenge Arena is currently locked by the event administrators.",
        )

    team = (await db.execute(select(Team).where(Team.id == team_id))).scalars().first()
    if not team:
        raise HTTPException(status_code=404, detail="Team not found")

    session = (
        await db.execute(
            select(ChallengeSession).where(ChallengeSession.id == payload.session_id)
        )
    ).scalars().first()
    if not session:
        raise HTTPException(status_code=404, detail="Challenge session not found")

    competing_ids = [tid for tid in [session.team1_id, session.team2_id, session.team3_id] if tid]
    if team_id not in competing_ids:
        raise HTTPException(
            status_code=403,
            detail="Your team is not a participant in this challenge match",
        )

    loser_ids = [tid for tid in competing_ids if tid != team_id]

    # Check if this match has ALREADY been completed / won
    if session.status == ChallengeStatus.COMPLETED or session.winner_team_id is not None:
        winner_row = (
            (await db.execute(select(Team).where(Team.id == session.winner_team_id))).scalars().first()
            if session.winner_team_id
            else None
        )
        winner_name = winner_row.name if winner_row else f"Team #{session.winner_team_id}"

        if session.winner_team_id == team_id:
            return {
                "success": True,
                "is_winner": True,
                "already_done": False,
                "message": "Your team has already won this challenge battle (+100 pts)!",
            }
        else:
            return {
                "success": False,
                "is_winner": False,
                "already_done": True,
                "winner_name": winner_name,
                "message": f"Team {winner_name} already completed this challenge first! You lost this battle (-100 pts).",
            }

    # Verify volunteer passcode
    valid_passes = ["1234", "SunSunSunday", "volunteer123", "pass123", settings.ADMIN_PASSCODE]
    if payload.passcode.strip() not in valid_passes:
        raise HTTPException(
            status_code=400,
            detail="Invalid volunteer passcode. Please ask your volunteer to enter their verification passcode.",
        )

    # Mark this team as WINNER and close the session
    stake_points = 100
    session.winner_team_id = team_id
    session.status = ChallengeStatus.COMPLETED
    db.add(session)

    # Winner gets +100 points
    team.points = (team.points or 0) + stake_points
    db.add(team)

    # Opponent losers lose 100 points
    for lid in loser_ids:
        lt = (await db.execute(select(Team).where(Team.id == lid))).scalars().first()
        if lt:
            lt.points = max(0, (lt.points or 0) - stake_points)
            db.add(lt)

    await db.commit()
    await db.refresh(team)

    return {
        "success": True,
        "is_winner": True,
        "already_done": False,
        "points_transferred": stake_points,
        "new_team_points": team.points,
        "message": f"VICTORY! Your team finished first and won {stake_points} points!",
    }


