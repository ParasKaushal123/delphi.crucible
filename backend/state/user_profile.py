"""
User Profile model and Redis schema.
"""

from pydantic import BaseModel
from typing import Dict

class Position(BaseModel):
    buy_price: float
    shares: int
    threshold: str = ""

class UserProfile(BaseModel):
    user_id: str
    income: float = 0.0
    risk_tolerance: str = "moderate"
    experience: str = "beginner"
    portfolio: Dict[str, Position] = {}
