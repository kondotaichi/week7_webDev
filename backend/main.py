from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from models import Base, User, Thread, Message
import datetime
import os
import requests

from dotenv import load_dotenv
load_dotenv()
GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")


app = FastAPI()

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

DATABASE_URL = "sqlite:///./chatapp.db"
engine = create_engine(DATABASE_URL, connect_args={"check_same_thread": False})
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")


class UserCreate(BaseModel):
    uid: str
    email: str
    name: str


@app.post("/register")
def register_user(user: UserCreate):
    db = SessionLocal()
    existing_user = db.query(User).filter(User.uid == user.uid).first()
    if existing_user:
        db.close()
        raise HTTPException(status_code=400, detail="User already exists")
    new_user = User(uid=user.uid, email=user.email, name=user.name)
    db.add(new_user)
    db.commit()
    db.close()
    return {"message": "User registered successfully"}


@app.get("/threads")
def get_threads(uid: str):
    db = SessionLocal()
    user = db.query(User).filter(User.uid == uid).first()
    if not user:
        db.close()
        raise HTTPException(status_code=404, detail="User not found")
    threads = db.query(Thread).filter(Thread.user_id == user.id).all()
    db.close()
    return [{"id": t.id, "title": t.title} for t in threads]


class ThreadCreate(BaseModel):
    uid: str
    title: str


@app.post("/threads")
def create_thread(thread: ThreadCreate):
    db = SessionLocal()
    user = db.query(User).filter(User.uid == thread.uid).first()
    if not user:
        db.close()
        raise HTTPException(status_code=404, detail="User not found")
    new_thread = Thread(user_id=user.id, title=thread.title, created_at=datetime.datetime.utcnow())
    db.add(new_thread)
    db.commit()
    db.close()
    return {"message": "Thread created successfully"}


@app.get("/messages")
def get_messages(thread_id: int):
    db = SessionLocal()
    messages = db.query(Message).filter(Message.thread_id == thread_id).all()
    db.close()
    return [{"id": m.id, "sender_type": m.sender_type, "content": m.content} for m in messages]


class MessageCreate(BaseModel):
    thread_id: int
    content: str


@app.post("/messages")
def add_message(message: MessageCreate):
    db = SessionLocal()
    past_messages = db.query(Message).filter(Message.thread_id == message.thread_id).all()
    context = "\n".join([f"{m.sender_type}: {m.content}" for m in past_messages])

    gemini_payload = {
        "contents": [{"parts": [{"text": f"{context}\nuser: {message.content}"}]}]
    }

    gemini_response = requests.post(
        f"https://generativelanguage.googleapis.com/v1beta/models/gemini-2.0-flash:generateContent?key={GEMINI_API_KEY}",
        json=gemini_payload
    )

    gemini_result = gemini_response.json()
    ai_reply = gemini_result.get("candidates", [{}])[0].get("content", {}).get("parts", [{}])[0].get("text", "エラー")

    user_message = Message(
        thread_id=message.thread_id,
        sender_type="user",
        content=message.content,
        timestamp=datetime.datetime.utcnow()
    )
    assistant_message = Message(
        thread_id=message.thread_id,
        sender_type="assistant",
        content=ai_reply,
        timestamp=datetime.datetime.utcnow()
    )
    db.add(user_message)
    db.add(assistant_message)
    db.commit()
    db.close()

    return {"reply": ai_reply}
