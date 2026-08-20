# pyrefly: ignore [missing-import]
from rank_bm25 import BM25Okapi

from rag_api.models import DocumentChunk


def _tokenize(text: str):
    """
    Simple tokenizer for BM25.

    We keep it intentionally lightweight for now:
    - lowercase
    - whitespace split

    This is sufficient for a student-scale RAG system and can be improved
    later with stemming, stopword removal, etc.
    """

    return text.lower().split()


def sparse_retrieve(query: str,conversation_id: int,k: int = 10):
    """
    Sparse keyword retrieval using BM25.

    Retrieval is restricted to the provided conversation so the search
    space exactly matches the active chat.

    Returns:
    [
        {
            'chunk_id': 123,
            'content': '...',
            'metadata': {...},
            'score': 12.34,
            'rank': 1,
        },
        ...
    ]

    NOTE:
    BM25 scores are relevance scores, so HIGHER is better.
    """

    # ------------------------------------------------------------------
    # NEW: Restrict BM25 search to the current conversation only.
    # This mirrors the dense retriever's security boundary.
    # ------------------------------------------------------------------
    chunks = list(
        DocumentChunk.objects.filter(
            document__conversation_id=conversation_id
        ).select_related('document')
    )

    if not chunks:
        return []

    # ------------------------------------------------------------------
    # Build BM25 corpus from chunk text stored in SQLite.
    # SQLite is treated as the source of truth for chunk content.
    # ------------------------------------------------------------------
    corpus = [
        _tokenize(chunk.content)
        for chunk in chunks
    ]

    bm25 = BM25Okapi(corpus)

    query_tokens = _tokenize(query)

    scores = bm25.get_scores(query_tokens)

    # ------------------------------------------------------------------
    # Sort chunk indices by BM25 score (highest first).
    # ------------------------------------------------------------------
    ranked_indices = sorted(
        range(len(scores)),
        key=lambda i: scores[i],
        reverse=True,
    )[:k]

    results = []

    for rank, idx in enumerate(ranked_indices, start=1):
        chunk = chunks[idx]

        results.append(
            {
                'chunk_id': chunk.id,
                'content': chunk.content,
                'metadata': {
                    'document_id': chunk.document.id,
                    'conversation_id': conversation_id,
                    'chunk_index': chunk.chunk_index,
                    'page': chunk.page_number,
                },
                'score': float(scores[idx]),  # higher BM25 score = better
                'rank': rank,
            }
        )
        
    print('\n=== BM25 RAW RESULTS ===')
    for r in results[:15]:
        print(r['rank'], r['metadata'].get('chunk_index'), r['score'])
        print(r['content'][:120])
        print('-' * 40)

    return results


if __name__ == '__main__':
    retrieved = sparse_retrieve(
        query='What is RAG?',
        conversation_id=1,
        k=3,
    )

    for item in retrieved:
        print('RANK:', item['rank'])
        print('SCORE:', item['score'])
        print(item['content'][:120])
        print('-' * 40)