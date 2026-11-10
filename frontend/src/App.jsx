import React, { useEffect, useState } from "react";

export default function App() {
    const [products, setProducts] = useState([]);
    const [email, setEmail] = useState("");
    const [password, setPassword] = useState("");
    const [message, setMessage] = useState("");
    const [token, setToken] = useState("");

    async function loadProducts() {
        const response = await fetch("/api/products");
        const data = await response.json();
        setProducts(data);
    }

    async function register() {
        const username = email.split("@")[0];

        const response = await fetch("/api/auth/register", {
            method: "POST",
            headers: {
                "Content-Type": "application/json"
            },
            body: JSON.stringify({
                username,
                email,
                password
            })
        });

        const data = await response.json();
        setMessage(data.message || data.error);
    }

    async function login(event) {
        event.preventDefault();

        const response = await fetch("/api/auth/login", {
            method: "POST",
            headers: {
                "Content-Type": "application/json"
            },
            body: JSON.stringify({
                email,
                password
            })
        });

        const data = await response.json();

        if (response.ok) {
            setToken(data.token);
            setMessage("Login successful");
        } else {
            setMessage(data.error || "Login failed");
        }
    }

    useEffect(() => {
        loadProducts().catch(() => {
            setMessage("Unable to load products");
        });
    }, []);

    return (
        <main style={{ fontFamily: "Arial", padding: "30px" }}>
            <h1>Online Shopping Application</h1>

            <h2>Customer Registration and Login</h2>

            <form onSubmit={login}>
                <input
                    type="email"
                    placeholder="Email"
                    value={email}
                    onChange={e => setEmail(e.target.value)}
                    required
                />

                <input
                    type="password"
                    placeholder="Password"
                    value={password}
                    onChange={e => setPassword(e.target.value)}
                    required
                />

                <button type="submit">Login</button>
            </form>

            <button onClick={register}>Register</button>

            <p>{message}</p>

            {token && <p>JWT token received successfully.</p>}

            <h2>Available Products</h2>

            {products.map(product => (
                <div key={product.id}>
                    <h3>{product.name}</h3>
                    <p>{product.category}</p>
                    <p>Price: ₹{product.price}</p>
                    <p>Stock: {product.stock}</p>
                </div>
            ))}
        </main>
    );
}