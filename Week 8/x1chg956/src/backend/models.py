from sqlalchemy import Column, Integer, String, Date, UniqueConstraint, ForeignKey
from database import Base

class User(Base):
    __tablename__ = "users"

    id = Column(Integer, primary_key=True, index=True)
    email = Column(String, unique=True, index=True)
    hashed_password = Column(String)


class Habit(Base):
    __tablename__ = "habits"

    habitId = Column(Integer, primary_key=True, index=True)
    name = Column(String, nullable=False)
    userId = Column(Integer, ForeignKey("users.id"), nullable=False, index=True)
    frequency = Column(String, nullable=False)  # "Daily" | "Weekly"


class HabitCompletion(Base):
    __tablename__ = "habit_completions"

    id = Column(Integer, primary_key=True, index=True)
    habitId = Column(Integer, ForeignKey("habits.habitId"), nullable=False, index=True)
    userId = Column(Integer, ForeignKey("users.id"), nullable=False, index=True)
    period_start = Column(Date, nullable=False)

    __table_args__ = (
        UniqueConstraint("userId", "habitId", "period_start", name="uq_user_habit_period_start"),)
