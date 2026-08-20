from pathlib import Path

from langchain_community.vectorstores import Chroma
from langchain_huggingface import HuggingFaceEmbeddings


# ----------------------------------------------------------------------
# Chroma vector store configuration
# ----------------------------------------------------------------------
BASE_DIR = Path(__file__).resolve().parent
VECTORSTORE_DIR = BASE_DIR / 'vectorstore'


# ----------------------------------------------------------------------
# Load the same embedding model that was used during ingestion.
# The embedding model must remain identical for retrieval to work.
# ----------------------------------------------------------------------
_embeddings = HuggingFaceEmbeddings(
    model_name='sentence-transformers/all-MiniLM-L6-v2'
)


# ----------------------------------------------------------------------
# Load the persisted Chroma database.
# This is shared across all conversations, so every query MUST use
# a conversation_id filter.
# ----------------------------------------------------------------------
_vectordb = Chroma(
    persist_directory=str(VECTORSTORE_DIR),
    embedding_function=_embeddings,
)


def dense_retrieve(
    query: str,
    conversation_id: int,
    k: int = 10,
):
    """
    Dense semantic retrieval using Chroma.

    Returns a ranked list of chunks belonging ONLY to the provided
    conversation.

    Output format:
    [
        {
            'chunk_id': 123,
            'content': '...',
            'metadata': {...},
            'score': 0.23,
            'rank': 1,
        },
        ...
    ]

    NOTE:
    Chroma returns a distance score, so LOWER is better.
    """

    # ------------------------------------------------------------------
    # NEW: Filter by conversation_id instead of document_id.
    # This guarantees chat-level isolation.
    # ------------------------------------------------------------------
    docs_with_scores = _vectordb.similarity_search_with_score(
        query=query,
        k=k,
        filter={'conversation_id': conversation_id},
    )

    results = []

    for rank, (doc, score) in enumerate(docs_with_scores, start=1):
        results.append(
            {
                'chunk_id': doc.metadata.get('chunk_id'),
                'content': doc.page_content,
                'metadata': doc.metadata,
                'score': float(score),  # lower distance = better match
                'rank': rank,
            }
        )

    print('\n=== DENSE RETRIEVAL RESULTS ===')
    for r in results[:15]:
        safe_content = r['content'][:120].encode('ascii', errors='ignore').decode('ascii')
        print(f"Rank {r['rank']} | Chunk ID: {r['chunk_id']} | Score: {r['score']:.4f}")
        print(safe_content)
        print('-' * 40)

    return results


if __name__ == '__main__':
    retrieved = dense_retrieve(
        query='What is RAG?',
        conversation_id=1,
        k=3,
    )

    for item in retrieved:
        print('RANK:', item['rank'])
        print('SCORE:', item['score'])
        print(item['content'][:120])
        print('-' * 40)