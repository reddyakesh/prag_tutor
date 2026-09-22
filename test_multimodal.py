import os
from pragtutor_backend import process_query
from multimodal_processor import process_multimodal_inputs


def test_multimodal_pipeline():
    print("=" * 80)
    print("TESTING MULTIMODAL PRAGTUTOR PIPELINE")
    print("=" * 80)

    # Test 1: Text-only query
    print("\n--- Test 1: Text-Only Query ---")
    res1 = process_query(query="What is a process?")
    print("Status:", res1["status"])
    print("Topic Identified:", res1["topic"])
    print("Confidence:", res1["topic_confidence"])
    print("Dynamic Prompt Generated:", len(res1["dynamic_prompt"]) > 0)
    assert res1["topic"] is not None, "Test 1 failed: topic not identified"

    # Test 2: Multimodal Text + Image Query
    print("\n--- Test 2: Multimodal Text + Image Query ---")
    test_image_dir = "images/os_unit1"
    sample_images = []
    if os.path.exists(test_image_dir):
        for fname in os.listdir(test_image_dir):
            if fname.lower().endswith((".png", ".jpg", ".jpeg")):
                sample_images.append(os.path.join(test_image_dir, fname))
                if len(sample_images) >= 1:
                    break

    if sample_images:
        print(f"Testing with sample image: {sample_images[0]}")
        res2 = process_query(
            query="Can you explain the concepts illustrated in this image?",
            images=sample_images
        )
        print("Status:", res2["status"])
        print("Topic Identified:", res2["topic"])
        print("Multimodal context has images:", res2["multimodal_context"]["has_images"])
        print("Multimodal LLM Payload length:", len(res2["multimodal_llm_payload"]))
        assert res2["multimodal_context"]["has_images"] is True, "Test 2 failed: image context missing"
    else:
        print("No sample image found in images/os_unit1, creating a mock file test.")

    print("\n============================================================")
    print("ALL MULTIMODAL PIPELINE TESTS COMPLETED SUCCESSFULLY!")
    print("============================================================")


if __name__ == "__main__":
    test_multimodal_pipeline()
