// src/Login.js
import React, { useState } from "react";
import axios from "axios";
import { useNavigate, Link } from "react-router-dom";
import "./Login.css";  // Import the CSS file here

function Login() {
  const navigate = useNavigate();
  const [username, setUsername] = useState("");
  const [password, setPassword] = useState("");

  const handleLogin = async (e) => {
    e.preventDefault();
    try {
      const response = await axios.post("http://localhost:8000/login", { username, password });
      localStorage.setItem("token", response.data.access_token);
      localStorage.setItem("username", username);
      navigate("/");  // Navigate to home page on successful login
    } catch (error) {
      console.error("Login error:", error);
      alert("Invalid username or password");
    }
  };

  return (
    <div className="container">
      <div className="card">
        <h2 className="title">Login</h2>
        <form onSubmit={handleLogin} className="form">
          <input
            type="text"
            placeholder="Username"
            value={username}
            onChange={(e) => setUsername(e.target.value)}
            required
            className="input"
          />
          <input
            type="password"
            placeholder="Password"
            value={password}
            onChange={(e) => setPassword(e.target.value)}
            required
            className="input"
          />
          <button type="submit" className="button">Login</button>
        </form>
        <p className="signupText">
          Don’t have an account? <Link to="/signup" className="signupLink">Sign up</Link>
        </p>
      </div>
    </div>
  );
}

export default Login;