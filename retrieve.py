import chromadb

from sentence_transformers import SentenceTransformer


# ============================================================
# CONFIGURATION
# ============================================================

CHROMA_PATH = "./chroma_db"

COLLECTION_NAME = "os_knowledge_base"

EMBEDDING_MODEL = "sentence-transformers/all-MiniLM-L6-v2"

TOP_K = 5


# ============================================================
# LOAD EMBEDDING MODEL
# ============================================================

print("Loading embedding model...")

embedding_model = SentenceTransformer(
    EMBEDDING_MODEL
)

print("Embedding model loaded.")


# ============================================================
# CONNECT TO CHROMADB
# ============================================================

print("Connecting to ChromaDB...")

client = chromadb.PersistentClient(
    path=CHROMA_PATH
)


# ============================================================
# LOAD EXISTING COLLECTION
# ============================================================

def get_subject_collection(subject_name=None):
    if not subject_name:
        subject_name = COLLECTION_NAME
    clean_sub = str(subject_name).lower().replace(" ", "_")
    target_name = f"{clean_sub}_knowledge_base" if not clean_sub.endswith("_knowledge_base") else clean_sub
    
    try:
        return client.get_collection(name=target_name)
    except Exception:
        try:
            return client.get_collection(name=COLLECTION_NAME)
        except Exception:
            return client.get_or_create_collection(name=target_name)

# Default collection reference for compatibility
try:
    collection = client.get_collection(name=COLLECTION_NAME)
except Exception:
    collection = None

# ============================================================
# RETRIEVE RELEVANT CONTENT
# ============================================================

def retrieve(
    query,
    top_k=TOP_K,
    subject=None
):
    """
    Retrieve the most relevant chunks
    from the PragTutor knowledge base.

    Parameters:
        query   -> student's question
        top_k   -> number of chunks to retrieve
        subject -> target subject domain (e.g. 'operating_systems', 'dbms')
    """

    target_collection = get_subject_collection(subject) if subject else collection
    if target_collection is None:
        return []

    # --------------------------------------------------------
    # Convert query into embedding
    # --------------------------------------------------------

    if isinstance(query, dict):
        search_text = query.get("combined_text") or query.get("raw_query") or ""
    else:
        search_text = str(query or "")

    if not search_text.strip():
        return []

    query_embedding = (
        embedding_model
        .encode(search_text)
        .tolist()
    )

    # --------------------------------------------------------
    # Search ChromaDB
    # --------------------------------------------------------

    if target_collection.count() == 0:
        return []

    actual_k = min(top_k, target_collection.count())
    results = target_collection.query(
        query_embeddings=[query_embedding],
        n_results=actual_k,
        include=["documents", "metadatas", "distances"]
    )

    # --------------------------------------------------------
    # Extract results
    # --------------------------------------------------------

    documents = results["documents"][0] if results.get("documents") else []
    metadatas = results["metadatas"][0] if results.get("metadatas") else []
    distances = results["distances"][0] if results.get("distances") else []

    retrieved_results = []
    for i in range(len(documents)):
        meta = metadatas[i] if i < len(metadatas) else {}
        result = {
            "content": documents[i],
            "unit": meta.get("unit", "General"),
            "page": meta.get("page", 1),
            "source": meta.get("source", "Document"),
            "distance": distances[i] if i < len(distances) else 0.0
        }
        retrieved_results.append(result)

    return retrieved_results



# ============================================================
# DISPLAY RETRIEVED RESULTS
# ============================================================

def display_results(
    query,
    results
):

    print()
    print("=" * 80)

    print(
        f"QUERY: {query}"
    )

    print("=" * 80)

    for i, result in enumerate(
        results,
        start=1
    ):

        print()

        print(
            f"RESULT {i}"
        )

        print("-" * 80)

        print(
            f"Unit: "
            f"{result['unit']}"
        )

        print(
            f"Page: "
            f"{result['page']}"
        )

        print(
            f"Source: "
            f"{result['source']}"
        )

        print(
            f"Distance: "
            f"{result['distance']:.4f}"
        )

        print()

        print(
            result["content"]
        )

        print("-" * 80)


# ============================================================
# MAIN - TEST RETRIEVER
# ============================================================

def main():

    print()
    print("=" * 80)
    print("PRAGTUTOR RAG RETRIEVER")
    print("=" * 80)

    while True:

        query = input(
            "\nEnter your question "
            "(type 'exit' to stop): "
        )

        # ----------------------------------------------------
        # Exit
        # ----------------------------------------------------

        if query.lower().strip() == "exit":

            print(
                "\nRetriever stopped."
            )

            break

        # ----------------------------------------------------
        # Empty query
        # ----------------------------------------------------

        if not query.strip():

            print(
                "Please enter a question."
            )

            continue

        # ----------------------------------------------------
        # Retrieve
        # ----------------------------------------------------

        results = retrieve(
            query
        )

        # ----------------------------------------------------
        # Display
        # ----------------------------------------------------

        display_results(
            query,
            results
        )


# ============================================================
# PROGRAM ENTRY POINT
# ============================================================

if __name__ == "__main__":

    main()