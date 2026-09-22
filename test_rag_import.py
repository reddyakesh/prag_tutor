from retrieve import retrieve


query = "Explain deadlock"

results = retrieve(
    query,
    top_k=5
)

print()
print("=" * 70)
print("RAG TEST")
print("=" * 70)

for i, result in enumerate(
    results,
    start=1
):

    print()
    print(f"Result {i}")
    print("-" * 70)

    print(
        "Unit:",
        result["unit"]
    )

    print(
        "Page:",
        result["page"]
    )

    print(
        "Source:",
        result["source"]
    )

    print(
        "Distance:",
        result["distance"]
    )

    print()

    print(
        result["content"]
    )