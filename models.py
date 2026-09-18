from datetime import time, date
from typing import Optional
from sqlalchemy import String, Date, Time, Integer, ForeignKey, Table, Column
from sqlalchemy.orm import Mapped, mapped_column, DeclarativeBase, relationship

class Base(DeclarativeBase):
    pass


class Subject(Base):
    __tablename__= "subjects"

    id: Mapped[int] = mapped_column(primary_key=True)
    name: Mapped[str] = mapped_column(String(99))
    start_date: Mapped[date] = mapped_column(Date)
    date_added: Mapped[date] = mapped_column(Date, default=date.today)
    
    topics: Mapped[list["Topic"]] = relationship(back_populates="subject", cascade="all, delete-orphan")
    exams: Mapped[list["Exam"]] = relationship(back_populates="subject", cascade="all, delete-orphan")

    def __repr__(self):
        return f"<Subject id={self.id}, name={self.name}>"

exam_topics = Table(
    "exam_topics",
    Base.metadata,
    Column("exam_id", ForeignKey("exams.id"), primary_key=True),
    Column("topic_id", ForeignKey("topics.id"), primary_key=True),
)

class Topic(Base):
    __tablename__ = "topics"

    id: Mapped[int] = mapped_column(primary_key=True)
    subject_id: Mapped[int] = mapped_column(ForeignKey("subjects.id"))
    name: Mapped[str] = mapped_column(String(99))
    difficulty: Mapped[int] = mapped_column(Integer, nullable=True)
    importance: Mapped[int] = mapped_column(Integer, nullable=True)
    estimated_hours: Mapped[int] = mapped_column(Integer, nullable=True)

    subject: Mapped["Subject"] = relationship(back_populates="topics")
    sessions: Mapped[list["StudySession"]] = relationship(back_populates="topic", cascade="all, delete-orphan")

    exams: Mapped[list["Exam"]] = relationship(secondary=exam_topics, back_populates="topics")


    def __repr__(self):
        return f"<Topic id={self.id}, name={self.name}, subject_name={self.subject.name}>"

class Exam(Base):
    __tablename__ = "exams"

    id: Mapped[int] = mapped_column(primary_key=True)
    subject_id: Mapped[int] = mapped_column(ForeignKey("subjects.id"))
    name: Mapped[str] = mapped_column(String(99))
    exam_date: Mapped[date] = mapped_column(Date)

    subject: Mapped["Subject"] = relationship(back_populates="exams")    

    topics: Mapped[list["Topic"]] = relationship(secondary=exam_topics, back_populates="exams")


class FreeSlot(Base):
    __tablename__ = "free_slots"

    id: Mapped[int] = mapped_column(primary_key=True)
    day_of_week: Mapped[int] = mapped_column(Integer)  # 0 = Monday ... 6 = Sunday
    start_time: Mapped[time] = mapped_column(Time)
    end_time: Mapped[time] = mapped_column(Time)

    def __repr__(self):
        return f"<FreeSlot day={self.day_of_week}, {self.start_time}-{self.end_time}>"


class StudySession(Base):
    __tablename__ = "study_sessions"

    id: Mapped[int] = mapped_column(primary_key=True)
    topic_id: Mapped[int] = mapped_column(ForeignKey("topics.id"))
    study_date: Mapped[date] = mapped_column(Date)
    start_time: Mapped[time] = mapped_column(Time)
    end_time: Mapped[time] = mapped_column(Time)
    is_completed: Mapped[bool] = mapped_column(default=False)

    topic: Mapped["Topic"] = relationship(back_populates="sessions")

    def __repr__(self):
        return f"<StudySession topic={self.topic.name}, date={self.study_date}>"

class Setting(Base):
    __tablename__ = "settings"

    id: Mapped[int] = mapped_column(primary_key=True)
    setting_name: Mapped[str] = mapped_column(String(99), unique=True)
    setting_value: Mapped[str] = mapped_column(String(255))