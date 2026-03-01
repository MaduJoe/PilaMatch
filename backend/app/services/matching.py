"""Matching score calculation service."""
from typing import Optional
from app.models import InstructorProfile, JobPost


def calculate_matching_score(
    instructor: InstructorProfile,
    job: JobPost,
) -> dict:
    """
    Calculate matching score between instructor and job post.

    Score is purely skill-based — premium status does not influence the score.

    Returns:
        dict with total score (0-100) and breakdown by category
    """
    scores = {
        "region": 0,
        "experience": 0,
        "certifications": 0,
        "rate": 0,
    }
    weights = {
        "region": 30,
        "experience": 25,
        "certifications": 25,
        "rate": 20,
    }

    # 1. Region matching (30%)
    instructor_regions = instructor.available_regions or []
    job_region = job.region or ""
    if job_region and instructor_regions:
        if job_region in instructor_regions:
            scores["region"] = 100
        else:
            # Partial match - check if any region contains the other
            for region in instructor_regions:
                if job_region in region or region in job_region:
                    scores["region"] = 70
                    break
    elif not job_region:
        # No region requirement
        scores["region"] = 100

    # 2. Experience matching (25%)
    required_exp = job.required_experience_years or 0
    instructor_exp = instructor.experience_years or 0
    if instructor_exp >= required_exp:
        scores["experience"] = 100
    elif required_exp > 0:
        scores["experience"] = min(100, int((instructor_exp / required_exp) * 100))
    else:
        scores["experience"] = 100

    # 3. Certification matching (25%)
    required_certs = job.required_certifications or []
    instructor_certs = instructor.certifications or []

    # Extract certification names from instructor certs
    instructor_cert_names = []
    for cert in instructor_certs:
        if isinstance(cert, dict):
            instructor_cert_names.append(cert.get("name", "").lower())
        else:
            instructor_cert_names.append(str(cert).lower())

    if not required_certs:
        scores["certifications"] = 100
    else:
        matched = 0
        for req_cert in required_certs:
            req_cert_lower = str(req_cert).lower()
            for inst_cert in instructor_cert_names:
                if req_cert_lower in inst_cert or inst_cert in req_cert_lower:
                    matched += 1
                    break
        scores["certifications"] = int((matched / len(required_certs)) * 100)

    # 4. Rate compatibility (20%)
    job_rate = float(job.hourly_rate) if job.hourly_rate else 0
    min_rate = float(instructor.hourly_rate_min) if instructor.hourly_rate_min else 0
    max_rate = float(instructor.hourly_rate_max) if instructor.hourly_rate_max else float('inf')

    if min_rate <= job_rate <= max_rate:
        scores["rate"] = 100
    elif job_rate > max_rate:
        # Job pays more than instructor's max - still good
        scores["rate"] = 100
    elif job_rate < min_rate and min_rate > 0:
        # Job pays less than instructor's min
        scores["rate"] = max(0, int((job_rate / min_rate) * 100))
    else:
        scores["rate"] = 80  # Default if no rate info

    # Calculate weighted total
    total = 0
    for key, score in scores.items():
        total += score * (weights[key] / 100)

    return {
        "total": round(total),
        "breakdown": {
            "region": {"score": scores["region"], "weight": weights["region"]},
            "experience": {"score": scores["experience"], "weight": weights["experience"]},
            "certifications": {"score": scores["certifications"], "weight": weights["certifications"]},
            "rate": {"score": scores["rate"], "weight": weights["rate"]},
        }
    }


def get_match_label(score: int) -> str:
    """Get a human-readable label for the matching score."""
    if score >= 90:
        return "Perfect Match"
    elif score >= 75:
        return "Great Match"
    elif score >= 60:
        return "Good Match"
    elif score >= 40:
        return "Fair Match"
    else:
        return "Low Match"
