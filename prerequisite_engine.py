import os
import json
import re

from student_database import get_student


# ============================================================
# CONFIGURATION
# ============================================================

COURSE_TOPICS_FILE = "data/course_topics.json"


# ============================================================
# NORMALIZE TOPIC
# ============================================================

def normalize_topic(topic):

    topic = topic.strip().lower()

    # Remove apostrophes
    topic = topic.replace("'", "")
    topic = topic.replace("’", "")

    # Remove spaces
    topic = topic.replace(" ", "")

    # Remove hyphens
    topic = topic.replace("-", "")

    # Remove underscores
    topic = topic.replace("_", "")

    return topic


# ============================================================
# DISPLAY TOPIC NAME
# ============================================================

def display_topic(topic):

    # Convert internal topic name into readable text

    topic = topic.replace("_", " ")

    # Special formatting
    replacements = {
        "pcb": "PCB",
        "cpu": "CPU",
        "fcfs": "FCFS",
        "sjf": "SJF",
        "srt": "SRT",
        "os": "OS",
        "tlb": "TLB",
        "ipc": "IPC",
        "fifo": "FIFO",
        "lru": "LRU",
        "raid": "RAID"
    }

    words = topic.split()

    formatted_words = []

    for word in words:

        if word.lower() in replacements:

            formatted_words.append(
                replacements[word.lower()]
            )

        else:

            formatted_words.append(
                word.capitalize()
            )

    return " ".join(formatted_words)


# ============================================================
# LOAD COURSE TOPICS
# ============================================================

SUBJECT_ID_MAP = {
    "os": "operating_systems",
    "operating systems": "operating_systems",
    "operating_systems": "operating_systems",
    "cn": "computer_networks",
    "computer networks": "computer_networks",
    "computer_networks": "computer_networks",
    "ds": "data_structures",
    "data structures": "data_structures",
    "data_structures": "data_structures",
    "dbms": "dbms",
    "database management systems": "dbms",
    "se": "software_engineering",
    "software engineering": "software_engineering",
    "software_engineering": "software_engineering"
}

def normalize_subject_id(subject_id):
    if not subject_id:
        return "default"
    clean = str(subject_id).lower().strip().replace("-", "_")
    clean_space = clean.replace("_", " ")
    if clean in SUBJECT_ID_MAP:
        return SUBJECT_ID_MAP[clean]
    if clean_space in SUBJECT_ID_MAP:
        return SUBJECT_ID_MAP[clean_space]
    return clean.replace(" ", "_")

def load_course_topics(subject_id=None):
    norm_sub = normalize_subject_id(subject_id)
    print()
    print(f"Loading course prerequisite graph for subject: {norm_sub}...")

    raw_data = None
    if subject_id:
        custom_prereq_file = os.path.join("data", f"prerequisites_{norm_sub}.json")
        if not os.path.exists(custom_prereq_file):
            base_dir = os.path.dirname(os.path.abspath(__file__))
            custom_prereq_file = os.path.join(base_dir, "data", f"prerequisites_{norm_sub}.json")

        if os.path.exists(custom_prereq_file):
            try:
                with open(custom_prereq_file, "r", encoding="utf-8") as file:
                    raw_data = json.load(file)
            except Exception as e:
                print(f"Error loading custom prerequisite file {custom_prereq_file}: {e}")

    # Only fallback to default COURSE_TOPICS_FILE if no subject_id is specified or subject is operating_systems/default
    if not raw_data and (not subject_id or norm_sub in ["default", "operating_systems"]):
        base_dir = os.path.dirname(os.path.abspath(__file__))
        topics_path = COURSE_TOPICS_FILE if os.path.exists(COURSE_TOPICS_FILE) else os.path.join(base_dir, COURSE_TOPICS_FILE)
        if os.path.exists(topics_path):
            try:
                with open(topics_path, "r", encoding="utf-8") as file:
                    raw_data = json.load(file)
            except Exception as e:
                print(f"Error loading {topics_path}: {e}")

    if not raw_data:
        return {"course": subject_id or "Default", "units": {}}

    if isinstance(raw_data, dict) and "units" in raw_data:
        return raw_data

    topics_map = {}

    if isinstance(raw_data, dict):
        if "topic_prerequisites" in raw_data and isinstance(raw_data["topic_prerequisites"], dict):
            for t_name, t_val in raw_data["topic_prerequisites"].items():
                topics_map[t_name] = t_val

        if "prerequisites" in raw_data:
            p_data = raw_data["prerequisites"]
            if isinstance(p_data, dict):
                for t_name, t_val in p_data.items():
                    if t_name not in topics_map:
                        topics_map[t_name] = t_val
            elif isinstance(p_data, list):
                for item in p_data:
                    if isinstance(item, dict):
                        t_name = item.get("topic") or item.get("name")
                        if t_name and t_name not in topics_map:
                            p_list = item.get("prerequisites") or item.get("prereqs") or []
                            topics_map[t_name] = p_list

        if "topics" in raw_data and isinstance(raw_data["topics"], dict):
            for t_name, t_val in raw_data["topics"].items():
                if t_name not in topics_map:
                    if isinstance(t_val, dict):
                        topics_map[t_name] = t_val.get("prerequisites", [])
                    elif isinstance(t_val, list):
                        topics_map[t_name] = t_val

        if not topics_map:
            for key, val in raw_data.items():
                if key not in ["subject", "course", "source_basis", "topic_prerequisites", "prerequisites", "topics", "units", "version"]:
                    if isinstance(val, list):
                        topics_map[key] = val
                    elif isinstance(val, dict):
                        topics_map[key] = val.get("prerequisites", [])

    formatted_topics = {}
    for top_name, prereqs in topics_map.items():
        clean_prereqs = []
        if isinstance(prereqs, list):
            for p in prereqs:
                if isinstance(p, str):
                    clean_prereqs.append(p)
                elif isinstance(p, dict):
                    p_str = p.get("topic") or p.get("name")
                    if p_str:
                        clean_prereqs.append(p_str)
        formatted_topics[top_name] = {"prerequisites": clean_prereqs}

    return {
        "course": subject_id or "Default",
        "units": {
            "custom": {
                "title": "Course Prerequisite Graph",
                "topics": formatted_topics
            }
        }
    }


# ============================================================
# BUILD COMPLETE GRAPH
# ============================================================

def build_graph(course_data):

    graph = {}

    units = course_data.get(
        "units",
        {}
    )

    for unit_name, unit_data in units.items():

        topics = unit_data.get(
            "topics",
            {}
        )

        for topic, information in topics.items():

            graph[topic] = {

                "unit": unit_name,

                "prerequisites":
                    information.get(
                        "prerequisites",
                        []
                    )
            }

    return graph


# ============================================================
# CREATE NORMALIZED TOPIC LOOKUP
# ============================================================

def create_topic_lookup(graph):

    lookup = {}

    for topic in graph:

        normalized = normalize_topic(
            topic
        )

        lookup[normalized] = topic

    return lookup


# ============================================================
# FIND CANONICAL TOPIC
# ============================================================

STOP_WORDS = {"a", "an", "the", "and", "or", "of", "in", "to", "for", "with", "on", "at", "by", "is", "what", "how", "why"}

def find_canonical_topic(
    user_topic,
    graph,
    topic_lookup
):
    if not user_topic or not graph or not topic_lookup:
        return None

    normalized = normalize_topic(
        user_topic
    )

    # --------------------------------------------------------
    # Exact normalized match
    # --------------------------------------------------------

    if normalized in topic_lookup:

        return topic_lookup[
            normalized
        ]

    # --------------------------------------------------------
    # Partial substring matching
    # --------------------------------------------------------

    for normalized_topic, canonical_topic in topic_lookup.items():

        if len(normalized) >= 3 and len(normalized_topic) >= 3:
            if (
                normalized in normalized_topic
                or
                normalized_topic in normalized
            ):

                return canonical_topic

    # --------------------------------------------------------
    # High-precision word overlap matching
    # --------------------------------------------------------

    raw_user_words = [w for w in re.findall(r'\w+', user_topic.lower()) if w not in STOP_WORDS]
    if not raw_user_words:
        return None
    user_words = set(raw_user_words)

    best_match = None
    best_score = 0.0

    for norm_t, canonical_topic in topic_lookup.items():
        cand_words = set([w for w in re.findall(r'\w+', canonical_topic.lower()) if w not in STOP_WORDS])
        if not cand_words:
            continue
        overlap = len(user_words.intersection(cand_words))
        if overlap > 0:
            coverage = overlap / max(len(user_words), len(cand_words))
            if coverage > best_score and coverage >= 0.5:
                best_score = coverage
                best_match = canonical_topic

    return best_match


# ============================================================
# GET DIRECT PREREQUISITES
# ============================================================

def get_direct_prerequisites(
    topic,
    graph
):

    if topic not in graph:

        return []

    return graph[
        topic
    ].get(
        "prerequisites",
        []
    )


# ============================================================
# GET ALL PREREQUISITES
# ============================================================

def get_all_prerequisites(
    topic,
    graph
):

    visited = set()

    result = []

    def dfs(current_topic):

        if current_topic in visited:

            return

        visited.add(
            current_topic
        )

        prerequisites = get_direct_prerequisites(
            current_topic,
            graph
        )

        for prerequisite in prerequisites:

            # First find its prerequisites
            dfs(
                prerequisite
            )

            # Then add the prerequisite itself
            if prerequisite not in result:

                result.append(
                    prerequisite
                )

    dfs(topic)

    return result


# ============================================================
# GET STUDENT COMPLETED TOPICS
# ============================================================

def get_completed_topics(
    student
):

    completed = student.get(
        "completed_topics",
        []
    )

    normalized_completed = set()

    for topic in completed:

        normalized_completed.add(
            normalize_topic(topic)
        )

    return normalized_completed


# ============================================================
# MAP NORMALIZED COMPLETED TOPICS
# TO CANONICAL TOPICS
# ============================================================

def get_known_topics(
    student,
    graph,
    topic_lookup
):

    known_topics = set()

    # ========================================================
    # STEP 1: Explicitly completed topics
    # ========================================================

    raw_topics = student.get(
        "completed_topics",
        []
    )

    for topic in raw_topics:

        normalized = normalize_topic(
            topic
        )

        if normalized in topic_lookup:

            canonical_topic = topic_lookup[
                normalized
            ]

            known_topics.add(
                canonical_topic
            )

    # ========================================================
    # STEP 2: Infer prerequisites
    #
    # If the student completed a topic,
    # we assume its prerequisites are known.
    # ========================================================

    def add_prerequisites(topic):

        if topic not in graph:
            return

        prerequisites = graph[
            topic
        ].get(
            "prerequisites",
            []
        )

        for prerequisite in prerequisites:

            if prerequisite not in known_topics:

                known_topics.add(
                    prerequisite
                )

                # Recursively infer prerequisites
                add_prerequisites(
                    prerequisite
                )

    # ========================================================
    # Apply inference to every completed topic
    # ========================================================

    completed_snapshot = list(
        known_topics
    )

    for topic in completed_snapshot:

        add_prerequisites(
            topic
        )

    return known_topics

    completed_topics = set()

    raw_topics = student.get(
        "completed_topics",
        []
    )

    for topic in raw_topics:

        normalized = normalize_topic(
            topic
        )

        if normalized in topic_lookup:

            completed_topics.add(
                topic_lookup[
                    normalized
                ]
            )

        else:

            # Keep the original topic if it isn't
            # present in our graph

            completed_topics.add(
                topic
            )

    return completed_topics


# ============================================================
# FIND MISSING PREREQUISITES
# ============================================================

def find_missing_prerequisites(
    student_id,
    target_topic,
    subject_id=None
):

    # --------------------------------------------------------
    # Load course graph
    # --------------------------------------------------------

    course_data = load_course_topics(subject_id)

    graph = build_graph(
        course_data
    )

    topic_lookup = create_topic_lookup(
        graph
    )

    # --------------------------------------------------------
    # Find canonical topic
    # --------------------------------------------------------

    canonical_topic = find_canonical_topic(
        target_topic,
        graph,
        topic_lookup
    )

    if canonical_topic is None:
        student = get_student(student_id) or {}
        comp_topics = set(student.get("completed_topics", []))
        return {
            "target_topic": target_topic,
            "all_prerequisites": set(),
            "student_completed": comp_topics,
            "missing_prerequisites": [],
            "graph": graph
        }

    # --------------------------------------------------------
    # Get student
    # --------------------------------------------------------

    student = get_student(
        student_id
    )

    if student is None:

        raise ValueError(
            f"Student '{student_id}' was not found "
            "in MongoDB."
        )

    # --------------------------------------------------------
    # Completed topics
    # --------------------------------------------------------

    known_topics = get_known_topics(
    student,
    graph,
    topic_lookup
    )

    # --------------------------------------------------------
    # Get all prerequisites
    # --------------------------------------------------------

    all_prerequisites = get_all_prerequisites(
        canonical_topic,
        graph
    )

    # --------------------------------------------------------
    # Find missing prerequisites
    # --------------------------------------------------------

    missing_prerequisites = []

    for prerequisite in all_prerequisites:

        if prerequisite not in known_topics:

            missing_prerequisites.append(
                prerequisite
            )

    # --------------------------------------------------------
    # Return result
    # --------------------------------------------------------

    return {

        "target_topic":
            canonical_topic,

        "all_prerequisites":
            all_prerequisites,

        "completed_topics":
            known_topics,

        "missing_prerequisites":
            missing_prerequisites,

        "graph":
            graph
    }


# ============================================================
# GENERATE LEARNING PATH
# ============================================================

def generate_learning_path(
    target_topic,
    missing_prerequisites,
    graph
):

    learning_path = []

    visited = set()

    # --------------------------------------------------------
    # Add prerequisites in prerequisite-first order
    # --------------------------------------------------------

    def add_topic(topic):

        if topic in visited:

            return

        visited.add(
            topic
        )

        for prerequisite in graph.get(
            topic,
            {}
        ).get(
            "prerequisites",
            []
        ):

            if prerequisite in missing_prerequisites:

                add_topic(
                    prerequisite
                )

        if (
            topic in missing_prerequisites
            and
            topic not in learning_path
        ):

            learning_path.append(
                topic
            )

    # --------------------------------------------------------
    # Process every missing prerequisite
    # --------------------------------------------------------

    for topic in missing_prerequisites:

        add_topic(
            topic
        )

    # --------------------------------------------------------
    # Target topic comes last
    # --------------------------------------------------------

    if target_topic not in learning_path:

        learning_path.append(
            target_topic
        )

    return learning_path


# ============================================================
# DISPLAY RESULT
# ============================================================

def display_result(
    result
):

    print()
    print("=" * 70)
    print("PRAGTUTOR - PREREQUISITE ANALYSIS")
    print("=" * 70)

    # --------------------------------------------------------
    # Target
    # --------------------------------------------------------

    print()
    print("Target Topic:")
    print(
        f"  {display_topic(result['target_topic'])}"
    )

    # --------------------------------------------------------
    # All prerequisites
    # --------------------------------------------------------

    print()
    print("All Required Prerequisites:")

    if result[
        "all_prerequisites"
    ]:

        for topic in result[
            "all_prerequisites"
        ]:

            print(
                f"  → {display_topic(topic)}"
            )

    else:

        print(
            "  None"
        )

    # --------------------------------------------------------
    # Completed topics
    # --------------------------------------------------------

    print()
    print("Student Completed:")

    completed = result[
        "completed_topics"
    ]

    if completed:

        for topic in sorted(
            completed
        ):

            print(
                f"  ✓ {display_topic(topic)}"
            )

    else:

        print(
            "  None"
        )

    # --------------------------------------------------------
    # Missing prerequisites
    # --------------------------------------------------------

    print()
    print("Missing Prerequisites:")

    missing = result[
        "missing_prerequisites"
    ]

    if missing:

        for topic in missing:

            print(
                f"  ⚠ {display_topic(topic)}"
            )

    else:

        print(
            "  ✓ No missing prerequisites"
        )

    # --------------------------------------------------------
    # Learning path
    # --------------------------------------------------------

    learning_path = generate_learning_path(

        result[
            "target_topic"
        ],

        result[
            "missing_prerequisites"
        ],

        result[
            "graph"
        ]
    )

    print()
    print("Recommended Learning Path:")

    for index, topic in enumerate(
        learning_path,
        start=1
    ):

        print(
            f"  {index}. {display_topic(topic)}"
        )

    print()
    print("=" * 70)


# ============================================================
# MAIN
# ============================================================

def main():

    print()
    print("=" * 70)
    print("PRAGTUTOR - PREREQUISITE ENGINE")
    print("=" * 70)

    # --------------------------------------------------------
    # Student
    # --------------------------------------------------------

    student_id = "STU001"

    # --------------------------------------------------------
    # User query/topic
    # --------------------------------------------------------

    target_topic = input(
        "\nEnter target topic: "
    )

    try:

        result = find_missing_prerequisites(

            student_id,

            target_topic

        )

        display_result(
            result
        )

    except ValueError as error:

        print()
        print(
            f"Error: {error}"
        )


# ============================================================
# ENTRY POINT
# ============================================================

if __name__ == "__main__":

    main()