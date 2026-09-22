import chromadb
import re
import json


# ============================================================
# CONFIGURATION
# ============================================================

CHROMA_PATH = "./chroma_db"
COLLECTION_NAME = "os_knowledge_base"

OUTPUT_FILE = "topics.json"


# ============================================================
# TOPIC KEYWORDS
# ============================================================

TOPIC_PATTERNS = {

    # --------------------------------------------------------
    # UNIT 1
    # --------------------------------------------------------

    "operating system": [
        "operating system",
        "os"
    ],

    "os functions": [
        "functions of operating system",
        "operating system functions"
    ],

    "process": [
        "process",
        "process management"
    ],

    "process states": [
        "process state",
        "process states"
    ],

    "pcb": [
        "process control block",
        "pcb"
    ],

    "process creation": [
        "process creation",
        "create process"
    ],

    "process termination": [
        "process termination",
        "terminate process"
    ],

    "cpu scheduling": [
        "cpu scheduling",
        "cpu scheduler"
    ],

    "fcfs": [
        "first come first serve",
        "fcfs"
    ],

    "sjf": [
        "shortest job first",
        "sjf"
    ],

    "priority scheduling": [
        "priority scheduling"
    ],

    "round robin": [
        "round robin",
        "round-robin"
    ],


    # --------------------------------------------------------
    # UNIT 2
    # --------------------------------------------------------

    "thread": [
        "thread",
        "threads",
        "multithreading"
    ],

    "thread scheduling": [
        "thread scheduling"
    ],

    "synchronization": [
        "process synchronization",
        "synchronization"
    ],

    "critical section": [
        "critical section"
    ],

    "mutex": [
        "mutex",
        "mutex lock"
    ],

    "semaphore": [
        "semaphore",
        "semaphores"
    ],

    "producer consumer": [
        "producer consumer",
        "producer-consumer"
    ],

    "reader writer": [
        "reader writer",
        "reader-writer"
    ],

    "dining philosophers": [
        "dining philosophers",
        "dining philosopher"
    ],


    # --------------------------------------------------------
    # UNIT 3
    # --------------------------------------------------------

    "resource allocation": [
        "resource allocation",
        "resource allocation graph"
    ],

    "resource allocation graph": [
        "resource allocation graph"
    ],

    "deadlock characterization": [
        "deadlock characterization"
    ],

    "deadlock": [
        "deadlock"
    ],

    "deadlock prevention": [
        "deadlock prevention"
    ],

    "deadlock avoidance": [
        "deadlock avoidance"
    ],

    "safe state": [
        "safe state"
    ],

    "unsafe state": [
        "unsafe state"
    ],

    "safe sequence": [
        "safe sequence"
    ],

    "banker's algorithm": [
        "banker's algorithm",
        "bankers algorithm",
        "banker algorithm"
    ],

    "deadlock detection": [
        "deadlock detection"
    ],

    "deadlock recovery": [
        "deadlock recovery"
    ],

    "resource preemption": [
        "resource preemption"
    ],


    # --------------------------------------------------------
    # UNIT 4
    # --------------------------------------------------------

    "memory management": [
        "memory management"
    ],

    "contiguous memory allocation": [
        "contiguous memory allocation"
    ],

    "fixed partition": [
        "fixed partition",
        "fixed partition scheme"
    ],

    "dynamic partition": [
        "dynamic partition",
        "dynamic partitioning"
    ],

    "paging": [
        "paging"
    ],

    "page table": [
        "page table"
    ],

    "segmentation": [
        "segmentation"
    ],

    "virtual memory": [
        "virtual memory"
    ],

    "page replacement": [
        "page replacement"
    ],

    "fifo page replacement": [
        "fifo page replacement"
    ],

    "lru page replacement": [
        "lru page replacement"
    ],


    # --------------------------------------------------------
    # UNIT 5
    # --------------------------------------------------------

    "file system": [
        "file system",
        "file systems"
    ],

    "file allocation": [
        "file allocation"
    ],

    "directory": [
        "directory",
        "directories"
    ],

    "disk scheduling": [
        "disk scheduling"
    ],

    "fcfs disk scheduling": [
        "fcfs disk scheduling"
    ],

    "sstf": [
        "shortest seek time first",
        "sstf"
    ],

    "scan": [
        "scan disk scheduling"
    ],

    "c-scan": [
        "c-scan",
        "c scan"
    ],

    "raid": [
        "raid"
    ]
}


# ============================================================
# NORMALIZE TEXT
# ============================================================

def normalize(text):

    text = text.lower()

    text = re.sub(r"\s+", " ", text)

    return text.strip()


# ============================================================
# CONNECT TO CHROMADB
# ============================================================

print()
print("=" * 70)
print("PRAGTUTOR - TOPIC EXTRACTOR")
print("=" * 70)

print()
print("Connecting to ChromaDB...")

client = chromadb.PersistentClient(
    path=CHROMA_PATH
)

collection = client.get_collection(
    name=COLLECTION_NAME
)

print("Connected successfully.")

print()
print("Collection:", COLLECTION_NAME)
print("Total documents:", collection.count())


# ============================================================
# GET ALL DOCUMENTS
# ============================================================

print()
print("Reading knowledge base...")

data = collection.get(
    include=["documents", "metadatas"]
)

documents = data["documents"]
metadatas = data["metadatas"]

print("Documents loaded:", len(documents))


# ============================================================
# EXTRACT TOPICS
# ============================================================

topics = {}


for topic, patterns in TOPIC_PATTERNS.items():

    matches = []

    for index, document in enumerate(documents):

        if not document:
            continue

        text = normalize(document)

        found = False

        for pattern in patterns:

            pattern = normalize(pattern)

            if pattern in text:
                found = True
                break

        if found:

            metadata = metadatas[index]

            matches.append({
                "chunk_index": index,
                "unit": metadata.get("unit", "Unknown"),
                "page": metadata.get("page", "Unknown"),
                "source": metadata.get("source", "Unknown")
            })

    if matches:

        topics[topic] = {
            "occurrences": len(matches),
            "locations": matches
        }


# ============================================================
# SAVE TOPICS
# ============================================================

with open(
    OUTPUT_FILE,
    "w",
    encoding="utf-8"
) as file:

    json.dump(
        topics,
        file,
        indent=4,
        ensure_ascii=False
    )


# ============================================================
# DISPLAY RESULTS
# ============================================================

print()
print("=" * 70)
print("TOPIC EXTRACTION COMPLETE")
print("=" * 70)

print()
print("Topics discovered:", len(topics))

print()

for topic, information in topics.items():

    print(
        f"✓ {topic} "
        f"({information['occurrences']} chunks)"
    )


# ============================================================
# UNIT-WISE SUMMARY
# ============================================================

unit_topics = {}

for topic, information in topics.items():

    for location in information["locations"]:

        unit = location["unit"]

        if unit not in unit_topics:
            unit_topics[unit] = set()

        unit_topics[unit].add(topic)


print()
print("=" * 70)
print("UNIT-WISE TOPICS")
print("=" * 70)

for unit in sorted(unit_topics):

    print()
    print(unit)

    for topic in sorted(unit_topics[unit]):

        print("  →", topic)


# ============================================================
# FINAL INFORMATION
# ============================================================

print()
print("=" * 70)
print("OUTPUT")
print("=" * 70)

print()
print("Topics saved to:", OUTPUT_FILE)

print()
print("Next step:")
print("Create prerequisite relationships between these topics.")

print()
print("=" * 70)