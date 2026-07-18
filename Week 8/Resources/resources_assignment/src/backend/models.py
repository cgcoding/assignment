from sqlalchemy import Column, Integer, String, Date, UniqueConstraint
from database import Base

class User(Base):
    __tablename__ = "users"

    id = Column(Integer, primary_key=True, index=True)
    email = Column(String, unique=True, index=True)
    hashed_password = Column(String)

#  Uncomment this after you have the habit and completion models defined. This says that the combination of userId, habitId, and period_start must be unique in a class which has the __table_args__ constraint.

# So that your HabiCompletion table  can't say that you have done PDT twice on 10th July.

    
    
    # __table_args__ = (
    #     UniqueConstraint("userId", "habitId", "period_start", name="uq_user_habit_period_start"),)
