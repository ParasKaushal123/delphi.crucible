"""
User Profile model and Redis schema.
"""

from pydantic import BaseModel
from typing import Dict

class Position(BaseModel):
    buy_price: float
    shares: int

class UserProfile(BaseModel):
    user_id: str
    capital: float
    risk_tolerance: str
    portfolio: Dict[str, Position]
