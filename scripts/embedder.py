from sentence_transformers import SentenceTransformer

embedding_model = SentenceTransformer('all-MiniLM-L6-v2')

def embed_text(chunks):
  return embedding_model.encode(chunks)
  return np.array(embeddings).astype('float32')