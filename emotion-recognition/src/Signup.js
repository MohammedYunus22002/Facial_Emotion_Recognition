// src/Signup.js
import React, { useState } from "react";
import axios from "axios";
import { useNavigate, Link } from "react-router-dom";


function Signup() {
  const navigate = useNavigate();
  const [username, setUsername] = useState("");
  const [password, setPassword] = useState("");

  const handleSignup = async (e) => {
    e.preventDefault();
    try {
      await axios.post("http://localhost:8000/signup", { username, password });
      alert("Signup successful! Please log in.");
      navigate("/login");
    } catch (error) {
      console.error("Signup error:", error);
      alert("Username already taken or invalid.");
    }
  };

  return (
    <div style={styles.container}>
      <div style={styles.card}>
        <h2 style={styles.title}>Signup</h2>
        <form onSubmit={handleSignup} style={styles.form}>
          <input
            type="text"
            placeholder="Username"
            value={username}
            onChange={(e) => setUsername(e.target.value)}
            required
            style={styles.input}
          />
          <input
            type="password"
            placeholder="Password"
            value={password}
            onChange={(e) => setPassword(e.target.value)}
            required
            style={styles.input}
          />
          <button type="submit" style={styles.button}>Signup</button>
        </form>
        <p style={styles.loginText}>
          Already have an account? <Link to="/login" style={styles.loginLink}>Log in</Link>
        </p>
      </div>
    </div>
  );
}

const styles = {
  container: {
    display: "flex",
    alignItems: "center",
    justifyContent: "center",
    height: "100vh",
    backgroundColor: "#f4f4f9",
  },
  card: {
    width: "400px",
    padding: "2rem",
    borderRadius: "8px",
    boxShadow: "0 4px 8px rgba(0, 0, 0, 0.2)",
    backgroundColor: "#fff",
    textAlign: "center",
  },
  title: {
    marginBottom: "1rem",
    fontSize: "1.8rem",
    color: "#333",
  },
  form: {
    display: "flex",
    flexDirection: "column",
  },
  input: {
    marginBottom: "1rem",
    padding: "0.8rem",
    fontSize: "1rem",
    borderRadius: "4px",
    border: "1px solid #ddd",
  },
  button: {
    padding: "0.8rem",
    fontSize: "1rem",
    color: "#fff",
    backgroundColor: "#007bff",
    border: "none",
    borderRadius: "4px",
    cursor: "pointer",
  },
  loginText: {
    marginTop: "1rem",
    fontSize: "0.9rem",
    color: "#333",
  },
  loginLink: {
    color: "#007bff",
    textDecoration: "none",
  },
};

export default Signup;
