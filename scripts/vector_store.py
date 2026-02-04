import faiss
import numpy as np

def build_faiss_index(embeddings):
  dim = embeddings.shape[1]
  index = faiss.IndexFlatL2(dim)
  index.add(np.array(embeddings))
  return index
