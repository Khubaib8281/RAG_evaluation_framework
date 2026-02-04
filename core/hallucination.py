import numpy as np
from sklearn.metrics.pairwise import cosine_similarity

def hallucination_check(answer_embs, context_embs, threhold=0.65):
    sims = cosine_similarity(
        [answer_embs],
        context_embs
    )[0]
    
    max_sim = float(np.max(sims))
    
    hallucinated = 1 if max_sim < threhold else 0
    return hallucinated, max_sim