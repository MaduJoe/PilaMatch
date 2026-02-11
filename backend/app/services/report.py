from typing import Optional, List
from uuid import UUID

from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

from app.models import Report, Block, User
from app.schemas.report import ReportCreate, BlockCreate


class ReportService:
    def __init__(self, db: AsyncSession):
        self.db = db

    async def create_report(
        self, reporter_user_id: UUID, data: ReportCreate
    ) -> Report:
        # Check if reported user exists
        reported_user = await self.db.execute(
            select(User).where(User.id == data.reported_user_id)
        )
        if not reported_user.scalar_one_or_none():
            raise ValueError("Reported user not found")

        # Can't report yourself
        if reporter_user_id == data.reported_user_id:
            raise ValueError("Cannot report yourself")

        report = Report(
            reporter_user_id=reporter_user_id,
            reported_user_id=data.reported_user_id,
            report_type=data.report_type,
            description=data.description,
        )
        self.db.add(report)
        await self.db.commit()
        await self.db.refresh(report)
        return report

    async def create_block(
        self, blocker_user_id: UUID, data: BlockCreate
    ) -> Block:
        # Check if blocked user exists
        blocked_user = await self.db.execute(
            select(User).where(User.id == data.blocked_user_id)
        )
        if not blocked_user.scalar_one_or_none():
            raise ValueError("User not found")

        # Can't block yourself
        if blocker_user_id == data.blocked_user_id:
            raise ValueError("Cannot block yourself")

        # Check if already blocked
        existing = await self.db.execute(
            select(Block).where(
                Block.blocker_user_id == blocker_user_id,
                Block.blocked_user_id == data.blocked_user_id,
            )
        )
        if existing.scalar_one_or_none():
            raise ValueError("User already blocked")

        block = Block(
            blocker_user_id=blocker_user_id,
            blocked_user_id=data.blocked_user_id,
        )
        self.db.add(block)
        await self.db.commit()
        await self.db.refresh(block)
        return block

    async def get_blocks(self, user_id: UUID) -> List[Block]:
        result = await self.db.execute(
            select(Block)
            .where(Block.blocker_user_id == user_id)
            .order_by(Block.created_at.desc())
        )
        return list(result.scalars().all())

    async def remove_block(self, blocker_user_id: UUID, blocked_user_id: UUID) -> bool:
        result = await self.db.execute(
            select(Block).where(
                Block.blocker_user_id == blocker_user_id,
                Block.blocked_user_id == blocked_user_id,
            )
        )
        block = result.scalar_one_or_none()

        if not block:
            return False

        await self.db.delete(block)
        await self.db.commit()
        return True
