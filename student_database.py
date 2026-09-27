import os
import time
from typing import Dict, Any, List, Optional
from pymongo import MongoClient, ASCENDING

MONGO_URL = os.environ.get("MONGO_URL", "mongodb://localhost:27017/")
DATABASE_NAME = "pragtutor"

# Collection Names
TEACHERS_COLLECTION = "teachers"
STUDENTS_COLLECTION = "students"
STUDENT_PROGRESS_COLLECTION = "student_progress"

# Globals
client: Optional[MongoClient] = None
db = None
teachers_col = None
students_col = None
progress_col = None
IS_MONGO_CONNECTED = False

# Fallback In-Memory cache (only used if MongoDB is unavailable)
IN_MEMORY_TEACHERS: Dict[str, Dict[str, Any]] = {}
IN_MEMORY_STUDENTS: Dict[str, Dict[str, Any]] = {}
IN_MEMORY_PROGRESS: Dict[str, Dict[str, Any]] = {}  # key: f"{student_id}:{subject}"

SUBJECT_ID_MAP = {
    "os": "operating_systems",
    "operating_systems": "operating_systems",
    "cn": "computer_networks",
    "computer_networks": "computer_networks",
    "ds": "data_structures",
    "data_structures": "data_structures",
    "dbms": "dbms",
    "se": "software_engineering",
    "software_engineering": "software_engineering"
}

def normalize_subject_id(sub: Optional[str]) -> str:
    if not sub:
        return "operating_systems"
    s = str(sub).lower().strip().replace(" ", "_")
    return SUBJECT_ID_MAP.get(s, s)

def init_mongodb():
    global client, db, teachers_col, students_col, progress_col, IS_MONGO_CONNECTED
    try:
        client = MongoClient(MONGO_URL, serverSelectionTimeoutMS=3000)
        # Verify connection
        client.admin.command('ping')
        db = client[DATABASE_NAME]
        teachers_col = db[TEACHERS_COLLECTION]
        students_col = db[STUDENTS_COLLECTION]
        progress_col = db[STUDENT_PROGRESS_COLLECTION]

        # Ensure unique and lookup indexes
        try:
            teachers_col.create_index([("teacher_id", ASCENDING)], unique=True, sparse=True)
            teachers_col.create_index([("email", ASCENDING)], unique=True)
        except Exception as e:
            print(f"Index creation note for teachers: {e}")

        try:
            students_col.create_index([("student_id", ASCENDING)], unique=True, sparse=True)
            students_col.create_index([("email", ASCENDING)], unique=True)
        except Exception as e:
            print(f"Index creation note for students: {e}")

        try:
            progress_col.create_index([("student_id", ASCENDING), ("subject", ASCENDING)], unique=True)
        except Exception as e:
            print(f"Index creation note for student_progress: {e}")

        IS_MONGO_CONNECTED = True
        print(f"✅ Connected to MongoDB ({DATABASE_NAME}) successfully.")
    except Exception as e:
        IS_MONGO_CONNECTED = False
        print(f"⚠️ MongoDB connection notice: {e}. Fallback cache active.")

# Initialize on import
init_mongodb()

# ============================================================
# PROGRESS COLLECTION HELPERS
# ============================================================

def get_student_progress(student_id: str, subject: Optional[str] = None) -> Dict[str, Any]:
    norm_sub = normalize_subject_id(subject)
    if IS_MONGO_CONNECTED and progress_col is not None:
        try:
            doc = progress_col.find_one({"student_id": student_id, "subject": norm_sub})
            if doc:
                doc.pop("_id", None)
                return doc
        except Exception as e:
            print(f"Error fetching progress for {student_id} ({norm_sub}): {e}")

    cache_key = f"{student_id}:{norm_sub}"
    if cache_key in IN_MEMORY_PROGRESS:
        return IN_MEMORY_PROGRESS[cache_key]

    new_record = {
        "student_id": student_id,
        "subject": norm_sub,
        "known_topics": [],
        "completed_topics": [],
        "in_progress_topics": [],
        "topic_progress": {},
        "query_history": [],
        "created_at": time.strftime("%Y-%m-%d %H:%M:%S"),
        "updated_at": time.strftime("%Y-%m-%d %H:%M:%S")
    }

    if IS_MONGO_CONNECTED and progress_col is not None:
        try:
            progress_col.update_one(
                {"student_id": student_id, "subject": norm_sub},
                {"$setOnInsert": new_record},
                upsert=True
            )
        except Exception as e:
            print(f"Error inserting initial progress for {student_id}: {e}")

    IN_MEMORY_PROGRESS[cache_key] = new_record
    return new_record

def update_student_progress_query(student_id: str, subject: Optional[str], query_text: str, topic: str):
    norm_sub = normalize_subject_id(subject)
    history_entry = {
        "query": query_text,
        "topic": topic,
        "timestamp": time.strftime("%Y-%m-%d %H:%M:%S")
    }

    if IS_MONGO_CONNECTED and progress_col is not None:
        try:
            progress_col.update_one(
                {"student_id": student_id, "subject": norm_sub},
                {
                    "$push": {"query_history": history_entry},
                    "$set": {"updated_at": time.strftime("%Y-%m-%d %H:%M:%S")},
                    "$setOnInsert": {
                        "known_topics": [],
                        "completed_topics": [],
                        "in_progress_topics": [],
                        "topic_progress": {},
                        "created_at": time.strftime("%Y-%m-%d %H:%M:%S")
                    }
                },
                upsert=True
            )
        except Exception as e:
            print(f"Error updating progress query history: {e}")

    cache_key = f"{student_id}:{norm_sub}"
    rec = get_student_progress(student_id, norm_sub)
    rec.setdefault("query_history", []).append(history_entry)
    rec["updated_at"] = time.strftime("%Y-%m-%d %H:%M:%S")
    IN_MEMORY_PROGRESS[cache_key] = rec

# ============================================================
# STUDENT COLLECTION & BACKWARD COMPATIBLE API
# ============================================================

def create_student(student_id: str, name: str, subject: Optional[str] = "operating_systems", email: Optional[str] = None, password: Optional[str] = None, selected_subjects: Optional[List[str]] = None) -> Dict[str, Any]:
    norm_sub = normalize_subject_id(subject)
    subs = [normalize_subject_id(s) for s in (selected_subjects or ([norm_sub] if norm_sub else []))]

    student_doc = {
        "student_id": student_id,
        "name": name,
        "email": email or f"{student_id.lower()}@pragtutor.edu",
        "password": password or "123456",
        "role": "student",
        "selected_subjects": subs,
        "subjects": subs,
        "account_status": "active",
        "status": "active",
        "access_granted": True,
        "created_at": time.strftime("%Y-%m-%d %H:%M:%S"),
        "joined_date": time.strftime("%Y-%m-%d")
    }

    if IS_MONGO_CONNECTED and students_col is not None:
        try:
            students_col.update_one(
                {"student_id": student_id},
                {"$set": student_doc},
                upsert=True
            )
        except Exception as e:
            print(f"Error creating student in Mongo: {e}")

    IN_MEMORY_STUDENTS[student_id] = student_doc
    # Ensure progress record exists
    get_student_progress(student_id, norm_sub)
    return get_student(student_id, norm_sub)

def get_student(student_id: str, subject: Optional[str] = None) -> Dict[str, Any]:
    norm_sub = normalize_subject_id(subject)
    stu_doc = None

    if IS_MONGO_CONNECTED and students_col is not None:
        try:
            stu_doc = students_col.find_one({"student_id": student_id})
            if not stu_doc:
                # Try finding by id or email
                stu_doc = students_col.find_one({"$or": [{"id": student_id}, {"email": student_id}]})
            if stu_doc:
                stu_doc.pop("_id", None)
        except Exception as e:
            print(f"Error reading student {student_id}: {e}")

    if not stu_doc:
        stu_doc = IN_MEMORY_STUDENTS.get(student_id, {
            "student_id": student_id,
            "name": f"Student {student_id}",
            "email": f"{student_id.lower()}@pragtutor.edu",
            "role": "student",
            "selected_subjects": [norm_sub],
            "subjects": [norm_sub],
            "account_status": "active",
            "status": "active",
            "access_granted": True,
            "created_at": time.strftime("%Y-%m-%d %H:%M:%S")
        })

    # Attach subject-aware progress to return payload for full backward compatibility
    progress = get_student_progress(student_id, norm_sub)
    
    # Combined dictionary containing account info + subject-specific progress
    res = dict(stu_doc)
    res["subject"] = norm_sub
    res["known_topics"] = progress.get("known_topics", [])
    res["completed_topics"] = progress.get("completed_topics", [])
    res["in_progress_topics"] = progress.get("in_progress_topics", [])
    res["topic_progress"] = progress.get("topic_progress", {})
    res["query_history"] = progress.get("query_history", [])
    return res

def mark_topic_as_learned(student_id: str, topic: str, subject: Optional[str] = None) -> Dict[str, Any]:
    if not topic:
        return get_student(student_id, subject)

    norm_sub = normalize_subject_id(subject)
    topic_clean = topic.strip()
    topic_lower = topic_clean.lower()
    topic_space = topic_lower.replace("_", " ")
    topic_underscore = topic_lower.replace(" ", "_")

    alias_list = [topic_clean, topic_lower, topic_space, topic_underscore]

    if IS_MONGO_CONNECTED and progress_col is not None:
        try:
            progress_col.update_one(
                {"student_id": student_id, "subject": norm_sub},
                {
                    "$addToSet": {
                        "known_topics": {"$each": alias_list},
                        "completed_topics": {"$each": alias_list}
                    },
                    "$set": {
                        f"topic_progress.{topic_clean}": 1.0,
                        f"topic_progress.{topic_lower}": 1.0,
                        "updated_at": time.strftime("%Y-%m-%d %H:%M:%S")
                    },
                    "$pull": {
                        "in_progress_topics": {
                            "$in": alias_list
                        }
                    },
                    "$setOnInsert": {
                        "created_at": time.strftime("%Y-%m-%d %H:%M:%S"),
                        "query_history": []
                    }
                },
                upsert=True
            )
        except Exception as e:
            print(f"Error marking topic learned in MongoDB: {e}")

    cache_key = f"{student_id}:{norm_sub}"
    rec = get_student_progress(student_id, norm_sub)
    for k in ["known_topics", "completed_topics"]:
        rec.setdefault(k, [])
        for a in alias_list:
            if a not in rec[k]:
                rec[k].append(a)

    rec.setdefault("topic_progress", {})
    rec["topic_progress"][topic_clean] = 1.0
    rec["topic_progress"][topic_lower] = 1.0

    if rec.get("in_progress_topics"):
        rec["in_progress_topics"] = [t for t in rec["in_progress_topics"] if t not in alias_list]

    rec["updated_at"] = time.strftime("%Y-%m-%d %H:%M:%S")
    IN_MEMORY_PROGRESS[cache_key] = rec

    print(f"✅ Topic '{topic_clean}' successfully marked as learned in student_progress for {student_id} ({norm_sub}).")
    return get_student(student_id, norm_sub)

def add_completed_topic(student_id: str, topic: str, subject: Optional[str] = None) -> Dict[str, Any]:
    return mark_topic_as_learned(student_id, topic, subject)

def add_in_progress_topic(student_id: str, topic: str, progress: float, subject: Optional[str] = None):
    norm_sub = normalize_subject_id(subject)
    if IS_MONGO_CONNECTED and progress_col is not None:
        try:
            progress_col.update_one(
                {"student_id": student_id, "subject": norm_sub},
                {
                    "$addToSet": {"in_progress_topics": topic},
                    "$set": {
                        f"topic_progress.{topic}": progress,
                        "updated_at": time.strftime("%Y-%m-%d %H:%M:%S")
                    },
                    "$setOnInsert": {
                        "known_topics": [],
                        "completed_topics": [],
                        "query_history": [],
                        "created_at": time.strftime("%Y-%m-%d %H:%M:%S")
                    }
                },
                upsert=True
            )
        except Exception as e:
            print(f"Error adding in-progress topic: {e}")

    rec = get_student_progress(student_id, norm_sub)
    if topic not in rec.setdefault("in_progress_topics", []):
        rec["in_progress_topics"].append(topic)
    rec.setdefault("topic_progress", {})[topic] = progress
    rec["updated_at"] = time.strftime("%Y-%m-%d %H:%M:%S")
    IN_MEMORY_PROGRESS[f"{student_id}:{norm_sub}"] = rec

def add_query_history(student_id: str, query: str, topic: str, subject: Optional[str] = None):
    update_student_progress_query(student_id, subject, query, topic)

def display_student(student_id: str, subject: Optional[str] = None):
    student = get_student(student_id, subject)
    print()
    print("=" * 70)
    print("STUDENT INFORMATION (MONGODB)")
    print("=" * 70)
    print(f"Student ID: {student.get('student_id')}")
    print(f"Name:       {student.get('name')}")
    print(f"Subject:    {student.get('subject')}")
    print("\nKnown / Completed Topics:")
    for topic in student.get("completed_topics", []):
        print(f"  ✓ {topic}")
    print("\nIn-Progress Topics:")
    for topic in student.get("in_progress_topics", []):
        prog = student.get("topic_progress", {}).get(topic, 0)
        print(f"  → {topic}: {prog * 100:.0f}%")
    print("\nQuery History:")
    for q in student.get("query_history", []):
        print(f"  • {q.get('query')} (Topic: {q.get('topic')})")

def main():
    print("=" * 70)
    print("PRAGTUTOR - STUDENT DATABASE VERIFICATION")
    print("=" * 70)
    stu = create_student(
        student_id="STU001",
        name="Student 1",
        subject="operating_systems"
    )
    print("Initial Student Record:", stu)
    mark_topic_as_learned("STU001", "process", subject="operating_systems")
    display_student("STU001", "operating_systems")

if __name__ == "__main__":
    main()