import hashlib
import datetime
import json
from .db import get_connection

def hash_query(query):
    return hashlib.md5(query.encode()).hexdigest()

def get_cache(query):
    conn = get_connection()
    cursor = conn.cursor()
    
    qhash = hash_query(query)
    
    cursor.execute("""SELECT answer, top_chunks FROM cache WHERE query_hash=?""", (qhash,))
    row = cursor.fetchone()
    
    conn.close()
    
    if row:
        return row[0], json.loads(row[1])
    else:
        return None, None
    
def save_cache(query , answer, top_chunks):
    conn = get_connection()
    cursor = conn.cursor()
    
    serialized_chunks = json.dumps(top_chunks, ensure_ascii=False)
    qhash = hash_query(query)
    
    cursor.execute("""INSERT OR REPLACE INTO cache(query_hash, answer, top_chunks, timestamp) VALUES(?, ?, ?, ?)""", (
        qhash,
        answer,
        serialized_chunks,
        datetime.datetime.utcnow().isoformat()
    ))
    
    conn.commit()
    conn.close()