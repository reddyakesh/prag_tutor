import os
os.environ["HF_HUB_OFFLINE"] = os.environ.get("HF_HUB_OFFLINE", "1")
import re
import glob
import json
import chromadb
from sentence_transformers import SentenceTransformer

# ============================================================
# CONFIGURATION
# ============================================================

ROOT_DIR = os.path.dirname(os.path.abspath(__file__))
DATA_FOLDER = os.path.join(ROOT_DIR, "data")
CHROMA_PATH = os.path.join(ROOT_DIR, "chroma_db")
MANIFEST_FILE = os.path.join(DATA_FOLDER, "pdf_manifest.json")
EMBEDDING_MODEL_NAME = "sentence-transformers/all-MiniLM-L6-v2"

CHUNK_SIZE = 500
CHUNK_OVERLAP = 75

# Lazy-loaded embedding model to avoid reload overhead
_embedding_model = None

def get_embedding_model():
    global _embedding_model
    if _embedding_model is None:
        print("Loading SentenceTransformer model...")
        _embedding_model = SentenceTransformer(EMBEDDING_MODEL_NAME)
    return _embedding_model

def clean_text(text):
    if not text:
        return ""
    text = re.sub(r"[ \t]+", " ", text)
    text = re.sub(r"\n+", "\n", text)
    return text.strip()

def extract_pdf_pages(pdf_path):
    pages = []
    filename = os.path.basename(pdf_path)
    
    # Try pdfplumber first
    try:
        import pdfplumber
        with pdfplumber.open(pdf_path) as pdf:
            for page_number, page in enumerate(pdf.pages, start=1):
                text = page.extract_text()
                if not text:
                    continue
                cleaned = clean_text(text)
                if cleaned:
                    pages.append({"page": page_number, "text": cleaned})
        if pages:
            return pages
    except Exception as e:
        print(f"pdfplumber error on {filename}: {e}. Trying fallback PyPDF2/pypdf...")

    # Fallback to PyPDF2 or pypdf
    try:
        try:
            import PyPDF2 as pdf_lib
        except ImportError:
            import pypdf as pdf_lib

        with open(pdf_path, "rb") as f:
            reader = pdf_lib.PdfReader(f)
            for page_number, page in enumerate(reader.pages, start=1):
                text = page.extract_text()
                if not text:
                    continue
                cleaned = clean_text(text)
                if cleaned:
                    pages.append({"page": page_number, "text": cleaned})
    except Exception as e2:
        print(f"PDF extraction error on {filename}: {e2}")

    return pages

def get_unit_name(filename):
    filename_lower = filename.lower()
    match = re.search(r"unit[_\-\s]?(\d+)", filename_lower)
    if match:
        return f"Unit {match.group(1)}"
    return "Course Material"

def create_chunks(pages, unit_name, source_file):
    chunks = []
    chunk_number = 0

    for page_data in pages:
        page_number = page_data["page"]
        text = page_data["text"]

        # Sentence split (using regex fallback for zero-dependency speed)
        sentences = [s.strip() for s in re.split(r'(?<=[.!?])\s+', text) if s.strip()]
        current_sentences = []
        current_word_count = 0

        for sentence in sentences:
            sentence_word_count = len(sentence.split())
            if (current_word_count + sentence_word_count > CHUNK_SIZE) and current_sentences:
                chunk_text = " ".join(current_sentences)
                chunk_id = f"{source_file}_p{page_number}_c{chunk_number}"
                chunks.append({
                    "id": chunk_id,
                    "text": chunk_text,
                    "page": page_number,
                    "unit": unit_name,
                    "source": source_file
                })
                chunk_number += 1

                # Calculate overlap
                overlap_sentences = []
                overlap_word_count = 0
                for prev_sent in reversed(current_sentences):
                    prev_count = len(prev_sent.split())
                    if overlap_word_count + prev_count <= CHUNK_OVERLAP:
                        overlap_sentences.insert(0, prev_sent)
                        overlap_word_count += prev_count
                    else:
                        break
                current_sentences = overlap_sentences
                current_word_count = overlap_word_count

            current_sentences.append(sentence)
            current_word_count += sentence_word_count

        if current_sentences:
            chunk_text = " ".join(current_sentences)
            chunk_id = f"{source_file}_p{page_number}_c{chunk_number}"
            chunks.append({
                "id": chunk_id,
                "text": chunk_text,
                "page": page_number,
                "unit": unit_name,
                "source": source_file
            })
            chunk_number += 1

    return chunks

def load_pdf_manifest():
    if os.path.exists(MANIFEST_FILE):
        try:
            with open(MANIFEST_FILE, "r") as f:
                return json.load(f)
        except Exception:
            pass
    return {}

def prepare_knowledge_base(subject_id: str = "operating_systems", status_callback=None):
    """
    Dynamically builds ChromaDB vector collection for target subject using uploaded PDFs.
    """
    def update_status(stage, progress_pct):
        if status_callback:
            status_callback(stage, progress_pct)
        print(f"[{subject_id}] ({progress_pct}%) -> {stage}")

    update_status("Locating uploaded PDF materials...", 10)

    # Find PDFs for this subject from manifest or directory scan
    manifest = load_pdf_manifest()
    subject_pdfs = manifest.get(subject_id, [])
    
    target_files = []
    if subject_pdfs:
        for pinfo in subject_pdfs:
            fname = pinfo.get("filename")
            fpath = os.path.join(DATA_FOLDER, fname)
            if os.path.exists(fpath):
                target_files.append(fpath)
    
    # Fallback directory search matching subject name if manifest empty
    if not target_files and os.path.exists(DATA_FOLDER):
        all_pdfs = glob.glob(os.path.join(DATA_FOLDER, "*.pdf"))
        for ppath in all_pdfs:
            fname = os.path.basename(ppath).lower()
            sub_key = subject_id.replace("_", "")
            if sub_key in fname or subject_id in fname or "os_" in fname:
                target_files.append(ppath)
            elif not manifest and subject_id == "operating_systems":
                target_files.append(ppath)

    sample_dir = os.path.join(ROOT_DIR, "sample_pdfs")
    if not target_files and os.path.exists(sample_dir):
        all_pdfs = glob.glob(os.path.join(sample_dir, "*.pdf"))
        for ppath in all_pdfs:
            fname = os.path.basename(ppath).lower()
            sub_key = subject_id.replace("_", "")
            if sub_key in fname or subject_id in fname or "os_" in fname or subject_id == "operating_systems":
                target_files.append(ppath)

    if not target_files:
        raise ValueError(f"No uploaded PDF documents found for subject '{subject_id}'. Please upload PDFs first.")

    update_status(f"Extracting text from {len(target_files)} PDF file(s)...", 30)
    all_chunks = []

    for idx, pdf_path in enumerate(target_files, start=1):
        filename = os.path.basename(pdf_path)
        unit_name = get_unit_name(filename)
        pages = extract_pdf_pages(pdf_path)
        chunks = create_chunks(pages, unit_name, filename)
        all_chunks.extend(chunks)

    if not all_chunks:
        raise ValueError("Could not extract any valid text chunks from uploaded PDF files.")

    update_status(f"Generated {len(all_chunks)} text chunks. Loading embedding model...", 60)
    model = get_embedding_model()

    update_status("Computing vector embeddings (all-MiniLM-L6-v2)...", 75)
    texts = [c["text"] for c in all_chunks]
    ids = [c["id"] for c in all_chunks]
    embeddings = model.encode(texts, show_progress_bar=False).tolist()

    update_status("Indexing chunks into ChromaDB collection...", 90)
    client = chromadb.PersistentClient(path=CHROMA_PATH)
    
    col_name = f"{subject_id}_knowledge_base"
    
    # Reset existing collection if exists to rebuild cleanly
    try:
        client.delete_collection(col_name)
    except Exception:
        pass

    collection = client.create_collection(name=col_name)

    # Format metadatas
    metadatas = [{
        "subject": subject_id,
        "unit": c["unit"],
        "page": c["page"],
        "source": c["source"]
    } for c in all_chunks]

    collection.add(
        ids=ids,
        documents=texts,
        embeddings=embeddings,
        metadatas=metadatas
    )

    # Also build/update os_knowledge_base alias if operating_systems for backward compatibility
    if subject_id == "operating_systems":
        try:
            client.delete_collection("os_knowledge_base")
        except Exception:
            pass
        os_col = client.create_collection(name="os_knowledge_base")
        os_col.add(ids=ids, documents=texts, embeddings=embeddings, metadatas=metadatas)

    update_status("ChromaDB Collection Indexed & Ready!", 100)
    return {
        "status": "ready",
        "collection_name": col_name,
        "pdf_count": len(target_files),
        "vector_chunks": len(all_chunks)
    }

def main():
    print("=" * 70)
    print("PRAGTUTOR KNOWLEDGE BASE BUILDER")
    print("=" * 70)
    try:
        res = prepare_knowledge_base("operating_systems")
        print("Build Result:", res)
    except Exception as e:
        print("Build error:", e)

if __name__ == "__main__":
    main()