// src/User.js
import React, { useState, useEffect } from "react";
import axios from "axios";
import { useNavigate } from "react-router-dom";

function User() {
  const [userData, setUserData] = useState(null);
  const [error, setError] = useState(null);
  const username = localStorage.getItem('username');
  const token = localStorage.getItem('token');


  // Fetch user data on component mount
  useEffect(() => {
    const getUser = async () => {
      try {
        const response = await axios.get(`http://localhost:8000/users/${username}`, {
            headers: { Authorization: 'Bearer ' + token },
            withCredentials: true 
          });
        console.log(response + "This is response"); // Log response to debug
        setUserData(response.data.user);
    } catch (error) {
        setError("Failed to fetch user data");
  
        // Check if error.response exists (for HTTP errors)
        if (error.response) {
          console.error("Error response:", error.response);
          console.error("Response status:", error.response.status);
          console.error("Response data:", error.response.data);
        } else {
          // Log the error message if there is no response (network errors, etc.)
          console.error("Error message:", error.message);
        }
        
        // Log the complete error object for further debugging
        console.error("Full error object:", error);
      }
    };

    if (username) {
      getUser();
    } else {
      setError("Username not found.");
    }
  }, [username]);

  return (
    <div style={styles.container}>
      {error ? (
        <div style={styles.errorMessage}>{error}</div>
      ) : userData ? (
        <div style={styles.card}>
          <h2 style={styles.title}>{userData.username}</h2>
          <p style={styles.detail}>Emotion: {userData.emotion || "Not detected"}</p>
          <p style={styles.detail}>
            Last Update: {userData.emotion_timestamp ? new Date(userData.emotion_timestamp).toLocaleString() : "Not available"}
          </p>
        </div>
      ) : (
        <div>Loading...</div>
      )}
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
  detail: {
    fontSize: "1rem",
    color: "#555",
    marginBottom: "0.8rem",
  },
  errorMessage: {
    color: "#e74c3c",
    fontSize: "1.2rem",
    textAlign: "center",
  },
};

export default User;
