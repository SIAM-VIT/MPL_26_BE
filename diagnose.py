import asyncio
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from app.database import AsyncSessionLocal
from sqlalchemy.future import select
from app.models import Team, QuestionSet, Question, TestCase
from app.services.arena import team_question_views


async def check():
    async with AsyncSessionLocal() as db:
        teams = (await db.execute(select(Team))).scalars().all()
        print("=== TEAMS ===")
        for t in teams:
            print(f"Team ID: {t.id}, Name: {t.name}, Token: {t.session_token[:10] if t.session_token else None}, Started: {t.timer_start_time}")
            views = await team_question_views(db, t)
            print(f"  -> Questions fetched ({len(views)}): {[v.title for v in views]}")

        print("\n=== QUESTION SETS ===")
        qsets = (await db.execute(select(QuestionSet))).scalars().all()
        for qs in qsets:
            print(f"Set ID: {qs.id}, Name: {qs.name}, Allocated: {qs.is_allocated}, Team ID: {qs.allocated_team_id}, Questions: Debug={qs.debug_question_id}, Math={qs.math_question_id}, Leet={qs.leetcode_question_id}")


if __name__ == "__main__":
    asyncio.run(check())
