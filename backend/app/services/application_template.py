"""Application template service for Premium members (v3.0 Phase 2)."""
from typing import List, Optional, Dict, Any
from uuid import UUID

from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, and_, update

from app.models import ApplicationTemplate, User
from app.services.subscription import SubscriptionService


class ApplicationTemplateService:
    """Service for managing application templates (Premium feature)."""

    MAX_TEMPLATES_PER_USER = 10  # Limit to prevent abuse

    def __init__(self, db: AsyncSession):
        self.db = db

    async def create_template(
        self,
        user_id: UUID,
        name: str,
        content: str,
        is_default: bool = False,
    ) -> ApplicationTemplate:
        """Create a new application template for Premium users only."""
        # Check if user is premium
        subscription_service = SubscriptionService(self.db)
        is_premium = await subscription_service.is_premium_user(user_id)

        if not is_premium:
            raise ValueError("PREMIUM_REQUIRED:응용 템플릿은 프리미엄 회원 전용 기능입니다")

        # Count existing templates
        count_result = await self.db.execute(
            select(ApplicationTemplate).where(ApplicationTemplate.user_id == user_id)
        )
        existing_templates = count_result.scalars().all()

        if len(existing_templates) >= self.MAX_TEMPLATES_PER_USER:
            raise ValueError(f"TEMPLATE_LIMIT:최대 {self.MAX_TEMPLATES_PER_USER}개의 템플릿만 저장 가능합니다")

        # If setting as default, unset other defaults
        if is_default and existing_templates:
            for template in existing_templates:
                template.is_default = False

        # Create template
        template = ApplicationTemplate(
            user_id=user_id,
            name=name,
            content=content,
            is_default=is_default or len(existing_templates) == 0,  # First template is default
        )

        self.db.add(template)
        await self.db.commit()
        await self.db.refresh(template)
        return template

    async def get_user_templates(self, user_id: UUID) -> List[ApplicationTemplate]:
        """Get all templates for a user."""
        result = await self.db.execute(
            select(ApplicationTemplate)
            .where(ApplicationTemplate.user_id == user_id)
            .order_by(ApplicationTemplate.is_default.desc(), ApplicationTemplate.created_at.desc())
        )
        return list(result.scalars().all())

    async def get_template(self, template_id: UUID, user_id: UUID) -> Optional[ApplicationTemplate]:
        """Get a specific template."""
        result = await self.db.execute(
            select(ApplicationTemplate).where(
                and_(
                    ApplicationTemplate.id == template_id,
                    ApplicationTemplate.user_id == user_id,
                )
            )
        )
        return result.scalar_one_or_none()

    async def update_template(
        self,
        template_id: UUID,
        user_id: UUID,
        name: Optional[str] = None,
        content: Optional[str] = None,
        is_default: Optional[bool] = None,
    ) -> Optional[ApplicationTemplate]:
        """Update an existing template."""
        template = await self.get_template(template_id, user_id)
        if not template:
            return None

        if name is not None:
            template.name = name
        if content is not None:
            template.content = content
        if is_default is not None:
            # If setting as default, unset other defaults
            if is_default:
                await self.db.execute(
                    update(ApplicationTemplate)
                    .where(
                        and_(
                            ApplicationTemplate.user_id == user_id,
                            ApplicationTemplate.id != template_id,
                        )
                    )
                    .values(is_default=False)
                )
            template.is_default = is_default

        await self.db.commit()
        await self.db.refresh(template)
        return template

    async def delete_template(self, template_id: UUID, user_id: UUID) -> bool:
        """Delete a template."""
        template = await self.get_template(template_id, user_id)
        if not template:
            return False

        # If deleting default, set another as default
        if template.is_default:
            other_result = await self.db.execute(
                select(ApplicationTemplate)
                .where(
                    and_(
                        ApplicationTemplate.user_id == user_id,
                        ApplicationTemplate.id != template_id,
                    )
                )
                .limit(1)
            )
            other_template = other_result.scalar_one_or_none()
            if other_template:
                other_template.is_default = True

        await self.db.delete(template)
        await self.db.commit()
        return True

    async def use_template(self, template_id: UUID, user_id: UUID) -> Optional[str]:
        """Mark a template as used and return its content."""
        template = await self.get_template(template_id, user_id)
        if not template:
            return None

        template.usage_count += 1
        await self.db.commit()
        return template.content

    async def get_default_template(self, user_id: UUID) -> Optional[ApplicationTemplate]:
        """Get the user's default template."""
        result = await self.db.execute(
            select(ApplicationTemplate).where(
                and_(
                    ApplicationTemplate.user_id == user_id,
                    ApplicationTemplate.is_default == True,
                )
            )
        )
        return result.scalar_one_or_none()

    async def get_template_suggestions(self, user_id: UUID, job_type: str = None) -> List[Dict[str, Any]]:
        """Get template suggestions based on job type (Premium feature)."""
        # Check if user is premium
        subscription_service = SubscriptionService(self.db)
        is_premium = await subscription_service.is_premium_user(user_id)

        if not is_premium:
            return []

        # Basic template suggestions
        suggestions = []

        if job_type == "substitute":
            suggestions.append(
                {
                    "name": "대타 전문 템플릿",
                    "content": "안녕하세요! 대타 전문 강사입니다.\n\n"
                    "즉시 투입 가능하며, 수업 준비를 철저히 하여 회원님들께 최상의 경험을 제공하겠습니다.\n\n"
                    "• 즉시 투입 가능\n"
                    "• 대타 경험 다수\n"
                    "• 유연한 스케줄\n\n"
                    "감사합니다.",
                }
            )
        elif job_type == "regular":
            suggestions.append(
                {
                    "name": "정규직 지원 템플릿",
                    "content": "안녕하세요! 귀 스튜디오의 정규직에 지원합니다.\n\n"
                    "장기적으로 함께 성장하고 싶은 열정적인 강사입니다.\n\n"
                    "• 안정적인 근무 가능\n"
                    "• 회원 관리 경험 풍부\n"
                    "• 팀워크 중시\n\n"
                    "면접 기회를 주시면 더 자세히 말씀드리겠습니다.\n"
                    "감사합니다.",
                }
            )
        else:
            # General template
            suggestions.append(
                {
                    "name": "기본 지원 템플릿",
                    "content": "안녕하세요!\n\n"
                    "귀 스튜디오에 지원하게 되어 기쁩니다.\n\n"
                    "제 강점:\n"
                    "• [강점 1]\n"
                    "• [강점 2]\n"
                    "• [강점 3]\n\n"
                    "좋은 인연이 되기를 바랍니다.\n"
                    "감사합니다.",
                }
            )

        return suggestions