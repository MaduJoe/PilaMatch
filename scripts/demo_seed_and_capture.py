"""
PilaMatch Demo 시딩 + Playwright 자동 스크린 캡처
─────────────────────────────────────────────────
1) API로 데모 계정 생성 (센터 1 + 강사 3)
2) 긴급 공고 등록 → 디스패치 트리거
3) 강사 수락 → 체크인 → 완료
4) Playwright로 각 Scene UI 스크린샷 캡처

사전 조건: docker compose up -d (backend:8000, frontend:3000, db:5432)
실행: .venv/bin/python3 scripts/demo_seed_and_capture.py
"""

import asyncio
import httpx
import os
import sys
from datetime import date, time, datetime
from playwright.async_api import async_playwright

# ─── Config ───
API = "http://localhost:8000/api/v1"
FRONTEND = "http://localhost:3000"
OUTPUT_DIR = os.path.join(os.path.dirname(__file__), "..", "data", "demo-screenshots")

# 센터: 트루바디필라테스 (양천구 목동)
STUDIO = {
    "email": "demo-studio@pilamatch.kr",
    "password": "Demo1234!",
    "role": "studio",
    "business_name": "트루바디필라테스",
}
STUDIO_PROFILE = {
    "business_name": "트루바디필라테스",
    "phone": "010-4150-2842",
    "address": "서울 양천구 신월로 165 3층",
    "region": "서울 양천구",
    "latitude": 37.5170,
    "longitude": 126.8560,
    "categories": ["pilates"],
}

# 강사 3명 (거리별)
INSTRUCTORS = [
    {
        "email": "demo-inst1@pilamatch.kr",
        "password": "Demo1234!",
        "role": "instructor",
        "display_name": "김민지",
        "profile": {
            "display_name": "김민지",
            "phone": "010-1234-5678",
            "categories": ["pilates"],
            "experience_years": 3,
            "hourly_rate_min": 25000,
            "hourly_rate_max": 35000,
            "available_regions": ["서울 양천구", "서울 강서구"],
            "certifications": [{"name": "STOTT Pilates", "issuer": "Merrithew", "year": 2023}],
        },
        # ~2km 떨어진 위치 (목동역 근처)
        "lat": 37.5245,
        "lng": 126.8678,
    },
    {
        "email": "demo-inst2@pilamatch.kr",
        "password": "Demo1234!",
        "role": "instructor",
        "display_name": "이수현",
        "profile": {
            "display_name": "이수현",
            "phone": "010-2345-6789",
            "categories": ["pilates", "yoga"],
            "experience_years": 5,
            "hourly_rate_min": 30000,
            "hourly_rate_max": 40000,
            "available_regions": ["서울 영등포구", "서울 양천구"],
            "certifications": [{"name": "Balanced Body", "issuer": "BB Education", "year": 2021}],
        },
        # ~5km 떨어진 위치 (영등포)
        "lat": 37.5165,
        "lng": 126.9074,
    },
    {
        "email": "demo-inst3@pilamatch.kr",
        "password": "Demo1234!",
        "role": "instructor",
        "display_name": "박서연",
        "profile": {
            "display_name": "박서연",
            "phone": "010-3456-7890",
            "categories": ["pilates"],
            "experience_years": 2,
            "hourly_rate_min": 25000,
            "hourly_rate_max": 30000,
            "available_regions": ["서울 강남구", "서울 서초구"],
            "certifications": [{"name": "PMA CPT", "issuer": "PMA", "year": 2024}],
        },
        # ~12km 떨어진 위치 (강남)
        "lat": 37.4979,
        "lng": 127.0276,
    },
]

# 긴급 공고
URGENT_JOB = {
    "title": "[긴급] 오후 6:30 타워리포머 5:1 그룹 대타",
    "description": "정규 강사 갑작스런 사정으로 오늘 저녁 대타 급구합니다.",
    "category": "pilates",
    "job_type": "substitute",
    "date": str(date.today()),
    "start_time": "18:30:00",
    "end_time": "21:30:00",
    "hourly_rate": 30000,
    "total_sessions": 3,
    "required_experience_years": 1,
    "region": "서울 양천구",
    "address": "서울 양천구 신월로 165 3층",
    "latitude": 37.5170,
    "longitude": 126.8560,
    "is_urgent": True,
    "handoff_class_topic": "타워리포머 5:1 그룹 (중급)",
    "handoff_class_sequence_info": "웜업 10분(풋워크) → 메인 35분(숄더브릿지, 레그서클, 사이드라잉 시리즈) → 쿨다운 5분",
    "handoff_atmosphere_preference": "밝고 에너지 넘치게",
    "handoff_member_notes": "3번 자리 회원님 허리디스크 주의, 5번 자리 회원님 임산부(20주)",
    "handoff_equipment_notes": "인투 기구 사용, 스프링 세팅: 빨강2+파랑1 기본",
}


# ═══════════════════════════════════════════════════════
#  Part 1: API Seeding
# ═══════════════════════════════════════════════════════

async def api_signup(client: httpx.AsyncClient, data: dict) -> dict | None:
    """회원가입 → 토큰 반환. 이미 존재하면 로그인 시도."""
    r = await client.post(f"{API}/auth/signup", json=data)
    if r.status_code in (200, 201):
        return r.json()
    # 이미 존재 → 로그인
    r = await client.post(f"{API}/auth/login", json={
        "email": data["email"], "password": data["password"]
    })
    if r.status_code == 200:
        return r.json()
    print(f"   ⚠ signup/login 실패: {data['email']} → {r.status_code} {r.text[:200]}")
    return None


def auth_header(token: str) -> dict:
    return {"Authorization": f"Bearer {token}"}


async def seed_data():
    """데모 데이터 시딩"""
    print("═══ Part 1: 데모 데이터 시딩 ═══")

    async with httpx.AsyncClient(timeout=30) as c:
        # ── 센터 계정 ──
        print("[1/5] 센터 계정 생성...")
        studio_tokens = await api_signup(c, STUDIO)
        if not studio_tokens:
            sys.exit("센터 계정 생성 실패")
        st = studio_tokens["access_token"]

        print("[2/5] 센터 프로필 업데이트...")
        r = await c.put(f"{API}/studios/me", json=STUDIO_PROFILE, headers=auth_header(st))
        print(f"   스튜디오 프로필: {r.status_code}")

        # ── 강사 계정 ──
        instructor_tokens = []
        print("[3/5] 강사 계정 생성...")
        for inst in INSTRUCTORS:
            tokens = await api_signup(c, {
                "email": inst["email"],
                "password": inst["password"],
                "role": inst["role"],
                "display_name": inst["display_name"],
            })
            if not tokens:
                continue
            it = tokens["access_token"]
            instructor_tokens.append({"token": it, **inst})

            # 프로필 업데이트
            await c.put(f"{API}/instructors/me", json=inst["profile"], headers=auth_header(it))

            # 대기열 등록 (Standby Pool)
            await c.put(f"{API}/availability", json={
                "is_available": True,
                "latitude": inst["lat"],
                "longitude": inst["lng"],
                "categories": ["pilates"],
                "max_distance_km": 15.0,
            }, headers=auth_header(it))

        print(f"   강사 {len(instructor_tokens)}명 생성 + 대기열 등록 완료")

        # ── 긴급 공고 등록 ──
        print("[4/5] 긴급 공고 등록...")
        r = await c.post(f"{API}/job-posts", json=URGENT_JOB, headers=auth_header(st))
        if r.status_code not in (200, 201):
            print(f"   ⚠ 공고 등록 실패: {r.status_code} {r.text[:300]}")
            return None
        job = r.json()
        job_id = job.get("id") or job.get("job_post_id")
        print(f"   ✓ 공고 등록 완료: {job_id}")

        # ── 디스패치 대기 + 강사1 수락 ──
        print("[5/5] 디스패치 수락 대기...")
        await asyncio.sleep(3)  # 디스패치 엔진 처리 대기

        # 강사1의 pending 디스패치 확인
        if instructor_tokens:
            it1 = instructor_tokens[0]["token"]
            r = await c.get(f"{API}/dispatch/my-pending", headers=auth_header(it1))
            pending = r.json() if r.status_code == 200 else []
            if pending:
                dr_id = pending[0].get("id") or pending[0].get("dispatch_record_id")
                print(f"   디스패치 레코드: {dr_id}")

                # 수락
                r = await c.post(f"{API}/dispatch/{dr_id}/accept", headers=auth_header(it1))
                print(f"   ✓ 강사1 수락: {r.status_code}")
            else:
                print("   ⚠ pending 디스패치 없음 (스케줄러 미실행 가능)")

    return {
        "studio_email": STUDIO["email"],
        "studio_password": STUDIO["password"],
        "instructor_email": INSTRUCTORS[0]["email"],
        "instructor_password": INSTRUCTORS[0]["password"],
        "job_id": job_id,
    }


# ═══════════════════════════════════════════════════════
#  Part 2: Playwright Screenshot Capture
# ═══════════════════════════════════════════════════════

async def login_ui(page, email: str, password: str):
    """프론트엔드 로그인"""
    await page.goto(f"{FRONTEND}/login", wait_until="networkidle")
    await page.fill('input[type="email"], input[name="email"]', email)
    await page.fill('input[type="password"], input[name="password"]', password)
    await page.click('button[type="submit"]')
    # 로그인 후 어딘가로 리다이렉트 대기 (dashboard, profile, steps 등)
    await page.wait_for_url(lambda url: "/login" not in url, timeout=10000)
    await page.wait_for_load_state("networkidle")
    # dashboard로 이동
    await page.goto(f"{FRONTEND}/dashboard", wait_until="networkidle")


async def capture_screenshots(demo_data: dict):
    """Playwright로 데모 스크린샷 캡처"""
    print("\n═══ Part 2: 스크린샷 캡처 ═══")
    os.makedirs(OUTPUT_DIR, exist_ok=True)

    async with async_playwright() as pw:
        browser = await pw.chromium.launch(
            headless=True,
            args=["--disable-gpu", "--disable-software-rasterizer", "--disable-dev-shm-usage"],
        )

        # ── Scene 1: 센터 - 긴급 공고 등록 ──
        print("[Scene 1] 센터 화면 캡처...")
        studio_ctx = await browser.new_context(
            viewport={"width": 375, "height": 812},
            device_scale_factor=2,
        )
        studio_page = await studio_ctx.new_page()

        try:
            await login_ui(studio_page, demo_data["studio_email"], demo_data["studio_password"])

            # 대시보드
            await studio_page.wait_for_timeout(1000)
            await studio_page.screenshot(path=f"{OUTPUT_DIR}/01-studio-dashboard.png", full_page=False)
            print("   ✓ 01-studio-dashboard.png")

            # 공고 등록 페이지
            await studio_page.goto(f"{FRONTEND}/steps/jobs", wait_until="networkidle")
            await studio_page.wait_for_timeout(1000)
            await studio_page.screenshot(path=f"{OUTPUT_DIR}/02-studio-job-post.png", full_page=False)
            print("   ✓ 02-studio-job-post.png")

            # 디스패치 상태 위젯 (지원자 탭)
            await studio_page.goto(f"{FRONTEND}/steps/offers", wait_until="networkidle")
            await studio_page.wait_for_timeout(1000)
            await studio_page.screenshot(path=f"{OUTPUT_DIR}/03-studio-dispatch-status.png", full_page=False)
            print("   ✓ 03-studio-dispatch-status.png")

        except Exception as e:
            print(f"   ⚠ 센터 캡처 실패: {e}")
        finally:
            await studio_ctx.close()

        # ── Scene 2+3: 강사 화면 ──
        print("[Scene 2-3] 강사 화면 캡처...")
        inst_ctx = await browser.new_context(
            viewport={"width": 375, "height": 812},
            device_scale_factor=2,
        )
        inst_page = await inst_ctx.new_page()

        try:
            await login_ui(inst_page, demo_data["instructor_email"], demo_data["instructor_password"])

            # 대시보드 (디스패치 알림)
            await inst_page.wait_for_timeout(1000)
            await inst_page.screenshot(path=f"{OUTPUT_DIR}/04-instructor-dashboard.png", full_page=False)
            print("   ✓ 04-instructor-dashboard.png")

            # 지원현황 (매칭 후 인수인계 노트)
            await inst_page.goto(f"{FRONTEND}/steps/offers", wait_until="networkidle")
            await inst_page.wait_for_timeout(1000)
            await inst_page.screenshot(path=f"{OUTPUT_DIR}/05-instructor-handoff-note.png", full_page=False)
            print("   ✓ 05-instructor-handoff-note.png")

            # 완료 탭 (체크인 + 완료)
            await inst_page.goto(f"{FRONTEND}/steps/complete", wait_until="networkidle")
            await inst_page.wait_for_timeout(1000)
            await inst_page.screenshot(path=f"{OUTPUT_DIR}/06-instructor-checkin-complete.png", full_page=False)
            print("   ✓ 06-instructor-checkin-complete.png")

        except Exception as e:
            print(f"   ⚠ 강사 캡처 실패: {e}")
        finally:
            await inst_ctx.close()

        await browser.close()

    print(f"\n✓ 스크린샷 저장: {OUTPUT_DIR}/")


# ═══════════════════════════════════════════════════════
#  Main
# ═══════════════════════════════════════════════════════

async def check_services():
    """백엔드 + 프론트엔드 헬스체크"""
    async with httpx.AsyncClient(timeout=5) as c:
        try:
            r = await c.get("http://localhost:8000/health")
            if r.status_code != 200:
                return False, "Backend unhealthy"
        except Exception:
            return False, "Backend not running (localhost:8000)"
        try:
            r = await c.get("http://localhost:3000")
            if r.status_code not in (200, 304):
                return False, "Frontend unhealthy"
        except Exception:
            return False, "Frontend not running (localhost:3000)"
    return True, "OK"


async def main():
    ok, msg = await check_services()
    if not ok:
        print(f"✗ 서비스 확인 실패: {msg}")
        print("  → docker compose up -d --build 실행 후 다시 시도")
        sys.exit(1)
    print("✓ 서비스 확인 OK\n")

    demo_data = await seed_data()
    if demo_data:
        await capture_screenshots(demo_data)
    else:
        print("시딩 실패 - 스크린샷 스킵")


if __name__ == "__main__":
    asyncio.run(main())
