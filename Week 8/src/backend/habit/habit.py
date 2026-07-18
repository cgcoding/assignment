from datetime import date, timedelta

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from database import get_db
from jwt_tokens import get_user_id
from models import Habit, HabitCompletion
from schemas import HabitCompletionIn, HabitCompletionOut, HabitCreate, HabitOut

router = APIRouter()


def _normalize_frequency(frequency: str) -> str:
    value = frequency.strip().lower()
    if value not in {"daily", "weekly", "monthly"}:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Frequency must be daily, weekly, or monthly"
        )
    return value


def _period_start(completed_on: date, frequency: str) -> date:
    if frequency == "daily":
        return completed_on

    if frequency == "weekly":
        # First day of the week (Monday) is used as tracking date.
        return completed_on - timedelta(days=completed_on.weekday())

    # First day of the month is used as tracking date.
    return completed_on.replace(day=1)


@router.get("/", response_model=list[HabitOut])
def getHabits(db: Session = Depends(get_db), current_user: int = Depends(get_user_id)):
    return db.query(Habit).filter(Habit.user_id == current_user).order_by(Habit.id.desc()).all()


@router.post("/", response_model=HabitOut, status_code=status.HTTP_201_CREATED)
def create_habit(
    habit_data: HabitCreate,
    db: Session = Depends(get_db),
    current_user: int = Depends(get_user_id)
):
    habit = Habit(
        name=habit_data.name.strip(),
        frequency=_normalize_frequency(habit_data.frequency),
        user_id=current_user
    )
    db.add(habit)
    db.commit()
    db.refresh(habit)
    return habit


@router.delete("/{habit_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_habit(
    habit_id: int,
    db: Session = Depends(get_db),
    current_user: int = Depends(get_user_id)
):
    habit = db.query(Habit).filter(Habit.id == habit_id, Habit.user_id == current_user).first()
    if not habit:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Habit not found")

    db.delete(habit)
    db.commit()
    return None


@router.post("/{habit_id}/complete", status_code=status.HTTP_201_CREATED)
def mark_complete(
    habit_id: int,
    data: HabitCompletionIn,
    db: Session = Depends(get_db),
    current_user: int = Depends(get_user_id)
):
    habit = db.query(Habit).filter(Habit.id == habit_id, Habit.user_id == current_user).first()
    if not habit:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Habit not found")

    period_start = _period_start(data.completed_on, habit.frequency)
    duplicate = db.query(HabitCompletion).filter(
        HabitCompletion.habit_id == habit_id,
        HabitCompletion.user_id == current_user,
        HabitCompletion.period_start == period_start
    ).first()

    if duplicate:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="Habit already completed for this period"
        )

    completion = HabitCompletion(
        habit_id=habit_id,
        user_id=current_user,
        completed_on=data.completed_on,
        period_start=period_start
    )
    db.add(completion)
    db.commit()

    return {
        "message": "Habit marked complete",
        "habit_id": habit_id,
        "completed_on": str(data.completed_on),
        "period_start": str(period_start)
    }


@router.get("/{habit_id}/completions", response_model=list[HabitCompletionOut])
def get_completions(
    habit_id: int,
    db: Session = Depends(get_db),
    current_user: int = Depends(get_user_id)
):
    habit = db.query(Habit).filter(Habit.id == habit_id, Habit.user_id == current_user).first()
    if not habit:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Habit not found")

    return db.query(HabitCompletion).filter(
        HabitCompletion.habit_id == habit_id,
        HabitCompletion.user_id == current_user
    ).order_by(HabitCompletion.completed_on.desc()).all()
