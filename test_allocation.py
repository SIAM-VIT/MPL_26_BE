import asyncio
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from app.database import AsyncSessionLocal
from app.routes.auth import login
from app.schemas import TeamLogin
from app.services.arena import team_question_views
from sqlalchemy.future import select
from app.models import Team, QuestionSet


async def test():
    async with AsyncSessionLocal() as db:
        res = await login(TeamLogin(name="Team Alpha", passcode="alpha123"), db)
        team = (await db.execute(select(Team).where(Team.id == res.id))).scalars().first()
        q_views = await team_question_views(db, team)
        print(f"Login success for team: {team.name}")
        qset = (await db.execute(select(QuestionSet).where(QuestionSet.allocated_team_id == team.id))).scalars().first()
        print(f"Allocated Question Set: {qset.name if qset else 'None'}")
        print("Questions returned to team arena:")
        for q in q_views:
            print(f"  [{q.sub_type}] {q.title} (Points: {q.points})")


if __name__ == "__main__":
    asyncio.run(test())
