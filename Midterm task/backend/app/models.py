from datetime import datetime
from sqlalchemy import Boolean, CheckConstraint, DateTime, Float, ForeignKey, Integer, String, Text, func
from sqlalchemy.orm import Mapped, mapped_column, relationship
from .database import Base

class WantedCriminal(Base):
    __tablename__ = "wanted_criminals"
    __table_args__ = (CheckConstraint("difficulty BETWEEN 1 AND 10", name="difficulty_range"),)
    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    name: Mapped[str | None] = mapped_column(String(255), nullable=True)
    nickname: Mapped[str] = mapped_column(String(255), nullable=False)
    reward: Mapped[float] = mapped_column(Float, nullable=False)
    last_known_latitude: Mapped[float | None] = mapped_column(Float, nullable=True)
    last_known_longitude: Mapped[float | None] = mapped_column(Float, nullable=True)
    last_known_note: Mapped[str | None] = mapped_column(Text, nullable=True)
    difficulty: Mapped[int] = mapped_column(Integer, nullable=False)
    armed: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    has_crew: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    escape_master: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    hunt_logs: Mapped[list["HuntLog"]] = relationship(back_populates="criminal")

class HuntLog(Base):
    __tablename__ = "hunt_logs"
    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    criminal_id: Mapped[int] = mapped_column(ForeignKey("wanted_criminals.id"), nullable=False)
    success: Mapped[bool] = mapped_column(Boolean, nullable=False)
    notes: Mapped[str] = mapped_column(Text, nullable=False)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )
    criminal: Mapped["WantedCriminal"] = relationship(back_populates="hunt_logs")
