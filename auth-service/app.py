import os
import time
import jwt
import psycopg2

from flask import Flask, request, jsonify
from werkzeug.security import generate_password_hash, check_password_hash
from datetime import datetime, timedelta, timezone

app = Flask(__name__)

DB_HOST = os.getenv("DB_HOST", "postgres-service")
DB_USER = os.getenv("DB_USER", "shopping")
DB_PASSWORD = os.getenv("DB_PASSWORD", "change-me")
JWT_SECRET = os.getenv("JWT_SECRET", "development-secret")


def get_connection():
    return psycopg2.connect(
        host=DB_HOST,
        dbname="auth_db",
        user=DB_USER,
        password=DB_PASSWORD
    )


def initialize_database():
    for attempt in range(20):
        try:
            with get_connection() as conn:
                with conn.cursor() as cur:
                    cur.execute("""
                        CREATE TABLE IF NOT EXISTS users (
                            id SERIAL PRIMARY KEY,
                            username VARCHAR(100) NOT NULL,
                            email VARCHAR(150) UNIQUE NOT NULL,
                            password_hash TEXT NOT NULL
                        )
                    """)
            return
        except psycopg2.OperationalError:
            time.sleep(3)

    raise RuntimeError("Could not connect to auth database")


def create_token(user_id, email):
    payload = {
        "sub": str(user_id),
        "email": email,
        "exp": datetime.now(timezone.utc) + timedelta(hours=2)
    }

    return jwt.encode(payload, JWT_SECRET, algorithm="HS256")


@app.get("/health")
def health():
    return jsonify({"status": "healthy"})


@app.post("/api/auth/register")
def register():
    data = request.get_json(silent=True) or {}

    username = data.get("username", "").strip()
    email = data.get("email", "").strip().lower()
    password = data.get("password", "")

    if not username or not email or not password:
        return jsonify({"error": "All fields are required"}), 400

    if len(password) < 8:
        return jsonify({"error": "Password must be at least 8 characters"}), 400

    password_hash = generate_password_hash(password)

    try:
        with get_connection() as conn:
            with conn.cursor() as cur:
                cur.execute("""
                    INSERT INTO users (username, email, password_hash)
                    VALUES (%s, %s, %s)
                    RETURNING id
                """, (username, email, password_hash))

                user_id = cur.fetchone()[0]

        return jsonify({
            "message": "Registration successful",
            "user_id": user_id
        }), 201

    except psycopg2.errors.UniqueViolation:
        return jsonify({"error": "Email already registered"}), 409


@app.post("/api/auth/login")
def login():
    data = request.get_json(silent=True) or {}

    email = data.get("email", "").strip().lower()
    password = data.get("password", "")

    with get_connection() as conn:
        with conn.cursor() as cur:
            cur.execute("""
                SELECT id, email, password_hash
                FROM users
                WHERE email = %s
            """, (email,))

            user = cur.fetchone()

    if not user or not check_password_hash(user[2], password):
        return jsonify({"error": "Invalid email or password"}), 401

    token = create_token(user[0], user[1])

    return jsonify({
        "message": "Login successful",
        "token": token
    })


@app.get("/api/auth/profile")
def profile():
    auth_header = request.headers.get("Authorization", "")

    if not auth_header.startswith("Bearer "):
        return jsonify({"error": "Missing bearer token"}), 401

    token = auth_header.split(" ", 1)[1]

    try:
        payload = jwt.decode(
            token,
            JWT_SECRET,
            algorithms=["HS256"]
        )
    except jwt.InvalidTokenError:
        return jsonify({"error": "Invalid or expired token"}), 401

    with get_connection() as conn:
        with conn.cursor() as cur:
            cur.execute("""
                SELECT id, username, email
                FROM users
                WHERE id = %s
            """, (payload["sub"],))

            user = cur.fetchone()

    if not user:
        return jsonify({"error": "User not found"}), 404

    return jsonify({
        "id": user[0],
        "username": user[1],
        "email": user[2]
    })


initialize_database()

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000)