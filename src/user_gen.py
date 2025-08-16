#!/usr/bin/env python3
import uuid
import sys
import pymysql

# === Config ===
DB_HOST = "127.0.0.1"
DB_USER = "chatuser"
DB_PASS = "chatpass"
DB_NAME = "chatdb"
CHAT_BASE_URL = "http://0.0.0.0:8000/chat"

# === UUID handling ===
if len(sys.argv) > 1:
    user_id = sys.argv[1]
else:
    user_id = str(uuid.uuid4())

# Generate a sessionId
session_id = str(uuid.uuid4())

# === DB insert ===
conn = pymysql.connect(host=DB_HOST, user=DB_USER, password=DB_PASS, database=DB_NAME)

try:
    with conn.cursor() as cur:
        # Insert the user (if not exists)
        cur.execute("INSERT IGNORE INTO users (user_id) VALUES (%s)", (user_id,))
        # Insert the session
        cur.execute(
            "INSERT INTO chat_sessions (session_id, user_id) VALUES (%s, %s)",
            (session_id, user_id),
        )
        conn.commit()
    print(f"[✔] User created: {user_id}")
    print(f"[✔] Session created: {session_id}")
    print(f"[→] Chat URL: {CHAT_BASE_URL}?userId={user_id}&sessionId={session_id}")
finally:
    conn.close()
