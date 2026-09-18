from pydantic import BaseModel
from datetime import date, time
from typing import Optional

class SubjectCreate(BaseModel):
    name: str
    start_date: date
    

class TopicCreate(BaseModel):
    name: str
    difficulty: Optional[int] = None
    importance: Optional[int] = None
    estimated_hours: Optional[int] = None

class ExamCreate(BaseModel):
    name: str
    exam_date: date
    topic_ids: list[int] = []

class FreeSlotCreate(BaseModel):
    day_of_week: int
    start_time: time
    end_time: time

class SubjectUpdate(BaseModel):
    name: Optional[str] = None
    start_date: Optional[date] = None
    
class TopicUpdate(BaseModel):
    name: Optional[str] = None
    difficulty: Optional[int] = None
    importance: Optional[int] = None
    estimated_hours: Optional[int] = None

class ExamUpdate(BaseModel):
    name: Optional[str] = None
    exam_date: Optional[date] = None

class FreeSlotUpdate(BaseModel):
    
    day_of_week: Optional[int] = None
    start_time: Optional[time] = None
    end_time: Optional[time] = None

class StudySessionUpdate(BaseModel):
    topic_id: Optional[int] = None
    study_date: Optional[date] = None
    start_time: Optional[time] = None
    end_time: Optional[time] = None
    is_completed: Optional[bool] = None


class SettingsUpdate(BaseModel):
    setting_value: str


