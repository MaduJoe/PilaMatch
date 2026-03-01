시나리오 기반 E2E 테스트를 Playwright MCP로 실행합니다.

## 실행 절차

1. 서비스 상태 확인 (docker-compose up -d)
2. `tests/e2e/scenarios/full_happy_path.md` 시나리오 파일 읽기
3. Playwright MCP 도구로 브라우저를 열어 http://localhost:3000 접속
4. 시나리오의 각 Phase를 순서대로 실행:
   - API 셋업 단계: Bash 도구로 curl 명령 실행
   - UI 단계: Playwright MCP 도구 사용 (browser_navigate, browser_click, browser_type, browser_snapshot, browser_screenshot)
   - 검증 단계: browser_snapshot으로 접근성 트리 확인, 예상 텍스트 존재 확인
5. 각 Phase 결과를 pass/fail로 보고
6. 실패 시 browser_screenshot으로 스크린샷 촬영

## Next.js 상호작용 주의사항

- **라우팅**: App Router 기반 SPA 네비게이션 — `<Link>` 컴포넌트로 페이지 전환, 전체 페이지 새로고침 불필요
- **폼**: React controlled components — 입력 후 상태 업데이트 대기
- **결제**: mock 모드 → "테스트 결제 완료" 버튼 클릭 또는 API 직접 confirm
- **OTP**: APP_ENV=development → API 응답에 _dev_otp 포함
- **두 유저 전환**: "로그아웃" 클릭 → 다른 유저 "로그인" (한 브라우저에 한 명만 로그인 가능)
- **API 직접 호출**: 상대방 액션이 UI 확인 불필요할 때 curl로 빠르게 처리
- **로딩 상태**: React 상태 업데이트 후 리렌더링 대기 (1-2초)

## 셀렉터 참조

| UI 요소 | 셀렉터 방식 |
|---------|------------|
| 링크/네비게이션 | `page.get_by_role("link", name="일 찾기")` |
| 텍스트 입력 | `page.get_by_label("이메일")` 또는 `page.get_by_placeholder("이메일 입력")` |
| 버튼 | `page.get_by_role("button", name="저장")` |
| 탭 | `page.get_by_role("tab", name="강사")` |
| 체크박스 | `page.get_by_label("위 약속 사항에 동의합니다")` |
| 셀렉트 | `page.get_by_role("combobox", name="지역")` |
| 확인 메시지 | `expect(page.get_by_text("공고가 등록되었습니다!")).to_be_visible(timeout=10000)` |
| data-testid | `page.get_by_test_id("submit-button")` — 컴포넌트에 testid가 있는 경우 |

## 보고 형식

각 Phase 완료 시:
```
✅ Phase N: [설명] - PASS
❌ Phase N: [설명] - FAIL (사유)
```

최종: `N/10 Phases 통과`
