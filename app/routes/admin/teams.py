"""Admin team management: create, list, add-time."""
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from sqlalchemy.exc import IntegrityError

from app.database import get_db
from app.models import Team
from app.schemas import TeamCreate, AddTimeRequest
from app.routes.admin.deps import verify_admin

router = APIRouter()


@router.post("/teams")
async def create_team(team: TeamCreate, db: AsyncSession = Depends(get_db), _: None = Depends(verify_admin)):
    existing = (await db.execute(select(Team).where(Team.name == team.name))).scalars().first()
    if existing:
        raise HTTPException(status_code=400, detail="A team with that name already exists")
    new_team = Team(name=team.name, passcode=team.passcode)
    db.add(new_team)
    try:
        await db.commit()
    except IntegrityError:
        await db.rollback()
        raise HTTPException(status_code=400, detail="A team with that name already exists")
    return {"message": "Team created successfully", "id": new_team.id}


@router.get("/teams")
async def list_teams(db: AsyncSession = Depends(get_db), _: None = Depends(verify_admin)):
    from app.models import QuestionSet, TeamQuestionState, Question, QuestionType, QuestionStateStatus
    teams = (await db.execute(select(Team).order_by(Team.id))).scalars().all()
    
    states = (await db.execute(select(TeamQuestionState))).scalars().all()
    qsets = (await db.execute(select(QuestionSet))).scalars().all()
    questions = {q.id: q for q in (await db.execute(select(Question))).scalars().all()}
    
    states_by_team = {}
    for s in states:
        states_by_team.setdefault(s.team_id, {})[s.question_id] = s
        
    qsets_by_team = {qs.allocated_team_id: qs for qs in qsets if qs.allocated_team_id}

    result = []
    for t in teams:
        team_states_map = states_by_team.get(t.id, {})
        qs = qsets_by_team.get(t.id)
        
        main_q_ids = []
        if qs:
            if qs.debug_question_id: main_q_ids.append(("DEBUGGING", qs.debug_question_id))
            if qs.math_question_id: main_q_ids.append(("MATH", qs.math_question_id))
            if qs.leetcode_question_id: main_q_ids.append(("CODING", qs.leetcode_question_id))
        
        main_details = []
        solved_count = 0
        for category, qid in main_q_ids:
            q = questions.get(qid)
            s = team_states_map.get(qid)
            status_str = s.status.value if (s and hasattr(s.status, "value")) else (str(s.status) if s else "NOT_STARTED")
            if status_str.upper() == "SOLVED":
                solved_count += 1
            main_details.append({
                "question_id": qid,
                "category": category,
                "title": q.title if q else f"Q#{qid}",
                "sub_type": (q.sub_type.value if (q and q.sub_type) else category),
                "status": status_str,
                "best_score": s.best_score if s else 0,
                "attempts": s.attempts if s else 0,
            })
            
        # Active or solved time boosts (exclude failed/cancelled historical attempts)
        boost_details = []
        for qid, s in team_states_map.items():
            q = questions.get(qid)
            s_status = s.status.value if hasattr(s.status, "value") else str(s.status)
            if q and q.type == QuestionType.TIME_BOOST and s_status in ["ASSIGNED", "SOLVED"]:
                boost_details.append({
                    "question_id": qid,
                    "title": q.title,
                    "difficulty": q.difficulty.value if hasattr(q.difficulty, "value") else str(q.difficulty),
                    "status": s_status,
                    "reward_seconds": q.reward_value or 300,
                })
            
        result.append({
            "id": t.id,
            "name": t.name,
            "passcode": t.passcode,
            "points": t.points,
            "timer_start_time": t.timer_start_time,
            "extra_time_seconds": t.extra_time_seconds,
            "started": t.timer_start_time is not None,
            "solved_count": solved_count,
            "total_questions": len(main_q_ids) if main_q_ids else 3,
            "question_set_id": qs.id if qs else None,
            "question_set_name": qs.name if qs else None,
            "main_questions": main_details,
            "boost_questions": boost_details,
        })
    return result


@router.post("/teams/{team_id}/add-time")
async def add_time(
    team_id: int,
    payload: AddTimeRequest,
    db: AsyncSession = Depends(get_db),
    _: None = Depends(verify_admin),
):
    """Grant extra minutes to one team (or all teams with team_id=0)."""
    if payload.seconds <= 0:
        raise HTTPException(status_code=400, detail="seconds must be positive")

    updated = []
    if team_id == 0:
        teams = (await db.execute(select(Team))).scalars().all()
    else:
        team = (await db.execute(select(Team).where(Team.id == team_id))).scalars().first()
        if not team:
            raise HTTPException(status_code=404, detail="Team not found")
        teams = [team]

    for team in teams:
        team.extra_time_seconds = (team.extra_time_seconds or 0) + payload.seconds
        db.add(team)
        updated.append({"id": team.id, "name": team.name,
                        "extra_time_seconds": team.extra_time_seconds})
    await db.commit()
    return {"message": f"Added {payload.seconds}s", "teams": updated}


@router.post("/teams/{team_id}/reset-timer")
async def reset_timer(
    team_id: int,
    db: AsyncSession = Depends(get_db),
    _: None = Depends(verify_admin),
):
    """Reset the main question clock for a team (or all teams with team_id=0).
    Restarts their timer fresh from now and resets extra time.
    """
    from app.services.access import now_naive_utc

    updated = []
    if team_id == 0:
        teams = (await db.execute(select(Team))).scalars().all()
    else:
        team = (await db.execute(select(Team).where(Team.id == team_id))).scalars().first()
        if not team:
            raise HTTPException(status_code=404, detail="Team not found")
        teams = [team]

    now = now_naive_utc()
    for team in teams:
        team.timer_start_time = now
        team.extra_time_seconds = 0
        db.add(team)
        updated.append({"id": team.id, "name": team.name, "timer_start_time": team.timer_start_time})

    await db.commit()
    return {"message": "Team timer reset successfully", "teams": updated}


@router.delete("/teams/{team_id}")
async def delete_team(
    team_id: int,
    db: AsyncSession = Depends(get_db),
    _: None = Depends(verify_admin),
):
    """Delete a team and unallocate its question set."""
    from app.models import QuestionSet, TeamQuestionState, Submission, ChallengeSession
    team = (await db.execute(select(Team).where(Team.id == team_id))).scalars().first()
    if not team:
        raise HTTPException(status_code=404, detail="Team not found")

    # Unallocate question sets
    qsets = (await db.execute(select(QuestionSet).where(QuestionSet.allocated_team_id == team_id))).scalars().all()
    for qs in qsets:
        qs.is_allocated = False
        qs.allocated_team_id = None
        qs.allocated_at = None

    # Delete challenge sessions involving this team
    ch_sessions = (await db.execute(select(ChallengeSession).where(
        (ChallengeSession.team1_id == team_id) |
        (ChallengeSession.team2_id == team_id) |
        (ChallengeSession.team3_id == team_id) |
        (ChallengeSession.winner_team_id == team_id)
    ))).scalars().all()
    for cs in ch_sessions:
        await db.delete(cs)

    # Delete states and submissions
    states = (await db.execute(select(TeamQuestionState).where(TeamQuestionState.team_id == team_id))).scalars().all()
    for s in states:
        await db.delete(s)

    submissions = (await db.execute(select(Submission).where(Submission.team_id == team_id))).scalars().all()
    for sub in submissions:
        await db.delete(sub)

    await db.delete(team)
    await db.commit()
    return {"message": f"Team {team.name} (id={team_id}) deleted successfully"}


@router.delete("/teams")
async def delete_all_teams(
    db: AsyncSession = Depends(get_db),
    _: None = Depends(verify_admin),
):
    """Delete ALL teams and unallocate all question sets."""
    from app.models import QuestionSet, TeamQuestionState, Submission, ChallengeSession

    # Unallocate question sets
    qsets = (await db.execute(select(QuestionSet))).scalars().all()
    for qs in qsets:
        qs.is_allocated = False
        qs.allocated_team_id = None
        qs.allocated_at = None

    for model in [Submission, TeamQuestionState, ChallengeSession, Team]:
        rows = (await db.execute(select(model))).scalars().all()
        for r in rows:
            await db.delete(r)

    await db.commit()
    return {"message": "All teams and associated progress successfully deleted"}


