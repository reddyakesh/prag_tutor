import base64
import mimetypes
import os
import re
from typing import Any, Dict, List, Optional, Union


# ============================================================
# MULTIMODAL IMAGE PROCESSOR
# ============================================================

def encode_image_to_base64(image_path: str) -> Optional[str]:
    """Reads a local image file and converts it to a base64 Data URI."""
    if not os.path.exists(image_path):
        return None

    mime_type, _ = mimetypes.guess_type(image_path)
    if not mime_type:
        ext = os.path.splitext(image_path)[1].lower()
        mime_map = {
            ".jpg": "image/jpeg",
            ".jpeg": "image/jpeg",
            ".png": "image/png",
            ".webp": "image/webp",
            ".gif": "image/gif",
            ".bmp": "image/bmp",
        }
        mime_type = mime_map.get(ext, "image/jpeg")

    with open(image_path, "rb") as image_file:
        encoded_string = base64.b64encode(image_file.read()).decode("utf-8")

    return f"data:{mime_type};base64,{encoded_string}"


def extract_ocr_text_from_image(image_input: Union[str, bytes]) -> str:
    """
    Extracts text from an image using available OCR packages.
    Falls back gracefully if OCR packages (pytesseract/easyocr) are not installed.
    """
    extracted_text = ""

    # Attempt 1: pytesseract
    try:
        import pytesseract
        from PIL import Image

        if isinstance(image_input, str) and os.path.exists(image_input):
            img = Image.open(image_input)
            extracted_text = pytesseract.image_to_string(img)
        elif isinstance(image_input, bytes):
            import io
            img = Image.open(io.BytesIO(image_input))
            extracted_text = pytesseract.image_to_string(img)
    except Exception:
        pass

    if extracted_text.strip():
        return extracted_text.strip()

    # Attempt 2: easyocr
    try:
        import easyocr
        reader = easyocr.Reader(['en'], gpu=False)
        if isinstance(image_input, str) and os.path.exists(image_input):
            results = reader.readtext(image_input, detail=0)
            extracted_text = " ".join(results)
    except Exception:
        pass

    return extracted_text.strip()


def extract_image_metadata(image_path: str) -> Dict[str, Any]:
    """Extracts basic image metadata (dimensions, file size, format)."""
    meta = {
        "filename": os.path.basename(image_path) if isinstance(image_path, str) else "image",
        "file_size": 0,
        "format": "Unknown",
        "dimensions": None
    }

    if isinstance(image_path, str) and os.path.exists(image_path):
        meta["file_size"] = os.path.getsize(image_path)
        meta["format"] = os.path.splitext(image_path)[1].lstrip(".").upper()

    try:
        from PIL import Image
        if isinstance(image_path, str) and os.path.exists(image_path):
            with Image.open(image_path) as img:
                meta["dimensions"] = img.size
                meta["format"] = img.format
    except Exception:
        pass

    return meta


def process_multimodal_inputs(
    query: Optional[str] = None,
    images: Optional[Union[str, List[str], List[Dict[str, Any]]]] = None
) -> Dict[str, Any]:
    """
    Processes text query and image inputs into a structured multimodal context.

    Parameters:
        query  -> Optional user text question.
        images -> Image path, base64 data URI, image URL, or list of them.

    Returns:
        Structured multimodal context dict with:
        - raw_query
        - combined_text (text query + OCR text)
        - image_details (list of metadata, OCR text, base64 data URIs)
        - llm_vision_payload (OpenAI API message format for vision models)
    """
    if images is None:
        images_list = []
    elif isinstance(images, (str, dict)):
        images_list = [images]
    else:
        images_list = list(images)

    text_query = (query or "").strip()
    image_details = []
    ocr_texts = []
    llm_image_payloads = []

    for idx, img_item in enumerate(images_list, start=1):
        image_url_or_data = None
        ocr_text = ""
        metadata = {}

        if isinstance(img_item, str):
            # Check if local file path
            if os.path.exists(img_item):
                image_url_or_data = encode_image_to_base64(img_item)
                ocr_text = extract_ocr_text_from_image(img_item)
                metadata = extract_image_metadata(img_item)
            # Check if base64 data URI
            elif img_item.startswith("data:image/"):
                image_url_or_data = img_item
                metadata = {"filename": f"image_{idx}.png", "type": "base64_data_uri"}
            # Check if HTTP/HTTPS URL
            elif img_item.startswith("http://") or img_item.startswith("https://"):
                image_url_or_data = img_item
                metadata = {"filename": f"image_{idx}.png", "type": "web_url"}
            else:
                # Raw base64 string
                mime_type = "image/png"
                image_url_or_data = f"data:{mime_type};base64,{img_item}"
                metadata = {"filename": f"image_{idx}.png", "type": "raw_base64"}

        elif isinstance(img_item, dict):
            url = img_item.get("url") or img_item.get("path") or img_item.get("data")
            if url and os.path.exists(url):
                image_url_or_data = encode_image_to_base64(url)
                ocr_text = extract_ocr_text_from_image(url)
                metadata = extract_image_metadata(url)
            elif url:
                image_url_or_data = url
                metadata = img_item

        if image_url_or_data:
            llm_image_payloads.append({
                "type": "image_url",
                "image_url": {"url": image_url_or_data}
            })

            if ocr_text:
                ocr_texts.append(f"[Image {idx} OCR Text]: {ocr_text}")

            image_details.append({
                "image_index": idx,
                "metadata": metadata,
                "ocr_text": ocr_text,
                "full_data_uri": image_url_or_data,
                "data_uri": image_url_or_data if len(image_url_or_data) < 200 else image_url_or_data[:50] + "..."
            })

    # Build combined text for semantic search and topic identification
    combined_parts = []
    if text_query:
        combined_parts.append(text_query)
    if ocr_texts:
        combined_parts.append("\n".join(ocr_texts))

    combined_text = "\n\n".join(combined_parts).strip()
    if not combined_text:
        combined_text = "Image query regarding operating systems concepts"

    return {
        "raw_query": text_query,
        "has_images": len(image_details) > 0,
        "num_images": len(image_details),
        "combined_text": combined_text,
        "ocr_text": "\n".join(ocr_texts),
        "image_details": image_details,
        "llm_image_payloads": llm_image_payloads
    }
