from collections import defaultdict


def rrf_fusion(
    dense_results: list,
    sparse_results: list,
    k: int = 60,
):
    """
    Fuse dense and sparse retrieval results using Reciprocal Rank Fusion.

    RRF score:
        score += 1 / (k + rank)

    We use ranks instead of raw scores because:
    - Dense retrieval returns a distance (lower is better)
    - BM25 returns a relevance score (higher is better)

    RRF is robust across different score scales.

    Returns:
    [
        {
            'chunk_id': 123,
            'fused_score': 0.0325,
        },
        ...
    ]
    ordered by fused_score descending.
    """

    fused_scores = defaultdict(float)

    # ------------------------------------------------------------------
    # Add contribution from dense retriever.
    # ------------------------------------------------------------------
    for item in dense_results:
        chunk_id = item.get('chunk_id')
        rank = item.get('rank')

        if chunk_id is None or rank is None:
            continue

        fused_scores[chunk_id] += 1.0 / (k + rank)

    # ------------------------------------------------------------------
    # Add contribution from sparse retriever.
    # ------------------------------------------------------------------
    for item in sparse_results:
        chunk_id = item.get('chunk_id')
        rank = item.get('rank')

        if chunk_id is None or rank is None:
            continue

        fused_scores[chunk_id] += 1.0 / (k + rank)

    # ------------------------------------------------------------------
    # Sort by fused score descending.
    # ------------------------------------------------------------------
    ranked = sorted(
        fused_scores.items(),
        key=lambda x: x[1],
        reverse=True,
    )

    results = [
        {
            'chunk_id': chunk_id,
            'fused_score': score,
        }
        for chunk_id, score in ranked
    ]

    print('\n=== RRF FUSED RESULTS ===')
    for item in results[:15]:
        print(f"Chunk ID: {item['chunk_id']} | Fused Score: {item['fused_score']:.4f}")

    return results


if __name__ == '__main__':
    dense = [
        {'chunk_id': 1, 'rank': 1},
        {'chunk_id': 2, 'rank': 2},
        {'chunk_id': 3, 'rank': 3},
    ]

    sparse = [
        {'chunk_id': 2, 'rank': 1},
        {'chunk_id': 4, 'rank': 2},
        {'chunk_id': 1, 'rank': 3},
    ]

    fused = rrf_fusion(dense, sparse)

    for item in fused:
        print(item)