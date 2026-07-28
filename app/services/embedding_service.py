"""
Embedding service — wraps sentence-transformers to turn text into vectors.

Model: BAAI/bge-small-en-v1.5
Chosen for retrieval quality (MTEB benchmark) over MiniLM, while remaining
small enough to run comfortably on CPU. See docs/project1-decisions-log.md
for the full B1 decision entry.
"""

from functools import lru_cache

from sentence_transformers import SentenceTransformer

EMBEDDING_MODEL_NAME = "BAAI/bge-small-en-v1.5"

# bge models are trained asymmetrically: queries need this exact instruction
# prefix prepended, passages (the chunks we're indexing) do not. Omitting
# this prefix on queries silently degrades retrieval quality -- it won't
# error, it'll just retrieve worse results with no signal that anything
# is wrong. Get this from the model's official card, don't guess at it.
QUERY_PREFIX = "Represent this sentence for searching relevant passages: "


@lru_cache(maxsize=1)
def get_embedding_model() -> SentenceTransformer:
    """
    Load and cache the embedding model as a singleton.

    lru_cache(maxsize=1) ensures the model is loaded into memory exactly
    once per process, regardless of how many times this function is called.
    Reloading a transformer model on every call would be a real, avoidable
    performance bug -- model loading takes real time and memory, and there's
    no reason to pay that cost more than once per worker/app process.
    """
    return SentenceTransformer(EMBEDDING_MODEL_NAME)


def embed_passages(texts: list[str]) -> list[list[float]]:
    """
    Embed a batch of document chunks (passages) for storage in the vector store.

    No prefix is applied -- bge's asymmetric training expects passages to be
    embedded plain, with only queries getting the instruction prefix.
    """
    model = get_embedding_model()
    embeddings = model.encode(
        texts,
        normalize_embeddings=True,
        convert_to_numpy=True,
    )
    return embeddings.tolist()


def embed_query(text: str) -> list[float]:
    """
    Embed a single search query for retrieval.

    Applies the required bge query prefix -- this is the one place in the
    codebase that prefix should ever be added. embed_passages() must never
    apply it, or query and passage embeddings won't be comparable.
    """
    model = get_embedding_model()
    embedding = model.encode(
        QUERY_PREFIX + text,
        normalize_embeddings=True,
        convert_to_numpy=True,
    )
    return embedding.tolist()