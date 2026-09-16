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
    teams = (await db.execute(select(Team).order_by(Team.id))).scalars().all()
    return [
        {
            "id": t.id,
            "name": t.name,
            "passcode": t.passcode,
            "points": t.points,
            "timer_start_time": t.timer_start_time,
            "extra_time_seconds": t.extra_time_seconds,
            "started": t.timer_start_time is not None,
        }
        for t in teams
    ]


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

