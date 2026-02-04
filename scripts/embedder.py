from sentence_transformers import SentenceTransformer
import numpy as np

embedding_model = SentenceTransformer('all-MiniLM-L6-v2')

def embed_text(chunks):
  embeddings =  embedding_model.encode(chunks)
  return np.array(embeddings).astype('float32')