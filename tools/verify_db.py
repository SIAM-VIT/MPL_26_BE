import asyncio
import os
import sys
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app.database import engine
from sqlalchemy import text

async def check():
    async with engine.begin() as conn:
        res = await conn.execute(text("""
            SELECT type, difficulty, COUNT(*), MIN(points), MAX(points) 
            FROM questions 
            GROUP BY type, difficulty 
            ORDER BY type, difficulty;
        """))
        print("Type | Difficulty | Count | Min Pts | Max Pts")
        print("-" * 50)
        for row in res.fetchall():
            print(f"{row[0]} | {row[1]} | {row[2]} | {row[3]} | {row[4]}")

if __name__ == '__main__':
    asyncio.run(check())
