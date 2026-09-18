from fastapi import FastAPI, Depends, HTTPException
from sqlalchemy.orm import Session

from database import get_db, SessionLocal
from models import Subject, Topic, FreeSlot, Exam, StudySession, Setting
from schemas import SubjectCreate, TopicCreate, FreeSlotCreate, ExamCreate, StudySessionUpdate, SubjectUpdate, TopicUpdate, ExamUpdate, FreeSlotUpdate, SettingsUpdate

app = FastAPI()

# START UP

@app.on_event("startup")
def create_default_settings():
    db = SessionLocal()
    sett = db.query(Setting).filter(Setting.setting_name == "study_duration").first()
    if sett is None:
        new_setting = Setting(
            setting_name = "study_duration",
            setting_value = "45"
        )
        db.add(new_setting)

    sett = db.query(Setting).filter(Setting.setting_name == "break_duration").first()
    if sett is None:    
        new_setting = Setting(
                setting_name = "break_duration",
                setting_value = "15"
            )
        db.add(new_setting)
    db.commit()
    db.close()

# CRUD
@app.get("/settings/{setting_name}")
def get_setting(setting_name: str, db: Session = Depends(get_db)):
    setting = db.query(Setting).filter(Setting.setting_name == setting_name).first()
    if setting is None:
        raise HTTPException(status_code=404, detail="Setting not found")
    return setting


@app.get("/")
def root():
    return {"message": "Study planner API running"}

@app.get("/subjects/{subject_id}")
def get_subject(subject_id: int, db: Session = Depends(get_db)):
    subject = db.query(Subject).filter(Subject.id == subject_id).first()
    if subject is None:
        raise HTTPException(status_code=404, detail="Subject not found")
    return subject

@app.patch("/settings/{setting_name}")
def update_setting(setting_name: str, updates: SettingsUpdate, db: Session = Depends(get_db)):
    setting = db.query(Setting).filter(Setting.setting_name == setting_name).first()
    if setting is None:
        raise HTTPException(status_code=404, detail="Setting not found")

    setting.setting_value = updates.setting_value

    db.commit()
    db.refresh(setting)
    return setting

@app.post("/subjects")
def create_subject(subject: SubjectCreate, db: Session = Depends(get_db)):
    new_subject = Subject(
        name=subject.name,
        start_date=subject.start_date,
    )
    db.add(new_subject)
    db.commit()
    db.refresh(new_subject)
    return new_subject

@app.patch("/subjects/{subject_id}")
def update_subject(subject_id: int, updates: SubjectUpdate, db: Session = Depends(get_db)):
    subject = db.query(Subject).filter(Subject.id == subject_id).first()
    if subject is None:
        raise HTTPException(status_code=404, detail="Subject not found")

    update_data = updates.model_dump(exclude_unset=True)
    for field, value in update_data.items():
        setattr(subject, field, value)

    db.commit()
    db.refresh(subject)
    return subject

@app.patch("/topics/{topic_id}")
def update_topic(topic_id: int, updates: TopicUpdate, db: Session = Depends(get_db)):
    topic = db.query(Topic).filter(Topic.id == topic_id).first()
    if topic is None:
        raise HTTPException(status_code=404, detail="Topic not found")

    update_data = updates.model_dump(exclude_unset=True)
    for field, value in update_data.items():
        setattr(topic, field, value)

    db.commit()
    db.refresh(topic)
    return topic

@app.post("/subjects/{subject_id}/topics")
def create_topic(subject_id: int, topic: TopicCreate, db: Session = Depends(get_db)):
    subject = db.query(Subject).filter(Subject.id == subject_id).first()
    if subject is None:
        raise HTTPException(status_code=404, detail="Subject not found")
    new_topic = Topic(
        subject_id=subject_id,
        name=topic.name,
        difficulty=topic.difficulty,
        importance=topic.importance,
        estimated_hours=topic.estimated_hours
    )
    db.add(new_topic)
    db.commit()
    db.refresh(new_topic)
    return new_topic

@app.post("/free-slots")
def create_free_slot(slot: FreeSlotCreate, db: Session = Depends(get_db)):

    if slot.end_time <= slot.start_time:
        raise HTTPException(status_code=400, detail="end_time must be after start_time")

    todays_slots = db.query(FreeSlot).filter(FreeSlot.day_of_week == slot.day_of_week).all()
    for slot_loop in todays_slots:
        if slot.start_time < slot_loop.end_time and slot.end_time > slot_loop.start_time:
            raise HTTPException(status_code=400, detail=f"times overlap with slot ID({slot_loop.id})")
    new_slot = FreeSlot(
        day_of_week=slot.day_of_week,
        start_time=slot.start_time,
        end_time=slot.end_time
    )
    db.add(new_slot)
    db.commit()
    db.refresh(new_slot)
    return new_slot

@app.patch("/free-slots/{free_slot_id}")
def update_free_slot(free_slot_id: int, updates: FreeSlotUpdate, db: Session = Depends(get_db)):
    slot = db.query(FreeSlot).filter(FreeSlot.id == free_slot_id).first()
    if slot is None:
        raise HTTPException(status_code=404, detail="Free Slot not found")



    update_data = updates.model_dump(exclude_unset=True)

    todays_slots = db.query(FreeSlot).filter(FreeSlot.day_of_week == slot.day_of_week).all()
    for slot_loop in todays_slots:
        if update_data.get("start_time", slot.start_time) < slot_loop.end_time and update_data.get("end_time", slot.end_time) > slot_loop.start_time:
            if slot_loop.id != slot.id:
                raise HTTPException(status_code=400, detail=f"times overlap with slot ID({slot_loop.id})")
            
    if update_data.get("end_time", slot.end_time) <= update_data.get("start_time", slot.start_time):
        raise HTTPException(status_code=400, detail="end_time must be after start_time")

    for field, value in update_data.items():
        setattr(slot, field, value)

    db.commit()
    db.refresh(slot)
    return slot

@app.post("/subjects/{subject_id}/exams")
def create_exams(subject_id: int, exam: ExamCreate, db: Session = Depends(get_db)):
    subject = db.query(Subject).filter(Subject.id == subject_id).first()
    if subject is None:
        raise HTTPException(status_code=404, detail="Subject Not Found")

    topics = db.query(Topic).filter(Topic.id.in_(exam.topic_ids)).all()
    if len(topics) != len(exam.topic_ids):
        raise HTTPException(status_code=404, detail="One Or More Topics Not Found")

    new_exam = Exam(
        subject_id=subject_id,
        name=exam.name,
        exam_date=exam.exam_date,
        topics=topics
    )

    db.add(new_exam)
    db.commit()
    db.refresh(new_exam)
    return new_exam


@app.get("/subjects")
def all_subjects(db: Session = Depends(get_db)):
    return db.query(Subject).all()

@app.get("/subjects/{subject_id}")
def get_subject(subject_id: int, db: Session = Depends(get_db)):
    subject = db.query(Subject).filter(Subject.id == subject_id).first()
    if subject is None:
        raise HTTPException(status_code=404, detail="Subject not found")
    return subject


@app.delete("/subjects/{subject_id}")
def delete_subject(subject_id: int, db: Session = Depends(get_db)):
    subject = db.query(Subject).filter(Subject.id == subject_id).first()
    if subject is None:
        raise HTTPException(status_code=404, detail="Subject not found")

    db.delete(subject)
    db.commit()
    return {"detail": "Subject deleted"}


@app.get("/topics")
def all_topics(db: Session = Depends(get_db)):
    return db.query(Topic).all()

@app.get("/topics/{topic_id}")
def get_topic(topic_id: int, db: Session = Depends(get_db)):
    topic = db.query(Topic).filter(Topic.id == topic_id).first()
    if topic is None:
        raise HTTPException(status_code=404, detail="Topic not found")
    return topic



@app.delete("/topics/{topic_id}")
def delete_topic(topic_id: int, db: Session = Depends(get_db)):
    topic = db.query(Topic).filter(Topic.id == topic_id).first()
    if topic is None:
        raise HTTPException(status_code=404, detail="Topic not found")

    db.delete(topic)
    db.commit()
    return {"detail": "topic deleted"}

@app.get("/subjects/{subject_id}/topics")
def get_subjects_topics(subject_id: int, db: Session = Depends(get_db)):
    subject = db.query(Subject).filter(Subject.id == subject_id).first()
    if subject is None:
        raise HTTPException(status_code=404, detail="Subject not found")

    topics = db.query(Topic).filter(Topic.subject_id == subject_id).all()

    return topics



@app.get("/exams")
def all_exams(db: Session = Depends(get_db)):
    return db.query(Exam).all()

@app.get("/exams/{exam_id}")
def get_exam(exam_id: int, db: Session = Depends(get_db)):
    exam = db.query(Exam).filter(Exam.id == exam_id).first()
    if exam is None:
        raise HTTPException(status_code=404, detail="Exam not found")
    return exam

@app.delete("/exams/{exam_id}")
def delete_exam(exam_id: int, db: Session = Depends(get_db)):
    exam = db.query(Exam).filter(Exam.id == exam_id).first()
    if exam is None:
        raise HTTPException(status_code=404, detail="Exam not found")

    db.delete(exam)
    db.commit()
    return {"detail": "exam deleted"}

@app.get("/free-slots")
def all_free_slots(db: Session = Depends(get_db)):
    return db.query(FreeSlot).all()

@app.get("/free-slots/{free_slot_id}")
def get_free_slot(free_slot_id: int, db: Session = Depends(get_db)):
    free_slot = db.query(FreeSlot).filter(FreeSlot.id == free_slot_id).first()
    if free_slot is None:
        raise HTTPException(status_code=404, detail="Free Slot not found")
    return free_slot

@app.delete("/free-slots/{free_slot_id}")
def delete_free_slot (free_slot_id: int, db: Session = Depends(get_db)):
    free_slot = db.query(FreeSlot).filter(FreeSlot.id == free_slot_id).first()
    if free_slot is None:
        raise HTTPException(status_code=404, detail="Free Slot not found")

    db.delete(free_slot)
    db.commit()
    return {"detail": "Free Slot deleted"}

@app.get("/subjects/{subject_id}/exams")
def get_subjects_exams(subject_id: int, db: Session = Depends(get_db)):
    subject = db.query(Subject).filter(Subject.id == subject_id).first()
    if subject is None:
        raise HTTPException(status_code=404, detail="Subject not found")

    exams = db.query(Exam).filter(Exam.subject_id == subject_id).all()

    return exams

@app.get("/study-sessions")
def all_study_sessions(db: Session = Depends(get_db)):
    return db.query(StudySession).all()

@app.get("/study-sessions/{study_sessions_id}")
def get_study_sessions(study_sessions_id: int, db: Session = Depends(get_db)):
    study_session = db.query(StudySession).filter(StudySession.id == study_sessions_id).first()
    if study_session is None:
        raise HTTPException(status_code=404, detail="Study Session not found")
    return study_session

@app.delete("/study-sessions/{study_sessions_id}")
def delete_study_session (study_sessions_id: int, db: Session = Depends(get_db)):
    study_session = db.query(StudySession).filter(StudySession.id == study_sessions_id).first()
    if study_session is None:
        raise HTTPException(status_code=404, detail="Study Session not found")

    db.delete(study_session)
    db.commit()
    return {"detail": "Study Session deleted"}

@app.get("/subjects/{subject_id}/study-sessions")
def get_subjects_study_sessions(subject_id: int, db: Session = Depends(get_db)):
    subject = db.query(Subject).filter(Subject.id == subject_id).first()
    if subject is None:
        raise HTTPException(status_code=404, detail="Subject not found")

    sessions = (
        db.query(StudySession)
        .join(Topic, StudySession.topic_id == Topic.id)
        .filter(Topic.subject_id == subject_id).all()
    )

    return sessions

@app.post("/generate-schedule")
def create_schedule(db: Session = Depends(get_db)):
    

    return True