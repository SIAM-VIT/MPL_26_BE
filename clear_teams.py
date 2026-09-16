#!/usr/bin/env python3
"""Script to delete all teams, unallocate question sets, and clear progress/submissions."""
import asyncio
from sqlalchemy.future import select

from app.database import engine, Base, AsyncSessionLocal
import app.models
from app.models import Team, QuestionSet, TeamQuestionState, Submission, ChallengeSession


async def delete_all_teams():
    # 1. Ensure all tables including question_sets exist
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)

    async with AsyncSessionLocal() as db:
        # 2. Unallocate all question sets
        qsets = (await db.execute(select(QuestionSet))).scalars().all()
        for qs in qsets:
            qs.is_allocated = False
            qs.allocated_team_id = None
            qs.allocated_at = None

        # 3. Delete team-related data
        for model in [Submission, TeamQuestionState, ChallengeSession, Team]:
            rows = (await db.execute(select(model))).scalars().all()
            for r in rows:
                await db.delete(r)

        await db.commit()
        print("[+] Successfully deleted all teams and unallocated all question sets.")


if __name__ == "__main__":
    asyncio.run(delete_all_teams())

