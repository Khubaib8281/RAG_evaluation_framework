from chunker import chunk_text
from embedder import embed_text
from vector_store import build_fais_index
from parser import load_text_file
from question_answer import get_best_chunk
from gemini_api import generate_answer_from_chunks

text = load_text_file('data/nlp.txt')

chunks = chunk_text(text, chunk_size=100)
if len(chunks) < 2:
    print("⚠️ Not enough content in the document to build FAISS index.")
else:
    

    embeddings = embed_text(chunks)

    index = build_fais_index(embeddings)

    # question = "What is the main focus of the research?"

    # while True:
    #     query = input("Ask your question in English: ")
    #     if query.lower() in ['exit', 'quit']:
    #         break
    #     answer = get_best_chunk(question, chunks, embeddings, index)
    #     print("\n📚 Answer:\n", answer)


    while True:
        query = input("Enter your question: ")
        if query.lower() in ['exit', 'quit']:
            break
        top_chunks = get_best_chunk(query, chunks, index)
        answer = generate_answer_from_chunks(top_chunks, query)
        print("\n📚 Answer:\n", answer)
