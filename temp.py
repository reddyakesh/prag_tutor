import chromadb

client = chromadb.PersistentClient(
    path="./chroma_db"
)

try:

    client.delete_collection(
        name="os_knowledge_base"
    )

    print("os_knowledge_base deleted successfully.")

except Exception as e:

    print("Collection not found.")
    print(e)