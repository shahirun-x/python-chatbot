from sqlalchemy import create_engine, Column, Integer, String, Text, DateTime, ForeignKey
from sqlalchemy.orm import declarative_base, sessionmaker, relationship
from datetime import datetime


# --- Database Setup ---
DATABASE_URL = "sqlite:///./chatbot.db"
engine = create_engine(DATABASE_URL, connect_args={"check_same_thread": False})
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
Base = declarative_base()

# --- Table Definitions (Models) ---

class Conversation(Base):
    __tablename__ = "conversations"

    id = Column(Integer, primary_key=True, index=True)
    session_id = Column(String, unique=True, index=True)
    created_at = Column(DateTime, default=datetime.utcnow)

    # This creates a link between a Conversation and its Messages
    messages = relationship("Message", back_populates="conversation")

class Message(Base):
    __tablename__ = "messages"

    id = Column(Integer, primary_key=True, index=True)
    conversation_id = Column(Integer, ForeignKey("conversations.id"))
    sender = Column(String, nullable=False) # "user" or "bot"
    text = Column(Text, nullable=False)
    timestamp = Column(DateTime, default=datetime.utcnow)

    # This links a Message back to its parent Conversation
    conversation = relationship("Conversation", back_populates="messages")

# --- Function to create the database tables ---
def create_db_and_tables():
    Base.metadata.create_all(bind=engine)