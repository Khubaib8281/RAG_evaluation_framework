from sklearn.metrics.pairwise import cosine_similarity
import numpy as np

def hallucination_check(answer_embs, context_embs, threshold=0.65):
    answer_embs = np.array(answer_embs).reshape(1, -1)
    context_embs = np.array(context_embs)

    # If context_embs is 1D (single chunk)
    if context_embs.ndim == 1:
        context_embs = context_embs.reshape(1, -1)

    sims = cosine_similarity(answer_embs, context_embs)[0]

    max_sim = float(np.max(sims))
    hallucinated = 1 if max_sim < threshold else 0

    return hallucinated, max_sim
