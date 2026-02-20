# T2: Frontend UI — TODO

## 이 터미널의 역할

Streamlit 프론트엔드 페이지, UI 컴포넌트, API 클라이언트 관련 작업 담당.

**담당 파일 범위:**
- `frontend/pages/` — Streamlit 페이지
- `frontend/components/` — UI 컴포넌트
- `frontend/utils/` — 유틸리티, 상수
- `frontend/app.py` — Streamlit 엔트리포인트
- `frontend/api_client.py` — HTTP 클라이언트

**CLAUDE.md 에이전트:** `frontend-ui`

---

## TODO 목록

| # | 우선순위 | 작업 | 의존성 |
|---|---------|------|--------|
| 9 | CRITICAL | 결제 페이지 하드코딩 키 제거 + APIClient 통일 | - |
| 10 | HIGH | 모든 API 호출에 spinner 추가 | - |
| 11 | HIGH | 공고 페이지네이션 + 자동 새로고침 | T1-#8 먼저 |
| 12 | MEDIUM | bare except → 구체적 예외 처리 | - |
| 13 | MEDIUM | API 클라이언트 retry + 타임아웃 개선 | - |
| 14 | LOW | 모바일 반응형 레이아웃 | - |

---

## 작업 상세

### #9 — 결제 페이지 하드코딩 키 제거 + APIClient 통일 [CRITICAL]

**문제:** `frontend/pages/payment.py:65`에 Toss 테스트 클라이언트 키가 하드코딩됨.

**수정 파일:**
- `frontend/pages/payment.py:65` — 하드코딩된 Toss 키 제거
- `frontend/pages/payment_success.py` — APIClient 사용 확인
- `frontend/pages/payment_fail.py` — 에러 처리 확인

**수정 내용:**
```python
# payment.py:65 현재
toss_client_key = 'test_ck_0RnYX2w532eGxBP9jDJe8NeyqApQ'  # 하드코딩!

# 수정 후
import os
toss_client_key = os.getenv('TOSS_CLIENT_KEY', '')
if not toss_client_key:
    st.error("결제 설정이 완료되지 않았습니다.")
    st.stop()
```

**프롬프트 예시:**
```
frontend/pages/payment.py:65의 하드코딩된 Toss 테스트 키를 환경변수로 바꿔줘.
os.getenv('TOSS_CLIENT_KEY')를 사용하고, 없으면 에러 메시지 표시.
payment_success.py와 payment_fail.py도 APIClient를 제대로 쓰고 있는지 확인해줘.
```

---

### #10 — 모든 API 호출에 spinner 추가 [HIGH]

**문제:** API 호출 시 사용자에게 로딩 표시가 없어 UX가 나쁨.

**수정 파일:**
- `frontend/pages/step1_profile.py` — 프로필 저장 시
- `frontend/pages/step2_jobs.py` — 공고 목록/지원 시
- `frontend/pages/step4_contracts.py` — 계약 관련 API 호출 시
- `frontend/pages/auth.py` — 로그인/회원가입 시

**수정 내용:**
```python
# 변경 전
response = client.post("/api/v1/applications", ...)

# 변경 후
with st.spinner("지원서를 제출하는 중..."):
    response = client.post("/api/v1/applications", ...)
```

**프롬프트 예시:**
```
frontend/pages/ 아래 모든 파일에서 API 호출(client.get, client.post, client.put, client.delete)을
st.spinner()로 감싸줘. 한국어 메시지 사용.
예: "로그인 중...", "프로필 저장 중...", "지원서 제출 중...", "계약 처리 중..."
```

---

### #11 — 공고 페이지네이션 + 자동 새로고침 [HIGH]

**의존성:** T1-#8 (백엔드 페이지네이션) 완료 후 작업

**문제:** 공고 목록이 전체를 한번에 로드. 페이지네이션 없음.

**수정 파일:**
- `frontend/pages/step2_jobs.py` — 페이지네이션 UI 추가

**수정 내용:**
```python
# 페이지 상태 관리
if 'job_page' not in st.session_state:
    st.session_state.job_page = 0

# 페이지네이션 파라미터
skip = st.session_state.job_page * 20
response = client.get(f"/api/v1/jobs?skip={skip}&limit=20")

# 페이지 네비게이션
col1, col2, col3 = st.columns(3)
with col1:
    if st.button("← 이전") and st.session_state.job_page > 0:
        st.session_state.job_page -= 1
        st.rerun()
with col3:
    if st.button("다음 →"):
        st.session_state.job_page += 1
        st.rerun()

# 자동 새로고침 (30초)
st_autorefresh(interval=30000, key="jobs_refresh")
```

**프롬프트 예시:**
```
step2_jobs.py에 공고 목록 페이지네이션을 추가해줘.
session_state로 현재 페이지 관리하고, skip/limit 파라미터 전달.
st-autorefresh로 30초 자동 새로고침도 추가해줘.
```

---

### #12 — bare except → 구체적 예외 처리 [MEDIUM]

**문제:** 12개 이상의 `except:` (bare except)가 모든 예외를 삼킴. 디버깅 어려움.

**수정 파일 및 라인:**
| 파일 | 라인 | 컨텍스트 |
|------|------|----------|
| `frontend/api_client.py` | :62 | JSON 파싱 에러 |
| `frontend/utils/helpers.py` | :53 | 프로필 완성도 확인 |
| `frontend/utils/helpers.py` | :74 | 오퍼/잡 조회 |
| `frontend/utils/helpers.py` | :94 | 계약 조회 |
| `frontend/pages/step2_jobs.py` | :29 | 내 지원서 조회 |
| `frontend/pages/step2_jobs.py` | :358 | 잡 리스트 렌더링 |
| `frontend/pages/step1_profile.py` | :257 | Trust Score 표시 |
| `frontend/pages/step5_complete.py` | :76, :196, :235 | 날짜 파싱, 리뷰 렌더링 |

**수정 패턴:**
```python
# 변경 전
except:
    pass

# 변경 후 (네트워크 호출)
except httpx.HTTPError as e:
    st.warning(f"서버 연결 오류: {e}")
except Exception as e:
    st.warning(f"알 수 없는 오류: {e}")

# 변경 후 (파싱)
except (ValueError, KeyError) as e:
    pass  # 파싱 실패 시 기본값 사용
```

**프롬프트 예시:**
```
프론트엔드 코드에서 bare except: 를 모두 찾아서 구체적 예외로 바꿔줘.
api_client.py:62, helpers.py:53,74,94, step2_jobs.py:29,358,
step1_profile.py:257, step5_complete.py:76,196,235 에 있어.
네트워크 호출은 httpx.HTTPError, 파싱은 ValueError/KeyError로 처리.
```

---

### #13 — API 클라이언트 retry + 타임아웃 개선 [MEDIUM]

**문제:** API 호출 실패 시 재시도 없음. 타임아웃 설정도 부족.

**수정 파일:**
- `frontend/api_client.py` — httpx 클라이언트 설정 개선

**수정 내용:**
```python
import httpx
from tenacity import retry, stop_after_attempt, wait_exponential

class APIClient:
    def __init__(self, base_url: str, timeout: float = 10.0):
        self.client = httpx.Client(
            base_url=base_url,
            timeout=httpx.Timeout(timeout, connect=5.0),
        )

    @retry(stop=stop_after_attempt(3), wait=wait_exponential(min=1, max=5))
    def _request(self, method, url, **kwargs):
        return self.client.request(method, url, **kwargs)
```

**프롬프트 예시:**
```
frontend/api_client.py에 retry 로직과 타임아웃 설정을 추가해줘.
httpx.Timeout으로 전체 10초, 연결 5초 설정.
tenacity로 최대 3회 재시도, exponential backoff 적용.
```

---

### #14 — 모바일 반응형 레이아웃 [LOW]

**문제:** Streamlit 기본 레이아웃은 모바일에서 불편.

**수정 파일:**
- `frontend/app.py` — 레이아웃 설정
- `frontend/pages/*.py` — 컬럼 레이아웃 조정

**수정 내용:**
```python
# 화면 너비 감지
st.set_page_config(layout="centered")  # 모바일 친화적

# 조건부 컬럼
if st.session_state.get('mobile_mode'):
    # 단일 컬럼
    col = st.container()
else:
    col1, col2 = st.columns(2)
```

**프롬프트 예시:**
```
Streamlit 페이지들을 모바일 친화적으로 개선해줘.
좁은 화면에서 컬럼이 깨지지 않도록 layout="centered" 사용하고,
카드 UI는 st.container()로 감싸줘.
```

---

## 실행 순서 가이드

```
1라운드: #9 (결제 하드코딩 제거) — 독립, 즉시 가능
   ↓
2라운드: #10 (spinner) + #12 (bare except) — 병렬 가능
   ↓
3라운드: #13 (retry/timeout) — #12 완료 후
   ↓
4라운드: #11 (페이지네이션) — T1-#8 완료 후
   ↓
5라운드: #14 (모바일 레이아웃) — 마지막
```

## 완료 체크리스트

- [x] #9 결제 페이지에 하드코딩된 키가 없음
- [x] #10 모든 API 호출에 spinner가 표시됨
- [ ] #11 공고 목록이 페이지 단위로 로드됨
- [x] #12 bare except가 0개
- [x] #13 네트워크 실패 시 자동 재시도
- [x] #14 모바일 화면에서 레이아웃이 깨지지 않음
