# FRONTEND Worktree — 작업 지시서

> **브랜치**: `feat/frontend`
> **수정 범위**: `frontend-next/src/` 전체, `frontend-next/public/`
> **수정 금지**: `backend/` 전체, `docker-compose.yml`, `pyproject.toml`
> **규칙**: 각 작업 단위 완료 후 git commit. 브라우저에서 모바일 뷰 확인.

---

## Task 1: 법적 문서 페이지 (Phase 1 — BLOCKER)

### 1-1. 법적 문서 공통 레이아웃

파일: `frontend-next/src/app/(legal)/layout.tsx` (신규)

```
- 깔끔한 문서 읽기 레이아웃
- 헤더: 뒤로가기 버튼 + 제목
- max-w-3xl mx-auto, 적절한 padding
- 하단: 홈으로 돌아가기 링크
```

### 1-2. 개인정보처리방침 페이지

파일: `frontend-next/src/app/(legal)/privacy/page.tsx` (신규)

```
- 한국어 개인정보처리방침 표시
- 내용은 docs/privacy-policy-ko.md 참조 (없으면 표준 PIPA 템플릿 사용)
- 필수 항목: 수집항목, 수집목적, 보유기간, 제3자 제공, 파기절차
- 수집 항목: 이메일, 전화번호, 사업자번호, 결제정보
- 제3자 제공: TossPayments(결제), CoolSMS(인증)
```

### 1-3. 이용약관 페이지

파일: `frontend-next/src/app/(legal)/terms/page.tsx` (신규)

```
- 한국어 이용약관
- 서비스 정의, 회원 의무, 금지행위
- 결제/환불 조건, 에스크로 규칙
- 계정 정지/해지 조건
```

### 1-4. 환불정책 페이지

파일: `frontend-next/src/app/(legal)/refund/page.tsx` (신규)

```
- 에스크로 환불: 계약 시작 전 100%, 진행 중 협의
- 프리미엄 구독: 7일 이내 전액, 이후 일할 계산
- 분쟁 기반 환불: 운영자 중재 프로세스
```

커밋: `feat: 법적 문서 페이지 (개인정보처리방침, 이용약관, 환불정책)`

---

## Task 2: 회원가입 약관 동의 UI (Phase 1 — BLOCKER)

파일: `frontend-next/src/app/(auth)/signup/page.tsx` 수정

```
- 약관 동의 체크박스 2개 추가 (가입 폼 하단, 가입 버튼 위):
  - ☐ [필수] 이용약관에 동의합니다 ("이용약관" 텍스트는 /terms 링크)
  - ☐ [필수] 개인정보 처리방침에 동의합니다 ("개인정보 처리방침" 텍스트는 /privacy 링크)
- 전체 동의 체크박스 (선택적 UX 개선)
- 두 체크박스 모두 체크해야 가입 버튼 활성화
- signupSchema(또는 해당 zod 스키마)에 terms_agreed, privacy_agreed boolean 필드 추가
- API 호출 시 terms_agreed, privacy_agreed 값 함께 전송
```

커밋: `feat: 회원가입 약관 동의 체크박스 UI`

---

## Task 3: 비밀번호 찾기/재설정 페이지 (Phase 1 — BLOCKER)

### 3-1. 비밀번호 찾기

파일: `frontend-next/src/app/(auth)/forgot-password/page.tsx` (신규)

```
- 3단계 UI:
  1. 이메일 입력 폼
  2. "전송" 버튼 클릭 → POST /api/v1/auth/forgot-password
  3. 성공 메시지: "비밀번호 재설정 링크가 이메일로 발송되었습니다"
- 이메일 validation (zod)
- 로그인 페이지로 돌아가기 링크
```

### 3-2. 비밀번호 재설정

파일: `frontend-next/src/app/(auth)/reset-password/page.tsx` (신규)

```
- URL에서 token 쿼리 파라미터 파싱
- 새 비밀번호 + 비밀번호 확인 입력
- POST /api/v1/auth/reset-password 호출
- 성공 시 "비밀번호가 변경되었습니다" + 로그인 페이지로 자동 이동 (3초)
- 토큰 만료/잘못된 경우 에러 메시지
```

### 3-3. 로그인 페이지 수정

파일: `frontend-next/src/app/(auth)/login/page.tsx` 수정

```
- 로그인 폼 하단에 "비밀번호를 잊으셨나요?" 링크 추가 → /forgot-password
```

커밋: `feat: 비밀번호 찾기/재설정 페이지`

---

## Task 4: 계정 삭제 UI (Phase 1 — BLOCKER)

파일: 프로필/설정 페이지에 추가 (기존 설정 페이지가 있으면 거기에, 없으면 `frontend-next/src/app/(app)/settings/page.tsx` 신규)

```
- "회원 탈퇴" 버튼 (빨간색, 페이지 하단)
- 클릭 시 확인 모달:
  - "정말 탈퇴하시겠습니까?"
  - "30일 내 로그인하면 복구 가능합니다"
  - "활성 계약은 자동 취소됩니다"
  - 비밀번호 재입력 필드
  - [취소] [탈퇴] 버튼
- DELETE /api/v1/users/me 호출
- 성공 시 로그아웃 + 홈으로 이동
```

커밋: `feat: 계정 삭제 UI (확인 모달 + 비밀번호 확인)`

---

## Task 5: 에러 바운더리 & 필수 UX (Phase 2 — 리젝 방지)

### 5-1. 글로벌 에러 바운더리

파일: `frontend-next/src/app/error.tsx` (신규)

```tsx
'use client'
// "문제가 발생했습니다" 메시지
// 재시도 버튼 (reset() 호출)
// 홈으로 돌아가기 버튼
// 에러 로깅 포인트 (console.error, 추후 Sentry)
```

### 5-2. 404 페이지

파일: `frontend-next/src/app/not-found.tsx` (신규)

```
- "페이지를 찾을 수 없습니다"
- 홈으로 돌아가기 버튼
- 이전 페이지로 돌아가기 버튼
```

### 5-3. 글로벌 로딩 UI

파일: `frontend-next/src/app/loading.tsx` (신규)

```
- 심플한 스피너 또는 스켈레톤 UI
- 중앙 정렬
```

커밋: `feat: error boundary, 404, loading UI`

---

## Task 6: 다크모드 (Phase 2)

파일: `frontend-next/src/app/layout.tsx` 수정

```
- next-themes가 이미 설치되어 있다면 ThemeProvider 래핑 추가
  <ThemeProvider attribute="class" defaultTheme="system" enableSystem>
- 미설치 시: npm install next-themes
- 테마 토글 버튼 컴포넌트 생성 (sun/moon 아이콘)
- 헤더 또는 설정에 토글 버튼 배치
```

커밋: `feat: 다크모드 (next-themes + 토글 버튼)`

---

## Task 7: PWA 매니페스트 & 메타데이터 (Phase 2)

### 7-1. manifest.json

파일: `frontend-next/public/manifest.json` (신규)

```json
{
  "name": "PilaMatch - 필라테스/요가 매칭",
  "short_name": "PilaMatch",
  "start_url": "/",
  "display": "standalone",
  "background_color": "#ffffff",
  "theme_color": "#7c3aed",
  "icons": [
    { "src": "/icon-192.png", "sizes": "192x192", "type": "image/png" },
    { "src": "/icon-512.png", "sizes": "512x512", "type": "image/png" }
  ]
}
```

### 7-2. 아이콘 생성

- SVG 기반 간단한 아이콘을 코드로 생성하거나 placeholder 사용
- `public/icon-192.png`, `public/icon-512.png`
- `public/apple-touch-icon.png` (180x180)
- 기존 `favicon.ico` 확인, 없으면 생성

### 7-3. layout.tsx 메타데이터 보강

파일: `frontend-next/src/app/layout.tsx` 수정

```typescript
export const metadata: Metadata = {
  title: "PilaMatch - 필라테스/요가 강사 매칭",
  description: "신뢰 기반 필라테스/요가 강사-스튜디오 매칭 플랫폼",
  manifest: "/manifest.json",
  themeColor: "#7c3aed",
  viewport: "width=device-width, initial-scale=1, maximum-scale=1",
  openGraph: {
    title: "PilaMatch",
    description: "신뢰 기반 필라테스/요가 강사-스튜디오 매칭",
    type: "website",
  },
  appleWebApp: {
    capable: true,
    statusBarStyle: "default",
    title: "PilaMatch",
  },
}
```

커밋: `feat: PWA manifest + 메타데이터 + 아이콘`

---

## Task 8: 프로필 사진 & 알림 UI (Phase 3)

### 8-1. 프로필 사진 업로드 컴포넌트

파일: `frontend-next/src/components/profile/photo-upload.tsx` (신규)

```
- 원형 미리보기 (Avatar)
- 업로드/변경/삭제 버튼
- 파일 선택 (input type=file, accept=image/*)
- 업로드 중 로딩 표시
- POST /api/v1/profiles/photo (multipart/form-data)
```

### 8-2. 알림 벨 아이콘

파일: `frontend-next/src/components/notification/notification-bell.tsx` (신규)

```
- 헤더에 벨 아이콘
- 미읽음 수 배지 (빨간 원)
- 클릭 시 드롭다운: 최근 알림 5개 + "전체 보기" 링크
- GET /api/v1/notifications?limit=5
- GET /api/v1/notifications/unread-count
```

### 8-3. 알림 목록 페이지

파일: `frontend-next/src/app/(app)/notifications/page.tsx` (신규)

```
- 알림 목록 (무한 스크롤 또는 페이지네이션)
- 각 알림: 아이콘 + 제목 + 본문 + 시간
- 클릭 시 읽음 처리 + 관련 페이지로 이동
- 빈 상태: "새로운 알림이 없습니다"
```

커밋: `feat: 프로필 사진 업로드 + 알림 UI`

---

## 작업 순서 요약

```
Task 1 (법적 문서) → Task 2 (약관 동의) → Task 3 (비밀번호) → Task 4 (계정 삭제)
→ Task 5 (에러/UX) → Task 6 (다크모드) → Task 7 (PWA) → Task 8 (사진/알림)
```

각 Task 완료 후:
1. `cd frontend-next && npm run build` 로 빌드 에러 없는지 확인
2. git commit
