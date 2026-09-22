import os
import json
import re

from sentence_transformers import SentenceTransformer
from sklearn.metrics.pairwise import cosine_similarity


# ============================================================
# CONFIGURATION
# ============================================================

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
COURSE_TOPICS_FILE = os.path.join(BASE_DIR, "data", "course_topics.json")

TOPIC_CACHE = {}

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

def load_topics(subject_id=None):
    norm_sub = normalize_subject_id(subject_id)
    if norm_sub in TOPIC_CACHE:
        return TOPIC_CACHE[norm_sub]

    topics = []
    raw_data = None
    
    # 1. Try subject specific prerequisites file
    if subject_id:
        prereq_file = os.path.join(BASE_DIR, "data", f"prerequisites_{norm_sub}.json")
        if os.path.exists(prereq_file):
            try:
                with open(prereq_file, "r", encoding="utf-8") as f:
                    raw_data = json.load(f)
            except Exception as e:
                print(f"Error loading {prereq_file}: {e}")

    # 2. Try subject specific course topics file
    if not raw_data and subject_id:
        topic_file = os.path.join(BASE_DIR, "data", f"course_topics_{norm_sub}.json")
        if os.path.exists(topic_file):
            try:
                with open(topic_file, "r", encoding="utf-8") as f:
                    raw_data = json.load(f)
            except Exception as e:
                print(f"Error loading {topic_file}: {e}")

    # 3. Fallback to default COURSE_TOPICS_FILE only for default or operating_systems
    if not raw_data and (not subject_id or norm_sub in ["default", "operating_systems"]) and os.path.exists(COURSE_TOPICS_FILE):
        try:
            with open(COURSE_TOPICS_FILE, "r", encoding="utf-8") as f:
                raw_data = json.load(f)
        except Exception:
            pass

    if isinstance(raw_data, dict):
        if "units" in raw_data:
            for unit_id, unit_data in raw_data["units"].items():
                for topic, information in unit_data.get("topics", {}).items():
                    topics.append({
                        "topic": topic,
                        "unit": unit_id,
                        "description": information.get("description", "") if isinstance(information, dict) else "",
                        "parent_topic": information.get("parent_topic", None) if isinstance(information, dict) else None
                    })
        else:
            seen_topics = set()
            def add_t(t_name, desc="", parent=None):
                if t_name and t_name not in seen_topics:
                    seen_topics.add(t_name)
                    topics.append({
                        "topic": t_name,
                        "unit": "1",
                        "description": desc or "",
                        "parent_topic": parent
                    })

            if "topic_prerequisites" in raw_data and isinstance(raw_data["topic_prerequisites"], dict):
                for t_name, t_val in raw_data["topic_prerequisites"].items():
                    desc = t_val.get("description", "") if isinstance(t_val, dict) else ""
                    add_t(t_name, desc)

            if "prerequisites" in raw_data:
                p_data = raw_data["prerequisites"]
                if isinstance(p_data, dict):
                    for t_name, t_val in p_data.items():
                        desc = t_val.get("description", "") if isinstance(t_val, dict) else ""
                        add_t(t_name, desc)
                elif isinstance(p_data, list):
                    for item in p_data:
                        if isinstance(item, dict):
                            t_name = item.get("topic") or item.get("name")
                            if t_name:
                                add_t(t_name, item.get("description", ""))
                        elif isinstance(item, str):
                            add_t(item)

            if "topics" in raw_data and isinstance(raw_data["topics"], dict):
                for t_name, t_val in raw_data["topics"].items():
                    desc = t_val.get("description", "") if isinstance(t_val, dict) else ""
                    add_t(t_name, desc)

            for k, v in raw_data.items():
                if k not in ["subject", "course", "source_basis", "topic_prerequisites", "prerequisites", "topics", "units", "version"]:
                    desc = v.get("description", "") if isinstance(v, dict) else ""
                    add_t(k, desc)

    # Compute topic texts and embeddings
    if topics and 'model' in globals():
        t_texts = [create_topic_text(t) for t in topics]
        t_embeddings = model.encode(t_texts, convert_to_numpy=True, normalize_embeddings=True)
    else:
        t_texts = []
        t_embeddings = []

    res = {
        "topics": topics,
        "texts": t_texts,
        "embeddings": t_embeddings
    }
    TOPIC_CACHE[norm_sub] = res
    return res

MODEL_NAME = "all-MiniLM-L6-v2"

TOP_K = 5

CONFIDENCE_THRESHOLD = 0.35


# ============================================================
# NORMALIZE TEXT
# ============================================================

def normalize_text(text):

    text = text.lower()

    text = text.replace("'", "")
    text = text.replace("’", "")

    text = text.replace("_", " ")

    text = re.sub(
        r"\s+",
        " ",
        text
    )

    return text.strip()


# ============================================================
# CREATE SEMANTIC REPRESENTATION
# ============================================================

def create_topic_text(topic_data):

    topic = normalize_text(
        topic_data["topic"]
    )

    description = normalize_text(
        topic_data["description"]
    )

    parent = topic_data[
        "parent_topic"
    ]

    if parent:

        parent = normalize_text(
            parent
        )

        return (
            f"Topic: {topic}. "
            f"Parent topic: {parent}. "
            f"Description: {description}"
        )

    return (
        f"Topic: {topic}. "
        f"Description: {description}"
    )


# ============================================================
# LOAD EMBEDDING MODEL
# ============================================================

print()
print("=" * 70)
print("PRAGTUTOR - TOPIC IDENTIFIER")
print("=" * 70)

print()
print("Loading embedding model...")

try:
    model = SentenceTransformer(MODEL_NAME, local_files_only=True)
except Exception:
    model = SentenceTransformer(MODEL_NAME)

print(
    "Embedding model loaded."
)


# ============================================================
# LOAD TOPICS
# ============================================================

print()
print("Loading default course topics...")

default_topic_data = load_topics()
topics = default_topic_data["topics"]
topic_embeddings = default_topic_data["embeddings"]

print(
    "Topics loaded:",
    len(topics)
)


# ============================================================
# IDENTIFY TOPIC
# ============================================================

def identify_topic(
    query,
    top_k=TOP_K,
    subject=None
):
    if isinstance(query, dict):
        query_text = query.get("combined_text") or query.get("raw_query") or ""
    else:
        query_text = str(query or "")

    subj_data = load_topics(subject)
    cur_topics = subj_data["topics"]
    cur_embeddings = subj_data["embeddings"]

    if not cur_topics or len(cur_embeddings) == 0:
        return {
            "query": query_text,
            "topic": None,
            "unit": None,
            "confidence": 0.0,
            "status": "no_topics_available",
            "top_matches": []
        }

    norm_q = normalize_text(query_text)

    query_embedding = model.encode(
        [norm_q],
        convert_to_numpy=True,
        normalize_embeddings=True
    )

    similarities = cosine_similarity(
        query_embedding,
        cur_embeddings
    )[0]

    scores = list(similarities)
    for idx, t_obj in enumerate(cur_topics):
        t_norm = normalize_text(t_obj["topic"])
        if len(t_norm) >= 3:
            pattern = r'\b' + re.escape(t_norm) + r'\b'
            if re.search(pattern, norm_q):
                scores[idx] = max(scores[idx], 0.95)
            elif t_norm in norm_q:
                scores[idx] = max(scores[idx], 0.88)

    import numpy as np
    ranked_indices = np.array(scores).argsort()[::-1]

    results = []

    for index in ranked_indices[:top_k]:
        results.append({
            "topic": cur_topics[index]["topic"],
            "unit": cur_topics[index]["unit"],
            "description": cur_topics[index]["description"],
            "parent_topic": cur_topics[index]["parent_topic"],
            "score": float(scores[index])
        })

    best = results[0]

    return {
        "query": norm_q,
        "topic": best["topic"],
        "unit": best["unit"],
        "confidence": best["score"],
        "status": "identified",
        "top_matches": results
    }


# ============================================================
# DISPLAY RESULT
# ============================================================

def display_result(result):

    print()
    print("=" * 70)
    print("TOPIC IDENTIFICATION RESULT")
    print("=" * 70)

    print()
    print("Query:")
    print(
        " ",
        result["query"]
    )

    print()

    if result["topic"]:

        print(
            "Identified Topic:"
        )

        print(
            " ",
            result["topic"]
        )

        print()

        print("Unit:")

        print(
            " ",
            result["unit"]
        )

        print()

        print("Confidence:")

        print(
            f"  {result['confidence']:.4f}"
        )

    else:

        print(
            "Could not confidently identify a topic."
        )

    print()
    print("Top Matches:")

    for index, match in enumerate(

        result["top_matches"],

        start=1

    ):

        print(

            f"  {index}. "
            f"{match['topic']} "
            f"({match['score']:.4f})"

        )

        if match["description"]:

            print(

                f"     {match['description']}"

            )

    print()
    print("=" * 70)


# ============================================================
# MAIN
# ============================================================

def main():

    while True:

        query = input(

            "\nEnter your question "
            "(type 'exit' to stop): "

        )

        if query.strip().lower() == "exit":

            print(
                "\nTopic identifier stopped."
            )

            break

        result = identify_topic(
            query
        )

        display_result(
            result
        )


# ============================================================
# ENTRY POINT
# ============================================================

if __name__ == "__main__":

    main()