import os
import time
import jwt
import psycopg2

from flask import Flask, request, jsonify

app = Flask(__name__)

DB_HOST = os.getenv("DB_HOST", "postgres-service")
DB_USER = os.getenv("DB_USER", "shopping")
DB_PASSWORD = os.getenv("DB_PASSWORD", "change-me")
JWT_SECRET = os.getenv("JWT_SECRET", "development-secret")


def get_connection():
    return psycopg2.connect(
        host=DB_HOST,
        dbname="product_db",
        user=DB_USER,
        password=DB_PASSWORD
    )


def initialize_database():
    for attempt in range(20):
        try:
            with get_connection() as conn:
                with conn.cursor() as cur:
                    cur.execute("""
                        CREATE TABLE IF NOT EXISTS products (
                            id SERIAL PRIMARY KEY,
                            name VARCHAR(150) NOT NULL,
                            category VARCHAR(100),
                            description TEXT,
                            price NUMERIC(10,2) NOT NULL,
                            stock INTEGER NOT NULL DEFAULT 0
                        )
                    """)

                    cur.execute("""
                        INSERT INTO products
                            (name, category, description, price, stock)
                        SELECT
                            'Laptop',
                            'Electronics',
                            'Business laptop',
                            55000,
                            10
                        WHERE NOT EXISTS (
                            SELECT 1 FROM products
                        )
                    """)

            return

        except psycopg2.OperationalError:
            time.sleep(3)

    raise RuntimeError("Could not connect to product database")


def authenticated():
    header = request.headers.get("Authorization", "")

    if not header.startswith("Bearer "):
        return None

    try:
        return jwt.decode(
            header.split(" ", 1)[1],
            JWT_SECRET,
            algorithms=["HS256"]
        )
    except jwt.InvalidTokenError:
        return None


@app.get("/health")
def health():
    return jsonify({"status": "healthy"})


@app.get("/api/products")
def list_products():
    with get_connection() as conn:
        with conn.cursor() as cur:
            cur.execute("""
                SELECT id, name, category, description, price, stock
                FROM products
                ORDER BY id
            """)

            rows = cur.fetchall()

    return jsonify([
        {
            "id": r[0],
            "name": r[1],
            "category": r[2],
            "description": r[3],
            "price": float(r[4]),
            "stock": r[5]
        } for r in rows
    ])


@app.get("/api/products/search")
def search_products():
    query = request.args.get("q", "").strip()

    with get_connection() as conn:
        with conn.cursor() as cur:
            cur.execute("""
                SELECT id, name, category, description, price, stock
                FROM products
                WHERE name ILIKE %s OR category ILIKE %s
            """, (f"%{query}%", f"%{query}%"))

            rows = cur.fetchall()

    return jsonify([
        {
            "id": r[0],
            "name": r[1],
            "category": r[2],
            "description": r[3],
            "price": float(r[4]),
            "stock": r[5]
        } for r in rows
    ])


@app.get("/api/products/<int:product_id>")
def get_product(product_id):
    with get_connection() as conn:
        with conn.cursor() as cur:
            cur.execute("""
                SELECT id, name, category, description, price, stock
                FROM products
                WHERE id = %s
            """, (product_id,))

            r = cur.fetchone()

    if not r:
        return jsonify({"error": "Product not found"}), 404

    return jsonify({
        "id": r[0],
        "name": r[1],
        "category": r[2],
        "description": r[3],
        "price": float(r[4]),
        "stock": r[5]
    })


@app.post("/api/products")
def add_product():
    if not authenticated():
        return jsonify({"error": "Valid JWT required"}), 401

    data = request.get_json(silent=True) or {}

    if not data.get("name") or data.get("price") is None:
        return jsonify({"error": "Name and price are required"}), 400

    with get_connection() as conn:
        with conn.cursor() as cur:
            cur.execute("""
                INSERT INTO products
                    (name, category, description, price, stock)
                VALUES (%s, %s, %s, %s, %s)
                RETURNING id
            """, (
                data["name"],
                data.get("category", ""),
                data.get("description", ""),
                data["price"],
                data.get("stock", 0)
            ))

            product_id = cur.fetchone()[0]

    return jsonify({
        "message": "Product added",
        "id": product_id
    }), 201


@app.put("/api/products/<int:product_id>")
def update_product(product_id):
    if not authenticated():
        return jsonify({"error": "Valid JWT required"}), 401

    data = request.get_json(silent=True) or {}

    with get_connection() as conn:
        with conn.cursor() as cur:
            cur.execute("""
                UPDATE products
                SET name=%s, category=%s, description=%s,
                    price=%s, stock=%s
                WHERE id=%s
            """, (
                data.get("name", ""),
                data.get("category", ""),
                data.get("description", ""),
                data.get("price", 0),
                data.get("stock", 0),
                product_id
            ))

            if cur.rowcount == 0:
                return jsonify({"error": "Product not found"}), 404

    return jsonify({"message": "Product updated"})


@app.delete("/api/products/<int:product_id>")
def delete_product(product_id):
    if not authenticated():
        return jsonify({"error": "Valid JWT required"}), 401

    with get_connection() as conn:
        with conn.cursor() as cur:
            cur.execute("""
                DELETE FROM products
                WHERE id = %s
            """, (product_id,))

            if cur.rowcount == 0:
                return jsonify({"error": "Product not found"}), 404

    return jsonify({"message": "Product deleted"})


initialize_database()

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000)