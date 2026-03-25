"""Auto Dispatch Engine -- cascading dispatch with time-window selection.

Implements the core 119-style emergency dispatch system. When a studio posts
an urgent job with auto_dispatch enabled, the engine sends push notifications
in expanding geographic waves.

**Time-window model** (not FCFS):
  1. All candidates in a wave receive push notifications simultaneously
  2. Instructors can accept within the wave timeout (window)
  3. When the window closes, the system picks the best candidate by
     Reliability Score among those who accepted
  4. If nobody accepted, the next wave starts

Wave cascade:
  Wave 1: 5km radius, top 5 candidates, 2-min window
  Wave 2: 10km radius, top 10 candidates, 2-min window
  Wave 3: 15km radius, top 15 candidates, 2-min window

If all waves exhaust without acceptance, the job falls back to manual mode.

Usage::

    engine = DispatchEngine(db)
    records = await engine.start_auto_dispatch(job_post_id)
    result = await engine.accept_dispatch(dispatch_record_id, user_id)
"""

import logging
from datetime import datetime, timedelta
from decimal import Decimal
from typing import Optional

from sqlalchemy import select, update, and_
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.dispatch_record import DispatchRecord
from app.models.instructor_availability import InstructorAvailability
from app.models.instructor import InstructorProfile
from app.models.job_post import JobPost
from app.models.application import Application
from app.models.studio import StudioProfile
from app.models.user import User
from app.models.enums import (
    DispatchStatus,
    ApplicationStatus,
    JobPostStatus,
    TeacherTier,
)
from app.utils.distance import haversine_distance
from app.services.event_log import EventLogService
from app.services.notification import NotificationService, NotificationType

logger = logging.getLogger(__name__)

# ---------------------------------------------------------------------------
# Dispatch configuration -- expanding wave cascade
# ---------------------------------------------------------------------------

WAVE_CONFIG = [
    {"wave": 1, "radius_km": 5, "max_candidates": 5, "timeout_seconds": 120},
    {"wave": 2, "radius_km": 10, "max_candidates": 10, "timeout_seconds": 120},
    {"wave": 3, "radius_km": 15, "max_candidates": 15, "timeout_seconds": 120},
]

# Tier name -> reliability weight (out of 100)
_TIER_WEIGHT_MAP: dict[str, int] = {
    TeacherTier.T3_PRO.value: 100,
    TeacherTier.T2_VERIFIED.value: 70,
    TeacherTier.T1_BASIC.value: 40,
}
_TIER_WEIGHT_DEFAULT = 20


def calculate_urgency_score(job_date: datetime.date, start_time: datetime.time) -> float:  # type: ignore[name-defined]
    """Compute urgency score (0-100) based on time until class starts.

    Closer classes get higher urgency, which prioritizes them in the system.

    Args:
        job_date: The date of the class.
        start_time: The start time of the class.

    Returns:
        Urgency score from 20 (> 24h away) to 100 (< 2h away).
    """
    class_datetime = datetime.combine(job_date, start_time)
    now = datetime.utcnow()
    delta = class_datetime - now
    total_hours = delta.total_seconds() / 3600

    if total_hours < 2:
        return 100.0
    if total_hours < 4:
        return 80.0
    if total_hours < 8:
        return 60.0
    if total_hours < 24:
        return 40.0
    return 20.0


async def calculate_reliability_score(
    db: AsyncSession,
    instructor_profile: InstructorProfile,
    user: User,
) -> int:
    """Calculate dispatch reliability score (0-100) for candidate ranking.

    Higher score = more reliable instructor = dispatched first.

    Components (weighted):
        - Tier weight (30%): T3=100, T2=70, T1=40, None=20
        - Dispatch success rate (25%): Historical accept rate
        - No-show history (20%): Penalised for past no-shows
        - Completed count (15%): Volume of completed jobs
        - Check-in accuracy (10%): GPS proximity at check-in time

    Args:
        db: Async SQLAlchemy session.
        instructor_profile: The instructor's profile record.
        user: The instructor's user record.

    Returns:
        Weighted reliability score as integer (0-100).
    """
    # --- Tier weight (30%) ---
    tier_value = _TIER_WEIGHT_MAP.get(user.tier, _TIER_WEIGHT_DEFAULT) if user.tier else _TIER_WEIGHT_DEFAULT
    tier_component = tier_value * 0.30

    # --- Dispatch success rate (25%) ---
    success_rate = float(instructor_profile.dispatch_success_rate or 0)
    dispatch_component = (success_rate * 100) * 0.25

    # --- No-show history (20%) ---
    no_show_count = user.no_show_count or 0
    no_show_score = max(0, 100 - (no_show_count * 33))
    noshow_component = no_show_score * 0.20

    # --- Completed count (15%) ---
    total_completions = instructor_profile.total_completions or 0
    completion_score = min(total_completions * 10, 100)
    completion_component = completion_score * 0.15

    # --- Check-in accuracy (10%) ---
    avg_dist = float(instructor_profile.avg_checkin_distance_m or 0)
    if avg_dist <= 200:
        checkin_score = 100.0
    else:
        checkin_score = max(0.0, 100.0 - (avg_dist - 200) / 5.0)
    checkin_component = checkin_score * 0.10

    total = tier_component + dispatch_component + noshow_component + completion_component + checkin_component

    return int(round(total))


class DispatchEngine:
    """Core auto-dispatch engine with cascading wave selection.

    Args:
        db: Async SQLAlchemy session.
    """

    def __init__(self, db: AsyncSession) -> None:
        self.db = db

    # ------------------------------------------------------------------
    # Candidate selection
    # ------------------------------------------------------------------

    async def get_dispatch_candidates(
        self,
        job_post: JobPost,
        wave_config: dict,
        excluded_instructor_ids: list[str],
    ) -> list[dict]:
        """Select and rank dispatch candidates for a given wave.

        Uses the same bounding-box + haversine pattern as the availability
        service, but adds reliability scoring and candidate limiting.

        Args:
            job_post: The urgent job post to match against.
            wave_config: Dict with radius_km, max_candidates, timeout_seconds.
            excluded_instructor_ids: Instructor IDs already dispatched in prior waves.

        Returns:
            List of candidate dicts sorted by reliability_score DESC, limited
            to wave_config["max_candidates"]. Each dict contains:
            - instructor_id: str
            - user_id: str
            - distance_km: float
            - reliability_score: int
            - matching_score: int (alias for reliability_score in dispatch context)
        """
        if job_post.latitude is None or job_post.longitude is None:
            logger.warning(
                "Job post %s has no GPS coordinates, cannot dispatch", job_post.id
            )
            return []

        job_lat = float(job_post.latitude)
        job_lng = float(job_post.longitude)
        radius_km = wave_config["radius_km"]
        now = datetime.utcnow()

        # Bounding box pre-filter
        lat_delta = radius_km / 111.0
        lng_delta = radius_km / 88.0

        min_lat = Decimal(str(job_lat - lat_delta))
        max_lat = Decimal(str(job_lat + lat_delta))
        min_lng = Decimal(str(job_lng - lng_delta))
        max_lng = Decimal(str(job_lng + lng_delta))

        stmt = (
            select(InstructorAvailability)
            .where(
                and_(
                    InstructorAvailability.is_available.is_(True),
                    InstructorAvailability.available_until > now,
                    InstructorAvailability.latitude >= min_lat,
                    InstructorAvailability.latitude <= max_lat,
                    InstructorAvailability.longitude >= min_lng,
                    InstructorAvailability.longitude <= max_lng,
                )
            )
        )

        result = await self.db.execute(stmt)
        availabilities = result.scalars().all()

        candidates: list[dict] = []

        for avail in availabilities:
            # Skip already-dispatched instructors
            instructor_id_str = str(avail.instructor_id)
            if instructor_id_str in excluded_instructor_ids:
                continue

            if avail.latitude is None or avail.longitude is None:
                continue

            # Precise distance check
            distance = haversine_distance(
                job_lat, job_lng,
                float(avail.latitude), float(avail.longitude),
            )
            if distance > radius_km:
                continue

            # Category filter: empty categories = accepts all
            if job_post.category and avail.categories:
                if job_post.category not in avail.categories:
                    continue

            # Fetch instructor profile and user for reliability scoring
            profile_result = await self.db.execute(
                select(InstructorProfile).where(
                    InstructorProfile.id == avail.instructor_id
                )
            )
            profile = profile_result.scalar_one_or_none()
            if not profile:
                continue

            user_result = await self.db.execute(
                select(User).where(User.id == avail.user_id)
            )
            user = user_result.scalar_one_or_none()
            if not user or not user.is_active:
                continue

            # Skip suspended users
            if user.suspension_until and user.suspension_until > now:
                continue

            reliability = await calculate_reliability_score(self.db, profile, user)

            candidates.append({
                "instructor_id": str(avail.instructor_id),
                "user_id": str(avail.user_id),
                "distance_km": round(distance, 2),
                "reliability_score": reliability,
                "matching_score": reliability,  # Alias for dispatch context
            })

        # Sort by reliability_score DESC (most reliable first)
        candidates.sort(key=lambda c: c["reliability_score"], reverse=True)

        # Limit to max_candidates
        max_count = wave_config["max_candidates"]
        candidates = candidates[:max_count]

        logger.info(
            "Dispatch candidates for job=%s wave=%s: %d found (radius=%dkm, max=%d)",
            job_post.id, wave_config["wave"], len(candidates),
            radius_km, max_count,
        )

        return candidates

    # ------------------------------------------------------------------
    # Wave dispatch
    # ------------------------------------------------------------------

    async def dispatch_wave(
        self,
        job_post_id: str,
        wave_number: int,
    ) -> list[DispatchRecord]:
        """Dispatch a single wave of push notifications to candidates.

        Creates DispatchRecord entries for each candidate and sends FCM
        push notifications. Updates the job post's wave tracking fields.

        Args:
            job_post_id: The urgent job post ID.
            wave_number: Wave number (1-indexed, must match WAVE_CONFIG).

        Returns:
            List of created DispatchRecord instances.

        Raises:
            ValueError: If job post not found, not OPEN, or invalid wave number.
        """
        # Load job post
        result = await self.db.execute(
            select(JobPost).where(JobPost.id == job_post_id)
        )
        job_post = result.scalar_one_or_none()
        if not job_post:
            raise ValueError("JOB_POST_NOT_FOUND")
        if job_post.status != JobPostStatus.OPEN.value:
            raise ValueError("JOB_POST_NOT_OPEN")

        # Get wave config
        wave_cfg = None
        for cfg in WAVE_CONFIG:
            if cfg["wave"] == wave_number:
                wave_cfg = cfg
                break
        if not wave_cfg:
            raise ValueError(f"INVALID_WAVE_NUMBER: {wave_number}")

        # Get already-dispatched instructor IDs for this job (all waves)
        existing_result = await self.db.execute(
            select(DispatchRecord.instructor_id).where(
                DispatchRecord.job_post_id == job_post_id
            )
        )
        excluded_ids = [str(row[0]) for row in existing_result.all()]

        # Get candidates
        candidates = await self.get_dispatch_candidates(job_post, wave_cfg, excluded_ids)

        if not candidates:
            logger.info(
                "No candidates for job=%s wave=%d", job_post_id, wave_number
            )
            return []

        # Create dispatch records and send notifications
        now = datetime.utcnow()
        records: list[DispatchRecord] = []
        notification_service = NotificationService(self.db)

        for candidate in candidates:
            record = DispatchRecord(
                job_post_id=job_post_id,
                instructor_id=candidate["instructor_id"],
                user_id=candidate["user_id"],
                wave_number=wave_number,
                status=DispatchStatus.DISPATCHED.value,
                dispatched_at=now,
                distance_km=Decimal(str(candidate["distance_km"])),
                matching_score=candidate["matching_score"],
                reliability_score=candidate["reliability_score"],
            )
            self.db.add(record)
            records.append(record)

        # Update job post tracking
        job_post.dispatch_wave = wave_number
        if wave_number == 1:
            job_post.dispatch_started_at = now

        # Flush to generate record IDs
        await self.db.flush()

        # Send push notifications to each candidate
        timeout_minutes = wave_cfg["timeout_seconds"] // 60
        for i, record in enumerate(records):
            candidate = candidates[i]
            try:
                await notification_service.send(
                    user_id=candidate["user_id"],
                    type=NotificationType.URGENT_SUBSTITUTE,
                    title="긴급 대타 요청",
                    body=(
                        f"{job_post.title} - {candidate['distance_km']}km "
                        f"({timeout_minutes}분 내 수락)"
                    ),
                    data={
                        "dispatch_record_id": str(record.id),
                        "job_post_id": str(job_post_id),
                        "wave_number": str(wave_number),
                        "timeout_seconds": str(wave_cfg["timeout_seconds"]),
                        "priority": "high",
                    },
                )
            except Exception:
                logger.exception(
                    "Failed to send dispatch notification: record=%s user=%s",
                    record.id, candidate["user_id"],
                )

        # Update instructor dispatch stats
        for candidate in candidates:
            await self.db.execute(
                update(InstructorProfile)
                .where(InstructorProfile.id == candidate["instructor_id"])
                .values(total_dispatches=InstructorProfile.total_dispatches + 1)
            )

        await self.db.flush()

        logger.info(
            "Wave %d dispatched for job=%s: %d records created",
            wave_number, job_post_id, len(records),
        )

        return records

    # ------------------------------------------------------------------
    # Accept / Decline
    # ------------------------------------------------------------------

    async def accept_dispatch(
        self,
        dispatch_record_id: str,
        user_id: str,
    ) -> dict:
        """Accept a dispatch -- time-window model (not FCFS).

        Marks the record as accepted (intent). The actual confirmation
        happens when the wave window closes via finalize_dispatch_window(),
        which picks the best candidate by Reliability Score.

        Args:
            dispatch_record_id: The dispatch record to accept.
            user_id: The authenticated user's ID (must match record owner).

        Returns:
            Dict with acceptance status and wave window info.

        Raises:
            ValueError: If record not found, already responded, or job already filled.
            PermissionError: If user doesn't own the record.
        """
        result = await self.db.execute(
            select(DispatchRecord).where(DispatchRecord.id == dispatch_record_id)
        )
        record = result.scalar_one_or_none()
        if not record:
            raise ValueError("DISPATCH_RECORD_NOT_FOUND")

        if str(record.user_id) != str(user_id):
            raise PermissionError("NOT_YOUR_DISPATCH")

        if record.status != DispatchStatus.DISPATCHED.value:
            raise ValueError("ALREADY_RESPONDED")

        # Check if job is already finalized (filled by a previous window)
        job_result = await self.db.execute(
            select(JobPost).where(JobPost.id == record.job_post_id)
        )
        job_post = job_result.scalar_one_or_none()
        if job_post and job_post.status == JobPostStatus.FILLED.value:
            record.status = DispatchStatus.CANCELLED.value
            record.responded_at = datetime.utcnow()
            await self.db.flush()
            raise ValueError("ALREADY_MATCHED")

        now = datetime.utcnow()

        # Mark as accepted (intent only — window still open)
        record.status = DispatchStatus.ACCEPTED.value
        record.responded_at = now

        # Update instructor dispatch stats
        instructor_result = await self.db.execute(
            select(InstructorProfile).where(
                InstructorProfile.id == record.instructor_id
            )
        )
        instructor_profile = instructor_result.scalar_one_or_none()
        if instructor_profile:
            accepts = int(instructor_profile.total_dispatch_accepts or 0) + 1
            instructor_profile.total_dispatch_accepts = accepts
            total_dispatches = int(instructor_profile.total_dispatches or 1)
            instructor_profile.dispatch_success_rate = Decimal(
                str(round(accepts / total_dispatches, 3))
            )

        await self.db.flush()

        # Notify studio that a candidate accepted (informational)
        try:
            studio_result = await self.db.execute(
                select(StudioProfile).where(StudioProfile.id == job_post.studio_id)
            )
            studio_profile = studio_result.scalar_one_or_none()
            if studio_profile:
                instructor_name = instructor_profile.display_name if instructor_profile else "강사"
                accepted_count_result = await self.db.execute(
                    select(DispatchRecord).where(
                        and_(
                            DispatchRecord.job_post_id == record.job_post_id,
                            DispatchRecord.status == DispatchStatus.ACCEPTED.value,
                        )
                    )
                )
                accepted_count = len(accepted_count_result.scalars().all())
                notification_service = NotificationService(self.db)
                await notification_service.send(
                    user_id=str(studio_profile.user_id),
                    type=NotificationType.URGENT_SUBSTITUTE,
                    title=f"강사 {accepted_count}명 수락",
                    body=f"{instructor_name}님이 수락했습니다. 윈도우 종료 후 최적 강사가 자동 배정됩니다.",
                    data={
                        "type": "dispatch_accepted_pending",
                        "job_post_id": str(record.job_post_id),
                        "accepted_count": str(accepted_count),
                    },
                )
        except Exception:
            logger.exception(
                "Failed to send studio notification for dispatch accept: job=%s",
                record.job_post_id,
            )

        # Log event
        event_service = EventLogService(self.db)
        await event_service.log(
            event_type="dispatch.accepted",
            actor_user_id=str(user_id),
            target_type="job_post",
            target_id=str(record.job_post_id),
            data={
                "dispatch_record_id": str(record.id),
                "wave_number": record.wave_number,
                "distance_km": float(record.distance_km) if record.distance_km else None,
                "reliability_score": record.reliability_score,
            },
            note=f"Instructor accepted dispatch in wave {record.wave_number} (window pending)",
        )

        # Calculate remaining window time
        wave_cfg = next((c for c in WAVE_CONFIG if c["wave"] == record.wave_number), None)
        window_seconds = wave_cfg["timeout_seconds"] if wave_cfg else 120
        elapsed = (now - record.dispatched_at).total_seconds()
        remaining_seconds = max(0, int(window_seconds - elapsed))

        logger.info(
            "Dispatch accepted (window): record=%s user=%s job=%s wave=%d remaining=%ds",
            dispatch_record_id, user_id, record.job_post_id, record.wave_number,
            remaining_seconds,
        )

        return {
            "status": "accepted_pending",
            "message": "수락이 접수되었습니다. 윈도우 종료 후 최적 강사가 선정됩니다.",
            "dispatch_record_id": str(record.id),
            "job_post_id": str(record.job_post_id),
            "wave_number": record.wave_number,
            "remaining_seconds": remaining_seconds,
        }

    async def decline_dispatch(
        self,
        dispatch_record_id: str,
        user_id: str,
    ) -> None:
        """Decline a dispatch and potentially trigger next wave.

        Args:
            dispatch_record_id: The dispatch record to decline.
            user_id: The authenticated user's ID.

        Raises:
            ValueError: If record not found or already responded.
            PermissionError: If user doesn't own the record.
        """
        # Load record
        result = await self.db.execute(
            select(DispatchRecord).where(DispatchRecord.id == dispatch_record_id)
        )
        record = result.scalar_one_or_none()
        if not record:
            raise ValueError("DISPATCH_RECORD_NOT_FOUND")

        # Validate ownership
        if str(record.user_id) != str(user_id):
            raise PermissionError("NOT_YOUR_DISPATCH")

        # Validate status
        if record.status != DispatchStatus.DISPATCHED.value:
            raise ValueError("ALREADY_RESPONDED")

        # Mark as declined
        record.status = DispatchStatus.DECLINED.value
        record.responded_at = datetime.utcnow()
        await self.db.flush()

        logger.info(
            "Dispatch declined: record=%s user=%s job=%s wave=%d",
            dispatch_record_id, user_id, record.job_post_id, record.wave_number,
        )

        # Check if all dispatches in current wave are terminated
        await self._maybe_advance_wave(record.job_post_id, record.wave_number)

    # ------------------------------------------------------------------
    # Entry point
    # ------------------------------------------------------------------

    async def start_auto_dispatch(
        self,
        job_post_id: str,
    ) -> list[DispatchRecord]:
        """Entry point: start auto-dispatch for an urgent job post.

        Called from the job_posts endpoint when is_urgent=True and
        dispatch_mode='auto_dispatch'. Calculates urgency score and
        dispatches wave 1.

        Args:
            job_post_id: The urgent job post ID.

        Returns:
            List of DispatchRecord instances created in wave 1.

        Raises:
            ValueError: If job post not found or not eligible.
        """
        # Load and validate job post
        result = await self.db.execute(
            select(JobPost).where(JobPost.id == job_post_id)
        )
        job_post = result.scalar_one_or_none()
        if not job_post:
            raise ValueError("JOB_POST_NOT_FOUND")

        # Calculate and store urgency score
        urgency = calculate_urgency_score(job_post.date, job_post.start_time)
        job_post.urgency_score = Decimal(str(urgency))
        job_post.dispatch_mode = "auto_dispatch"
        await self.db.flush()

        logger.info(
            "Starting auto-dispatch: job=%s urgency=%.0f",
            job_post_id, urgency,
        )

        # Log event
        event_service = EventLogService(self.db)
        await event_service.log(
            event_type="dispatch.started",
            target_type="job_post",
            target_id=str(job_post_id),
            data={
                "urgency_score": urgency,
                "date": str(job_post.date),
                "start_time": str(job_post.start_time),
            },
            note="Auto-dispatch initiated",
        )

        # Dispatch wave 1
        records = await self.dispatch_wave(job_post_id, wave_number=1)

        # If no candidates found in wave 1, try wave 2 immediately
        if not records:
            logger.info(
                "No candidates in wave 1 for job=%s, trying wave 2", job_post_id
            )
            records = await self.dispatch_wave(job_post_id, wave_number=2)

        # If still no candidates, try wave 3
        if not records:
            logger.info(
                "No candidates in wave 2 for job=%s, trying wave 3", job_post_id
            )
            records = await self.dispatch_wave(job_post_id, wave_number=3)

        # If absolutely no candidates, fall back to manual
        if not records:
            await self._fallback_to_manual(job_post_id, job_post)

        return records

    # ------------------------------------------------------------------
    # Timeout handling (scheduler)
    # ------------------------------------------------------------------

    async def check_dispatch_timeouts(self) -> int:
        """Process expired wave windows — finalize or advance.

        Called periodically (every 30s). For each wave whose timeout has
        elapsed:
        1. Mark remaining 'dispatched' records as timed out
        2. Call finalize_dispatch_window to pick the best accepted candidate
        3. If nobody accepted, advance to next wave

        Returns:
            Count of records that timed out.
        """
        now = datetime.utcnow()
        timeout_count = 0
        affected_waves: list[tuple[str, int]] = []  # (job_post_id, wave_number)

        for wave_cfg in WAVE_CONFIG:
            wave_num = wave_cfg["wave"]
            timeout_secs = wave_cfg["timeout_seconds"]
            cutoff = now - timedelta(seconds=timeout_secs)

            # Find dispatched (non-responded) records past their window
            stmt = select(DispatchRecord).where(
                and_(
                    DispatchRecord.status == DispatchStatus.DISPATCHED.value,
                    DispatchRecord.wave_number == wave_num,
                    DispatchRecord.dispatched_at < cutoff,
                )
            )
            result = await self.db.execute(stmt)
            timed_out_records = result.scalars().all()

            for record in timed_out_records:
                record.status = DispatchStatus.TIMEOUT.value
                record.responded_at = now
                timeout_count += 1
                job_wave = (str(record.job_post_id), wave_num)
                if job_wave not in affected_waves:
                    affected_waves.append(job_wave)

        if timeout_count > 0:
            await self.db.flush()

        # For each affected wave, try to finalize the window
        for job_post_id, wave_number in affected_waves:
            # Skip if job is already filled
            job_result = await self.db.execute(
                select(JobPost).where(JobPost.id == job_post_id)
            )
            jp = job_result.scalar_one_or_none()
            if jp and jp.status == JobPostStatus.FILLED.value:
                continue

            # Try to finalize — picks best accepted candidate
            contact = await self.finalize_dispatch_window(job_post_id, wave_number)

            if contact is None:
                # Nobody accepted in this wave — advance
                await self._maybe_advance_wave(job_post_id, wave_number)

        if timeout_count > 0:
            logger.info("Dispatch timeouts processed: %d records", timeout_count)

        return timeout_count

    # ------------------------------------------------------------------
    # Internal helpers
    # ------------------------------------------------------------------

    async def finalize_dispatch_window(
        self,
        job_post_id: str,
        wave_number: int,
    ) -> Optional[dict]:
        """Finalize a wave's time window — pick the best accepted candidate.

        Called when the wave timeout expires. Among all accepted records in
        this wave, the one with the highest reliability_score is confirmed.
        Others are cancelled. If nobody accepted, returns None (caller should
        advance to next wave).

        Returns:
            Contact info dict if a winner was selected, None otherwise.
        """
        # Check if job is already filled (another wave finalized first)
        job_result = await self.db.execute(
            select(JobPost).where(JobPost.id == job_post_id)
        )
        job_post = job_result.scalar_one_or_none()
        if not job_post or job_post.status == JobPostStatus.FILLED.value:
            return None

        # Find all accepted records in this wave, sorted by reliability score
        accepted_result = await self.db.execute(
            select(DispatchRecord).where(
                and_(
                    DispatchRecord.job_post_id == job_post_id,
                    DispatchRecord.wave_number == wave_number,
                    DispatchRecord.status == DispatchStatus.ACCEPTED.value,
                )
            ).order_by(DispatchRecord.reliability_score.desc())
        )
        accepted_records = accepted_result.scalars().all()

        if not accepted_records:
            logger.info(
                "No accepted candidates in window: job=%s wave=%d",
                job_post_id, wave_number,
            )
            return None

        # Winner = highest reliability score
        winner = accepted_records[0]
        now = datetime.utcnow()

        logger.info(
            "Finalizing window: job=%s wave=%d winner=%s (score=%s) out of %d",
            job_post_id, wave_number, winner.instructor_id,
            winner.reliability_score, len(accepted_records),
        )

        # Cancel all other accepted records for this job (losers)
        for record in accepted_records[1:]:
            record.status = DispatchStatus.CANCELLED.value

        # Cancel remaining dispatched (non-responded) records
        await self.db.execute(
            update(DispatchRecord)
            .where(
                and_(
                    DispatchRecord.job_post_id == job_post_id,
                    DispatchRecord.id != winner.id,
                    DispatchRecord.status == DispatchStatus.DISPATCHED.value,
                )
            )
            .values(status=DispatchStatus.CANCELLED.value)
        )

        # Create Application for the winner
        application = Application(
            job_post_id=winner.job_post_id,
            instructor_id=winner.instructor_id,
            status=ApplicationStatus.ACCEPTED.value,
            contact_revealed=True,
            contact_revealed_at=now,
            dispatch_record_id=winner.id,
            cover_letter="[Auto-dispatch window selection]",
        )
        self.db.add(application)

        # Update job post to FILLED
        job_post.status = JobPostStatus.FILLED.value
        job_post.matched_instructor_id = winner.instructor_id
        job_post.auto_accepted_at = now
        job_post.application_count = (job_post.application_count or 0) + 1

        await self.db.flush()

        # Gather contact info
        instructor_result = await self.db.execute(
            select(InstructorProfile).where(InstructorProfile.id == winner.instructor_id)
        )
        instructor_profile = instructor_result.scalar_one_or_none()

        studio_result = await self.db.execute(
            select(StudioProfile).where(StudioProfile.id == job_post.studio_id)
        )
        studio_profile = studio_result.scalar_one_or_none()

        # Notify winner
        notification_service = NotificationService(self.db)
        try:
            await notification_service.send(
                user_id=str(winner.user_id),
                type=NotificationType.URGENT_SUBSTITUTE,
                title="축하합니다! 대타로 선정되었습니다",
                body=f"{job_post.title} - 연락처를 확인하세요.",
                data={
                    "type": "dispatch_confirmed",
                    "job_post_id": str(job_post_id),
                    "application_id": str(application.id),
                },
            )
        except Exception:
            logger.exception("Failed to notify winner: job=%s", job_post_id)

        # Notify studio
        if studio_profile:
            try:
                instructor_name = instructor_profile.display_name if instructor_profile else "강사"
                await notification_service.send(
                    user_id=str(studio_profile.user_id),
                    type=NotificationType.URGENT_SUBSTITUTE,
                    title="최적 강사가 배정되었습니다!",
                    body=f"{instructor_name}님이 배정되었습니다. 연락처를 확인하세요.",
                    data={
                        "type": "dispatch_confirmed",
                        "job_post_id": str(job_post_id),
                        "application_id": str(application.id),
                    },
                )
            except Exception:
                logger.exception("Failed to notify studio: job=%s", job_post_id)

        # Notify losers
        for record in accepted_records[1:]:
            try:
                await notification_service.send(
                    user_id=str(record.user_id),
                    type=NotificationType.URGENT_SUBSTITUTE,
                    title="다른 강사가 선정되었습니다",
                    body="이번 공고는 다른 강사에게 배정되었습니다. 다음 기회에 뵙겠습니다!",
                    data={
                        "type": "dispatch_not_selected",
                        "job_post_id": str(job_post_id),
                    },
                )
            except Exception:
                logger.exception("Failed to notify loser: record=%s", record.id)

        # Log event
        event_service = EventLogService(self.db)
        await event_service.log(
            event_type="dispatch.window_finalized",
            target_type="job_post",
            target_id=str(job_post_id),
            data={
                "winner_instructor_id": str(winner.instructor_id),
                "winner_reliability_score": winner.reliability_score,
                "total_accepted": len(accepted_records),
                "wave_number": wave_number,
            },
            note=f"Window finalized: {len(accepted_records)} accepted, best score={winner.reliability_score}",
        )

        return {
            "application_id": str(application.id),
            "instructor_phone": instructor_profile.phone if instructor_profile else None,
            "instructor_name": instructor_profile.display_name if instructor_profile else None,
            "studio_phone": studio_profile.phone if studio_profile else None,
            "studio_name": studio_profile.business_name if studio_profile else None,
            "studio_address": studio_profile.address if studio_profile else None,
        }

    async def _maybe_advance_wave(
        self,
        job_post_id: str,
        current_wave: int,
    ) -> None:
        """Check if all records in current wave are terminal, and advance if so.

        Terminal statuses: accepted, declined, timeout, cancelled.
        If an accepted record exists, do nothing (job is filled).
        If all terminal and no accept, trigger next wave or fallback to manual.

        Args:
            job_post_id: The job post ID.
            current_wave: The wave number to check.
        """
        # Check if any record is still pending (dispatched) in this wave
        pending_result = await self.db.execute(
            select(DispatchRecord).where(
                and_(
                    DispatchRecord.job_post_id == job_post_id,
                    DispatchRecord.wave_number == current_wave,
                    DispatchRecord.status == DispatchStatus.DISPATCHED.value,
                )
            )
        )
        still_pending = pending_result.scalars().first()
        if still_pending:
            # Wave still in progress
            return

        # Check if any record was accepted (across all waves for safety)
        accepted_result = await self.db.execute(
            select(DispatchRecord).where(
                and_(
                    DispatchRecord.job_post_id == job_post_id,
                    DispatchRecord.status == DispatchStatus.ACCEPTED.value,
                )
            )
        )
        if accepted_result.scalars().first():
            # Already matched, nothing to do
            return

        # All records in current wave are terminal, no accept found
        # Try next wave
        next_wave = current_wave + 1
        max_wave = max(cfg["wave"] for cfg in WAVE_CONFIG)

        if next_wave <= max_wave:
            logger.info(
                "Advancing to wave %d for job=%s", next_wave, job_post_id
            )
            await self.dispatch_wave(job_post_id, next_wave)
        else:
            # All waves exhausted -- fall back to manual mode
            job_result = await self.db.execute(
                select(JobPost).where(JobPost.id == job_post_id)
            )
            job_post = job_result.scalar_one_or_none()
            if job_post:
                await self._fallback_to_manual(job_post_id, job_post)

    async def _fallback_to_manual(
        self,
        job_post_id: str,
        job_post: JobPost,
    ) -> None:
        """Switch job post to manual mode after all dispatch waves fail.

        Notifies the studio owner that auto-dispatch did not find a match
        and the job is now open for manual applications.

        Args:
            job_post_id: The job post ID.
            job_post: The job post model instance.
        """
        job_post.dispatch_mode = "manual"
        await self.db.flush()

        logger.info(
            "Dispatch exhausted, falling back to manual: job=%s", job_post_id
        )

        # Notify studio
        studio_result = await self.db.execute(
            select(StudioProfile).where(StudioProfile.id == job_post.studio_id)
        )
        studio = studio_result.scalar_one_or_none()

        if studio:
            try:
                notification_service = NotificationService(self.db)
                await notification_service.send(
                    user_id=str(studio.user_id),
                    type=NotificationType.URGENT_SUBSTITUTE,
                    title="자동 매칭 실패",
                    body="자동 매칭에 실패했습니다. 수동 모드로 전환합니다.",
                    data={
                        "type": "dispatch_fallback",
                        "job_post_id": str(job_post_id),
                    },
                )
            except Exception:
                logger.exception(
                    "Failed to notify studio about manual fallback: job=%s",
                    job_post_id,
                )

        # Log event
        event_service = EventLogService(self.db)
        await event_service.log(
            event_type="dispatch.fallback_manual",
            target_type="job_post",
            target_id=str(job_post_id),
            data={"final_wave": job_post.dispatch_wave},
            note="All dispatch waves exhausted, switched to manual mode",
        )
