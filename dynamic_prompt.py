# ============================================================
# PRAGTUTOR - DYNAMIC PROMPT BUILDER
# ============================================================


# ============================================================
# FORMAT RETRIEVED KNOWLEDGE
# ============================================================

def format_retrieved_content(
    retrieved_content
):

    if not retrieved_content:

        return "No course material was retrieved."

    formatted = []

    for index, result in enumerate(
        retrieved_content,
        start=1
    ):

        chunk = f"""
--- Retrieved Source {index} ---

Unit: {result['unit']}
Page: {result['page']}
Source: {result['source']}

Content:
{result['content']}
"""

        formatted.append(
            chunk
        )

    return "\n".join(
        formatted
    )


# ============================================================
# FORMAT TOPICS
# ============================================================

def format_topic_list(
    topics
):

    if not topics:

        return "None"

    return "\n".join(
        f"- {topic}"
        for topic in topics
    )


# ============================================================
# BUILD DYNAMIC PROMPT
# ============================================================

# ============================================================
# BUILD DYNAMIC PROMPT
# ============================================================

def build_dynamic_prompt(
    query,
    topic,
    topic_confidence,
    student_completed,
    missing_prerequisites,
    learning_path,
    retrieved_content,
    multimodal_context=None,
    subject=None,
    level="beginner"
):

    if isinstance(query, dict):
        raw_query_text = query.get("raw_query") or query.get("combined_text") or ""
        multimodal_context = query
    else:
        raw_query_text = str(query or "")

    subj_display = subject.replace("_", " ").title() if isinstance(subject, str) and subject else "Operating Systems"

    visual_section = ""
    if multimodal_context and multimodal_context.get("has_images"):
        ocr_text = multimodal_context.get("ocr_text", "")
        num_imgs = multimodal_context.get("num_images", 0)
        visual_section = f"""
============================================================
MULTIMODAL ATTACHMENTS & VISUAL CONTEXT
============================================================

Number of attached images: {num_imgs}
Extracted Text / OCR from attached images:
{ocr_text if ocr_text else "No readable text detected in images (visual inspection required)."}
"""

    knowledge_context = (
        format_retrieved_content(
            retrieved_content
        )
    )

    completed_context = (
        format_topic_list(
            student_completed
        )
    )

    missing_context = (
        format_topic_list(
            missing_prerequisites
        )
    )

    learning_path_context = (
        format_topic_list(
            learning_path
        )
    )

    # Determine Student Level Directives
    target_level = str(level or "beginner").lower().strip()
    if target_level in ["beginner", "beg"]:
        level_label = "BEGINNER LEVEL"
        level_instruction = (
            "The student selected the BEGINNER explanation level. "
            "Explain concepts using simple, beginner-friendly language, real-world analogies, step-by-step intuition, "
            "and foundational explanations. Avoid overwhelming the student with dense low-level code or complex math without explaining every step."
        )
    elif target_level in ["advance", "advanced", "adv"]:
        level_label = "ADVANCE / ADVANCED LEVEL"
        level_instruction = (
            "The student selected the ADVANCE explanation level. "
            "Provide an in-depth, highly technical, and rigorous explanation. Include low-level system mechanics, performance tradeoffs, "
            "architectural details, edge cases, and deep theoretical concepts."
        )
    else:
        level_label = "INTERMEDIATE LEVEL"
        level_instruction = (
            "The student selected the INTERMEDIATE explanation level. "
            "Provide a balanced explanation appropriate for an undergraduate computer science student. "
            "Combine core theoretical concepts, practical application examples, standard technical terminology, and structured code/pseudocode logic."
        )

    # ========================================================
    # DYNAMIC PROMPT
    # ========================================================

    prompt = f"""
You are PragTutor, an intelligent tutoring system
for {subj_display}.

Your goal is to provide adaptive, personalized,
multimodal, and structured explanations based on the student's
current knowledge and provided images/questions.

============================================================
STUDENT QUERY & LEVEL SELECTION
============================================================

Query: {raw_query_text}
Selected Explanation Level: {level_label}
Level Directive: {level_instruction}
{visual_section}

============================================================
IDENTIFIED TOPIC
============================================================

{topic}

Topic identification confidence:
{topic_confidence:.4f}


============================================================
STUDENT'S KNOWN TOPICS
============================================================

{completed_context}


============================================================
MISSING PREREQUISITES
============================================================

{missing_context}


============================================================
PERSONALIZED LEARNING PATH
============================================================

{learning_path_context}


============================================================
RETRIEVED COURSE MATERIAL
============================================================

{knowledge_context}


============================================================
TEACHING INSTRUCTIONS
============================================================

1. Answer the student's question using the retrieved
   course material and any attached image diagrams/screenshots
   as primary sources.

2. Adhere strictly to the requested explanation level ({level_label}):
   {level_instruction}

3. Respect the student's current knowledge state.

4. Do not assume that the student knows a prerequisite
   that is listed as missing.

5. If prerequisites are missing, teach the required
   prerequisite concepts before explaining the target
   concept.

6. Follow the personalized learning path when explaining
   the concepts.

7. Move from foundational concepts to the target concept
   in a logical sequence.

8. Clearly distinguish prerequisite explanations from the
   explanation of the target topic.

9. Give examples when the retrieved course material or
   provided diagrams support them.

10. Do not invent facts that are not supported by the
    retrieved course material.

11. If the retrieved material does not contain enough
    information to answer something, explicitly state
    that the available course material does not provide
    enough information.

12. Do not mention internal implementation details such as
    ChromaDB, MongoDB, embeddings, prerequisite graphs,
    or prompt engineering to the student.

13. The final response should feel like a personalized
    tutor explanation, not a database result.


============================================================
FINAL RESPONSE
============================================================

Provide a clear, structured, level-appropriate explanation for the student.
"""

    return prompt


# ============================================================
# BUILD MULTIMODAL LLM PAYLOAD
# ============================================================

def build_multimodal_llm_payload(
    prompt,
    multimodal_context=None
):
    """
    Builds structured message content blocks compatible with
    OpenAI Vision APIs (e.g. GPT-4o / GPT-5.5).
    """
    if not multimodal_context or not multimodal_context.get("has_images"):
        return prompt

    content_blocks = [
        {
            "type": "text",
            "text": prompt
        }
    ]

    image_payloads = multimodal_context.get("llm_image_payloads", [])
    content_blocks.extend(image_payloads)

    return [
        {
            "role": "user",
            "content": content_blocks
        }
    ]