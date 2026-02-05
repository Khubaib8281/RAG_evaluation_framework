import datetime
from core.db import get_connection

def log_request(query, answer, latency_ms, tokens_used, confidence, hallucination):
    conn = get_connection()
    cursor = conn.cursor()
    
    cursor.execute("""
    INSERT INTO requests(timestamp, query, answer, latency_ms, tokens_used, confidence, hallucination)
    VALUES (?, ?, ?, ?, ?, ?, ?)
    """, (
        datetime.datetime.utcnow().isoformat(),
        query,
        answer,
        latency_ms,
        tokens_used,
        confidence,
        hallucination
    ))
    
    conn.commit()
    conn.close()
    
def log_error_message(error_message):
    conn = get_connection()
    cursor = conn.cursor()
    
    cursor.execute("""
        INSERT INTO errors(timestamp, error_message)
        VALUES(?, ?)
    """, (
        datetime.datetime.utcnow().isoformat(),
        error_message
    ))
    
    conn.commit()
    conn.close()