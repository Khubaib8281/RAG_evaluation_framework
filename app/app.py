import streamlit as st
import os
import sys
import pandas as pd

# Append project path for imports
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))
from scripts.parser import extract_text_from_file
from scripts.chunker import chunk_text
from core.db import init_db
from core.logger import log_error_message, log_request
from core.metrics import MetricsTracker, estimate_tokens
from scripts.embedder import embed_text
from scripts.vector_store import build_faiss_index
from scripts.question_answer import get_best_chunk
from scripts.embedder import embed_text
from scripts.gemini_api import generate_answer_from_chunks
from core.hallucination import hallucination_check
from core.confidence import compute_similarity

# Page configuration
st.set_page_config(page_title="AskMyDoc", page_icon="📄", layout="centered")
tab1, tab2 = st.tabs(["User Mode", "Developer Mode"])
# ────────────────────────
# Custom CSS Styling
# ────────────────────────
st.markdown("""
<style>
/* Global Styles */
html, body, [class*="css"] {
    background-color: #f2f6fc;
    font-family: 'Segoe UI', sans-serif;
}

/* Streamlit title override */
.title-style {
    font-size: 2.8rem;
    font-weight: 700;
    color: ##ECF0F1;
    text-align: center;
    margin-bottom: 1rem;
}

/* File uploader styling */
section[data-testid="stFileUploader"] > div {
    border: 2px dashed #4682b4;
    background-color: #eaf4ff;
    border-radius: 10px;
    padding: 1.5rem;
    transition: 0.3s ease-in-out;
}

section[data-testid="stFileUploader"] > div:hover {
    background-color: #d4eaff;
}

/* Input box */
input[type="text"] {
    border: 1px solid #4682b4;
    border-radius: 5px;
    padding: 0.5rem;
}

/* Answer box */
.stSuccess {
    background-color: #e0f3ec;
    color: #1e4633;
    font-weight: 500;
    border-left: 5px solid #2e8b57;
    padding: 1rem;
    margin-top: 1rem;
    border-radius: 10px;
}

/* Expander content */
[data-testid="stExpander"] div[role="button"] {
    background-color: #1f4e79;
    color: white;
    border-radius: 8px;
    font-weight: bold;
}

[data-testid="stExpander"] .streamlit-expanderContent {
    background-color: #ffffff;
    color: #333333;
    border-left: 4px solid #1f4e79;
    padding: 1rem;
}

/* Footer */
.footer {
    margin-top: 4rem;
    text-align: center;
    font-size: 14px;
    color: #666;
}
</style>
""", unsafe_allow_html=True)

# ────────────────────────
# TITLE & HEADER
# ────────────────────────

with tab1:
    
    st.markdown("<div class='title-style'>📝 AskMyDoc</div>", unsafe_allow_html=True)
    st.write("Upload your document and ask questions about its content.")

    # ────────────────────────
    # How it Works
    # ────────────────────────
    with st.expander("ℹ️ How It Works"):
        st.markdown("""
        1. **Upload your document** (`.pdf`, `.docx`)  
        2. It gets converted into text, split into smart chunks  
        3. **Ask your question** → AI finds the best answers from context  
        """)

    # ────────────────────────
    # 📤 File Upload
    # ────────────────────────

    init_db()
    uploaded_file = st.file_uploader("📁 Upload your file", type=["pdf", "docx"])

    if uploaded_file:
        with st.spinner("🔍 Processing document..."):
            # Unpack the tuple to get the extracted text and the message
            extracted_text, message = extract_text_from_file(uploaded_file)
            
            # Check if text was successfully extracted before chunking
            if extracted_text:
                chunks = chunk_text(extracted_text)
                total_chunks = len(chunks)
                
                if total_chunks < 2:
                    st.error("⚠️ The document is too short for answering questions. Please upload a longer document.")
                    log_error_message(str(message))
                else:
                    st.success(message)

            else:
                # Handle cases where no text was extracted (e.g., unsupported file type)
                log_error_message(str(message))
                st.error(message)
                st.stop()

            embeddings = embed_text(chunks)
            index = build_faiss_index(embeddings)

        # st.success("✅ Document processed successfully!")

        # ────────────────────────
        # Q&A Section
        # ────────────────────────
        st.subheader("💬 Ask a Question")
        user_question = st.text_input("Enter your question here")
        hallucination_toggle = st.checkbox("Enable hallucination check")

        if st.button("🧠 Get Answer"):
            if user_question.strip() == "":
                st.warning("⚠️ Please enter a question.")
            else:
                with st.spinner("⏳ Analyzing document and generating answer..."):
                    
                    tracker = MetricsTracker()
                    tracker.start()
                    
                    top_chunks = get_best_chunk(user_question, chunks, index)
                    answer = generate_answer_from_chunks(top_chunks, user_question)
                    
                    latency = tracker.stop()
                    tokens = estimate_tokens(user_question + answer)
                    
                    answer_emb = embed_text(answer)
                    chunk_embs = embed_text(top_chunks)

                    hallucinated, similarity = hallucination_check(answer_emb, chunk_embs)
                    confidence = compute_similarity(similarity)
                    
                    log_request(user_question, answer, latency, tokens, confidence, hallucinated)
                    
                    
                st.markdown("### 📚 Answer")
                st.success(answer)
                st.write(f"Latency: {latency:.2f} ms")
                st.write(f"Confidence: {confidence}")
                if hallucinated:
                    st.warning("⚠ Possible hallucination detected")

with tab2:
    st.subheader("System Analytics")
    
    import sqlite3
    conn = sqlite3.connect("data/logs.db")
    
    df = pd.read_sql("SELECT * FROM requests", conn)
    st.dataframe(df)
    
    st.metric("Avg Latency", round(df["latency_ms"].mean(),2))
    st.metric("Hallucination Rate", round(df["hallucination"].mean()*100,2))
# ────────────────────────
#  Footer
# ────────────────────────
st.markdown("""
<div class='footer'>
    &copy; 2025 • Developed by <strong>Muhammad Khubaib Ahmad</strong> | AskMyDoc
</div>
""", unsafe_allow_html=True)
