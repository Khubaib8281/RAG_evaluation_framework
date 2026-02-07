def generate_answer_from_chunks_local(chunks, question):
    import requests
    import time

    context = "\n\n".join(chunks)

    prompt = f"""
You are a document question-answering assistant.
Your task is to use the provided context to respond to the user's question as completely and accurately as possible.

Rules:
1. If the user asks to "show full content" → return the context exactly.
2. If the user asks to summarize or explain → simplify the relevant parts.
3. Otherwise, answer directly using only the context.

If the answer is not in the context, reply exactly:
"The document does not provide this information."

Context:
{context}

Question:
{question}

Answer:
"""

    payload = {
        "model": "tinyllama",  # llama-server ignores name, but keep it
        "messages": [
            {"role": "system", "content": "You are a helpful assistant."},
            {"role": "user", "content": prompt}
        ],
        "temperature": 0.7,
        "top_p": 0.9,
        "max_tokens": 256,
        "stream": False
    }

    start = time.perf_counter()

    response = requests.post(
        "http://127.0.0.1:8080/v1/chat/completions",
        json=payload,
        timeout=120
    )

    latency_ms = (time.perf_counter() - start) * 1000

    if response.status_code != 200:
        raise RuntimeError(f"Local LLM error: {response.text}")

    data = response.json()

    answer = data["choices"][0]["message"]["content"].strip()
    tokens_used = data.get("usage", {}).get("total_tokens", None)

    return {
        "text": answer,
        "latency_ms": latency_ms,
        "tokens_used": tokens_used,
        "provider": "local"
    }
