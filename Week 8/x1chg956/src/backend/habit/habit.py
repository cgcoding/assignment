from datetime import date, timedelta
from typing import List

from fastapi import APIRouter, HTTPException, Depends, status
from sqlalchemy.orm import Session
from sqlalchemy.exc import IntegrityError

from database import get_db
from models import Habit, HabitCompletion
from schemas import HabitCreate, HabitResponse, CompletionRequest, CompletionResponse
from jwt_tokens import get_user_id

router = APIRouter()


def _get_owned_habit(db: Session, habit_id: int, user_id: int) -> Habit:
    habit = db.query(Habit).filter(Habit.habitId == habit_id).first()
    if habit is None or habit.userId != user_id:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Habit not found")
    return habit


def _current_period_start(habit: Habit, reference_date: date) -> date:
    if habit.frequency == "Weekly":
        return reference_date - timedelta(days=reference_date.weekday())
    return reference_date


def _is_completed_for_current_period(db: Session, habit: Habit, user_id: int, today: date) -> bool:
    period_start = _current_period_start(habit, today)
    return db.query(HabitCompletion).filter(
        HabitCompletion.userId == user_id,
        HabitCompletion.habitId == habit.habitId,
        HabitCompletion.period_start == period_start,
    ).first() is not None


def _to_response(habit: Habit, completed: bool) -> HabitResponse:
    return HabitResponse(habitId=habit.habitId, name=habit.name, frequency=habit.frequency, completed=completed)


@router.post("", response_model=HabitResponse, status_code=status.HTTP_201_CREATED)
def create_habit(data: HabitCreate, user_id: int = Depends(get_user_id), db: Session = Depends(get_db)):
    habit = Habit(name=data.name, userId=user_id, frequency=data.frequency)
    db.add(habit)
    db.commit()
    db.refresh(habit)
    return _to_response(habit, completed=False)


@router.get("", response_model=List[HabitResponse])
def list_habits(user_id: int = Depends(get_user_id), db: Session = Depends(get_db)):
    habits = db.query(Habit).filter(Habit.userId == user_id).all()
    today = date.today()
    return [_to_response(habit, _is_completed_for_current_period(db, habit, user_id, today)) for habit in habits]


@router.delete("/{habit_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_habit(habit_id: int, user_id: int = Depends(get_user_id), db: Session = Depends(get_db)):
    habit = _get_owned_habit(db, habit_id, user_id)
    db.query(HabitCompletion).filter(HabitCompletion.habitId == habit_id).delete()
    db.delete(habit)
    db.commit()
    return None


@router.post("/{habit_id}/complete", response_model=CompletionResponse, status_code=status.HTTP_201_CREATED)
def complete_habit(
    habit_id: int,
    data: CompletionRequest,
    user_id: int = Depends(get_user_id),
    db: Session = Depends(get_db),
):
    habit = _get_owned_habit(db, habit_id, user_id)

    if data.date > date.today():
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Cannot complete a habit for a future date")

    period_start = _current_period_start(habit, data.date)

    existing = db.query(HabitCompletion).filter(
        HabitCompletion.userId == user_id,
        HabitCompletion.habitId == habit_id,
        HabitCompletion.period_start == period_start,
    ).first()
    if existing:
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="Habit already completed for this period")

    completion = HabitCompletion(habitId=habit_id, userId=user_id, period_start=period_start)
    db.add(completion)
    try:
        db.commit()
    except IntegrityError:
        db.rollback()
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="Habit already completed for this period")
    db.refresh(completion)
    return completion


@router.get("/{habit_id}/completions", response_model=List[date])
def list_completions(habit_id: int, user_id: int = Depends(get_user_id), db: Session = Depends(get_db)):
    _get_owned_habit(db, habit_id, user_id)
    rows = (
        db.query(HabitCompletion.period_start)
        .filter(HabitCompletion.userId == user_id, HabitCompletion.habitId == habit_id)
        .order_by(HabitCompletion.period_start)
        .all()
    )
    return [r[0] for r in rows]
