#!/usr/bin/env python3
"""Direct database seeder for questions, test cases, and question sets."""
import asyncio
import os
import sys
import json

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from sqlalchemy.future import select

from app.database import engine, Base, AsyncSessionLocal
from app.models import Question, TestCase, QuestionSet
from seeding.questions import QUESTIONS, QUESTION_SETS_CONFIG



async def seed():
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)

    async with AsyncSessionLocal() as db:
        print("[+] Seeding Questions and Testcases...")
        title_to_q = {}
        for q_data in QUESTIONS:
            cases = q_data.get("_cases", [])
            title = q_data["title"]

            existing_q = (await db.execute(select(Question).where(Question.title == title))).scalars().first()
            if not existing_q:
                new_q = Question(
                    title=q_data["title"],
                    description=q_data["description"],
                    test_cases=q_data.get("test_cases", "[]"),
                    type=q_data["type"],
                    difficulty=q_data["difficulty"],
                    reward_value=q_data.get("reward_value", 0),
                    sub_type=q_data.get("sub_type"),
                    starter_code=q_data.get("starter_code"),
                    allowed_languages=q_data.get("allowed_languages"),
                    compare_mode=q_data.get("compare_mode"),
                    points=q_data.get("points", 0),
                    cpu_time_limit=q_data.get("cpu_time_limit", 5.0),
                    wall_time_limit=q_data.get("wall_time_limit", 10.0),
                    memory_limit_kb=q_data.get("memory_limit_kb", 256000),
                    order_index=q_data.get("order_index", 0),
                )
                db.add(new_q)
                await db.flush()
                target_q = new_q
            else:
                target_q = existing_q

            title_to_q[title] = target_q

            # Seed test cases if none exist
            existing_cases = (await db.execute(select(TestCase).where(TestCase.question_id == target_q.id))).scalars().all()
            if not existing_cases:
                for idx, c in enumerate(cases):
                    db.add(
                        TestCase(
                            question_id=target_q.id,
                            stdin=c.get("stdin", ""),
                            expected_output=c.get("expected_output", ""),
                            is_hidden=c.get("is_hidden", True),
                            weight=c.get("weight", 1.0),
                            position=c.get("position", idx),
                        )
                    )

        await db.commit()

        print("[+] Seeding Question Sets...")
        for qset in QUESTION_SETS_CONFIG:
            existing_set = (await db.execute(select(QuestionSet).where(QuestionSet.name == qset["name"]))).scalars().first()
            debug_q = title_to_q.get(qset["debug"])
            math_q = title_to_q.get(qset["math"])
            lc_q = title_to_q.get(qset["leetcode"])

            if not existing_set:
                new_set = QuestionSet(
                    name=qset["name"],
                    debug_question_id=debug_q.id if debug_q else None,
                    math_question_id=math_q.id if math_q else None,
                    leetcode_question_id=lc_q.id if lc_q else None,
                    is_allocated=False,
                )
                db.add(new_set)
                print(f"    - Created {qset['name']} (Debug ID: {new_set.debug_question_id}, Math ID: {new_set.math_question_id}, Leetcode ID: {new_set.leetcode_question_id})")
            else:
                existing_set.debug_question_id = debug_q.id if debug_q else existing_set.debug_question_id
                existing_set.math_question_id = math_q.id if math_q else existing_set.math_question_id
                existing_set.leetcode_question_id = lc_q.id if lc_q else existing_set.leetcode_question_id
                db.add(existing_set)
                print(f"    - Updated {qset['name']}")

        await db.commit()
        print("[+] Seeding complete!")


if __name__ == "__main__":
    asyncio.run(seed())
