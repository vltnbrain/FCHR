"""
Main API router for AI Hub v1
"""
from fastapi import APIRouter

from app.api.v1.endpoints import ideas, users, reviews, assignments, dashboard

api_router = APIRouter()

# Include all endpoint routers
api_router.include_router(ideas.router, prefix="/ideas", tags=["ideas"])
api_router.include_router(users.router, prefix="/users", tags=["users"])
api_router.include_router(reviews.router, prefix="/reviews", tags=["reviews"])
api_router.include_router(assignments.router, prefix="/assignments", tags=["assignments"])
api_router.include_router(dashboard.router, prefix="/dashboard", tags=["dashboard"])
