from datetime import time, date, timedelta, datetime
import math
from models import StudySession

def data_preparation(topics, exams):
    output = []

    for topic in topics:
        deadline = get_deadlines(topic, exams)

        output.append({
            "topic_id": topic.id,
            "difficulty": topic.difficulty,
            "importance": topic.importance,
            "estimated_hours": topic.estimated_hours,
            "deadline": deadline,
            "start_date": topic.subject.start_date,
        })

    return output

def get_deadlines(topic, exams):
    # assumes no exam dates before 2000 if that is no longer true refactor
    latest_date = date(2000, 1, 1)

    if topic.exams:
        for exam in topic.exams:
            if exam.exam_date > latest_date:
                latest_date = exam.exam_date
            
    else:
        for exam in exams:
            if topic.subject_id == exam.subject_id and exam.exam_date > latest_date :
                latest_date = exam.exam_date

        if latest_date == date(2000, 1, 1):
            for exam in exams:
                if exam.exam_date > latest_date:
                    latest_date = exam.exam_date
                
        if latest_date == date(2000, 1, 1):
            return None
    return latest_date

def get_end_date(prepared_topics, start_date):
    output: date = start_date

    for topic in prepared_topics:
        if topic["deadline"]:
            if output < topic["deadline"]:
                output = topic["deadline"]

    if output == start_date:
        output = output + timedelta(weeks=26)

    return output


def get_expanded_free_slots(free_slots, start_date, end_date):

    output = []

    for slot in free_slots:
        
        x = (slot.day_of_week - start_date.weekday()) % 7
        current_date = start_date + timedelta(days=x)

        while current_date <= end_date:
            pass
            # create slot
            output.append ({
                "date": current_date,
                "start": slot.start_time,
                "end": slot.end_time,
            })

            current_date = current_date + timedelta(days=7)

    # return a dict of "date, start time, end time" for each slot
    return output


def add_minutes(t: time, minutes: int) -> time:
    dummy = datetime.combine(date.today(), t)
    return (dummy + timedelta(minutes=minutes)).time()

def get_minutes(start: time, end: time) -> int:
    dummy = date.today()
    start_dt = datetime.combine(dummy, start)
    end_dt = datetime.combine(dummy, end)
    
    difference = end_dt - start_dt
    
    total_minutes = difference.total_seconds() / 60
    return int(total_minutes)


def get_study_sessions(free_slots_expanded, study_duration, break_duration):

    study_sessions = []

    for slot in free_slots_expanded:
        
        time1 = get_minutes(slot["start"], slot["end"])
        study_slots = time1 // (study_duration + break_duration)
        time2 = time1 % (study_duration + break_duration)
        if time2 >= study_duration:
            study_slots = study_slots + 1

        for i in range(study_slots):
            study_sessions.append({
                "date": slot["date"],
                "start": (add_minutes(slot["start"], (study_duration + break_duration) * i)),
                "end": (add_minutes(slot["start"], ((study_duration + break_duration) * i) + study_duration)),
                "type": "Study",
                "topic": None,
            })
            study_sessions.append({
                "date": slot["date"],
                "start": (add_minutes(slot["start"], ((study_duration + break_duration) * i) + study_duration)),
                "end": (add_minutes(slot["start"], ((study_duration + break_duration) * i) + study_duration + break_duration)),
                "type": "Break",
                "topic": None,
            })
    return study_sessions

def get_deadline_topic(topic):
    return topic["deadline"]

def get_deadline_study(study_session):
    return study_session["date"]

def check_deadlines_time(prepared_data, study_sessions, study_duration):

    already_checked = []

    prepared_data_no_deadline = []
    prepared_data_deadline = []

    study_sessions_filtered = []

    for session in study_sessions:
        if session["type"] == "Study":
            study_sessions_filtered.append(session)

    for data in prepared_data:
        if data["deadline"] == None:
            prepared_data_no_deadline.append(data)
        else:
            prepared_data_deadline.append(data)
    sorted_prepared_data = sorted(prepared_data_deadline, key=get_deadline_topic)
    sorted_study_sessions = sorted(study_sessions_filtered, key=get_deadline_study)

    current_item = 0
    current_date: date
    total_data_time = 0
    total_session_time = 0

    for data in sorted_prepared_data:
        already_checked.append(data["topic_id"])
        current_date = data["deadline"]

        while current_item < len(sorted_study_sessions) and sorted_study_sessions[current_item]["date"] < current_date:
            total_session_time += study_duration
            current_item += 1

        estimated_min = (data["estimated_hours"] * 60)
        estimated_min = math.ceil(estimated_min / study_duration)
        estimated_min = estimated_min * study_duration

        total_data_time += estimated_min

        if total_data_time > total_session_time:
            
            return already_checked

    while current_item < len(sorted_study_sessions):
                total_session_time += study_duration
                current_item += 1

    for data in prepared_data_no_deadline:
        already_checked.append(data["topic_id"])

        estimated_min = (data["estimated_hours"] * 60)
        estimated_min = math.ceil(estimated_min / study_duration)
        estimated_min = estimated_min * study_duration

        total_data_time += estimated_min

    if total_data_time > total_session_time:
                
                return already_checked



    already_checked = []
    return already_checked

#scale-down loop can theoretically fail to converge if available time before a deadline is less than one study_duration chunk per topic

# CREATE SCALE DOWN FUNC

def get_deadline_topic(topic):
    return topic["deadline"]

def get_slot_date(slot):
    return slot["date"]

def get_required_time_topic(topic, study_duration):
    estimated_min = (topic["estimated_hours"] * 60)
    estimated_min = math.ceil(estimated_min / study_duration)
    return estimated_min

def assign_slot_to_topic(prepared_data, slots, study_duration):
    sorted_data = sorted(prepared_data, key=get_deadline_topic)

    for data in sorted_data:
        study_slots = []
        for slot in slots:
            if slot["type"] == "Study" and slot["topic"] == None:
                if slot["date"] >= data["start_date"] and slot["date"] <= data["deadline"]:
                    study_slots.append(slot)

        required_slots = get_required_time_topic(data, study_duration)
        slot_count = len(study_slots)
        if slot_count == 0:
            print(f"ERROR: topic_id {data['topic_id']} has 0 available study slots before its deadline ")
            continue

        for i in range(required_slots):
            index = i * slot_count // required_slots
            selected_slot = study_slots[index]
            selected_slot["topic"] = data["topic_id"]

    slot_counts = {}

    for data in sorted_data:
        if data["importance"] >= 9:
            x = 1
        elif data["importance"] >= 6:
            x = 2
        elif data["importance"] >= 3:
            x = 3
        else:
            x = 4
        slot_counts[data["topic_id"]] = x

    while True:
        unclaimed_slots = []
        for slot in slots:
            if slot["type"] == "Study" and slot["topic"] == None:
                unclaimed_slots.append(slot)

        if len(unclaimed_slots) == 0:
            break

        valid_topics = []
        for data in sorted_data:
            can_claim = False
            for slot in unclaimed_slots:
                if slot["date"] >= data["start_date"] and slot["date"] <= data["deadline"]:
                    can_claim = True
                    break
            if can_claim:
                valid_topics.append(data)

        if len(valid_topics) == 0:
            break

        current_topic = valid_topics[0]
        for data in valid_topics[1:]:
            if slot_counts[data["topic_id"]] < slot_counts[current_topic["topic_id"]]:
                current_topic = data
            elif slot_counts[data["topic_id"]] == slot_counts[current_topic["topic_id"]]:
                if data["difficulty"] > current_topic["difficulty"]:
                    current_topic = data
                elif data["difficulty"] == current_topic["difficulty"]:
                    if data["deadline"] < current_topic["deadline"]:
                        current_topic = data
                    elif data["deadline"] == current_topic["deadline"]:
                        if data["topic_id"] < current_topic["topic_id"]:
                            current_topic = data

        current_topic_valid_slots = []
        for slot in unclaimed_slots:
            if slot["date"] >= current_topic["start_date"] and slot["date"] <= current_topic["deadline"]:
                current_topic_valid_slots.append(slot)

        current_slot = max(current_topic_valid_slots, key=get_slot_date)
        current_slot["topic"] = current_topic["topic_id"]
        slot_counts[current_topic["topic_id"]] += 1

    return slots


def clean_output(slots):

    output = []

    for slot in slots:
        if slot["type"] == "Study" and slot["topic"] is not None:
            new_session = StudySession(
                topic_id=slot["topic"],
                study_date=slot["date"],
                start_time=slot["start"],
                end_time=slot["end"],
            )
            output.append(new_session)

    return output