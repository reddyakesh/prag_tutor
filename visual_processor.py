import os
import re
import glob
import json
import time
import io
import logging
from typing import List, Dict, Any, Optional
import pypdf
from PIL import Image

logging.getLogger("pypdf").setLevel(logging.ERROR)

ROOT_DIR = os.path.dirname(os.path.abspath(__file__))
MEDIA_DIR = os.path.join(ROOT_DIR, "media")
DATA_DIR = os.path.join(ROOT_DIR, "data")

def clean_text(text: str) -> str:
    if not text:
        return ""
    text = re.sub(r"[ \t]+", " ", text)
    text = re.sub(r"\n+", " ", text)
    return text.strip()

def get_unit_name(filename: str) -> str:
    fn_lower = filename.lower()
    match = re.search(r"unit[_\-\s]?(\d+)", fn_lower)
    if match:
        return f"Unit {match.group(1)}"
    return "Unit 1"

def infer_topics_from_text(text: str) -> List[str]:
    text_lower = text.lower()
    discovered_topics = []
    
    # Common CS topic keywords across subjects
    keywords_map = {
        "process": ["process", "process state", "pcb", "task control block"],
        "cpu_scheduling": ["scheduling", "fcfs", "sjf", "round robin", "priority scheduling", "gantt chart"],
        "synchronization": ["semaphore", "mutex", "critical section", "synchronization", "peterson"],
        "deadlock": ["deadlock", "resource allocation", "banker's algorithm", "safe state", "wait-for graph"],
        "memory_management": ["paging", "segmentation", "virtual memory", "page table", "tlb", "lru", "page replacement"],
        "file_system": ["file system", "directory", "disk scheduling", "fcfs disk", "scan", "c-scan", "raid"],
        "osi_model": ["osi", "tcp/ip", "protocol", "layer", "transport layer", "network layer"],
        "routing": ["routing", "ip address", "subnet", "packet", "router"],
        "tree": ["binary tree", "bst", "traversal", "node", "tree"],
        "graph": ["graph", "bfs", "dfs", "dijkstra", "shortest path"],
        "sql": ["sql", "query", "select", "join", "table", "schema", "relational"],
        "normalization": ["normalization", "1nf", "2nf", "3nf", "bcnf", "dependency"],
        "transaction": ["transaction", "acid", "concurrency", "lock", "serializability"],
        "agile": ["agile", "scrum", "sdlc", "waterfall", "sprint"],
        "uml": ["uml", "use case", "class diagram", "sequence diagram"]
    }
    
    for topic_key, kws in keywords_map.items():
        if any(kw in text_lower for kw in kws):
            discovered_topics.append(topic_key)
            
    return list(set(discovered_topics))

def infer_caption_from_page(page_text: str, page_num: int, img_idx: int) -> str:
    cleaned = clean_text(page_text)
    if not cleaned:
        return f"Course Figure (Page {page_num}, Figure {img_idx})"
        
    # Search for "Figure X: ...", "Diagram X: ...", "Chart: ..."
    fig_match = re.search(r"(figure|fig\.|diagram|chart|table)\s*\d*[\.\:]?\s*([^\.\n]+)", cleaned, re.IGNORECASE)
    if fig_match:
        caption = fig_match.group(0).strip()
        if len(caption) < 100:
            return caption.capitalize()

    # Fallback to first meaningful sentence on page
    sentences = [s.strip() for s in cleaned.split(".") if len(s.strip()) > 15]
    if sentences:
        first_sent = sentences[0]
        if len(first_sent) > 90:
            first_sent = first_sent[:87] + "..."
        return first_sent.capitalize()
        
    return f"Course Visual Reference (Page {page_num})"

def extract_pdf_visuals(
    pdf_path: str,
    subject_id: str = "operating_systems",
    min_width: int = 80,
    min_height: int = 80
) -> List[Dict[str, Any]]:
    """
    Extracts visual images from a PDF file using pypdf and PIL, saving them to
    subject-isolated directory media/<subject_id>/unit<N>/ and returning metadata objects.
    """
    if not os.path.exists(pdf_path):
        print(f"Warning: PDF file not found at {pdf_path}")
        return []

    filename = os.path.basename(pdf_path)
    unit_name = get_unit_name(filename)
    unit_slug = unit_name.lower().replace(" ", "")

    # Create subject and unit storage directory
    subj_media_dir = os.path.join(MEDIA_DIR, subject_id, unit_slug)
    os.makedirs(subj_media_dir, exist_ok=True)

    extracted_visuals = []

    try:
        reader = pypdf.PdfReader(pdf_path)
        for page_idx, page in enumerate(reader.pages, start=1):
            page_text = clean_text(page.extract_text() or "")
            page_images = getattr(page, "images", [])
            
            for img_idx, img_obj in enumerate(page_images, start=1):
                try:
                    img_data = img_obj.data
                    img_name = img_obj.name
                    pil_img = Image.open(io.BytesIO(img_data))

                    width, height = pil_img.size
                    if width < min_width or height < min_height:
                        continue  # Skip tiny icons or decoration images

                    # Save image as PNG
                    image_id = f"{subject_id}_{unit_slug}_p{page_idx}_img{img_idx}"
                    out_filename = f"page_{page_idx}_img_{img_idx}.png"
                    out_filepath = os.path.join(subj_media_dir, out_filename)
                    
                    # Convert palette or RGBA to RGB for clean PNG saving
                    if pil_img.mode in ("P", "RGBA"):
                        pil_img = pil_img.convert("RGB")

                    pil_img.save(out_filepath, "PNG")

                    rel_path = f"media/{subject_id}/{unit_slug}/{out_filename}"
                    web_url = f"/media/{subject_id}/{unit_slug}/{out_filename}"

                    caption = infer_caption_from_page(page_text, page_idx, img_idx)
                    topics = infer_topics_from_text(f"{caption} {page_text}")

                    metadata = {
                        "image_id": image_id,
                        "subject": subject_id,
                        "unit": unit_name,
                        "page": page_idx,
                        "source": filename,
                        "path": rel_path,
                        "url": web_url,
                        "width": width,
                        "height": height,
                        "caption": caption,
                        "page_context": page_text[:400],
                        "related_topics": topics,
                        "extracted_at": time.strftime("%Y-%m-%d %H:%M:%S")
                    }

                    extracted_visuals.append(metadata)

                except Exception as img_err:
                    print(f"Error extracting image {img_idx} on page {page_idx} of {filename}: {img_err}")
                    continue

    except Exception as pdf_err:
        print(f"Failed to process PDF {filename} for visuals: {pdf_err}")

    return extracted_visuals

def load_visual_metadata(subject_id: str) -> List[Dict[str, Any]]:
    metadata_file = os.path.join(DATA_DIR, f"visual_metadata_{subject_id}.json")
    if os.path.exists(metadata_file):
        try:
            with open(metadata_file, "r", encoding="utf-8") as f:
                return json.load(f)
        except Exception as e:
            print(f"Error loading visual metadata for {subject_id}: {e}")
    return []

def save_visual_metadata(subject_id: str, metadata_list: List[Dict[str, Any]]):
    os.makedirs(DATA_DIR, exist_ok=True)
    metadata_file = os.path.join(DATA_DIR, f"visual_metadata_{subject_id}.json")
    try:
        with open(metadata_file, "w", encoding="utf-8") as f:
            json.dump(metadata_list, f, indent=2)
    except Exception as e:
        print(f"Error saving visual metadata for {subject_id}: {e}")

def clear_subject_visuals(subject_id: str):
    """Cleanly deletes existing media directory and metadata JSON for target subject."""
    import shutil
    subj_media_dir = os.path.join(MEDIA_DIR, subject_id)
    if os.path.exists(subj_media_dir):
        try:
            shutil.rmtree(subj_media_dir)
        except Exception as e:
            print(f"Error clearing media directory for {subject_id}: {e}")

    metadata_file = os.path.join(DATA_DIR, f"visual_metadata_{subject_id}.json")
    if os.path.exists(metadata_file):
        try:
            os.remove(metadata_file)
        except Exception as e:
            print(f"Error deleting visual metadata file for {subject_id}: {e}")

if __name__ == "__main__":
    print("=" * 70)
    print("TESTING VISUAL PROCESSOR")
    print("=" * 70)
    test_pdf = os.path.join(ROOT_DIR, "sample_pdfs", "os_unit1.pdf")
    if os.path.exists(test_pdf):
        visuals = extract_pdf_visuals(test_pdf, "operating_systems")
        print(f"Extracted {len(visuals)} visual elements from {os.path.basename(test_pdf)}")
        if visuals:
            print("First visual metadata sample:", json.dumps(visuals[0], indent=2))
            save_visual_metadata("operating_systems", visuals)
    else:
        print("Sample PDF not found for testing.")
