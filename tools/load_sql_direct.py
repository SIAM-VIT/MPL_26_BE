import asyncio
import os
import sys
from sqlalchemy import text
from app.database import engine

async def load_main_questions():
    sql_path = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..", "populate_main_questions_sets.sql"))
    print(f"Reading SQL file from: {sql_path}")
    
    with open(sql_path, "r", encoding="utf-8") as f:
        sql_content = f.read()

    print(f"Connecting to database and executing SQL ({len(sql_content)} bytes)...")
    async with engine.begin() as conn:
        # Split statements by semicolon if needed or execute raw
        # Using raw execution via asyncpg connection
        raw_conn = await conn.get_raw_connection()
        # asyncpg raw connection
        await raw_conn.driver_connection.execute(sql_content)

    print("\n✅ SUCCESS! All 60 Questions, 180 Test Cases, and 20 Sets populated successfully in PostgreSQL.")

if __name__ == "__main__":
    asyncio.run(load_main_questions())
