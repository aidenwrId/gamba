from __future__ import annotations

from datetime import datetime
from typing import Optional

from pydantic import BaseModel, EmailStr, Field


class Token(BaseModel):
    access_token: str
    token_type: str = "bearer"


class UserBase(BaseModel):
    username: str = Field(..., min_length=3, max_length=50)
    email: EmailStr


class UserCreate(UserBase):
    password: str = Field(..., min_length=8)
    age: int = Field(..., ge=18)


class UserLogin(BaseModel):
    username: str
    password: str


class UserProfile(BaseModel):
    username: str
    email: EmailStr
    balance: int
    loyalty_points: int
    created_at: datetime
    last_bonus_claim: Optional[datetime]

    class Config:
        orm_mode = True


class GameRequest(BaseModel):
    bet: int = Field(..., gt=0)


class SlotsResult(BaseModel):
    symbols: list[str]
    payout: int
    net: int
    message: str


class BlackjackResult(BaseModel):
    player_hand: list[str]
    dealer_hand: list[str]
    outcome: str
    net: int


class VirtualSportBet(BaseModel):
    bet: int = Field(..., gt=0)
    selection: str = Field(..., regex=r"^(aurora|nebula)$")


class VirtualSportResult(BaseModel):
    selection: str
    winner: str
    net: int
    odds: float


class BonusClaim(BaseModel):
    awarded: bool
    amount: int
    next_claim: Optional[datetime]


class PurchaseRequest(BaseModel):
    package_id: str


class PurchaseResponse(BaseModel):
    success: bool
    amount: int
    balance: int
    loyalty_points: int
    message: str


class GameHistoryEntry(BaseModel):
    game_type: str
    bet_amount: int
    net_result: int
    details: str
    created_at: datetime


class TransactionsResponse(BaseModel):
    type: str
    amount: float
    description: str
    created_at: datetime


class DashboardSnapshot(BaseModel):
    profile: UserProfile
    recent_sessions: list[GameHistoryEntry]
    transactions: list[TransactionsResponse]
