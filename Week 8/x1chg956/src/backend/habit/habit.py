from datetime import date, timedelta

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from database import get_db
from jwt_tokens import get_user_id
from models import Habit, HabitCompletion
from schemas import HabitCompletionIn, HabitCreate, HabitOut, HabitStreakOut

router = APIRouter()


def _period_start_for_frequency(frequency: str, completion_date: date) -> date:
    if frequency == "weekly":
        return completion_date - timedelta(days=completion_date.weekday())
    return completion_date


def _step_for_frequency(frequency: str) -> timedelta:
    if frequency == "weekly":
        return timedelta(days=7)
    return timedelta(days=1)


def _calculate_streaks(periods: list[date], frequency: str) -> tuple[int, int]:
    if not periods:
        return 0, 0

    sorted_periods = sorted(set(periods))
    step = _step_for_frequency(frequency)

    longest_streak = 1
    running_streak = 1
    for index in range(1, len(sorted_periods)):
        if sorted_periods[index] - sorted_periods[index - 1] == step:
            running_streak += 1
        else:
            running_streak = 1
        if running_streak > longest_streak:
            longest_streak = running_streak

    current_streak = 1
    for index in range(len(sorted_periods) - 1, 0, -1):
        if sorted_periods[index] - sorted_periods[index - 1] == step:
            current_streak += 1
        else:
            break

    return current_streak, longest_streak


@router.get("/", response_model=list[HabitOut])
def getHabits(db: Session = Depends(get_db), current_user: int = Depends(get_user_id)):
    return db.query(Habit).filter(Habit.userId == current_user).order_by(Habit.id.desc()).all()


@router.post("/", response_model=HabitOut)
def create_habit(
    habit_data: HabitCreate,
    db: Session = Depends(get_db),
    current_user: int = Depends(get_user_id),
):
    frequency = habit_data.frequency.lower().strip()
    if frequency not in {"daily", "weekly"}:
        raise HTTPException(status_code=400, detail="Frequency must be either daily or weekly")

    habit = Habit(
        userId=current_user,
        name=habit_data.name.strip(),
        frequency=frequency,
    )
    db.add(habit)
    db.commit()
    db.refresh(habit)
    return habit


@router.get("/streaks", response_model=list[HabitStreakOut])
def get_streaks(
    db: Session = Depends(get_db),
    current_user: int = Depends(get_user_id),
):
    habits = db.query(Habit).filter(Habit.userId == current_user).order_by(Habit.id.desc()).all()
    streaks: list[HabitStreakOut] = []

    for habit in habits:
        completions = db.query(HabitCompletion).filter(
            HabitCompletion.userId == current_user,
            HabitCompletion.habitId == habit.id,
        ).order_by(HabitCompletion.period_start.asc()).all()

        periods = [completion.period_start for completion in completions]
        current_streak, longest_streak = _calculate_streaks(periods, habit.frequency)
        last_completed_date = completions[-1].completion_date if completions else None

        streaks.append(
            HabitStreakOut(
                habitId=habit.id,
                name=habit.name,
                frequency=habit.frequency,
                current_streak=current_streak,
                longest_streak=longest_streak,
                last_completed_date=last_completed_date,
            )
        )

    return streaks


@router.delete("/{habit_id}")
def delete_habit(
    habit_id: int,
    db: Session = Depends(get_db),
    current_user: int = Depends(get_user_id),
):
    habit = db.query(Habit).filter(Habit.id == habit_id, Habit.userId == current_user).first()
    if not habit:
        raise HTTPException(status_code=404, detail="Habit not found")

    db.query(HabitCompletion).filter(
        HabitCompletion.habitId == habit_id,
        HabitCompletion.userId == current_user,
    ).delete()
    db.delete(habit)
    db.commit()

    return {"message": "Habit deleted"}


@router.post("/{habit_id}/complete")
def mark_complete(
    habit_id: int,
    data: HabitCompletionIn,
    db: Session = Depends(get_db),
    current_user: int = Depends(get_user_id),
):
    habit = db.query(Habit).filter(Habit.id == habit_id, Habit.userId == current_user).first()
    if not habit:
        raise HTTPException(status_code=404, detail="Habit not found")

    period_start = _period_start_for_frequency(habit.frequency, data.completion_date)

    existing = db.query(HabitCompletion).filter(
        HabitCompletion.userId == current_user,
        HabitCompletion.habitId == habit_id,
        HabitCompletion.period_start == period_start,
    ).first()

    if existing:
        raise HTTPException(status_code=400, detail="Habit already marked complete for this period")

    completion = HabitCompletion(
        userId=current_user,
        habitId=habit_id,
        period_start=period_start,
        completion_date=data.completion_date,
    )
    db.add(completion)
    db.commit()

    return {"message": "Habit marked complete", "completion_date": data.completion_date}
