import streamlit as st
import os
import sys
import pandas as pd
import sqlite3
import altair as alt

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
from core.cache import get_cache, save_cache
from core.confidence import compute_similarity

# Page configuration
st.set_page_config(page_title="QueryVault", page_icon="📄", layout="centered")
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

def get_logs():
    conn = sqlite3.connect("data/logs.db")
    
    df = pd.read_sql("SELECT * FROM requests ORDER BY timestamp DESC", conn)
    conn.close()
    
    return df

import streamlit as st
import altair as alt

# --- HELPER TO RESET ON NEW UPLOAD ---
def reset_document_state():
    for key in ["chunks", "index", "processed_file_name"]:
        if key in st.session_state:
            del st.session_state[key]

with tab1:
    st.markdown("<div class='title-style'>📝 QueryVault</div>", unsafe_allow_html=True)
    st.write("Upload your document and ask questions about its content.")

    with st.expander("ℹ️ How It Works"):
        st.markdown("""
        1. **Upload your document** (`.pdf`, `.docx`)  
        2. It gets converted into text, split into smart chunks  
        3. **Ask your question** → AI finds the best answers from context  
        """)

    init_db()
    
    # Use an on_change callback to clear memory when a new file is uploaded
    uploaded_file = st.file_uploader("📁 Upload your file", type=["pdf", "docx"], on_change=reset_document_state)

    if uploaded_file:
        # Check if we have already processed THIS specific file
        file_id = f"{uploaded_file.name}_{uploaded_file.size}"
        
        if "processed_file_name" not in st.session_state or st.session_state.processed_file_name != file_id:
            with st.spinner("🔍 Processing document and building vector index..."):
                extracted_text, message = extract_text_from_file(uploaded_file)
                
                if extracted_text:
                    chunks = chunk_text(extracted_text)
                    if len(chunks) < 2:
                        st.error("⚠️ The document is too short.")
                        st.stop()
                    
                    # --- THE HEAVY LIFTING ---
                    embeddings = embed_text(chunks)
                    index = build_faiss_index(embeddings)
                    
                    # --- STORE IN SESSION STATE ---
                    st.session_state.chunks = chunks
                    st.session_state.index = index
                    st.session_state.processed_file_name = file_id
                    st.success("✅ Document indexed and saved to memory!")
                else:
                    st.error(message)
                    st.stop()
        else:
            st.info(f"⚡ Using cached index for: {uploaded_file.name}")

        # ────────────────────────
        # Q&A Section
        # ────────────────────────
        st.subheader("💬 Ask a Question")
        user_question = st.text_input("Enter your question here")

        if st.button("🧠 Get Answer"):
            if user_question.strip() == "":
                st.warning("⚠️ Please enter a question.")
            else:
                # Retrieve from session state instead of re-processing
                chunks = st.session_state.chunks
                index = st.session_state.index

                with st.spinner("⏳ Analyzing context..."):
                    tracker = MetricsTracker()
                    tracker.start()

                    # Cache check logic
                    cached_answer, cached_chunks = get_cache(user_question)

                    if cached_answer:
                        answer = cached_answer
                        top_chunks = cached_chunks
                    else:
                        # Use the index stored in session state
                        top_chunks = get_best_chunk(user_question, chunks, index)
                        answer = generate_answer_from_chunks(top_chunks, user_question)
                        save_cache(user_question, answer, top_chunks)

                    latency = tracker.stop()
                    tokens = estimate_tokens(user_question + answer)
                    
                    # Hallucination Check
                    answer_emb = embed_text(answer)
                    chunk_embs = embed_text(top_chunks)
                    hallucinated, similarity = hallucination_check(answer_emb, chunk_embs)
                    confidence = compute_similarity(similarity)

                    log_request(user_question, answer, latency, tokens, confidence, hallucinated)

                st.markdown("### 📚 Answer")
                st.success(answer)
                
                # Metrics Display
                col1, col2, col3 = st.columns(3)
                col1.metric("Latency", f"{latency:.0f}ms")
                col2.metric("Confidence", f"{confidence}%")
                col3.metric("Tokens", tokens)

                if hallucinated:
                    st.warning("⚠ Possible hallucination detected")

with tab2:
    st.title("Developer Analytics Dashboard")
    df = get_logs()
    
    if not df.empty:
        m1, m2, m3, m4 = st.columns(4)
        m1.metric("Total Requests", len(df))
        m2.metric("Avg Latency (ms)", round(df['latency_ms'].mean(), 2))
        m3.metric("Hallucination Rate (%)", round(df['hallucination'].mean()*100, 2))
        m4.metric("Avg Confidence (%)", round(df['confidence'].mean(), 2))

        st.subheader("Request Latency Distribution")
        chart = alt.Chart(df).mark_bar().encode(
        x=alt.X('latency_ms', bin=alt.Bin(maxbins=30)),
        y='count()'
        )
        st.altair_chart(chart, use_container_width=True, width='stretch')

        st.subheader("Hallucination Trend")
        hall_chart = alt.Chart(df).mark_line().encode(
        x='timestamp',
        y='hallucination'
    )
        st.altair_chart(hall_chart, use_container_width=True, width='stretch')

        st.subheader("Top User Queries")
        st.dataframe(df[['query', 'latency_ms', 'confidence', 'hallucination']].head(20))
    else:
        st.info("No logs available yet.")
# ────────────────────────
#  Footer
# ────────────────────────
st.markdown("""
<div class='footer'>
    &copy; 2025 • Developed by <strong>Muhammad Khubaib Ahmad</strong> | QueryVault
</div>
""", unsafe_allow_html=True)
