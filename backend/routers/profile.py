from fastapi import APIRouter, Request, HTTPException
from pydantic import BaseModel
from state.user_profile import UserProfile
import json

router = APIRouter(prefix="/api/user", tags=["User Profile"])

MOCK_USER_ID = "demo_user"

class ProfileUpdate(BaseModel):
    income: float
    risk_tolerance: str
    experience: str

@router.get("/profile", response_model=UserProfile)
async def get_profile(request: Request):
    store = request.app.state.session_store
    data = await store._redis.get(f"user_profile:{MOCK_USER_ID}")
    if not data:
        raise HTTPException(status_code=404, detail="Profile not found")
    return UserProfile.model_validate_json(data)

@router.post("/profile")
async def update_profile(profile_data: ProfileUpdate, request: Request):
    store = request.app.state.session_store
    data = await store._redis.get(f"user_profile:{MOCK_USER_ID}")
    
    if data:
        profile = UserProfile.model_validate_json(data)
    else:
        profile = UserProfile(user_id=MOCK_USER_ID)
        
    profile.income = profile_data.income
    profile.risk_tolerance = profile_data.risk_tolerance
    profile.experience = profile_data.experience
    
    await store._redis.set(f"user_profile:{MOCK_USER_ID}", profile.model_dump_json())
    return {"status": "success", "profile": profile.model_dump()}
