import os
import json
import uuid
import asyncio
import numpy as np
import faiss
import google.generativeai as genai
from dotenv import load_dotenv
from fastapi import FastAPI, HTTPException, Depends, UploadFile, File
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import StreamingResponse
from pydantic import BaseModel
from sentence_transformers import SentenceTransformer
from sqlalchemy.orm import Session
from models import create_db_and_tables, SessionLocal, Conversation, Message
from pypdf import PdfReader
import io

# --- Initialization ---
load_dotenv()
genai.configure(api_key=os.environ["GOOGLE_API_KEY"])
create_db_and_tables()

app = FastAPI()

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# --- Load Models and Data ---
retriever_model = SentenceTransformer('all-MiniLM-L6-v2')
faiss_index = faiss.read_index('knowledge_base.index')
with open('corpus_chunks.json', 'r', encoding='utf-8') as f:
    corpus_chunks = json.load(f)
llm = genai.GenerativeModel('gemini-pro-latest')

# --- Pydantic Models & DB ---
class Query(BaseModel):
    query: str
    session_id: str | None = None

def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
        
@app.get("/")
def read_root():
    return {"status": "Backend is running"}


# --- Streaming RAG API ENDPOINT ---
@app.post("/api/chat")
async def chat_endpoint(query: Query, db: Session = Depends(get_db)):
    user_query = query.query
    session_id = query.session_id
    
    if not session_id:
        session_id = str(uuid.uuid4())
        db.add(Conversation(session_id=session_id))
        db.commit()

    conversation = db.query(Conversation).filter(Conversation.session_id == session_id).first()
    if not conversation:
        raise HTTPException(status_code=404, detail="Conversation not found")

    db.add(Message(conversation_id=conversation.id, sender="user", text=user_query))
    db.commit()

    query_embedding = retriever_model.encode([user_query])
    D, I = faiss_index.search(np.array(query_embedding, dtype=np.float32), k=3)
    retrieved_chunks = [corpus_chunks[i] for i in I[0]]

    history = db.query(Message).filter(Message.conversation_id == conversation.id).order_by(Message.timestamp.desc()).limit(5).all()
    history.reverse()
    chat_history_text = "\n".join([f"{msg.sender}: {msg.text}" for msg in history])

    context_str = ""
    if retrieved_chunks:
        if isinstance(retrieved_chunks[0], dict):
            context_str = ' '.join([str(item) for item in retrieved_chunks])
        else:
            context_str = ' '.join(retrieved_chunks)

    prompt = f"""
You are a friendly Python tutor. Based on the following context, answer the user's question.

**Chat History:**
{chat_history_text}

**Context from Knowledge Base:**
{context_str}

**User's Latest Question:**
{user_query}
"""

    async def stream_generator():
        full_response_text = ""
        try:
            stream = llm.generate_content(prompt, stream=True)
            for chunk in stream:
                if chunk.text:
                    full_response_text += chunk.text
                    yield chunk.text
                    await asyncio.sleep(0.01)
            bot_message = Message(conversation_id=conversation.id, sender="bot", text=full_response_text)
            db.add(bot_message)
            db.commit()
        except Exception as e:
            print(f"An error occurred: {e}")
            yield "Sorry, I ran into an error."
    
    return StreamingResponse(stream_generator(), media_type="text/plain", headers={'X-Session-Id': session_id})

# --- PDF Processing and Chunking Logic ---
def process_pdf(file_bytes: bytes, chunk_size: int = 1000, chunk_overlap: int = 200) -> list[str]:
    """Reads a PDF from bytes, extracts text, and splits it into chunks."""
    text_chunks = []
    try:
        pdf_file = io.BytesIO(file_bytes)
        reader = PdfReader(pdf_file)
        full_text = ""
        for page in reader.pages:
            full_text += page.extract_text() or ""
        
        start = 0
        while start < len(full_text):
            end = start + chunk_size
            text_chunks.append(full_text[start:end])
            start += chunk_size - chunk_overlap
            
    except Exception as e:
        print(f"Error processing PDF: {e}")

    return text_chunks


# --- UPDATED FILE UPLOAD ENDPOINT ---
@app.post("/api/upload")
async def upload_document(file: UploadFile = File(...)):
    print(f"Current Working Directory: {os.getcwd()}")
    if not file.filename:
        raise HTTPException(status_code=400, detail="No file was uploaded.")

    # Only process PDF files for now
    if file.content_type != 'application/pdf':
        raise HTTPException(status_code=400, detail="Only PDF files are supported.")

    print(f"Processing uploaded file: {file.filename}")
    
    # Read the file content into memory
    file_bytes = await file.read()
    
    # Process the PDF to get text chunks
    text_chunks = process_pdf(file_bytes)
    
    if not text_chunks:
        raise HTTPException(status_code=500, detail="Could not extract text from the PDF.")

    # Save the processed chunks to a new JSON file
    output_dir = 'uploaded_data'
    os.makedirs(output_dir, exist_ok=True)
    output_path = os.path.join(output_dir, f"{file.filename}.json")
    
    output_data = {
        "source": file.filename,
        "chunks": text_chunks
    }
    
    with open(output_path, 'w', encoding='utf-8') as f:
        json.dump(output_data, f, indent=2)

    print(f"Successfully processed and saved chunks to {output_path}")

    return {"message": f"File '{file.filename}' processed and saved successfully."}