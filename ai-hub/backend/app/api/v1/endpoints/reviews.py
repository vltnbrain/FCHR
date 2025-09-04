"""
Reviews API endpoints for AI Hub
"""
from fastapi import APIRouter

router = APIRouter()

@router.post("/")
async def create_review():
    """Create a review (analyst or finance decision)"""
    return {"message": "Create review endpoint - TODO: implement"}

@router.get("/")
async def list_reviews():
    """List reviews with optional filtering"""
    return {"message": "List reviews endpoint - TODO: implement"}
