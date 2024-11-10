// src/ProtectedRoute.js
import React from "react";
import { Navigate } from "react-router-dom";

const ProtectedRoute = ({ children }) => {
  const token = localStorage.getItem("token"); // Check for token in local storage

  if (!token) {
    return <Navigate to="/login" />; // Redirect to login if token is missing
  }

  return children; // Render the child component if token is present
};

export default ProtectedRoute;
