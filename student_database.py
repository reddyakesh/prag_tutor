from pymongo import MongoClient


# ============================================================
# CONFIGURATION
# ============================================================

MONGO_URL = "mongodb://localhost:27017/"

DATABASE_NAME = "pragtutor"

COLLECTION_NAME = "students"


# ============================================================
# CONNECT TO MONGODB (WITH FALLBACK)
# ============================================================

IN_MEMORY_STUDENTS = {
    "STU001": {
        "student_id": "STU001",
        "name": "Student 1",
        "subject": "Operating Systems",
        "completed_topics": [],
        "in_progress_topics": [],
        "topic_progress": {},
        "query_history": []
    }
}

IS_MONGO_CONNECTED = False
client = None
db = None
students = None
print("Using in-memory student database for PragTutor.")


# ============================================================
# CREATE STUDENT
# ============================================================

def create_student(
    student_id,
    name,
    subject
):

    student = {

        "student_id": student_id,

        "name": name,

        "subject": subject,

        "completed_topics": [],

        "in_progress_topics": [],

        "topic_progress": {},

        "query_history": []

    }

    if IS_MONGO_CONNECTED and students is not None:
        try:
            result = students.insert_one(student)
        except Exception:
            pass

    IN_MEMORY_STUDENTS[student_id] = student
    return student


# ============================================================
# GET STUDENT
# ============================================================

def get_student(
    student_id
):
    if IS_MONGO_CONNECTED and students is not None:
        try:
            doc = students.find_one({"student_id": student_id})
            if doc:
                return doc
        except Exception:
            pass

    return IN_MEMORY_STUDENTS.setdefault(student_id, {
        "student_id": student_id,
        "name": f"Student {student_id}",
        "subject": "Operating Systems",
        "completed_topics": [],
        "in_progress_topics": [],
        "topic_progress": {},
        "query_history": []
    })


def mark_topic_as_learned(student_id, topic):
    if not topic:
        return get_student(student_id)

    topic_clean = topic.strip()
    topic_lower = topic_clean.lower()
    topic_space = topic_lower.replace("_", " ")
    topic_underscore = topic_lower.replace(" ", "_")

    if IS_MONGO_CONNECTED and students is not None:
        try:
            students.update_one(
                {"student_id": student_id},
                {
                    "$addToSet": {
                        "completed_topics": {
                            "$each": [topic_clean, topic_lower, topic_space, topic_underscore]
                        }
                    },
                    "$set": {
                        f"topic_progress.{topic_clean}": 1.0,
                        f"topic_progress.{topic_lower}": 1.0
                    },
                    "$pull": {
                        "in_progress_topics": {
                            "$in": [topic_clean, topic_lower, topic_space, topic_underscore]
                        }
                    }
                }
            )
        except Exception as e:
            print(f"Mongo update error: {e}")

    stu = get_student(student_id)
    if "completed_topics" not in stu or stu["completed_topics"] is None:
        stu["completed_topics"] = []
    
    for t in [topic_clean, topic_lower, topic_space, topic_underscore]:
        if t not in stu["completed_topics"]:
            stu["completed_topics"].append(t)
            
    if "topic_progress" not in stu or stu["topic_progress"] is None:
        stu["topic_progress"] = {}
    stu["topic_progress"][topic_clean] = 1.0
    stu["topic_progress"][topic_lower] = 1.0

    if "in_progress_topics" in stu and stu["in_progress_topics"]:
        stu["in_progress_topics"] = [
            t for t in stu["in_progress_topics"] 
            if t not in [topic_clean, topic_lower, topic_space, topic_underscore]
        ]

    print(f"✅ Topic '{topic_clean}' successfully marked as learned in student database for {student_id}.")
    return stu


# ============================================================
# ADD COMPLETED TOPIC
# ============================================================

def add_completed_topic(
    student_id,
    topic
):
    return mark_topic_as_learned(student_id, topic)



# ============================================================
# ADD IN-PROGRESS TOPIC
# ============================================================

def add_in_progress_topic(
    student_id,
    topic,
    progress
):

    students.update_one(

        {
            "student_id": student_id
        },

        {
            "$addToSet": {
                "in_progress_topics": topic
            },

            "$set": {
                f"topic_progress.{topic}": progress
            }
        }

    )

    print(
        f"In-progress topic updated: "
        f"{topic} -> {progress}"
    )


# ============================================================
# ADD QUERY HISTORY
# ============================================================

def add_query_history(
    student_id,
    query,
    topic
):

    history_entry = {

        "query": query,

        "topic": topic

    }

    students.update_one(

        {
            "student_id": student_id
        },

        {
            "$push": {
                "query_history": history_entry
            }
        }

    )

    print(
        "Query added to history."
    )


# ============================================================
# DISPLAY STUDENT
# ============================================================

def display_student(
    student_id
):

    student = get_student(
        student_id
    )

    if student is None:

        print(
            "Student not found."
        )

        return

    print()
    print("=" * 70)
    print("STUDENT INFORMATION")
    print("=" * 70)

    print(
        f"Student ID: "
        f"{student['student_id']}"
    )

    print(
        f"Name: "
        f"{student['name']}"
    )

    print(
        f"Subject: "
        f"{student['subject']}"
    )

    print()
    print(
        "Completed Topics:"
    )

    for topic in student[
        "completed_topics"
    ]:

        print(
            f"  ✓ {topic}"
        )

    print()
    print(
        "In-Progress Topics:"
    )

    for topic in student[
        "in_progress_topics"
    ]:

        progress = student[
            "topic_progress"
        ].get(
            topic,
            0
        )

        print(
            f"  → {topic}: "
            f"{progress * 100:.0f}%"
        )

    print()
    print(
        "Query History:"
    )

    for query in student[
        "query_history"
    ]:

        print(
            f"  • {query['query']}"
        )

        print(
            f"    Topic: "
            f"{query['topic']}"
        )


# ============================================================
# TEST
# ============================================================

def main():

    print()
    print("=" * 70)
    print("PRAGTUTOR - STUDENT DATABASE")
    print("=" * 70)

    # --------------------------------------------------------
    # Create a test student
    # --------------------------------------------------------

    create_student(

        student_id="STU001",

        name="Student 1",

        subject="Operating Systems"

    )

    # --------------------------------------------------------
    # Add completed topics
    # --------------------------------------------------------

    add_completed_topic(
        "STU001",
        "process"
    )

    add_completed_topic(
        "STU001",
        "process states"
    )

    add_completed_topic(
        "STU001",
        "pcb"
    )

    # --------------------------------------------------------
    # Add in-progress topic
    # --------------------------------------------------------

    add_in_progress_topic(

        "STU001",

        "cpu scheduling",

        0.4

    )

    # --------------------------------------------------------
    # Add query history
    # --------------------------------------------------------

    add_query_history(

        "STU001",

        "What is a process?",

        "process"

    )

    add_query_history(

        "STU001",

        "Explain CPU scheduling",

        "cpu scheduling"

    )

    # --------------------------------------------------------
    # Display student
    # --------------------------------------------------------

    display_student(
        "STU001"
    )


# ============================================================
# PROGRAM ENTRY POINT
# ============================================================

if __name__ == "__main__":

    main()