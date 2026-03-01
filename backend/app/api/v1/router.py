from fastapi import APIRouter

from app.api.v1.endpoints import (
    auth, instructors, studios, job_posts, applications,
    reviews, reports, support,
    verification, profiles, trust,
    notifications,
)

# PMF pivot: These imports kept for future reactivation but routes disabled
# from app.api.v1.endpoints import (
#     offers, contracts, chat, subscription, templates, usage,
# )

api_router = APIRouter()

# === Active routes (PMF pivot: urgent substitute matching) ===
api_router.include_router(auth.router, prefix="/auth", tags=["auth"])
api_router.include_router(verification.router, prefix="/verification", tags=["verification"])
api_router.include_router(profiles.router, tags=["profiles"])
api_router.include_router(trust.router, tags=["trust"])
api_router.include_router(instructors.router, prefix="/instructors", tags=["instructors"])
api_router.include_router(studios.router, prefix="/studios", tags=["studios"])
api_router.include_router(job_posts.router, prefix="/job-posts", tags=["job-posts"])
api_router.include_router(applications.router, tags=["applications"])
api_router.include_router(reviews.router, tags=["reviews"])
api_router.include_router(reports.router, tags=["reports"])
api_router.include_router(support.router, tags=["support"])
api_router.include_router(notifications.router, prefix="/notifications", tags=["notifications"])

# === Disabled routes (PMF pivot: reactivate post-PMF) ===
# api_router.include_router(subscription.router, prefix="/subscriptions", tags=["subscriptions"])
# api_router.include_router(offers.router, prefix="/offers", tags=["offers"])
# api_router.include_router(contracts.router, prefix="/contracts", tags=["contracts"])
# api_router.include_router(chat.router, prefix="/threads", tags=["chat"])
# api_router.include_router(templates.router, tags=["templates"])
# api_router.include_router(usage.router, prefix="/usage", tags=["usage"])
