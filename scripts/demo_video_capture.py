"""
PilaMatch 1분 데모 영상용 Playwright 자동 재현 + 스크린샷
feedback.md 기반 9개 핵심 장면 + 강사/센터 구분 라벨 + 버튼 하이라이트

출력: data/demo-video/
  - 원본 PNG (01~09)
  - 라벨+자막 합성 PNG (*_labeled.png)
  - GIF 시퀀스
"""

import asyncio
import httpx
import os
from datetime import date
from PIL import Image, ImageDraw, ImageFont
from playwright.async_api import async_playwright

API = "http://localhost:8000/api/v1"
FRONTEND = "http://localhost:3000"
OUT = os.path.join(os.path.dirname(__file__), "..", "data", "demo-video")
FONT_PATH = "/usr/share/fonts/truetype/wqy/wqy-zenhei.ttc"

HIDE_TABBAR_JS = """
document.querySelectorAll("nav").forEach(n => {
    const style = getComputedStyle(n);
    if (style.position === "fixed" && parseInt(style.bottom) === 0) {
        n.style.setProperty("display", "none", "important");
    }
});
"""

URGENT_JOB = {
    "title": "[긴급] 오후 6:30 타워리포머 5:1 그룹 대타",
    "description": "정규 강사 갑작스런 사정으로 오늘 저녁 대타 급구합니다.",
    "category": "pilates", "job_type": "substitute",
    "date": str(date.today()),
    "start_time": "18:30:00", "end_time": "21:30:00",
    "hourly_rate": 30000, "total_sessions": 3,
    "required_experience_years": 1,
    "region": "서울 양천구", "address": "서울 양천구 신월로 165 3층",
    "latitude": 37.5170, "longitude": 126.8560,
    "is_urgent": True,
    "handoff_class_topic": "타워리포머 5:1 그룹 (중급)",
    "handoff_class_sequence_info": "웜업 10분(풋워크) → 메인 35분 → 쿨다운 5분",
    "handoff_atmosphere_preference": "밝고 에너지 넘치게",
    "handoff_member_notes": "3번 허리디스크 주의, 5번 임산부(20주)",
    "handoff_equipment_notes": "인투 기구, 스프링: 빨강2+파랑1",
}

# (role_label, role_color, subtitle, button_hint)
SCENES = [
    ("", (20, 20, 20), "갑자기 강사 결근.\n아직도 커뮤니티에 글 올리고\n기다리시나요?", ""),
    ("센터", (199, 21, 133), "센터장이 앱을 엽니다", ""),
    ("센터", (199, 21, 133), "긴급 공고 등록 10초", "[공고 등록하기] 탭"),
    ("강사", (16, 185, 129), "강사는 대기 중...", ""),
    ("강사", (16, 185, 129), "자동 디스패치! 즉시 알림 도착", "[확인하기 >] 탭"),
    ("강사", (16, 185, 129), "강사가 수락합니다", "[수락] 버튼 탭"),
    ("센터", (199, 21, 133), "센터에 매칭 완료 알림!", ""),
    ("강사", (16, 185, 129), "수업 내용·회원 주의사항 자동 전달", ""),
    ("강사", (16, 185, 129), "GPS 도착 인증 28.4m", "[체크인] 완료"),
    ("강사", (16, 185, 129), "양측 완료 확인 → 정산 분쟁 방지", "[수업 완료] 확인"),
]


def add_label_and_subtitle(img_path: str, scene_idx: int, out_path: str):
    """이미지에 상단 역할 라벨 + 하단 자막 + 버튼 힌트 추가"""
    role, color, subtitle, hint = SCENES[scene_idx]
    img = Image.open(img_path)
    w, h = img.size

    # 상단 라벨 높이, 하단 자막 높이
    top_h = 56 if role else 0
    lines = subtitle.split("\n")
    bot_h = 60 + len(lines) * 34
    if hint:
        bot_h += 30

    new_h = top_h + h + bot_h
    canvas = Image.new("RGB", (w, new_h), (0, 0, 0))

    # 상단 라벨 배경
    if role:
        draw_top = ImageDraw.Draw(canvas)
        draw_top.rectangle([(0, 0), (w, top_h)], fill=color)
        font_label = ImageFont.truetype(FONT_PATH, 28)
        icon = "🏢 " if role == "센터" else "👩‍🏫 "
        label_text = f"{icon}{role} 화면"
        bbox = draw_top.textbbox((0, 0), label_text, font=font_label)
        tw = bbox[2] - bbox[0]
        draw_top.text(((w - tw) // 2, (top_h - 34) // 2), label_text, fill=(255, 255, 255), font=font_label)

    # 원본 이미지 삽입
    canvas.paste(img, (0, top_h))

    # 하단 자막
    draw = ImageDraw.Draw(canvas)
    font_sub = ImageFont.truetype(FONT_PATH, 26)
    y = top_h + h + 14
    for line in lines:
        bbox = draw.textbbox((0, 0), line, font=font_sub)
        tw = bbox[2] - bbox[0]
        draw.text(((w - tw) // 2, y), line, fill=(255, 255, 255), font=font_sub)
        y += 34

    # 버튼 힌트 (작은 글씨, 밝은 회색)
    if hint:
        font_hint = ImageFont.truetype(FONT_PATH, 20)
        bbox = draw.textbbox((0, 0), hint, font=font_hint)
        tw = bbox[2] - bbox[0]
        draw.text(((w - tw) // 2, y + 6), hint, fill=(180, 180, 180), font=font_hint)

    canvas.save(out_path)


def make_problem_slide(out_path: str):
    """Scene 0: 검은 배경 + 문제 제시 텍스트"""
    w, h = 750, 1624
    img = Image.new("RGB", (w, h), (20, 20, 20))
    draw = ImageDraw.Draw(img)
    font = ImageFont.truetype(FONT_PATH, 34)
    lines = SCENES[0][2].split("\n")
    total_h = len(lines) * 50
    y = (h - total_h) // 2
    for line in lines:
        bbox = draw.textbbox((0, 0), line, font=font)
        tw = bbox[2] - bbox[0]
        draw.text(((w - tw) // 2, y), line, fill=(255, 255, 255), font=font)
        y += 50
    img.save(out_path)


async def login(page, email):
    await page.goto(f"{FRONTEND}/login", wait_until="networkidle")
    await page.fill('input[type="email"]', email)
    await page.fill('input[type="password"]', "Demo1234!")
    await page.click('button[type="submit"]')
    await page.wait_for_url(lambda u: "/login" not in u, timeout=10000)
    await page.wait_for_load_state("networkidle")


async def shot(page, name, wait=1000):
    await page.wait_for_timeout(wait)
    path = os.path.join(OUT, f"{name}.png")
    await page.screenshot(path=path, full_page=False)
    return path


async def seed_fresh_dispatch():
    """새 긴급 공고 등록 + 강사 대기열 활성화"""
    async with httpx.AsyncClient(timeout=30) as c:
        # 강사들 대기열 재활성화
        coords = [(37.5245, 126.8678), (37.5165, 126.9074), (37.4979, 127.0276)]
        for i, email in enumerate(["demo-inst1@pilamatch.kr", "demo-inst2@pilamatch.kr", "demo-inst3@pilamatch.kr"]):
            r = await c.post(f"{API}/auth/login", json={"email": email, "password": "Demo1234!"})
            t = r.json()["access_token"]
            await c.put(f"{API}/availability", json={
                "is_available": True, "latitude": coords[i][0], "longitude": coords[i][1],
                "categories": ["pilates"], "max_distance_km": 15.0,
            }, headers={"Authorization": f"Bearer {t}"})

        # 센터: 긴급 공고 등록
        r = await c.post(f"{API}/auth/login", json={"email": "demo-studio@pilamatch.kr", "password": "Demo1234!"})
        st = r.json()["access_token"]
        r = await c.post(f"{API}/job-posts", json=URGENT_JOB, headers={"Authorization": f"Bearer {st}"})
        job = r.json()
        job_id = job.get("id")
        print(f"  새 긴급 공고: {job_id}")

        # 디스패치 엔진 처리 대기
        await asyncio.sleep(4)

        # 강사1: pending 디스패치 확인
        r = await c.post(f"{API}/auth/login", json={"email": "demo-inst1@pilamatch.kr", "password": "Demo1234!"})
        it = r.json()["access_token"]
        r = await c.get(f"{API}/dispatch/my-pending", headers={"Authorization": f"Bearer {it}"})
        pending = r.json() if r.status_code == 200 else []
        dr_id = pending[0]["id"] if pending else None
        print(f"  디스패치 레코드: {dr_id}")

        return job_id, dr_id, st, it


async def main():
    os.makedirs(OUT, exist_ok=True)
    labeled_paths = []

    print("═══ 시딩 ═══")
    job_id, dr_id, studio_token, inst_token = await seed_fresh_dispatch()

    print("\n═══ 캡처 ═══")
    async with async_playwright() as pw:
        browser = await pw.chromium.launch(
            headless=True,
            args=["--disable-gpu", "--disable-software-rasterizer", "--disable-dev-shm-usage"],
        )

        # 0. 문제 제시
        p0 = os.path.join(OUT, "00_problem.png")
        make_problem_slide(p0)
        labeled_paths.append(p0)
        print("  ✓ 00 문제 제시")

        # ═══ 센터 브라우저 ═══
        s_ctx = await browser.new_context(viewport={"width": 375, "height": 812}, device_scale_factor=2)
        s_page = await s_ctx.new_page()
        await login(s_page, "demo-studio@pilamatch.kr")

        # 1. 센터 대시보드
        await s_page.goto(f"{FRONTEND}/dashboard", wait_until="networkidle")
        p = await shot(s_page, "01_studio_dashboard")
        lp = p.replace(".png", "_labeled.png")
        add_label_and_subtitle(p, 1, lp)
        labeled_paths.append(lp)
        print("  ✓ 01 센터 대시보드")

        # 2. 센터 공고 등록
        await s_page.goto(f"{FRONTEND}/steps/jobs", wait_until="networkidle")
        p = await shot(s_page, "02_studio_urgent_post")
        lp = p.replace(".png", "_labeled.png")
        add_label_and_subtitle(p, 2, lp)
        labeled_paths.append(lp)
        print("  ✓ 02 센터 긴급 공고")

        # ═══ 강사 브라우저 ═══
        i_ctx = await browser.new_context(
            viewport={"width": 375, "height": 812}, device_scale_factor=2,
            geolocation={"latitude": 37.5245, "longitude": 126.8678},
            permissions=["geolocation"],
        )
        i_page = await i_ctx.new_page()
        await login(i_page, "demo-inst1@pilamatch.kr")

        # 3. 강사 대기 (공고 등록 전 상태 — 기존 before 이미지 활용)
        before = os.path.join(os.path.dirname(OUT), "demo-screenshots", "04a-instructor-before.png")
        if os.path.exists(before):
            lp = os.path.join(OUT, "03_instructor_before_labeled.png")
            add_label_and_subtitle(before, 3, lp)
        else:
            await i_page.goto(f"{FRONTEND}/dashboard", wait_until="networkidle")
            p = await shot(i_page, "03_instructor_before")
            lp = p.replace(".png", "_labeled.png")
            add_label_and_subtitle(p, 3, lp)
        labeled_paths.append(lp)
        print("  ✓ 03 강사 대기 (before)")

        # 4. 강사 알림 도착 (after)
        await i_page.goto(f"{FRONTEND}/dashboard", wait_until="networkidle")
        p = await shot(i_page, "04_instructor_dispatch", wait=1500)
        lp = p.replace(".png", "_labeled.png")
        add_label_and_subtitle(p, 4, lp)
        labeled_paths.append(lp)
        print("  ✓ 04 강사 디스패치 알림")

        # 5. 강사 수락 다이얼로그
        # "확인하기" 버튼 클릭 시도
        btn = await i_page.query_selector('text=확인하기')
        if btn:
            await btn.click()
            await i_page.wait_for_timeout(1500)
        p = await shot(i_page, "05_instructor_accept")
        lp = p.replace(".png", "_labeled.png")
        add_label_and_subtitle(p, 5, lp)
        labeled_paths.append(lp)
        print("  ✓ 05 강사 수락")

        # API로 실제 수락 처리
        if dr_id:
            async with httpx.AsyncClient(timeout=10) as c:
                await c.post(f"{API}/dispatch/{dr_id}/accept",
                             headers={"Authorization": f"Bearer {inst_token}"})
        print("     (API 수락 완료)")

        # 6. 센터 매칭 완료 (지원자 탭)
        await s_page.goto(f"{FRONTEND}/steps/offers", wait_until="networkidle")
        p = await shot(s_page, "06_studio_matched", wait=1500)
        lp = p.replace(".png", "_labeled.png")
        add_label_and_subtitle(p, 6, lp)
        labeled_paths.append(lp)
        print("  ✓ 06 센터 매칭 완료")

        # 기존 완료된 job 데이터로 나머지 캡처
        # 7. 인수인계 노트
        await i_page.goto(f"{FRONTEND}/steps/offers", wait_until="networkidle")
        await i_page.wait_for_timeout(1500)
        await i_page.evaluate("window.scrollTo(0, 300)")
        await i_page.wait_for_timeout(500)
        p = await shot(i_page, "07_handoff_note")
        lp = p.replace(".png", "_labeled.png")
        add_label_and_subtitle(p, 7, lp)
        labeled_paths.append(lp)
        print("  ✓ 07 인수인계 노트")

        # 8. GPS 체크인
        await i_page.evaluate("window.scrollTo(0, 650)")
        await i_page.wait_for_timeout(500)
        p = await shot(i_page, "08_gps_checkin")
        lp = p.replace(".png", "_labeled.png")
        add_label_and_subtitle(p, 8, lp)
        labeled_paths.append(lp)
        print("  ✓ 08 GPS 체크인")

        # 9. 완료 확인
        await i_page.evaluate("window.scrollTo(0, 1000)")
        await i_page.wait_for_timeout(500)
        p = await shot(i_page, "09_completion")
        lp = p.replace(".png", "_labeled.png")
        add_label_and_subtitle(p, 9, lp)
        labeled_paths.append(lp)
        print("  ✓ 09 완료 확인")

        await s_ctx.close()
        await i_ctx.close()
        await browser.close()

    # ═══ GIF ═══
    print("\n  GIF 생성...")
    frames = []
    durations = [3000, 2000, 2500, 2000, 3000, 2500, 2500, 3000, 3000, 3000]
    for path in labeled_paths:
        if os.path.exists(path):
            img = Image.open(path).convert("RGB")
            target_w = 375
            img = img.resize((target_w, img.height * target_w // img.width), Image.LANCZOS)
            frames.append(img)

    if frames:
        gif = os.path.join(OUT, "demo_sequence.gif")
        frames[0].save(gif, save_all=True, append_images=frames[1:],
                       duration=durations[:len(frames)], loop=0)
        print(f"  ✓ GIF ({len(frames)} frames)")

    print(f"\n✓ 완료: {OUT}/")


if __name__ == "__main__":
    asyncio.run(main())
