# DATA Worktree — 작업 지시서

> **브랜치**: `feat/data`
> **수정 범위**: `backend/app/models/`, `backend/alembic/`, `backend/app/services/` 중 payment/trust 서비스
> **수정 금지**: `backend/app/api/` (BACKEND 전용), `frontend-next/` (FRONTEND 전용), `docker-compose.yml`
> **규칙**: 모델 변경 후 반드시 Alembic 마이그레이션 생성. 각 작업 완료 후 git commit.

---

## Task 1: User 모델 법적 필드 추가 (Phase 1 — BLOCKER)

파일: `backend/app/models/user.py` 수정

기존 User 모델에 다음 필드 추가:

```python
# 약관 동의
terms_agreed_at = Column(DateTime, nullable=True)       # 이용약관 동의 일시
privacy_agreed_at = Column(DateTime, nullable=True)      # 개인정보 동의 일시

# 계정 삭제 (soft-delete)
deleted_at = Column(DateTime, nullable=True)             # soft-delete 일시
deletion_scheduled_at = Column(DateTime, nullable=True)  # 영구 삭제 예정일 (deleted_at + 30일)
```

참고: GUID 타입, String(20) 컨벤션 등 기존 패턴 따를 것.

커밋: `feat: User 모델 법적 필드 추가 (약관동의, soft-delete)`

---

## Task 2: 마이그레이션 012 생성 (Phase 1)

```bash
cd backend
alembic revision --autogenerate -m "add_legal_and_deletion_fields"
```

생성된 마이그레이션 파일 검토:
- `terms_agreed_at`, `privacy_agreed_at`, `deleted_at`, `deletion_scheduled_at` 4개 컬럼 추가 확인
- nullable=True 확인
- downgrade에서 컬럼 삭제 확인

```bash
alembic upgrade head  # 적용 확인
```

커밋: `chore: migration 012 — legal and deletion fields`

---

## Task 3: Notification 모델 (Phase 3)

파일: `backend/app/models/notification.py` (신규)

```python
from app.models.base import Base, GUID, TimestampMixin
from sqlalchemy import Column, String, Boolean, DateTime, Text, ForeignKey, JSON

class Notification(Base, TimestampMixin):
    __tablename__ = "notifications"

    id = Column(GUID, primary_key=True, default=generate_uuid)
    user_id = Column(GUID, ForeignKey("users.id"), nullable=False, index=True)
    type = Column(String(30), nullable=False)  # NEW_APPLICATION, OFFER_RECEIVED, etc.
    title = Column(String(200), nullable=False)
    body = Column(Text, nullable=True)
    data_json = Column(JSON, nullable=True)  # 추가 데이터 (관련 ID 등)
    is_read = Column(Boolean, default=False, nullable=False)
    read_at = Column(DateTime, nullable=True)
```

알림 타입 상수 (같은 파일 또는 enums.py):
```python
class NotificationType:
    NEW_APPLICATION = "NEW_APPLICATION"
    OFFER_RECEIVED = "OFFER_RECEIVED"
    CONTRACT_STATUS = "CONTRACT_STATUS"
    PAYMENT_COMPLETED = "PAYMENT_COMPLETED"
    NO_SHOW_REPORTED = "NO_SHOW_REPORTED"
    CHAT_MESSAGE = "CHAT_MESSAGE"
```

커밋: `feat: Notification 모델`

---

## Task 4: DeviceToken 모델 (Phase 3)

파일: `backend/app/models/device_token.py` (신규)

```python
class DeviceToken(Base, TimestampMixin):
    __tablename__ = "device_tokens"

    id = Column(GUID, primary_key=True, default=generate_uuid)
    user_id = Column(GUID, ForeignKey("users.id"), nullable=False, index=True)
    token = Column(String(500), nullable=False, unique=True)
    platform = Column(String(20), nullable=False)  # "ios" / "android" / "web"
    is_active = Column(Boolean, default=True, nullable=False)
```

커밋: `feat: DeviceToken 모델`

---

## Task 5: 프로필 사진 필드 추가 (Phase 3)

파일: `backend/app/models/instructor.py` 수정 — InstructorProfile에 추가:
```python
photo_url = Column(String(500), nullable=True)
```

파일: `backend/app/models/studio.py` 수정 — StudioProfile에 추가:
```python
photo_url = Column(String(500), nullable=True)
```

커밋: `feat: 프로필 사진 URL 필드 추가`

---

## Task 6: models/__init__.py 업데이트

파일: `backend/app/models/__init__.py` 수정

새 모델 import 추가:
```python
from app.models.notification import Notification, NotificationType
from app.models.device_token import DeviceToken
```

커밋: `chore: models __init__ 업데이트`

---

## Task 7: 마이그레이션 013 생성 (Phase 3)

```bash
cd backend
alembic revision --autogenerate -m "add_photo_notification_device_token"
```

검토 사항:
- `instructor_profiles.photo_url` VARCHAR(500) nullable
- `studio_profiles.photo_url` VARCHAR(500) nullable
- `notifications` 테이블 신규 생성
- `device_tokens` 테이블 신규 생성
- 인덱스: `notifications.user_id`, `device_tokens.user_id`

```bash
alembic upgrade head  # 적용 확인
```

커밋: `chore: migration 013 — photo, notification, device_token`

---

## Task 8: 스키마 추가 (Phase 3)

파일: `backend/app/schemas/notification.py` (신규)

```python
from pydantic import BaseModel
from datetime import datetime
from typing import Optional

class NotificationResponse(BaseModel):
    id: str
    type: str
    title: str
    body: Optional[str]
    data_json: Optional[dict]
    is_read: bool
    created_at: datetime

class NotificationListResponse(BaseModel):
    items: list[NotificationResponse]
    total: int

class DeviceTokenCreate(BaseModel):
    token: str
    platform: str  # ios / android / web

class UnreadCountResponse(BaseModel):
    count: int
```

커밋: `feat: Notification/DeviceToken 스키마`

---

## 작업 순서 요약

```
Task 1 (User 필드) → Task 2 (migration 012) → Task 3-6 (Notification/DeviceToken/Photo 모델)
→ Task 7 (migration 013) → Task 8 (스키마)
```

각 Task 완료 후:
1. `cd backend && uv run pytest tests/ -x -q` 로 기존 테스트 깨지지 않는지 확인
2. 마이그레이션 후 `alembic upgrade head` 성공 확인
3. git commit
