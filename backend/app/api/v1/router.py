from fastapi import APIRouter

from app.api.v1.endpoints import (
    auth, instructors, studios, job_posts, applications,
    offers, contracts, payments, chat, reviews, reports, support,
    verification, deposit, subscription
)

api_router = APIRouter()

api_router.include_router(auth.router, prefix="/auth", tags=["auth"])
api_router.include_router(verification.router, prefix="/verification", tags=["verification"])
api_router.include_router(deposit.router, prefix="/deposit", tags=["deposit"])
api_router.include_router(subscription.router, prefix="/subscriptions", tags=["subscriptions"])
api_router.include_router(instructors.router, prefix="/instructors", tags=["instructors"])
api_router.include_router(studios.router, prefix="/studios", tags=["studios"])
api_router.include_router(job_posts.router, prefix="/job-posts", tags=["job-posts"])
api_router.include_router(applications.router, tags=["applications"])
api_router.include_router(offers.router, prefix="/offers", tags=["offers"])
api_router.include_router(contracts.router, prefix="/contracts", tags=["contracts"])
api_router.include_router(payments.router, tags=["payments"])
api_router.include_router(chat.router, prefix="/threads", tags=["chat"])
api_router.include_router(reviews.router, tags=["reviews"])
api_router.include_router(reports.router, tags=["reports"])
api_router.include_router(support.router, tags=["support"])
