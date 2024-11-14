import React, { useRef, useEffect } from "react";
import { useNavigate } from "react-router-dom";  // Import useNavigate
import "./EmotionRecognition.css";
import logo from './logo.svg';
import * as tf from "@tensorflow/tfjs";
import Webcam from "react-webcam";
import { drawMesh } from "./utilities";
import Logout from "./Logout";

function EmotionRecognition() {
  const webcamRef = useRef(null);
  const canvasRef = useRef(null);
  const blazeface = require('@tensorflow-models/blazeface');
  const navigate = useNavigate();  // Initialize navigate function

  const runFaceDetectorModel = async () => {
    const model = await blazeface.load();
    console.log("FaceDetection Model Loaded.");
    setInterval(() => {
      detect(model);
    }, 100);
  };

  const detect = async (net) => {
    if (
      webcamRef.current &&
      webcamRef.current.video.readyState === 4
    ) {
      const video = webcamRef.current.video;
      const videoWidth = video.videoWidth;
      const videoHeight = video.videoHeight;

      webcamRef.current.video.width = videoWidth;
      webcamRef.current.video.height = videoHeight;
      canvasRef.current.width = videoWidth;
      canvasRef.current.height = videoHeight;

      const face = await net.estimateFaces(video);
      const socket = new WebSocket('ws://localhost:8000');
      const imageSrc = webcamRef.current.getScreenshot();
      const username = localStorage.getItem('username');
      const apiCall = {
        event: "localhost:subscribe",
        data: { 
          image: imageSrc,
          username: username
        },
      };

      socket.onopen = () => socket.send(JSON.stringify(apiCall));
      socket.onmessage = function(event) {
        const predLog = JSON.parse(event.data);
        const emotions = ["Angry", "Neutral", "Happy", "Fear", "Surprise", "Sad", "Disgust"];
        emotions.forEach(emotion => {
          document.getElementById(emotion).value = Math.round(predLog['predictions'][emotion.toLowerCase()] * 100);
        });
        document.getElementById("emotion_text").value = predLog['emotion'];
        
        const ctx = canvasRef.current.getContext("2d");
        requestAnimationFrame(() => drawMesh(face, predLog, ctx));
      };
    }
  };

  useEffect(() => {
    runFaceDetectorModel();
  }, []);

  const navigateToUserPage = () => {
    navigate('/user');  // Navigate to the user page
  };

  return (
    <div className="emotion-recognition">
      <Webcam ref={webcamRef} className="webcam" />
      <canvas ref={canvasRef} className="canvas" />

      <header className="header">
        <img src={logo} className="logo" alt="logo" />
        <div className="emotion-container">
          {["Angry", "Neutral", "Happy", "Fear", "Surprise", "Sad", "Disgust"].map((emotion) => (
            <div className="emotion-bar" key={emotion}>
              <label htmlFor={emotion} className="emotion-label" style={{ color: getEmotionColor(emotion) }}>
                {emotion}
              </label>
              <progress id={emotion} value="0" max="100" className="progress-bar" />
            </div>
          ))}
        </div>
        <input id="emotion_text" className="emotion-text" readOnly />
        <div className="logout-button">
          <Logout />
        </div>
        {/* Add the new button for navigation */}
        <button onClick={navigateToUserPage} className="redirect-button">
          Go to User Page
        </button>
      </header>
    </div>
  );
}

function getEmotionColor(emotion) {
  const colors = {
    Angry: "red",
    Neutral: "lightgreen",
    Happy: "orange",
    Fear: "lightblue",
    Surprise: "yellow",
    Sad: "gray",
    Disgust: "pink",
  };
  return colors[emotion];
}

export default EmotionRecognition;