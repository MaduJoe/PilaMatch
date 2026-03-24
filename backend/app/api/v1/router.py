from fastapi import APIRouter

from app.api.v1.endpoints import (
    auth, instructors, studios, job_posts, applications,
    reviews, reports, support,
    verification, profiles, tier, penalties, payment_confirmation,
    notifications, backup_instructors,
    subscription, kakao,
    availability, dispatch,
    checkin, completion, handoff_templates,
)

# PMF pivot: These imports kept for future reactivation but routes disabled
# from app.api.v1.endpoints import (
#     offers, contracts, chat, templates, usage, trust,
# )

api_router = APIRouter()

# === Active routes (PMF pivot: urgent substitute matching) ===
api_router.include_router(auth.router, prefix="/auth", tags=["auth"])
api_router.include_router(verification.router, prefix="/verification", tags=["verification"])
api_router.include_router(profiles.router, tags=["profiles"])
api_router.include_router(tier.router, tags=["tier"])
api_router.include_router(penalties.router, tags=["penalties"])
api_router.include_router(payment_confirmation.router, tags=["payment-confirmation"])
api_router.include_router(instructors.router, prefix="/instructors", tags=["instructors"])
api_router.include_router(studios.router, prefix="/studios", tags=["studios"])
api_router.include_router(job_posts.router, prefix="/job-posts", tags=["job-posts"])
api_router.include_router(applications.router, tags=["applications"])
api_router.include_router(backup_instructors.router, prefix="/studios/me/backup-instructors", tags=["backup-instructors"])
api_router.include_router(reviews.router, tags=["reviews"])
api_router.include_router(reports.router, tags=["reports"])
api_router.include_router(support.router, tags=["support"])
api_router.include_router(notifications.router, prefix="/notifications", tags=["notifications"])
api_router.include_router(kakao.router, prefix="/kakao", tags=["kakao"])
api_router.include_router(availability.router, prefix="/availability", tags=["availability"])
api_router.include_router(dispatch.router, prefix="/dispatch", tags=["dispatch"])
api_router.include_router(checkin.router, tags=["checkin"])
api_router.include_router(completion.router, tags=["completion"])
api_router.include_router(handoff_templates.router, tags=["handoff-templates"])

# === Disabled routes (PMF pivot: reactivate post-PMF) ===
# api_router.include_router(trust.router, tags=["trust"])  # Replaced by tier
api_router.include_router(subscription.router, prefix="/subscriptions", tags=["subscriptions"])
# api_router.include_router(offers.router, prefix="/offers", tags=["offers"])
# api_router.include_router(contracts.router, prefix="/contracts", tags=["contracts"])
# api_router.include_router(chat.router, prefix="/threads", tags=["chat"])
# api_router.include_router(templates.router, tags=["templates"])
# api_router.include_router(usage.router, prefix="/usage", tags=["usage"])
