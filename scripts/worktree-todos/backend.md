# BACKEND Worktree — 작업 지시서

> **브랜치**: `feat/backend`
> **수정 범위**: `backend/app/api/`, `backend/app/services/`, `backend/app/schemas/`, `backend/app/core/`
> **수정 금지**: `backend/app/models/` (DATA worktree 전용), `pyproject.toml`, `docker-compose.yml`
> **규칙**: 각 작업 단위 완료 후 git commit. 테스트 통과 확인 후 커밋.

---

## Task 1: 계정 삭제 API (Phase 1 — BLOCKER)

Apple/Google 스토어 필수 요구사항. 없으면 100% 리젝.

### 1-1. `DELETE /api/v1/users/me` 엔드포인트

파일: `backend/app/api/v1/endpoints/auth.py`에 추가

```
- 30일 유예기간 soft-delete
- 즉시 처리:
  - user.is_active = False
  - user.deleted_at = now()
  - user.deletion_scheduled_at = now() + 30일
  - 현재 토큰 무효화 (블랙리스트)
- Cascade 처리:
  - 활성 계약 → 자동 취소 (contract.status = CANCELLED)
  - 에스크로 잔액 → 환불 처리 (escrow.status = REFUNDED)
  - 구독 → 자동 해지
  - 프로필/리뷰 → soft-delete
```

### 1-2. `POST /api/v1/users/me/cancel-deletion` 복구 엔드포인트

파일: `backend/app/api/v1/endpoints/auth.py`에 추가

```
- deleted_at이 설정되어 있고 deletion_scheduled_at이 아직 지나지 않은 경우만 허용
- is_active = True, deleted_at = None, deletion_scheduled_at = None
```

### 1-3. 계정 삭제 서비스

파일: `backend/app/services/account_deletion.py` (신규)

```python
class AccountDeletionService:
    async def request_deletion(self, user_id: str) -> None
    async def cancel_deletion(self, user_id: str) -> None
    async def process_expired_deletions(self) -> int  # cron용
    async def _anonymize_user(self, user: User) -> None  # 이메일 해시, 이름 마스킹
    async def _cascade_cancel_contracts(self, user_id: str) -> None
    async def _cascade_refund_escrows(self, user_id: str) -> None
    async def _cascade_cancel_subscriptions(self, user_id: str) -> None
```

### 1-4. 스키마

파일: `backend/app/schemas/auth.py`에 추가

```python
class AccountDeletionRequest(BaseModel):
    password: str  # 비밀번호 재확인

class AccountDeletionResponse(BaseModel):
    message: str
    deletion_scheduled_at: datetime
```

커밋: `feat: 계정 삭제 API (soft-delete + 30일 유예 + cascade)`

---

## Task 2: 비밀번호 재설정 API (Phase 1 — BLOCKER)

### 2-1. `POST /api/v1/auth/forgot-password`

파일: `backend/app/api/v1/endpoints/auth.py`에 추가

```
- 이메일로 리셋 토큰 발송
- JWT 리셋 토큰 생성 (1시간 만료, purpose="password_reset")
- 이메일 발송 (EmailService 사용)
- 존재하지 않는 이메일도 200 응답 (정보 유출 방지)
- Rate limit: 동일 이메일 3회/시간
```

### 2-2. `POST /api/v1/auth/reset-password`

파일: `backend/app/api/v1/endpoints/auth.py`에 추가

```
- 토큰 검증 + 새 비밀번호 설정
- 토큰 1회 사용 후 무효화 (DB에 used_at 기록 또는 JWT jti 블랙리스트)
- 기존 세션 전체 로그아웃
```

### 2-3. 이메일 서비스

파일: `backend/app/services/email.py` (신규)

```python
class EmailService:
    """이메일 발송 서비스. mock/smtp/sendgrid 전환 가능."""

    async def send_password_reset(self, email: str, token: str) -> None
    async def send_account_deletion_notice(self, email: str) -> None

    # 내부
    async def _send_mock(self, to: str, subject: str, body: str) -> None  # 콘솔 로그
    async def _send_smtp(self, to: str, subject: str, body: str) -> None
```

### 2-4. Config 추가

파일: `backend/app/core/config.py`에 추가

```python
EMAIL_PROVIDER: str = "mock"  # mock / smtp / sendgrid
SMTP_HOST: str = ""
SMTP_PORT: int = 587
SMTP_USER: str = ""
SMTP_PASSWORD: str = ""
PASSWORD_RESET_EXPIRE_MINUTES: int = 60
```

### 2-5. 스키마

파일: `backend/app/schemas/auth.py`에 추가

```python
class ForgotPasswordRequest(BaseModel):
    email: EmailStr

class ResetPasswordRequest(BaseModel):
    token: str
    new_password: str  # min 8자, 영문+숫자
```

커밋: `feat: 비밀번호 재설정 API (forgot + reset + email service)`

---

## Task 3: 기존 TODO 수정 (Phase 1-2)

### 3-1. Trust Score Rate Limit

파일: `backend/app/api/v1/endpoints/trust.py` (약 51행)

```
- Trust Score 새로고침에 rate limit 추가
- 방법: 엔드포인트에서 마지막 갱신 시간 체크, 1시간 이내면 캐시된 값 반환
- slowapi가 없으면 수동으로 시간 체크 로직 구현
```

### 3-2. Billing Key 역방향 조회

파일: `backend/app/api/v1/endpoints/subscription.py` (약 239행) 또는 `backend/app/services/subscription.py`

```
- billing key로 사용자 조회하는 로직 구현
- Toss Payments 웹훅에서 billing key로 구독 갱신 시 필요
```

커밋: `fix: trust score rate limit + billing key 역방향 조회`

---

## Task 4: 프로필 사진 업로드 서비스 (Phase 3)

### 4-1. 파일 업로드 서비스

파일: `backend/app/services/file_upload.py` (신규)

```python
class FileUploadService:
    """local(개발) / S3(프로덕션) 전환 가능 파일 업로드."""

    async def upload_profile_photo(self, user_id: str, file: UploadFile) -> str
    async def delete_profile_photo(self, user_id: str, photo_url: str) -> None

    def _validate_image(self, file: UploadFile) -> None  # 타입, 크기 검증
    async def _resize_image(self, data: bytes) -> dict  # 원본 + 썸네일(200x200) + 중간(600x600)
    async def _save_local(self, path: str, data: bytes) -> str
    async def _save_s3(self, key: str, data: bytes) -> str
```

- 파일 검증: JPEG/PNG/WebP, 10MB 이하
- 경로: `/uploads/profiles/{user_id}/{uuid}.{ext}`
- Pillow(PIL) 사용하여 리사이즈

### 4-2. API 엔드포인트

파일: `backend/app/api/v1/endpoints/profiles.py`에 추가

```python
@router.post("/photo")
async def upload_profile_photo(
    file: UploadFile = File(...),
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
)

@router.delete("/photo")
async def delete_profile_photo(...)
```

### 4-3. Config 추가

파일: `backend/app/core/config.py`에 추가

```python
STORAGE_BACKEND: str = "local"  # local / s3
S3_BUCKET: str = ""
S3_REGION: str = ""
UPLOAD_MAX_SIZE_MB: int = 10
```

커밋: `feat: 프로필 사진 업로드 (local/S3 + 리사이즈)`

---

## Task 5: 푸시 알림 서비스 (Phase 3)

### 5-1. 알림 서비스

파일: `backend/app/services/notification.py` (신규)

```python
class NotificationService:
    """FCM + APNs 통합. 초기엔 mock (DB 저장만)."""

    async def send(self, user_id: str, type: str, title: str, body: str, data: dict = None) -> None
    async def send_bulk(self, user_ids: list[str], ...) -> None
    async def mark_read(self, notification_id: str, user_id: str) -> None
    async def get_notifications(self, user_id: str, skip: int, limit: int) -> list
    async def get_unread_count(self, user_id: str) -> int
```

알림 유형: `NEW_APPLICATION`, `OFFER_RECEIVED`, `CONTRACT_STATUS`, `PAYMENT_COMPLETED`, `NO_SHOW_REPORTED`, `CHAT_MESSAGE`

### 5-2. API 엔드포인트

파일: `backend/app/api/v1/endpoints/notifications.py` (신규)

```python
@router.post("/device-token")    # 디바이스 토큰 등록
@router.get("/")                  # 알림 목록 (페이지네이션)
@router.patch("/{id}/read")      # 읽음 처리
@router.get("/unread-count")     # 미읽음 수
```

### 5-3. 기존 서비스에 알림 트리거 추가

각 서비스에서 상태 변경 시 `NotificationService.send()` 호출 추가:
- `application.py` → 지원 시 스튜디오에 알림
- `offer.py` → 오퍼 시 강사에 알림
- `contract.py` → 상태 변경 시 양쪽에 알림

### 5-4. 라우터 등록

파일: `backend/app/api/v1/router.py`에 notifications 라우터 추가

커밋: `feat: 푸시 알림 서비스 (mock + DB 저장 + API)`

---

## 작업 순서 요약

```
Task 1 (계정 삭제) → Task 2 (비밀번호 재설정) → Task 3 (TODO 수정) → Task 4 (사진 업로드) → Task 5 (알림)
```

각 Task 완료 후 반드시:
1. `cd backend && uv run pytest tests/ -x -q` 로 기존 테스트 깨지지 않는지 확인
2. git commit
