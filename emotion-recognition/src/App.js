// src/App.js
import React from "react";
import { BrowserRouter as Router, Route, Routes } from "react-router-dom";
import EmotionRecognition from "./EmotionRecognition";
import Login from "./Login";
import Signup from "./Signup";

function App() {
  return (
    <Router>
      <Routes>
        <Route path="/" element={<EmotionRecognition />} />
        <Route path="/login" element={<Login />} />
        <Route path="/signup" element={<Signup />} />
      </Routes>
    </Router>
  );
}

export default App;
