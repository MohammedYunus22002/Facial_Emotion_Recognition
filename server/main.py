import json
import base64
import pytz  
from typing import Optional
from fastapi import FastAPI, WebSocket, WebSocketDisconnect, Depends, HTTPException, status
from pydantic import BaseModel
from passlib.context import CryptContext
from jose import JWTError, jwt
from datetime import datetime, timedelta
import motor.motor_asyncio  
import cv2
import numpy as np
from dotenv import load_dotenv
import os
from fastapi.middleware.cors import CORSMiddleware
import tensorflow as tf
import asyncio

# Load environment variables
load_dotenv()

# App setup
app = FastAPI()

# TensorFlow model setup
model_path = r'./best_model.h5'
model = tf.keras.models.load_model(model_path)

# Emotion list and color mapping
emotions = ['Angry', 'Disgust', 'Fear', 'Happy', 'Sad', 'Surprise', 'Neutral']
emotion_colors = {
    'Angry': '#FF0000',
    'Disgust': '#00FF00',
    'Fear': '#0000FF',
    'Happy': '#FFFF00',
    'Sad': '#000080',
    'Surprise': '#FFA500',
    'Neutral': '#808080'
}

SECRET_KEY = os.getenv("SECRET_KEY")
ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = 30

# Custom CORS middleware for selective route control
class SelectiveCORSMiddleware(CORSMiddleware):
    async def dispatch(self, request, call_next):
        if "/users/" in request.url.path or "/EmotionRecognition" in request.url.path:
            response = await call_next(request)
            response.headers["Access-Control-Allow-Origin"] = "http://localhost:3000"  # Your frontend URL
            response.headers["Access-Control-Allow-Credentials"] = "true"
            return response
        else:
            return await super().dispatch(request, call_next)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000"],  
    allow_credentials=True, 
    allow_methods=["*"],  
    allow_headers=["*"],
)

# MongoDB connection setup
MONGO_URL = os.getenv("MONGO_URL")
client = motor.motor_asyncio.AsyncIOMotorClient(MONGO_URL)
db = client["emotion_app"]
users_collection = db["users"]
emotions_collection = db["emotions"]

# CryptContext for password hashing
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

# User and Token models
class User(BaseModel):
    username: str
    password: str
    emotion: Optional[str] = None  
    emotion_timestamp: Optional[datetime] = None

class Token(BaseModel):
    access_token: str
    token_type: str

class Emotion(BaseModel):
    username: str
    emotion: str
    timestamp: datetime

# Utility functions
def user_to_model(user_data):
    user_data["id"] = str(user_data["_id"])
    return User(**user_data)

def verify_password(plain_password, hashed_password):
    return pwd_context.verify(plain_password, hashed_password)

def get_password_hash(password):
    return pwd_context.hash(password)

def create_access_token(data: dict, expires_delta: Optional[timedelta] = None):
    to_encode = data.copy()
    local_timezone = pytz.timezone("Asia/Kolkata")
    if expires_delta:
        expire = datetime.now(local_timezone) + expires_delta
    else:
        expire = datetime.now(local_timezone) + timedelta(minutes=15)
    to_encode.update({"exp": expire})
    encoded_jwt = jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)
    return encoded_jwt

async def authenticate_user(username: str, password: str):
    user = await users_collection.find_one({"username": username})
    if user is None or not verify_password(password, user["password"]):
        return False
    return user

# Signup endpoint
@app.post("/signup")
async def signup(user: User):
    existing_user = await users_collection.find_one({"username": user.username})
    if existing_user:
        raise HTTPException(status_code=400, detail="Username already registered")
    hashed_password = get_password_hash(user.password)
    user_data = {"username": user.username, "password": hashed_password}
    await users_collection.insert_one(user_data)
    return {"msg": "User registered successfully"}

# Login endpoint
@app.post("/login", response_model=Token)
async def login(user: User):
    user_data = await authenticate_user(user.username, user.password)
    if not user_data:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect username or password",
            headers={"WWW-Authenticate": "Bearer"},
        )
    access_token_expires = timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    access_token = create_access_token(
        data={"sub": user.username}, expires_delta=access_token_expires
    )
    return {"access_token": access_token, "token_type": "bearer"}

@app.websocket("/")
async def websocket_endpoint(websocket: WebSocket):
    await websocket.accept()
    local_timezone = pytz.timezone("Asia/Kolkata")
    last_store_time = datetime.now(local_timezone)
    print("WebSocket connection established.")
    
    try:
        while True:
            try:
                payload = await asyncio.wait_for(websocket.receive_text(), timeout=30)
                payload = json.loads(payload)
                imageByt64 = payload['data']['image'].split(',')[1]
                image = np.frombuffer(base64.b64decode(imageByt64), np.uint8)
                image = cv2.imdecode(image, cv2.IMREAD_COLOR)

                username = payload.get("data", {}).get("username", "").strip()

                gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
                face_cascade = cv2.CascadeClassifier(cv2.data.haarcascades + 'haarcascade_frontalface_default.xml')
                faces = face_cascade.detectMultiScale(gray, 1.3, 5)

                for (x, y, w, h) in faces:
                    roi_gray = gray[y:y+h, x:x+w]
                    roi_gray = cv2.resize(roi_gray, (48, 48))
                    roi = roi_gray.astype('float') / 255.0
                    roi = np.expand_dims(roi, axis=0)
                    roi = np.expand_dims(roi, axis=-1)
                    prediction = model.predict(roi, verbose=0)[0]
                    current_emotion = emotions[prediction.argmax()]

                    print(f"Detected emotion: {current_emotion}")

                    current_time = datetime.now(local_timezone)
                    if username:
                        user = await users_collection.find_one({"username": username})
                        if user:
                            await users_collection.update_one(
                                {"username": username},
                                {
                                    "$set": {
                                        "emotion": current_emotion,
                                        "emotion_timestamp": current_time
                                    }
                                }
                            )
                            last_store_time = current_time

                    emotion_color = emotion_colors.get(current_emotion, '#FFFFFF')

                    response = {
                        "predictions": prediction.tolist(),
                        "emotion": current_emotion,
                        "color": emotion_color
                    }

                    await websocket.send_json(response)

            except asyncio.TimeoutError:
                print("No data received for 30 seconds. Sending ping to keep connection alive.")
                await websocket.send_json({"message": "ping"})

    except WebSocketDisconnect:
        print("WebSocket connection closed.")
    except Exception as e:
        print(f"Error in WebSocket connection: {e}")
    finally:
        await websocket.close()
        print("WebSocket connection closed gracefully.")

# Dependency to get current user
async def get_current_user(token: str = Depends()):
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Could not validate credentials",
        headers={"WWW-Authenticate": "Bearer"},
    )
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        username: str = payload.get("sub")
        if username is None:
            raise credentials_exception
    except JWTError:
        raise credentials_exception
    user = await users_collection.find_one({"username": username})
    if user is None:
        raise credentials_exception
    return user

# Get unique user by username
@app.get("/users/{username}")
async def get_user(username: str):
    user = await users_collection.find_one({"username": {"$regex": f"^{username}$", "$options": "i"}})
    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User not found"
        )
    user_data = {
        "username": user["username"],
        "emotion": user.get("emotion"),
        "emotion_timestamp": user.get("emotion_timestamp")
    }
    return {"user": user_data}

@app.get("/users")
async def get_users():
    users_cursor = users_collection.find()
    users_list = []
    async for user in users_cursor:
        user_data = {
            "username": user["username"],
            "emotion": user.get("emotion"),
            "emotion_timestamp": user.get("emotion_timestamp")
        }
        users_list.append(user_data)
    return {"users": users_list}