from __future__ import annotations

from datetime import datetime, timedelta
import math

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from ..auth import get_current_user
from ..config import settings
from ..database import get_db
from ..game_logic import render_session_details, simulate_blackjack, spin_slots, virtual_sport_event
from ..models import GameSession, Transaction, User
from ..schemas import (
    BlackjackResult,
    BonusClaim,
    DashboardSnapshot,
    GameHistoryEntry,
    GameRequest,
    PurchaseRequest,
    PurchaseResponse,
    SlotsResult,
    TransactionsResponse,
    UserProfile,
    VirtualSportBet,
    VirtualSportResult,
)

router = APIRouter(prefix="/players", tags=["players"])


@router.get("/me", response_model=UserProfile)
def get_profile(
    user: User = Depends(get_current_user), db: Session = Depends(get_db)
) -> UserProfile:
    db.refresh(user)
    return UserProfile.from_orm(user)


@router.post("/daily-bonus", response_model=BonusClaim)
def claim_daily_bonus(
    user: User = Depends(get_current_user), db: Session = Depends(get_db)
) -> BonusClaim:
    now = datetime.utcnow()
    if user.last_bonus_claim and now - user.last_bonus_claim < timedelta(hours=20):
        next_claim = user.last_bonus_claim + timedelta(hours=20)
        return BonusClaim(awarded=False, amount=0, next_claim=next_claim)
    user.balance += settings.daily_bonus_amount
    user.loyalty_points += settings.loyalty_points_per_game
    user.last_bonus_claim = now
    db.add(
        Transaction(
            user_id=user.id,
            amount=settings.daily_bonus_amount,
            type="bonus",
            description="Daily cosmic recharge",
        )
    )
    db.commit()
    db.refresh(user)
    return BonusClaim(awarded=True, amount=settings.daily_bonus_amount, next_claim=now + timedelta(hours=20))


@router.post("/purchase", response_model=PurchaseResponse)
def purchase_credits(
    payload: PurchaseRequest,
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> PurchaseResponse:
    packages = {
        "meteor": 1500,
        "starlight": 4000,
        "supercluster": 10000,
    }
    if payload.package_id not in packages:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Unknown package")
    amount = packages[payload.package_id]
    user.balance += amount
    user.loyalty_points += math.ceil(amount / 100)
    db.add(
        Transaction(
            user_id=user.id,
            amount=amount,
            type="purchase",
            description=f"Mock purchase: {payload.package_id}",
        )
    )
    db.commit()
    db.refresh(user)
    return PurchaseResponse(
        success=True,
        amount=amount,
        balance=user.balance,
        loyalty_points=user.loyalty_points,
        message="Purchase completed via mock processor",
    )


@router.post("/games/slots", response_model=SlotsResult)
def play_slots(
    payload: GameRequest,
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> SlotsResult:
    if payload.bet > user.balance:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Insufficient funds")
    symbols, payout, message = spin_slots(payload.bet)
    net = payout - payload.bet
    user.balance += net
    user.loyalty_points += settings.loyalty_points_per_game
    session = GameSession(
        user_id=user.id,
        game_type="slots",
        bet_amount=payload.bet,
        net_result=net,
        details=render_session_details({"symbols": symbols, "message": message}),
    )
    db.add(session)
    db.add(
        Transaction(
            user_id=user.id,
            amount=net,
            type="slots_result",
            description=f"Spin outcome: {', '.join(symbols)} — {message}",
        )
    )
    db.commit()
    db.refresh(user)
    return SlotsResult(symbols=symbols, payout=payout, net=net, message=message)


@router.post("/games/blackjack", response_model=BlackjackResult)
def play_blackjack(
    payload: GameRequest,
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> BlackjackResult:
    if payload.bet > user.balance:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Insufficient funds")
    player, dealer, net, outcome = simulate_blackjack(payload.bet)
    user.balance += net
    user.loyalty_points += settings.loyalty_points_per_game
    session = GameSession(
        user_id=user.id,
        game_type="blackjack",
        bet_amount=payload.bet,
        net_result=net,
        details=render_session_details(
            {
                "player": player,
                "dealer": dealer,
                "outcome": outcome,
            }
        ),
    )
    db.add(session)
    db.add(
        Transaction(
            user_id=user.id,
            amount=net,
            type="blackjack_result",
            description=(
                f"Outcome: {outcome.title()} — player {', '.join(player)} vs dealer {', '.join(dealer)}"
            ),
        )
    )
    db.commit()
    db.refresh(user)
    return BlackjackResult(player_hand=player, dealer_hand=dealer, outcome=outcome, net=net)


@router.post("/games/virtual-sport", response_model=VirtualSportResult)
def play_virtual_sport(
    payload: VirtualSportBet,
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> VirtualSportResult:
    if payload.bet > user.balance:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Insufficient funds")
    winner, net, odds = virtual_sport_event(payload.selection, payload.bet)
    user.balance += net
    user.loyalty_points += settings.loyalty_points_per_game
    session = GameSession(
        user_id=user.id,
        game_type="virtual_sport",
        bet_amount=payload.bet,
        net_result=net,
        details=render_session_details(
            {
                "selection": payload.selection,
                "winner": winner,
                "odds": odds,
            }
        ),
    )
    db.add(session)
    db.add(
        Transaction(
            user_id=user.id,
            amount=net,
            type="virtual_sport_result",
            description=(
                f"Backed {payload.selection.title()} — winner {winner.title()} at {odds}x"
            ),
        )
    )
    db.commit()
    db.refresh(user)
    return VirtualSportResult(selection=payload.selection, winner=winner, net=net, odds=odds)


@router.get("/dashboard", response_model=DashboardSnapshot)
def dashboard(
    user: User = Depends(get_current_user), db: Session = Depends(get_db)
) -> DashboardSnapshot:
    recent_sessions = (
        db.query(GameSession)
        .filter(GameSession.user_id == user.id)
        .order_by(GameSession.created_at.desc())
        .limit(10)
        .all()
    )
    transactions = (
        db.query(Transaction)
        .filter(Transaction.user_id == user.id)
        .order_by(Transaction.created_at.desc())
        .limit(10)
        .all()
    )
    return DashboardSnapshot(
        profile=UserProfile.from_orm(user),
        recent_sessions=[
            GameHistoryEntry(
                game_type=session.game_type,
                bet_amount=session.bet_amount,
                net_result=session.net_result,
                details=session.details,
                created_at=session.created_at,
            )
            for session in recent_sessions
        ],
        transactions=[
            TransactionsResponse(
                type=txn.type,
                amount=txn.amount,
                description=txn.description,
                created_at=txn.created_at,
            )
            for txn in transactions
        ],
    )
