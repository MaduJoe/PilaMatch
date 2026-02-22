# Full Happy Path E2E Scenario

두 명의 사용자(강사 + 스튜디오)가 StudioBridge 플랫폼의 전체 플로우를 사용하는 MCP 시나리오.
Claude Code가 이 파일을 읽고 Playwright MCP 도구로 각 Phase를 실행한다.

**전략**: 브라우저 조작(UI 검증)과 API 직접 호출(빠른 셋업)을 혼합하여 속도와 커버리지를 균형있게 확보.

---

## Phase 1: 회원가입 (API 셋업)

> 두 유저를 API로 빠르게 생성한다.

```bash
# 강사 생성
curl -s -X POST http://localhost:8000/api/v1/auth/signup \
  -H "Content-Type: application/json" \
  -d '{"email":"e2e_inst@test.com","password":"testpass123","role":"instructor","display_name":"E2E강사"}'
# → access_token 저장 (INST_TOKEN)

# 스튜디오 생성
curl -s -X POST http://localhost:8000/api/v1/auth/signup \
  -H "Content-Type: application/json" \
  -d '{"email":"e2e_studio@test.com","password":"testpass123","role":"studio","business_name":"E2E스튜디오"}'
# → access_token 저장 (STUDIO_TOKEN)
```

**검증**: 두 응답 모두 `access_token` 포함

---

## Phase 2: 스튜디오 로그인 + 프로필 완성 (브라우저)

> 스튜디오로 로그인하여 프로필을 작성한다.

1. `browser_navigate` → `http://localhost:8501`
2. "로그인" 탭 클릭
3. 이메일: `e2e_studio@test.com`, 비밀번호: `testpass123` 입력
4. "로그인" 버튼 클릭
5. **검증**: `StudioBridge - 스튜디오` 텍스트 표시 확인
6. 프로필 폼 작성:
   - "스튜디오명 *" → `E2E테스트스튜디오`
   - "소개" → `E2E 테스트용 스튜디오입니다`
   - "지역 *" → `강남`
   - "주소" → `강남구 테헤란로 123`
7. "저장" 버튼 클릭
8. **검증**: 페이지가 공고 등록 페이지로 전환됨 (또는 성공 메시지)

---

## Phase 3: 스튜디오 공고 등록 (브라우저)

> 공고 등록 페이지에서 새 공고를 등록한다.

1. "공고 등록" 네비게이션이 활성화되어 있는지 확인
2. 종목: "필라테스" 버튼 클릭
3. 유형: "대타 (1회)" 버튼 클릭
4. 시급: "5만" 버튼 클릭
5. "공고 등록하기" 버튼 클릭
6. **검증**: "공고가 등록되었습니다!" 메시지 확인

---

## Phase 4: 강사 로그인 + 프로필 완성 (브라우저)

> 로그아웃 후 강사로 로그인하여 프로필을 작성한다.

1. "로그아웃" 버튼 클릭
2. **검증**: 로그인/회원가입 페이지로 복귀
3. "로그인" 탭 클릭
4. 이메일: `e2e_inst@test.com`, 비밀번호: `testpass123` 입력
5. "로그인" 버튼 클릭
6. **검증**: `StudioBridge - 강사` 텍스트 표시
7. 프로필 폼 작성:
   - "활동명 *" → `E2E테스트강사`
   - "자기소개" → `E2E 테스트용 강사입니다`
   - "경력 (년)" → `3`
   - "활동 가능 지역 *" → `강남, 서초`
   - "최소 희망시급" → `40000`
   - "최대 희망시급" → `60000`
8. "저장" 버튼 클릭
9. **검증**: 일 찾기 페이지로 전환

---

## Phase 5: 강사 일 찾기 + 지원 (브라우저)

> 등록된 공고를 찾아 지원한다.

1. "일 찾기" 페이지에서 공고 목록 확인
2. **검증**: Phase 3에서 등록한 공고 카드 표시
3. "지원하기" 버튼 클릭
4. **검증**: "지원 완료!" 또는 "지원완료" 텍스트 표시

---

## Phase 6: 스튜디오 오퍼 전송 (API)

> API로 빠르게 오퍼를 전송한다.

```bash
# 1. 공고의 지원자 목록 조회
curl -s http://localhost:8000/api/v1/job-posts/{JOB_POST_ID}/applications \
  -H "Authorization: Bearer $STUDIO_TOKEN"
# → application_id 저장

# 2. 오퍼 전송
curl -s -X POST http://localhost:8000/api/v1/offers \
  -H "Authorization: Bearer $STUDIO_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{"application_id":"APPLICATION_ID","proposed_rate":50000,"message":"오퍼를 전달합니다"}'
# → offer_id 저장
```

**검증**: 오퍼 생성 응답에 `id` 포함

---

## Phase 7: 강사 오퍼 수락 + 계약 생성 (브라우저)

> 강사가 오퍼를 확인하고 수락한 후 계약을 생성한다.

1. "오퍼 확인" 네비게이션 클릭
2. **검증**: 오퍼 카드 표시 (제안 시급 50,000원)
3. "수락" 버튼 클릭
4. 3초 대기 (Streamlit rerun)
5. "계약 생성" 버튼 클릭
6. **검증**: "계약이 생성되었습니다!" 메시지 또는 계약 진행 페이지로 전환

---

## Phase 8: 양쪽 서명 (브라우저 + API)

> 강사가 UI에서 서명, 스튜디오는 API로 서명.

### 8a. 강사 서명 (브라우저)
1. "계약 진행" 네비게이션 클릭
2. **검증**: 계약 카드 표시 (서명 대기 상태)
3. "약관 확인 후 서명" 확장 클릭
4. "위 약속 사항에 동의합니다" 레이블 클릭 (체크박스 숨김, 레이블로 조작)
5. "서명하기" 버튼 클릭
6. **검증**: 강사 서명 완료 표시

### 8b. 스튜디오 서명 (API)
```bash
curl -s -X POST http://localhost:8000/api/v1/contracts/{CONTRACT_ID}/set-in-progress \
  -H "Authorization: Bearer $STUDIO_TOKEN"
```

### 8c. 결제 (선택사항)
> 참고: 컨테이너에 Toss 테스트 키가 설정된 경우 mock 모드가 아님.
> 결제 확인은 별도 단위 테스트로 검증. 계약 완료는 결제 없이도 진행 가능.

---

## Phase 9: 수업 완료 확인 (브라우저 + API)

> 양쪽이 수업 완료를 확인한다.

### 9a. 스튜디오 완료 확인 (브라우저)
1. "계약 진행" 페이지에서 진행 중 계약 확인
2. "수업 완료" 버튼 클릭
3. **검증**: 완료 대기 상태로 전환

### 9b. 강사 완료 확인 (API)
```bash
curl -s -X POST http://localhost:8000/api/v1/contracts/{CONTRACT_ID}/confirm-completion \
  -H "Authorization: Bearer $INST_TOKEN"
```

**검증**: 계약 상태 `completed`

---

## Phase 10: 리뷰 작성 (브라우저 + API)

> 양쪽이 리뷰를 작성한다.

### 10a. 스튜디오 리뷰 작성 (API - 빠르게)
```bash
curl -s -X POST http://localhost:8000/api/v1/contracts/{CONTRACT_ID}/reviews \
  -H "Authorization: Bearer $STUDIO_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{"rating":5,"comment":"훌륭한 강사였습니다!"}'
```

### 10b. 강사 리뷰 작성 (브라우저)
1. "로그아웃" → 강사 로그인
2. "완료/리뷰" 네비게이션 클릭
3. "✍️ 내가 쓴 리뷰" 탭 클릭
4. 리뷰 작성 폼 확장 → 평점 5 선택 → 후기 입력
5. "리뷰 작성" 버튼 클릭
6. **검증**: "리뷰가 작성되었습니다!" 메시지

---

## 결과 보고 형식

각 Phase 완료 시:
```
✅ Phase 1: 회원가입 (API) - PASS
✅ Phase 2: 스튜디오 프로필 완성 - PASS
❌ Phase 3: 공고 등록 - FAIL (사유: "공고 등록하기" 버튼을 찾을 수 없음)
```

최종: `N/10 Phases 통과`
