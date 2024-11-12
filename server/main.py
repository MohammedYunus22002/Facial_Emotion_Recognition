
import json
import base64
from typing import Optional
from fastapi import FastAPI, WebSocket, Depends, HTTPException, status
from pydantic import BaseModel
from passlib.context import CryptContext
from jose import JWTError, jwt
from datetime import datetime, timedelta
import motor.motor_asyncio  
import cv2
import numpy as np
from fer import FER
from dotenv import load_dotenv
import os
from fastapi.middleware.cors import CORSMiddleware
from starlette.middleware.base import BaseHTTPMiddleware
from fastapi import Request

# Load environment variables
load_dotenv()

# App setup
app = FastAPI()
detector = FER()
SECRET_KEY = os.getenv("SECRET_KEY")
ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = 30

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
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
    user_data["id"] = str(user_data["_id"])  # Convert _id to id string
    return User(**user_data)
def verify_password(plain_password, hashed_password):
    return pwd_context.verify(plain_password, hashed_password)

def get_password_hash(password):
    return pwd_context.hash(password)

def create_access_token(data: dict, expires_delta: Optional[timedelta] = None):
    to_encode = data.copy()
    if expires_delta:
        expire = datetime.utcnow() + expires_delta
    else:
        expire = datetime.utcnow() + timedelta(minutes=15)
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

# Emotion detection with WebSocket
@app.websocket("/")
async def websocket_endpoint(websocket: WebSocket):
    await websocket.accept()
    last_store_time = datetime.utcnow()  # Initialize the last store timestamp
    try:
        # Authenticate user with token
        while True:
            # Continue with emotion detection
            payload = await websocket.receive_text()
            payload = json.loads(payload)
            imageByt64 = payload['data']['image'].split(',')[1]
            # decode and convert into image
            image = np.fromstring(base64.b64decode(imageByt64), np.uint8)
            image = cv2.imdecode(image, cv2.IMREAD_COLOR)

            # Extract the token from the already parsed payload
            username = payload.get("data", {}).get("username", "").strip()

            # Detect Emotion via Tensorflow model
            prediction = detector.detect_emotions(image)

            # Get dominant emotion
            current_emotion = max(prediction[0]['emotions'], key=prediction[0]['emotions'].get)
            current_time = datetime.utcnow()
            if (current_time - last_store_time).seconds >= 3:
                # Fetch the user document from the users collection using the username
                user = await users_collection.find_one({"username": {"$regex": f"^{username}$", "$options": "i"}})

                print(f"Users fetched from database: {user}")
                if user:
                    try:
                        updated_user = await users_collection.update_one(
                            {"username": username},
                            {
                                "$set": {
                                    "emotion": current_emotion,
                                    "emotion_timestamp": current_time
                                }
                            }
                        )
                        if updated_user.modified_count == 0:
                            print(f"No update for {username}, maybe no change in emotion.")
                        else:
                            print(f"Emotion for {username} updated successfully.")
                    except Exception as e:
                        print(f"Error updating emotion for {username}: {e}")


                    last_store_time = current_time

                
            response = {
                "predictions": prediction[0]['emotions'],
                "emotion": max(prediction[0]['emotions'], key=prediction[0]['emotions'].get)
            }
            await websocket.send_json(response)
            await websocket.close()
    
    except Exception as e:
        print(f"Error in WebSocket connection: {e}")
    finally:
        await websocket.close()

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
    
    # Return the user data including the optional fields
    user_data = {
        "username": user["username"],
        "emotion": user.get("emotion"),  # Optional field
        "emotion_timestamp": user.get("emotion_timestamp")  # Optional field
    }
    return {"user": user_data}


@app.get("/users")
async def get_users():
    # Query to get all users from the users collection
    users_cursor = users_collection.find()
    
    # Convert the cursor into a list of user data
    users_list = []
    async for user in users_cursor:
        # Only include necessary fields (avoid sending passwords)
        user_data = {
            "username": user["username"],
            # You can add more fields as needed, e.g., "emotion", "last_updated" etc.
        }
        users_list.append(user_data)

    return {"users": users_list}