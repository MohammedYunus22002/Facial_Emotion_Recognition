// src/App.js
import React from "react";
import { BrowserRouter as Router, Route, Routes } from "react-router-dom";
import EmotionRecognition from "./EmotionRecognition";
import Login from "./Login";
import Signup from "./Signup";
import ProtectedRoute from "./ProtectedRoute"; 

function App() {
  return (
    <Router>
      <Routes>
      <Route
          path="/"
          element={
            <ProtectedRoute>
              <EmotionRecognition />
            </ProtectedRoute>
          }
        />
        <Route path="/login" element={<Login />} />
        <Route path="/signup" element={<Signup />} />
      </Routes>
    </Router>
  );
}

export default App;
