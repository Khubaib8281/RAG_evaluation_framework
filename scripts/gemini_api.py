def generate_answer_from_chunks_gemini(chunks, question):
    import os
    from dotenv import load_dotenv
    import google.generativeai as genai
    
    load_dotenv()
    
    api_key = os.getenv("GEMINI_API_KEY")
    
    if not api_key:
        raise ValueError("GOOGLE_API_KEY not found in environment")
    
    genai.configure(api_key = api_key)
    gemini_model = genai.GenerativeModel("gemini-2.5-flash")
    context = "\n\n".join(chunks)
    prompt = f"""
    You are a document question-answering assistant. 
    Your task is to use the provided context to respond to the user's question as completely and accurately as possible. 
    Adapt your response style based on the type of request:
    
    1. If the user asks to "show full content" or requests the document section directly → return the context text exactly as it appears, without summarizing.  
    2. If the user asks to "summarize", "explain", "simplify", or requests an easier explanation → rewrite the relevant context into clear, simple, and easy-to-understand language.  
    3. Otherwise, answer the question directly using details from the context. Be complete and avoid leaving out important information.  
    
    If the answer cannot be found in the context, clearly reply:  
    "The document does not provide this information."
    
    Context:
    {context}
    
    Question:
    {question}
    
    Answer:
    """


    response = gemini_model.generate_content(prompt)
    return response.text.strip()
