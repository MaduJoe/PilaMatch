# PilaMatch - 앱스토어 런칭 TODO

> **작업 구조**: 4개 Git Worktree (`FE`, `BE`, `INFRA`, `DATA`)
> **현재 완성도**: 웹 서비스 75%, 스토어 등록 준비도 30%
> **목표**: 스토어 등록 가능 상태 (예상 7-8주, 최소 경로 3-4주)

---

## Phase 1: 법적 필수 — 없으면 스토어 등록 불가 (1주)

### BE — 계정 삭제 API

- [ ] `DELETE /api/v1/users/me` 엔드포인트 구현 (`app/api/v1/endpoints/auth.py`)
  - Apple 2022.06~, Google 2024~ **필수**. 없으면 100% 리젝
  - 30일 유예기간 soft-delete: `deleted_at`, `deletion_scheduled_at` 필드 추가
  - 즉시 처리: `is_active=False`, 토큰 블랙리스트
  - 30일 후 영구 삭제: 개인정보 익명화 (이메일 해시, 이름 마스킹)
  - Cascade 처리:
    - 활성 계약 → 자동 취소 + 상대방 알림
    - 에스크로 잔액 → 환불 처리
    - 구독 → 자동 해지
    - 프로필/리뷰 → soft-delete (작성한 리뷰는 "탈퇴한 회원"으로 표시)
- [ ] `POST /api/v1/users/me/cancel-deletion` 30일 내 복구 엔드포인트
- [ ] Cron job: 30일 지난 soft-deleted 계정 영구 삭제 스케줄러
- [ ] 관련 스키마: `AccountDeletionRequest`, `AccountDeletionResponse`

### BE — 비밀번호 재설정

- [ ] `POST /api/v1/auth/forgot-password` (이메일로 리셋 토큰 발송)
  - 비밀번호 리셋 토큰 생성 (JWT, 1시간 만료)
  - 이메일 발송 서비스 연동 (초기: 콘솔 로그, 추후 SendGrid/SES)
  - Rate limit: IP당 3회/시간
- [ ] `POST /api/v1/auth/reset-password` (토큰 검증 + 새 비밀번호 설정)
  - 토큰 1회 사용 후 무효화
  - 기존 세션 전체 로그아웃 (refresh token 일괄 블랙리스트)
- [ ] `app/services/email.py` 이메일 서비스 (mock/smtp/sendgrid 전환 가능)
- [ ] `app/core/config.py`에 이메일 관련 환경변수 추가:
  - `EMAIL_PROVIDER`, `SMTP_HOST`, `SMTP_PORT`, `SMTP_USER`, `SMTP_PASSWORD`

### FE — 법적 문서 페이지 + 동의 UI

- [ ] `src/app/(legal)/privacy/page.tsx` — 개인정보처리방침 표시 페이지
- [ ] `src/app/(legal)/terms/page.tsx` — 이용약관 표시 페이지
- [ ] `src/app/(legal)/refund/page.tsx` — 환불정책 표시 페이지
- [ ] `src/app/(legal)/layout.tsx` — 법적 문서 공통 레이아웃 (헤더, 뒤로가기)
- [ ] 회원가입 페이지 수정 (`src/app/(auth)/signup/page.tsx`):
  - 약관 동의 체크박스 2개 추가 (필수):
    - `[필수] 이용약관에 동의합니다` (링크 → /terms)
    - `[필수] 개인정보 처리방침에 동의합니다` (링크 → /privacy)
  - 동의하지 않으면 가입 버튼 비활성화
  - `signupSchema` 에 `terms_agreed`, `privacy_agreed` boolean 필드 추가
- [ ] 비밀번호 찾기 페이지 (`src/app/(auth)/forgot-password/page.tsx`):
  - 이메일 입력 → 전송 → 확인 메시지 3단계 UI
- [ ] 비밀번호 재설정 페이지 (`src/app/(auth)/reset-password/page.tsx`):
  - URL 토큰 파싱 → 새 비밀번호 입력 → 완료 후 로그인 페이지로 이동
- [ ] 로그인 페이지에 "비밀번호를 잊으셨나요?" 링크 추가
- [ ] 계정 삭제 UI:
  - 프로필/설정 페이지에 "회원 탈퇴" 버튼
  - 확인 모달: "정말 탈퇴하시겠습니까? 30일 내 복구 가능합니다"
  - 비밀번호 재입력 확인

### DATA — 스키마 변경

- [ ] User 모델 필드 추가 (`app/models/user.py`):
  - `terms_agreed_at: DateTime` — 약관 동의 일시
  - `privacy_agreed_at: DateTime` — 개인정보 동의 일시
  - `deleted_at: DateTime` — soft-delete 일시
  - `deletion_scheduled_at: DateTime` — 영구 삭제 예정일
- [ ] Alembic 마이그레이션 생성: `012_add_legal_and_deletion_fields.py`

### DOCS — 법적 문서 작성

- [ ] `docs/privacy-policy-ko.md` — 개인정보처리방침 (한국어)
  - PIPA 필수 항목: 수집항목, 수집목적, 보유기간, 제3자 제공, 파기절차
  - 수집 항목: 이메일, 전화번호, 사업자번호, 결제정보, 위치정보
  - 보유기간: 회원탈퇴 후 30일 (법정 의무보관 항목 제외)
  - 제3자 제공: TossPayments(결제), CoolSMS(인증)
- [ ] `docs/privacy-policy-en.md` — Privacy Policy (English)
- [ ] `docs/terms-of-service-ko.md` — 이용약관 (한국어)
  - 서비스 정의, 회원 의무, 금지행위
  - 결제/환불 조건, 에스크로 규칙
  - 분쟁해결 절차, 면책조항, 계정 정지/해지 조건
- [ ] `docs/terms-of-service-en.md` — Terms of Service (English)
- [ ] `docs/refund-policy.md` — 환불정책 (한/영)
  - 에스크로 환불: 계약 시작 전 100%, 진행 중 협의
  - 프리미엄 구독: 7일 이내 전액, 이후 일할 계산
  - 분쟁 기반 환불: 운영자 중재 프로세스

---

## Phase 2: 스토어 리젝 방지 (1-2주)

### FE — 에러 바운더리 & UX 필수

- [ ] `src/app/error.tsx` — 글로벌 에러 바운더리
  - "문제가 발생했습니다" 메시지 + 재시도 버튼 + 홈으로 돌아가기
  - `'use client'` 필수 (Next.js error boundary 규칙)
  - 에러 로깅 훅 포인트 (추후 Sentry 연동)
- [ ] `src/app/not-found.tsx` — 404 페이지
  - "페이지를 찾을 수 없습니다" + 홈으로 돌아가기 버튼
- [ ] `src/app/loading.tsx` — 글로벌 로딩 UI (스피너 또는 스켈레톤)
- [ ] 다크모드 활성화:
  - `next-themes` 이미 설치됨, `ThemeProvider` 래핑만 추가
  - `layout.tsx`에 `<ThemeProvider attribute="class" defaultTheme="system">` 추가
  - 테마 토글 버튼 (설정 또는 헤더에)

### FE — PWA 매니페스트 & 메타데이터

- [ ] `public/manifest.json` 생성:
  ```json
  {
    "name": "PilaMatch - 필라테스/요가 매칭",
    "short_name": "PilaMatch",
    "start_url": "/",
    "display": "standalone",
    "background_color": "#ffffff",
    "theme_color": "#7c3aed",
    "icons": [...]
  }
  ```
- [ ] `public/favicon.ico` — 파비콘 (최소 32x32)
- [ ] `public/icon-192.png`, `public/icon-512.png` — PWA 아이콘
- [ ] `public/apple-touch-icon.png` — iOS 홈 화면 아이콘 (180x180)
- [ ] `layout.tsx` 메타데이터 보강:
  - `manifest` 링크
  - `theme-color` 메타태그
  - `apple-mobile-web-app-capable`, `apple-mobile-web-app-status-bar-style`
  - Open Graph 태그 (카카오톡/SNS 공유 시 미리보기)
  - `viewport` — `width=device-width, initial-scale=1, maximum-scale=1`

### FE — 앱 설명문 & 스토어 에셋 (디자인 필요)

- [ ] `docs/store-description-ko.md` — 한국어 스토어 설명문
- [ ] `docs/store-description-en.md` — 영어 스토어 설명문
- [ ] 앱 아이콘 디자인 요청 (1024x1024 마스터 → 사이즈별 자동 생성)
- [ ] 스크린샷 4장 이상:
  - iPhone 6.7" (1290x2796) — Apple 필수
  - Android phone (1080x1920) — Google 필수
  - 대상 화면: 매칭 목록, 프로필, 계약 상세, 결제

---

## Phase 3: 핵심 기능 보완 (2주)

### BE — 프로필 사진 업로드

- [ ] `app/services/file_upload.py` 파일 업로드 서비스
  - 스토리지 백엔드: local(개발) / S3(프로덕션) 전환 가능
  - 이미지 리사이징: 원본 + 썸네일(200x200) + 중간(600x600)
  - 파일 검증: 타입(JPEG/PNG/WebP), 크기(10MB 이하)
  - 경로: `/uploads/profiles/{user_id}/{uuid}.{ext}`
- [ ] `POST /api/v1/profiles/photo` 프로필 사진 업로드 엔드포인트
- [ ] `DELETE /api/v1/profiles/photo` 프로필 사진 삭제
- [ ] InstructorProfile, StudioProfile 모델에 `photo_url` 필드 추가
- [ ] `app/core/config.py`에 추가:
  - `STORAGE_BACKEND` (local/s3)
  - `S3_BUCKET`, `S3_REGION`, `S3_ACCESS_KEY`, `S3_SECRET_KEY`
  - `UPLOAD_MAX_SIZE_MB`

### BE — 푸시 알림 시스템

- [ ] `app/services/notification.py` 알림 서비스 (신규)
  - FCM(Android) + APNs(iOS) 통합 발송
  - 초기: mock 모드 (DB 저장만), 추후 실제 발송
  - 알림 유형:
    - `NEW_APPLICATION` — 새 지원서 도착
    - `OFFER_RECEIVED` — 오퍼 수신
    - `CONTRACT_STATUS` — 계약 상태 변경
    - `PAYMENT_COMPLETED` — 결제 완료
    - `NO_SHOW_REPORTED` — 노쇼 신고됨
    - `CHAT_MESSAGE` — 새 채팅 메시지
- [ ] `app/models/notification.py` 알림 모델
  - `id`, `user_id`, `type`, `title`, `body`, `data_json`, `is_read`, `created_at`
- [ ] `app/models/device_token.py` 디바이스 토큰 모델
  - `id`, `user_id`, `token`, `platform` (ios/android/web), `created_at`
- [ ] `POST /api/v1/notifications/device-token` 디바이스 토큰 등록
- [ ] `GET /api/v1/notifications` 알림 목록 조회 (페이지네이션)
- [ ] `PATCH /api/v1/notifications/{id}/read` 읽음 처리
- [ ] 기존 서비스에 알림 트리거 추가:
  - `application.py` → 지원 시 스튜디오에 알림
  - `offer.py` → 오퍼 시 강사에 알림
  - `contract.py` → 상태 변경 시 양쪽에 알림
  - `chat.py` → 새 메시지 시 상대방에 알림

### FE — 프로필 사진 & 알림 UI

- [ ] 프로필 사진 업로드 컴포넌트 (`src/components/profile/photo-upload.tsx`)
  - 원형 미리보기 + 업로드/변경/삭제 버튼
  - 드래그 앤 드롭 또는 파일 선택
  - 크롭 기능 (선택적)
- [ ] 알림 벨 아이콘 + 드롭다운 (`src/components/notification/notification-bell.tsx`)
  - 헤더에 알림 아이콘, 미읽음 수 배지
  - 클릭 시 최근 알림 드롭다운
- [ ] 알림 목록 페이지 (`src/app/(app)/notifications/page.tsx`)

### DATA — 스키마 변경

- [ ] `013_add_photo_and_notification.py` 마이그레이션
  - `instructor_profiles` + `studio_profiles`: `photo_url VARCHAR(500)`
  - `notifications` 테이블 신규
  - `device_tokens` 테이블 신규

---

## Phase 4: 프로덕션 준비 (1-2주)

### INFRA — Docker & 배포 설정

- [ ] `backend/entrypoint.sh` 수정:
  - `--reload` 제거 → `--workers ${WORKERS:-4} --loop uvloop`
  - health check 엔드포인트 대기 로직 추가
- [ ] `docker-compose.yml` 프로덕션 모드 분리:
  - `volumes: ./backend:/app` 제거 (핫 리로드용 → 개발 전용)
  - `docker-compose.override.yml`에 개발 전용 설정 분리
- [ ] `docker-compose.prod.yml` 생성:
  - 리소스 제한 (memory, cpu)
  - restart 정책
  - 로그 드라이버 설정
  - health check 강화
- [ ] CORS 설정 프로덕션 대응 (`app/core/config.py`):
  - `ALLOWED_ORIGINS`에 프로덕션 도메인 추가 로직
  - 환경변수: `CORS_ORIGINS=https://pilamatch.com,https://www.pilamatch.com`
- [ ] `.env.example` 완성 (현재 28줄 → 전체 환경변수):
  ```
  # 추가 필요:
  APP_ENV=production
  WORKERS=4
  CORS_ORIGINS=
  EMAIL_PROVIDER=mock
  SMTP_HOST=
  SMTP_PORT=587
  SMTP_USER=
  SMTP_PASSWORD=
  STORAGE_BACKEND=local
  S3_BUCKET=
  S3_REGION=
  S3_ACCESS_KEY=
  S3_SECRET_KEY=
  UPLOAD_MAX_SIZE_MB=10
  FCM_SERVER_KEY=
  SENTRY_DSN=
  ```
- [ ] Nginx 리버스 프록시 설정 (선택):
  - SSL 종료, 정적 파일 서빙, rate limiting

### INFRA — 모니터링 & 로깅

- [ ] Sentry 연동:
  - BE: `sentry-sdk[fastapi]` 패키지 추가, `app/main.py`에 init
  - FE: `@sentry/nextjs` 패키지 추가, `sentry.client.config.ts`
- [ ] 구조화 로깅 (JSON format):
  - `structlog` 또는 `python-json-logger` 도입
  - 현재 stdout 출력 → JSON 형식으로 변환
  - 요청 ID 트레이싱 (`X-Request-ID` 헤더)
- [ ] 헬스체크 엔드포인트 강화 (`GET /api/v1/health`):
  - DB 연결 상태, Redis 연결 상태, 디스크 공간

### INFRA — CI/CD 파이프라인

- [ ] `.github/workflows/ci.yml`:
  - lint (ruff) → test (pytest) → build (docker) → push (ECR/GCR)
- [ ] `.github/workflows/deploy.yml`:
  - staging 자동 배포, production 수동 승인 후 배포

---

## Phase 5: 모바일 앱 패키징 (2주)

### FE — PWA 강화

- [ ] Service Worker 등록 (`public/sw.js`):
  - 오프라인 폴백 페이지
  - 정적 에셋 캐싱 (App Shell 전략)
  - 웹 푸시 알림 수신
- [ ] `next.config.ts`에 PWA 관련 헤더 추가:
  - `Content-Security-Policy`
  - `X-Content-Type-Options: nosniff`
  - `Referrer-Policy`

### FE — Capacitor 래핑 (네이티브 앱)

- [ ] Capacitor 초기 설정:
  - `npx cap init PilaMatch com.pilamatch.app`
  - `capacitor.config.ts` 생성
  - iOS/Android 프로젝트 생성
- [ ] 네이티브 플러그인 연동:
  - `@capacitor/push-notifications` — FCM/APNs
  - `@capacitor/camera` — 프로필 사진 촬영
  - `@capacitor/haptics` — 햅틱 피드백
  - `@capacitor/status-bar` — 상태바 제어
  - `@capacitor/splash-screen` — 스플래시 화면
- [ ] Apple IAP / Google Play Billing:
  - 프리미엄 구독(월 9,900원) → Apple IAP로 전환 필수
  - `@capgo/capacitor-purchases` 또는 RevenueCat SDK
  - BE: `/api/v1/subscriptions/verify-receipt` 영수증 검증 엔드포인트
  - Apple 정책: 디지털 서비스 구독은 IAP 외 결제 수단 사용 시 리젝

---

## 코드 내 TODO 수정 (Phase 1-2 사이 처리)

### BE — 기존 TODO 해결

| 우선순위 | 파일 | 라인 | 내용 | Worktree |
|---------|------|------|------|----------|
| HIGH | `api/v1/endpoints/deposit.py` | :86 | 환불 시 활성 계약 체크 누락 | BE |
| MEDIUM | `api/v1/endpoints/trust.py` | :51 | Trust Score 새로고침 Rate Limit | BE |
| MEDIUM | `services/subscription.py` | :221 | 구독 취소 시 보증금 환불 미처리 | BE |
| MEDIUM | `api/v1/endpoints/subscription.py` | :239 | billing key 역방향 조회 미구현 | BE |
| LOW | `services/trust_score.py` | :218 | 응답률 추적 미구현 | BE |
| LOW | `services/dispute.py` | :313 | 분쟁 리마인더 시스템 미구현 | BE |

> 참고: `deposit.py`는 v3.0에서 DEPRECATED (전체 no-op). 실질적 수정 불필요.
> `subscription.py:221`의 보증금 환불도 deposit 시스템 제거로 dead code.

### 실질적 수정 대상 (2건):
- [ ] `trust.py:51` — `@limiter.limit("1/hour")` 데코레이터 추가
- [ ] `subscription.py:239` — billing key로 사용자 조회 로직 구현

---

## 프로덕션 이슈 수정

| Worktree | 파일 | 이슈 | 수정 내용 |
|----------|------|------|-----------|
| INFRA | `entrypoint.sh:12` | `--reload` (개발 전용) | `--workers 4`로 교체 |
| INFRA | `docker-compose.yml:63` | `./backend:/app` 볼륨 마운트 | override로 분리 |
| FE | `frontend-next/public/` | 완전히 비어있음 | favicon, manifest, 아이콘 추가 |
| INFRA | `.env.example` | 불완전 (28줄) | 전체 환경변수 문서화 |
| BE | `core/config.py:56` | CORS localhost만 | 환경변수 기반 도메인 추가 |
| INFRA | 로그 | stdout만 출력 | 구조화 로깅(JSON) 도입 |

---

## Worktree별 작업 요약

### `FE` (frontend-next/)
```
Phase 1: 법적 문서 페이지, 약관 동의 UI, 비밀번호 찾기/재설정, 계정 삭제 UI
Phase 2: error.tsx, not-found.tsx, loading.tsx, 다크모드, PWA 메타데이터
Phase 3: 프로필 사진 업로드 컴포넌트, 알림 UI
Phase 5: Service Worker, Capacitor 래핑
```

### `BE` (backend/)
```
Phase 1: 계정 삭제 API, 비밀번호 재설정 API, 이메일 서비스
Phase 3: 파일 업로드 서비스, 푸시 알림 서비스
TODO:   trust.py rate limit, subscription billing key 조회
```

### `INFRA` (docker, CI/CD, 배포)
```
Phase 4: entrypoint.sh 수정, docker-compose 분리, .env.example 완성
Phase 4: CORS 프로덕션 설정, Sentry, 구조화 로깅, CI/CD
```

### `DATA` (models, migrations)
```
Phase 1: User 모델 법적 필드 + 마이그레이션 012
Phase 3: 프로필 사진 + 알림/디바이스토큰 테이블 + 마이그레이션 013
```

---

## 우선순위 정리

```
[BLOCKER]  Phase 1  →  스토어 등록 자체가 불가능
[CRITICAL] Phase 2  →  심사 리젝 확률 매우 높음
[HIGH]     Phase 3  →  DAU/리텐션에 직접 영향
[HIGH]     Phase 4  →  프로덕션 안정성
[MEDIUM]   Phase 5  →  네이티브 앱 (PWA로 우선 대체 가능)
```

---

*작성일: 2026-02-26*
