"""Matching score calculation service."""
from typing import Optional
from app.models import InstructorProfile, JobPost
from app.utils.distance import haversine_distance


def _calculate_distance_score(distance_km: float) -> int:
    """Convert distance in km to a 0-100 score.

    Scoring tiers:
        0-2km:   100 points
        2-5km:    80 points
        5-10km:   60 points
        10-20km:  40 points
        20-30km:  20 points
        >30km:    10 points

    Args:
        distance_km: Distance in kilometers.

    Returns:
        Score between 0 and 100.
    """
    if distance_km <= 2:
        return 100
    elif distance_km <= 5:
        return 80
    elif distance_km <= 10:
        return 60
    elif distance_km <= 20:
        return 40
    elif distance_km <= 30:
        return 20
    else:
        return 10


def _calculate_style_score(instructor_style: dict, job_style: dict) -> int:
    """Calculate style compatibility score (0-100).

    Compares matching keys between instructor's teaching style and job's preferred style.
    Returns 50 (neutral) if either side has no style data.

    Args:
        instructor_style: Instructor's teaching style dict.
        job_style: Job post's preferred style dict.

    Returns:
        Score between 0 and 100.
    """
    if not instructor_style or not job_style:
        return 50  # Neutral when no data

    comparable_keys = set(job_style.keys()) & set(instructor_style.keys())
    if not comparable_keys:
        return 50

    matches = sum(
        1 for k in comparable_keys
        if instructor_style.get(k) == job_style.get(k)
    )
    return int((matches / len(comparable_keys)) * 100)


def calculate_matching_score(
    instructor: InstructorProfile,
    job: JobPost,
    instructor_lat: Optional[float] = None,
    instructor_lng: Optional[float] = None,
) -> dict:
    """Calculate matching score between instructor and job post.

    Score is purely skill-based -- premium status does not influence the score.

    Weight distribution depends on available data:
        distance + style: distance 25%, style 20%, region 10%, experience 20%,
                          certifications 15%, rate 10%
        distance only:    distance 35%, region 10%, experience 25%,
                          certifications 15%, rate 15%
        style only:       style 20%, region 25%, experience 20%,
                          certifications 20%, rate 15%
        neither:          region 30%, experience 25%, certifications 25%, rate 20%

    Args:
        instructor: InstructorProfile model instance.
        job: JobPost model instance.
        instructor_lat: Optional latitude override for the instructor.
            Falls back to instructor.latitude if not provided.
        instructor_lng: Optional longitude override for the instructor.
            Falls back to instructor.longitude if not provided.

    Returns:
        dict with total score (0-100), breakdown by category, and
        optionally distance_km when distance was calculated.
    """
    # Resolve instructor coordinates (parameter > model field)
    i_lat = instructor_lat if instructor_lat is not None else (
        float(instructor.latitude) if instructor.latitude is not None else None
    )
    i_lng = instructor_lng if instructor_lng is not None else (
        float(instructor.longitude) if instructor.longitude is not None else None
    )

    # Resolve job coordinates from the model
    j_lat = float(job.latitude) if job.latitude is not None else None
    j_lng = float(job.longitude) if job.longitude is not None else None

    # Determine whether distance-aware scoring is possible
    has_distance = (
        i_lat is not None and i_lng is not None
        and j_lat is not None and j_lng is not None
    )

    # Resolve style data
    instructor_style = getattr(instructor, 'teaching_style', None) or {}
    job_style = getattr(job, 'preferred_style', None) or {}
    has_style = bool(instructor_style) and bool(job_style)

    distance_km: Optional[float] = None

    if has_distance:
        distance_km = haversine_distance(i_lat, i_lng, j_lat, j_lng)  # type: ignore[arg-type]

    scores: dict[str, int] = {
        "region": 0,
        "experience": 0,
        "certifications": 0,
        "rate": 0,
    }

    if has_distance:
        scores["distance"] = _calculate_distance_score(distance_km)  # type: ignore[arg-type]

    if has_style:
        scores["style"] = _calculate_style_score(instructor_style, job_style)

    # Assign weights based on available data dimensions
    if has_distance and has_style:
        weights: dict[str, int] = {
            "distance": 25, "style": 20, "region": 10,
            "experience": 20, "certifications": 15, "rate": 10,
        }
    elif has_distance:
        weights = {
            "distance": 35, "region": 10, "experience": 25,
            "certifications": 15, "rate": 15,
        }
    elif has_style:
        weights = {
            "style": 20, "region": 25, "experience": 20,
            "certifications": 20, "rate": 15,
        }
    else:
        weights = {
            "region": 30, "experience": 25, "certifications": 25, "rate": 20,
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

    breakdown: dict = {
        "region": {"score": scores["region"], "weight": weights["region"]},
        "experience": {"score": scores["experience"], "weight": weights["experience"]},
        "certifications": {"score": scores["certifications"], "weight": weights["certifications"]},
        "rate": {"score": scores["rate"], "weight": weights["rate"]},
    }

    if has_distance:
        breakdown["distance"] = {
            "score": scores["distance"],
            "weight": weights["distance"],
        }

    if has_style:
        breakdown["style"] = {
            "score": scores["style"],
            "weight": weights["style"],
        }

    result: dict = {
        "total": round(total),
        "breakdown": breakdown,
    }

    if distance_km is not None:
        result["distance_km"] = round(distance_km, 2)

    return result


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
