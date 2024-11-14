// src/User.js
import React, { useState, useEffect } from "react";
import axios from "axios";
import "./User.css";

function User() {
  const [userData, setUserData] = useState(null);
  const [error, setError] = useState(null);
  const username = localStorage.getItem("username");
  const token = localStorage.getItem("token");

  // Fetch user data on component mount
  useEffect(() => {
    const getUser = async () => {
      try {
        const response = await axios.get(`http://localhost:8000/users/${username}`, {
          headers: { Authorization: "Bearer " + token },
          withCredentials: true,
        });
        setUserData(response.data.user);
      } catch (error) {
        setError("Failed to fetch user data");
        if (error.response) {
          console.error("Error response:", error.response);
          console.error("Response status:", error.response.status);
          console.error("Response data:", error.response.data);
        } else {
          console.error("Error message:", error.message);
        }
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
    <div className="user-container">
      {error ? (
        <div className="error-message">{error}</div>
      ) : userData ? (
        <div className="user-card">
          <h2 className="user-title">{userData.username}</h2>
          <p className="user-detail">Emotion: {userData.emotion || "Not detected"}</p>
          <p className="user-detail">
            Last Update: {userData.emotion_timestamp ? new Date(userData.emotion_timestamp).toLocaleString() : "Not available"}
          </p>
        </div>
      ) : (
        <div>Loading...</div>
      )}
    </div>
  );
}

export default User;
