from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from app.models.setting import AppSetting


async def get_setting(db: AsyncSession, key: str, default: str = "") -> str:
    res = await db.execute(select(AppSetting).where(AppSetting.key == key))
    row = res.scalars().first()
    return row.value if row else default


async def set_setting(db: AsyncSession, key: str, value: str):
    res = await db.execute(select(AppSetting).where(AppSetting.key == key))
    row = res.scalars().first()
    if row:
        row.value = value
        db.add(row)
    else:
        new_row = AppSetting(key=key, value=value)
        db.add(new_row)
    await db.commit()


async def is_challenge_portal_unlocked(db: AsyncSession) -> bool:
    val = await get_setting(db, "challenge_portal_unlocked", "false")
    return val.lower() in ("true", "1", "yes")


async def set_challenge_portal_unlocked(db: AsyncSession, unlocked: bool):
    await set_setting(db, "challenge_portal_unlocked", "true" if unlocked else "false")
