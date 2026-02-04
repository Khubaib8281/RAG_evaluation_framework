from sentence_transformers import SentenceTransformer

embedding_model = SentenceTransformer('all-MiniLM-L6-v2')

def get_best_chunk(question, chunks, index):
  question_embeddings = embedding_model.encode([question]).astype('float32')

  _, I = index.search(question_embeddings, k = 5)
  return chunks[I[0][0]]