#!/usr/bin/env python3
"""Test account management — uses app's own registration API internally.

Usage (run inside backend container):
    python scripts/manage_test_accounts.py list
    python scripts/manage_test_accounts.py setup
    python scripts/manage_test_accounts.py set-tier <email> <T1|T2|T3|C1|C2>
    python scripts/manage_test_accounts.py reset
    python scripts/manage_test_accounts.py delete <email>
"""
import asyncio
import sys
import os
from uuid import uuid4
from datetime import datetime, timedelta

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))
os.environ.setdefault("SECRET_KEY", "test-script-key")

from sqlalchemy import text
from app.db.session import engine, AsyncSessionLocal

# ── Definitions ─────────────────────────────────────────────────────────────

TEST_ACCOUNTS = [
    {"email": "t1_basic@test.com",    "pw": "Test1234!", "role": "instructor", "tier": "T1", "name": "T1기본강사", "phone": "01012345671"},
    {"email": "t2_verified@test.com", "pw": "Test1234!", "role": "instructor", "tier": "T2", "name": "T2인증강사", "phone": "01012345672"},
    {"email": "t3_premium@test.com",  "pw": "Test1234!", "role": "instructor", "tier": "T3", "name": "T3프로강사", "phone": "01012345673"},
    {"email": "c1_basic@test.com",    "pw": "Test1234!", "role": "studio",     "tier": "C1", "name": "C1기본센터", "phone": "01012345674"},
    {"email": "c2_verified@test.com", "pw": "Test1234!", "role": "studio",     "tier": "C2", "name": "C2인증센터", "phone": "01012345675"},
    {"email": "c3_premium@test.com",  "pw": "Test1234!", "role": "studio",     "tier": "C3", "name": "C3프로센터", "phone": "01012345676"},
]

# Tier → what flags/data to set AFTER account creation
TIER_CONFIG = {
    "T1": {"phone_verified": True,  "identity_verified": False, "certs": "[]",                                      "completed": 0},
    "T2": {"phone_verified": True,  "identity_verified": True,  "certs": '[{"name":"PMA-CPT","is_verified":true}]', "completed": 2},
    "T3": {"phone_verified": True,  "identity_verified": True,  "certs": '[{"name":"PMA-CPT","is_verified":true}]', "completed": 5, "membership_tier": "premium"},
    "C1": {"phone_verified": True,  "identity_verified": False, "business_verified": False},
    "C2": {"phone_verified": True,  "identity_verified": True,  "business_verified": True},
    "C3": {"phone_verified": True,  "identity_verified": True,  "business_verified": True, "membership_tier": "premium"},
}


# ── Commands ────────────────────────────────────────────────────────────────

async def cmd_list():
    async with AsyncSessionLocal() as db:
        result = await db.execute(text("""
            SELECT u.email, u.role, u.phone_verified, u.identity_verified,
                   u.business_verified, u.is_active, u.is_suspended, u.tier,
                   COALESCE(ip.display_name, sp.business_name) as name
            FROM users u
            LEFT JOIN instructor_profiles ip ON ip.user_id = u.id
            LEFT JOIN studio_profiles sp ON sp.user_id = u.id
            WHERE u.email LIKE '%@test.com'
            ORDER BY u.role, u.email
        """))
        rows = result.mappings().all()
        if not rows:
            print("No test accounts found.")
            return

        print(f"\n{'Email':<30} {'Role':<12} {'Name':<15} {'Phone':<6} {'ID':<6} {'Biz':<6} {'Tier':<10}")
        print("─" * 95)
        for r in rows:
            print(
                f"{r['email']:<30} {r['role']:<12} {(r['name'] or '-'):<15} "
                f"{'✓' if r['phone_verified'] else '✗':<6} "
                f"{'✓' if r['identity_verified'] else '✗':<6} "
                f"{'✓' if r['business_verified'] else '✗':<6} "
                f"{(r['tier'] or '-'):<10}"
            )
        print()


async def cmd_setup():
    """Create test accounts using the app's own signup endpoint via httpx."""
    import httpx

    base = "http://localhost:8000/api/v1"

    async with httpx.AsyncClient(base_url=base, timeout=10) as client:
        for acct in TEST_ACCOUNTS:
            # 1. Check if exists
            login_resp = await client.post("/auth/login", json={
                "email": acct["email"], "password": acct["pw"]
            })
            if login_resp.status_code == 200:
                print(f"  Exists: {acct['email']} — skipping")
                continue

            # 2. Register
            signup_data = {
                "email": acct["email"],
                "password": acct["pw"],
                "role": acct["role"],
            }
            if acct["role"] == "instructor":
                signup_data["display_name"] = acct["name"]
            else:
                signup_data["business_name"] = acct["name"]

            signup_resp = await client.post("/auth/signup", json=signup_data)
            if signup_resp.status_code not in (200, 201):
                print(f"  FAIL signup {acct['email']}: {signup_resp.text}")
                continue

            token = signup_resp.json().get("access_token")
            headers = {"Authorization": f"Bearer {token}"}

            # 3. Create profile
            if acct["role"] == "instructor":
                await client.put("/instructors/me", json={
                    "display_name": acct["name"],
                    "bio": f"{acct['name']}의 프로필입니다. 필라테스 전문 강사입니다.",
                    "experience_years": 3,
                    "categories": ["pilates"],
                    "available_regions": ["강남구", "서초구"],
                }, headers=headers)
            else:
                await client.put("/studios/me", json={
                    "business_name": acct["name"],
                    "description": f"{acct['name']}의 센터입니다. 필라테스 전문 스튜디오입니다.",
                    "phone": "02-1234-5678",
                    "address": "서울시 강남구 테스트",
                    "region": "강남구",
                    "categories": ["pilates"],
                }, headers=headers)

            # 4. Set tier flags via DB
            await _apply_tier(acct["email"], acct["tier"])
            print(f"  Created: {acct['email']} ({acct['tier']}) — pw: {acct['pw']}")

    print("\nDone! All passwords: Test1234!")
    print("\n  T1 Basic:    t1_basic@test.com     (phone only, no cert)")
    print("  T2 Verified: t2_verified@test.com  (identity + cert + 2 completed)")
    print("  T3 Premium:  t3_premium@test.com   (identity + cert + 5 completed)")
    print("  C1 Basic:    c1_basic@test.com     (phone only, no biz verified)")
    print("  C2 Verified: c2_verified@test.com  (phone + identity + biz verified)")
    print("  C3 Premium:  c3_premium@test.com   (phone + identity + biz verified + premium)")


async def _apply_tier(email: str, tier: str):
    """Set verification flags and create fake completed contracts for a tier."""
    cfg = TIER_CONFIG[tier]

    # Find phone from TEST_ACCOUNTS
    phone_num = ""
    for acct in TEST_ACCOUNTS:
        if acct["email"] == email:
            phone_num = acct.get("phone", "")
            break

    async with AsyncSessionLocal() as db:
        # Get user id
        result = await db.execute(
            text("SELECT id, role FROM users WHERE email = :e"), {"e": email}
        )
        row = result.mappings().first()
        if not row:
            return
        uid = str(row["id"])
        role = row["role"]

        # Update verification flags + phone + membership_tier
        await db.execute(
            text("""
                UPDATE users SET
                    phone_verified = :phone_v,
                    identity_verified = :identity,
                    business_verified = :biz,
                    is_verified = :identity,
                    phone = COALESCE(NULLIF(:phone_num, ''), phone),
                    membership_tier = :mem_tier
                WHERE id = :uid
            """), {
                "uid": uid,
                "phone_v": cfg.get("phone_verified", False),
                "identity": cfg.get("identity_verified", False),
                "biz": cfg.get("business_verified", False),
                "phone_num": phone_num,
                "mem_tier": cfg.get("membership_tier", "free"),
            }
        )

        # Instructor-specific
        if role == "instructor":
            certs = cfg.get("certs", "[]")
            await db.execute(
                text("""UPDATE instructor_profiles SET
                    certifications = CAST(:c AS jsonb),
                    phone = COALESCE(NULLIF(:phone_num, ''), phone)
                WHERE user_id = :uid"""),
                {"uid": uid, "c": certs, "phone_num": phone_num},
            )

            # Create accepted applications (tier uses Application count, not contracts)
            n = cfg.get("completed", 0)
            if n > 0:
                # Get instructor profile ID (applications reference profile, not user)
                prof_r = await db.execute(
                    text("SELECT id FROM instructor_profiles WHERE user_id = :uid"),
                    {"uid": uid},
                )
                profile_id = prof_r.scalar()

                # Check existing accepted apps
                r = await db.execute(text("""
                    SELECT COUNT(*) FROM applications
                    WHERE instructor_id = :pid AND status = 'accepted'
                    AND created_at >= NOW() - INTERVAL '30 days'
                """), {"pid": str(profile_id)})
                existing = r.scalar() or 0

                if existing < n and profile_id:
                    # Get job posts to apply to
                    jobs_r = await db.execute(text(
                        "SELECT id FROM job_posts LIMIT :lim"
                    ), {"lim": n - existing})
                    job_ids = [str(row[0]) for row in jobs_r.fetchall()]

                    for i, jid in enumerate(job_ids):
                        # Check unique constraint
                        exists_r = await db.execute(text("""
                            SELECT 1 FROM applications
                            WHERE job_post_id = :jid AND instructor_id = :pid
                        """), {"jid": jid, "pid": str(profile_id)})
                        if exists_r.scalar():
                            continue

                        ts = datetime.utcnow() - timedelta(days=i + 1)
                        await db.execute(text("""
                            INSERT INTO applications (id, job_post_id, instructor_id,
                                status, created_at, updated_at, contact_revealed)
                            VALUES (:id, :job, :inst, 'accepted', :ts, :ts, true)
                        """), {
                            "id": str(uuid4()), "job": jid,
                            "inst": str(profile_id), "ts": ts,
                        })

                # Clear penalties
                await db.execute(text("""
                    DELETE FROM penalty_records WHERE user_id = :uid
                    AND created_at >= NOW() - INTERVAL '30 days'
                """), {"uid": uid})

        await db.commit()


async def cmd_set_tier(email: str, tier: str):
    tier = tier.upper()
    if tier not in TIER_CONFIG:
        print(f"Invalid tier. Choose: {', '.join(TIER_CONFIG.keys())}")
        return
    await _apply_tier(email, tier)
    print(f"✓ {email} → {tier}")


async def cmd_delete(email: str):
    if not email.endswith("@test.com"):
        print("Safety: only @test.com accounts can be deleted")
        return

    async with AsyncSessionLocal() as db:
        r = await db.execute(text("SELECT id FROM users WHERE email = :e"), {"e": email})
        row = r.scalar()
        if not row:
            print(f"Not found: {email}")
            return
        uid = str(row)

        # Delete deps then user
        for tbl in ["contract_event_logs", "contracts", "applications", "reviews",
                     "penalty_records", "payment_confirmations", "daily_usage_limits",
                     "subscriptions", "instructor_profiles", "studio_profiles",
                     "handoff_notes", "backup_instructors", "event_logs"]:
            for col in ["user_id", "instructor_id", "studio_id", "reviewer_id"]:
                try:
                    await db.execute(text(f"DELETE FROM {tbl} WHERE {col} = :uid"), {"uid": uid})
                except Exception:
                    pass

        await db.execute(text("DELETE FROM users WHERE id = :uid"), {"uid": uid})
        await db.commit()
        print(f"✓ Deleted: {email}")


async def cmd_reset():
    for acct in TEST_ACCOUNTS:
        await cmd_delete(acct["email"])
    await cmd_setup()


async def main():
    if len(sys.argv) < 2:
        print(__doc__)
        return

    cmd = sys.argv[1]
    if cmd == "list":
        await cmd_list()
    elif cmd == "setup":
        await cmd_setup()
    elif cmd == "set-tier":
        if len(sys.argv) < 4:
            print("Usage: set-tier <email> <T1|T2|T3|C1|C2>")
            return
        await cmd_set_tier(sys.argv[2], sys.argv[3])
    elif cmd == "delete":
        if len(sys.argv) < 3:
            print("Usage: delete <email>")
            return
        await cmd_delete(sys.argv[2])
    elif cmd == "reset":
        await cmd_reset()
    else:
        print(f"Unknown: {cmd}\n")
        print(__doc__)

    await engine.dispose()

if __name__ == "__main__":
    asyncio.run(main())
