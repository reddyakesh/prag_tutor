import os
import json

from dynamic_prompt import build_dynamic_prompt, build_multimodal_llm_payload
from llm_service import generate_response
from multimodal_processor import process_multimodal_inputs
from topic_identifier import identify_topic

from prerequisite_engine import (
    find_missing_prerequisites,
    generate_learning_path
)

from retrieve import retrieve


# ============================================================
# CONFIGURATION
# ============================================================

STUDENT_ID = "STU001"

TOP_K = 5



# ============================================================
# ============================================================
# CHECK KB AVAILABILITY
# ============================================================

def check_subject_kb_availability(subject):
    from topic_identifier import normalize_subject_id
    norm_sub = normalize_subject_id(subject)
    status_file = os.path.join(os.path.dirname(os.path.abspath(__file__)), "data", "kb_status.json")
    if os.path.exists(status_file):
        try:
            with open(status_file, "r", encoding="utf-8") as f:
                kb_data = json.load(f)
                if norm_sub in kb_data or subject in kb_data:
                    sub_data = kb_data.get(norm_sub) or kb_data.get(subject) or {}
                    status_val = str(sub_data.get("status") or sub_data.get("kb_status") or "").lower()
                    pdf_uploaded = sub_data.get("pdf_uploaded", False)
                    if status_val == "ready" and pdf_uploaded:
                        return True
                    else:
                        return False
        except Exception:
            pass

    # Fallback check against ChromaDB collection count directly
    try:
        import chromadb
        client = chromadb.PersistentClient(path=os.path.join(os.path.dirname(os.path.abspath(__file__)), "chroma_db"))
        col_names = [f"{norm_sub}_knowledge_base", f"{subject}_knowledge_base"]
        if norm_sub in ["operating_systems", "os"]:
            col_names.append("os_knowledge_base")
        for col_name in set(col_names):
            try:
                c = client.get_collection(col_name)
                if c and c.count() > 0:
                    return True
            except Exception:
                pass
    except Exception:
        pass

    return False


# ============================================================
# PROCESS QUERY
# ============================================================

def find_relevant_topic_images(topic=None, query=None, subject="operating_systems"):
    images_found = []
    root_dir = os.path.dirname(os.path.abspath(__file__))
    
    q_str = str(query or "").lower()
    t_str = str(topic or "").lower()
    
    requested_image = any(w in q_str for w in ["image", "img", "diagram", "figure", "picture", "photo", "flowchart", "show", "draw", "visualize"])

    diagram_map = [
        {
            "keys": ["process_state", "process state", "state transition", "process states"],
            "rel_path": "images/os_unit1/page_3_img_3.jpeg",
            "caption": "Process State Transition Diagram (New, Running, Waiting, Ready, Terminated)"
        },
        {
            "keys": ["pcb", "process control block", "task control block"],
            "rel_path": "images/os_unit1/page_10_img_1.jpeg",
            "caption": "Process Control Block (PCB) Structure & Registers"
        },
        {
            "keys": ["context_switch", "context switching", "cpu switch"],
            "rel_path": "images/os_unit1/page_13_img_1.jpeg",
            "caption": "Diagram of CPU Context Switch between Processes"
        },
        {
            "keys": ["process_creation", "process tree", "parent process", "fork"],
            "rel_path": "images/os_unit1/page_20_img_2.jpeg",
            "caption": "Process Hierarchy & Tree Structure Diagram"
        },
        {
            "keys": ["queue", "scheduling queue", "ready queue", "device queue"],
            "rel_path": "images/os_unit1/page_25_img_1.jpeg",
            "caption": "Process Scheduling Queues (Job Queue, Ready Queue, Device Queue)"
        },
        {
            "keys": ["cpu_scheduling", "cpu scheduler", "preemptive", "non-preemptive", "scheduling algorithm"],
            "rel_path": "images/os_unit1/page_28_img_1.jpeg",
            "caption": "CPU Scheduling Architecture & Dispatcher Workflow"
        },
        {
            "keys": ["round_robin", "gantt chart", "turnaround time", "waiting time"],
            "rel_path": "images/os_unit1/page_34_img_1.jpeg",
            "caption": "CPU Scheduling Criteria & Execution Timeline Diagram"
        }
    ]

    for item in diagram_map:
        matches = any(k in t_str or k in q_str for k in item["keys"])
        if matches:
            full_p = os.path.join(root_dir, item["rel_path"])
            if os.path.exists(full_p):
                images_found.append({
                    "url": f"/images/os_unit1/{os.path.basename(full_p)}",
                    "caption": item["caption"],
                    "is_requested": requested_image
                })

    if requested_image and not images_found:
        default_p = os.path.join(root_dir, "images/os_unit1/page_3_img_3.jpeg")
        if os.path.exists(default_p):
            images_found.append({
                "url": "/images/os_unit1/page_3_img_3.jpeg",
                "caption": f"Course Diagram Reference for {(t_str or 'Operating Systems').replace('_', ' ').title()}",
                "is_requested": True
            })

    return images_found


def process_query(
    query=None,
    images=None,
    student_id=STUDENT_ID,
    subject="operating_systems",
    level="beginner"
):
    print()
    print("=" * 80)
    print(f"PRAGTUTOR MULTIMODAL BACKEND (Subject: {subject}, Level: {level})")
    print("=" * 80)

    # Step 0: Check KB Availability (DO NOT CALL RETRIEVE/LLM IF UNAVAILABLE)
    if not check_subject_kb_availability(subject):
        print(f"⚠️ Knowledge base not available for subject: {subject}")
        return {
            "status": "kb_unavailable",
            "subject": subject,
            "message": "PDFs have not been uploaded by your teachers for this subject yet."
        }

    # Step 0.5: Multimodal Processing
    mm_context = process_multimodal_inputs(query=query, images=images)

    print()
    print("User Text Query:", mm_context["raw_query"] if mm_context["raw_query"] else "[None provided]")
    if mm_context["has_images"]:
        print(f"Attached Images: {mm_context['num_images']} image(s)")
        if mm_context["ocr_text"]:
            print("Extracted OCR Text Preview:", mm_context["ocr_text"][:200] + "...")

    # ========================================================
    # STEP 1: TOPIC IDENTIFICATION
    # ========================================================

    print()
    print("STEP 1: Topic Identification")

    topic_result = identify_topic(
        mm_context,
        subject=subject
    )

    target_topic = topic_result.get("topic")
    if not target_topic:
        target_topic = "General Concept"

    print(
        "Identified Topic:",
        target_topic
    )

    print(
        "Confidence:",
        f"{topic_result.get('confidence', 0):.4f}"
    )

    # ========================================================
    # STEP 2: PREREQUISITE ANALYSIS
    # ========================================================

    print()
    print("STEP 2: Prerequisite Analysis")

    prerequisite_result = (
        find_missing_prerequisites(

            student_id,

            target_topic,

            subject_id=subject

        )
    )

    missing_prerequisites = (
        prerequisite_result[
            "missing_prerequisites"
        ]
    )

    graph = (
        prerequisite_result[
            "graph"
        ]
    )

    # ========================================================
    # STEP 3: PERSONALIZED LEARNING PATH
    # ========================================================

    print()
    print(
        "STEP 3: Personalized Learning Path"
    )

    learning_path = generate_learning_path(

        target_topic,

        missing_prerequisites,

        graph

    )

    for index, topic in enumerate(

        learning_path,

        start=1

    ):

        print(
            f"{index}. {topic}"
        )

    # ========================================================
    # STEP 4: RAG RETRIEVAL & DIAGRAM MATCHING
    # ========================================================

    print()
    print("STEP 4: RAG Retrieval")

    retrieved_content = retrieve(
        mm_context,
        top_k=TOP_K,
        subject=subject
    )

    print(
        "Retrieved chunks:",
        len(retrieved_content)
    )

    retrieved_images = find_relevant_topic_images(
        topic=target_topic,
        query=mm_context.get("raw_query") or query,
        subject=subject
    )

    # ========================================================
    # STEP 5: BUILD TUTOR CONTEXT
    # ========================================================

    print()
    print("STEP 5: Building Tutor Context")

    student_completed = list(
        prerequisite_result.get(
            "completed_topics",
            prerequisite_result.get("student_completed", [])
        )
    )

    all_prerequisites = list(
        prerequisite_result.get(
            "all_prerequisites",
            []
        )
    )

    # ========================================================
    # STEP 6: BUILD DYNAMIC PROMPT & LLM PAYLOAD
    # ========================================================

    print()
    print("STEP 6: Building Dynamic Prompt & Multimodal Payload")

    dynamic_prompt = build_dynamic_prompt(

        query=mm_context,

        topic=target_topic,

        topic_confidence=topic_result[
            "confidence"
        ],

        student_completed=
            student_completed,

        missing_prerequisites=
            missing_prerequisites,

        learning_path=
            learning_path,

        retrieved_content=
            retrieved_content,

        multimodal_context=
            mm_context,

        subject=
            subject,

        level=
            level
    )

    multimodal_llm_payload = build_multimodal_llm_payload(
        dynamic_prompt,
        mm_context
    )

    # Generate response via LLM service
    llm_response = generate_response(
        dynamic_prompt,
        multimodal_payload=multimodal_llm_payload,
        multimodal_context=mm_context
    )

    # Append retrieved diagram markdown if student requested an image/diagram
    if retrieved_images and llm_response and not llm_response.startswith("["):
        img_md_blocks = []
        for img in retrieved_images:
            img_md_blocks.append(f"\n\n![{img['caption']}]({img['url']})\n*Figure: {img['caption']}*")
        
        # Append images if requested or relevant
        q_lower = str(query or "").lower()
        if any(w in q_lower for w in ["image", "img", "diagram", "figure", "picture", "show", "draw", "visualize"]) or len(retrieved_images) > 0:
            llm_response = llm_response + "\n\n### 🖼️ Course Diagram & Visual Reference" + "".join(img_md_blocks)

    # ========================================================
    # BUILD FINAL CONTEXT
    # ========================================================

    context = {

        "status":
            "success",

        "query":
            query,

        "level":
            level,

        "multimodal_context":
            mm_context,

        "topic":
            target_topic,

        "topic_confidence":
            topic_result[
                "confidence"
            ],

        "all_prerequisites":
            all_prerequisites,

        "student_completed":
            student_completed,

        "missing_prerequisites":
            missing_prerequisites,

        "learning_path":
            learning_path,

        "retrieved_content":
            retrieved_content,

        "retrieved_images":
            retrieved_images,

        "dynamic_prompt":
            dynamic_prompt,

        "multimodal_llm_payload":
            multimodal_llm_payload,

        "llm_response":
            llm_response
    }

    # ========================================================
    # RETURN
    # ========================================================

    return context


# ============================================================
# DISPLAY CONTEXT
# ============================================================

def display_context(
    context
):

    print()
    print("=" * 80)
    print("PRAGTUTOR BACKEND SUMMARY")
    print("=" * 80)

    print()
    print("Query:", context["query"])

    mm_ctx = context.get("multimodal_context", {})
    if mm_ctx.get("has_images"):
        print(f"Attached Images: {mm_ctx['num_images']} image(s)")

    print("Identified Topic:", context["topic"])
    print(f"Topic Confidence: {context['topic_confidence']:.4f}")

    if context.get("missing_prerequisites"):
        print("Missing Prerequisites:", context["missing_prerequisites"])
    if context.get("learning_path"):
        print("Personalized Learning Path:", context["learning_path"])

    print()
    print("=" * 80)
    print("🎓 TUTOR ANSWER (LLM GENERATED RESPONSE)")
    print("=" * 80)
    print()
    print(context.get("llm_response"))
    print()
    print("=" * 80)


# ============================================================
# MAIN
# ============================================================

def main():

    print("=" * 80)
    print("PRAGTUTOR MULTIMODAL BACKEND INTERACTIVE TERMINAL")
    print("=" * 80)
    print("Instructions:")
    print("  - Type your question directly (e.g. 'What is a process control block?')")
    print("  - To attach an image, add '+ <image_path>' (e.g. 'Explain this + images/sample.jpg')")
    print("  - Or type an image path directly to ask a visual question")
    print("  - Type 'exit' to quit")
    print("=" * 80)

    while True:

        user_input = input(
            "\nEnter question (or 'exit'): "
        ).strip()

        if user_input.lower() == "exit":

            print(
                "\nPragTutor backend stopped."
            )

            break

        if not user_input:

            print(
                "Please enter a question or image path."
            )

            continue

        query = user_input
        images = None

        # Check if user passed '+' for image path (e.g. "What is this? + image.jpg")
        if "+" in user_input:
            parts = user_input.split("+", 1)
            query = parts[0].strip()
            img_candidate = parts[1].strip()
            if img_candidate:
                images = [img_candidate]
        # Check if user input is an image file path directly
        elif os.path.exists(user_input):
            query = "Explain the concepts shown in this attached image."
            images = [user_input]

        try:

            context = process_query(
                query=query,
                images=images
            )

            if context["topic"] is None:

                print()
                print(
                    "Could not identify "
                    "the topic confidently."
                )

                continue

            display_context(
                context
            )

        except Exception as error:

            print()
            print(
                "ERROR:",
                error
            )


# ============================================================
# ENTRY POINT
# ============================================================

if __name__ == "__main__":

    main()