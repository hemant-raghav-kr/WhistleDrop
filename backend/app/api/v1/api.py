"""Aggregated API router for version 1."""

from fastapi import APIRouter

from app.api.v1.endpoints import admin, auth, moderator, reports

api_router = APIRouter()

api_router.include_router(
    reports.router,
    prefix="/reports",
    tags=["Reports"],
)

api_router.include_router(
    auth.router,
    prefix="/auth",
    tags=["Authentication"],
)

api_router.include_router(
    moderator.router,
    prefix="/moderator",
    tags=["Moderator"],
)

api_router.include_router(
    admin.router,
    prefix="/admin",
    tags=["Admin User Management"],
)
