from sqlalchemy import Column, Date, ForeignKey, Integer, String, UniqueConstraint
from database import Base

class User(Base):
    __tablename__ = "users"

    id = Column(Integer, primary_key=True, index=True)
    email = Column(String, unique=True, index=True)
    hashed_password = Column(String)


class Habit(Base):
    __tablename__ = "habits"

    id = Column("habitId", Integer, primary_key=True, index=True)
    userId = Column(Integer, ForeignKey("users.id"), nullable=False, index=True)
    name = Column(String, nullable=False)
    frequency = Column(String, nullable=False)


class HabitCompletion(Base):
    __tablename__ = "habit_completions"

    id = Column(Integer, primary_key=True, index=True)
    userId = Column(Integer, ForeignKey("users.id"), nullable=False, index=True)
    habitId = Column(Integer, ForeignKey("habits.habitId"), nullable=False, index=True)
    period_start = Column(Date, nullable=False)
    completion_date = Column(Date, nullable=True)

    __table_args__ = (
        UniqueConstraint("userId", "habitId", "period_start", name="uq_user_habit_period_start"),
    )

#  Uncomment this after you have the habit and completion models defined. This says that the combination of userId, habitId, and period_start must be unique in a class which has the __table_args__ constraint.

# So that your HabiCompletion table  can't say that you have done PDT twice on 10th July.

    
    
    # __table_args__ = (
    #     UniqueConstraint("userId", "habitId", "period_start", name="uq_user_habit_period_start"),)
