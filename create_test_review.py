#!/usr/bin/env python3
"""Create a test review directly via SQL."""

import psycopg2
from datetime import datetime
import uuid

# Database connection
conn = psycopg2.connect(
    host="localhost",
    port=5432,
    database="StudioBridge",
    user="postgres",
    password="password"
)

cur = conn.cursor()

# First, check if there are any completed contracts
cur.execute("""
    SELECT id, studio_id, instructor_id, status
    FROM contracts
    WHERE status = 'completed'
    LIMIT 2
""")
contracts = cur.fetchall()

if not contracts:
    print("No completed contracts found")
else:
    print(f"Found {len(contracts)} completed contracts:")

    for contract in contracts:
        contract_id, studio_id, instructor_id, status = contract
        print(f"  Contract: {contract_id}")
        print(f"    Studio: {studio_id}")
        print(f"    Instructor: {instructor_id}")
        print(f"    Status: {status}")

        # Check if review already exists from studio
        cur.execute("""
            SELECT id FROM reviews
            WHERE contract_id = %s
            AND reviewer_user_id = (
                SELECT user_id FROM studio_profiles WHERE id = %s
            )
        """, (contract_id, studio_id))

        existing_studio_review = cur.fetchone()

        if existing_studio_review:
            print(f"    ✅ Studio already reviewed this contract")
        else:
            # Get studio user_id
            cur.execute("SELECT user_id FROM studio_profiles WHERE id = %s", (studio_id,))
            studio_user = cur.fetchone()

            if studio_user:
                studio_user_id = studio_user[0]

                # Create a review from studio
                review_id = str(uuid.uuid4())
                cur.execute("""
                    INSERT INTO reviews (
                        id, contract_id, reviewer_user_id,
                        reviewee_instructor_id, reviewee_studio_id,
                        rating, comment, created_at, updated_at
                    ) VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s)
                """, (
                    review_id,
                    contract_id,
                    studio_user_id,
                    instructor_id,  # Studio is reviewing instructor
                    None,
                    5,
                    "훌륭한 강사님입니다! 전문적이고 친절하세요.",
                    datetime.now(),
                    datetime.now()
                ))

                conn.commit()
                print(f"    ✅ Created studio review with ID: {review_id[:8]}...")

        # Check if review already exists from instructor
        cur.execute("""
            SELECT id FROM reviews
            WHERE contract_id = %s
            AND reviewer_user_id = (
                SELECT user_id FROM instructor_profiles WHERE id = %s
            )
        """, (contract_id, instructor_id))

        existing_instructor_review = cur.fetchone()

        if existing_instructor_review:
            print(f"    ✅ Instructor already reviewed this contract")
        else:
            # Get instructor user_id
            cur.execute("SELECT user_id FROM instructor_profiles WHERE id = %s", (instructor_id,))
            instructor_user = cur.fetchone()

            if instructor_user:
                instructor_user_id = instructor_user[0]

                # Create a review from instructor
                review_id = str(uuid.uuid4())
                cur.execute("""
                    INSERT INTO reviews (
                        id, contract_id, reviewer_user_id,
                        reviewee_instructor_id, reviewee_studio_id,
                        rating, comment, created_at, updated_at
                    ) VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s)
                """, (
                    review_id,
                    contract_id,
                    instructor_user_id,
                    None,
                    studio_id,  # Instructor is reviewing studio
                    4,
                    "깨끗하고 좋은 시설입니다. 다시 일하고 싶어요.",
                    datetime.now(),
                    datetime.now()
                ))

                conn.commit()
                print(f"    ✅ Created instructor review with ID: {review_id[:8]}...")

# Check total reviews
cur.execute("SELECT COUNT(*) FROM reviews")
total_reviews = cur.fetchone()[0]
print(f"\n📊 Total reviews in database: {total_reviews}")

# Show all reviews
cur.execute("""
    SELECT r.id, r.contract_id, r.rating, r.comment,
           u.email as reviewer_email, u.role as reviewer_role
    FROM reviews r
    JOIN users u ON r.reviewer_user_id = u.id
    ORDER BY r.created_at DESC
""")

reviews = cur.fetchall()
if reviews:
    print("\n📝 All reviews:")
    for review in reviews:
        review_id, contract_id, rating, comment, email, role = review
        print(f"  Review {review_id[:8]}... by {email} ({role})")
        print(f"    Contract: {contract_id[:8]}...")
        print(f"    Rating: {'⭐' * rating}")
        print(f"    Comment: {comment[:50]}..." if comment and len(comment) > 50 else f"    Comment: {comment}")

cur.close()
conn.close()
print("\n✅ Done!")