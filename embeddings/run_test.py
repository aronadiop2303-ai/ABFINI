"""Local smoke test for ABFINI's embedding pipeline.

Run from the repository root after installing embeddings/requirements.txt.
This script never commits vectors or secrets; it prints only validation results.
"""
from .local_sentence_transformers import LocalSentenceTransformerProvider

MODEL = "BAAI/bge-base-en-v1.5"
EXPECTED_DIMENSIONS = 768


def main() -> None:
    provider = LocalSentenceTransformerProvider(
        MODEL, expected_dimension=EXPECTED_DIMENSIONS
    )
    result = provider.embed(["ABFINI provides documentary knowledge to OMNI Agent."])
    vector = result.vectors[0]
    assert result.dimensions == EXPECTED_DIMENSIONS
    assert len(vector) == EXPECTED_DIMENSIONS
    assert abs(sum(x * x for x in vector) - 1.0) < 1e-3
    print(f"OK model={MODEL} dimensions={result.dimensions}")


if __name__ == "__main__":
    main()
