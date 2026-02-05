from sentence_transformers import SentenceTransformer
import numpy as np

embedding_model = SentenceTransformer('all-MiniLM-L6-v2')

def embed_text(texts):
    if isinstance(texts, str):
        texts = [texts]
    embeddings = embedding_model.encode(texts)
    return np.array(embeddings, dtype="float32")