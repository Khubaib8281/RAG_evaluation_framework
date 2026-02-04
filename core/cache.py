import hashlib
import datetime
from .db import get_connection

def hash_query(query):
    return hashlib.md5(query.encode()).hexdigest()

def get_cache(query):
    conn = get_connection()
    cursor = conn.cursor()
    
    qhash = hash_query(query)
    
    cursor.execute("""SELECT answer FROM cache WHERE query_hash=?""", (qhash,))
    row = cursor.fetchone()
    
    conn.close()
    
    if row:
        return row[0]
    else:
        return None
    
def save_cache(query , answer):
    conn = get_connection()
    cursor = conn.cursor()
    
    qhash = hash_query(query)
    
    cursor.execute("""INSERT OR REPLACE INTO cache(query_hash, answer, timestamp) VALUES(?, ?, ?)""", (
        qhash,
        answer,
        datetime.datetime.utcnow().isoformat()
    ))
    
    conn.commit()
    conn.close()