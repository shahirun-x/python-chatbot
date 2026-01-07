import os
import json
import uuid
import asyncio
import io
import numpy as np
from dotenv import load_dotenv
from fastapi import FastAPI, HTTPException, Depends, UploadFile, File
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import StreamingResponse
from pydantic import BaseModel
from sqlalchemy.orm import Session
from pypdf import PdfReader

from models import create_db_and_tables, SessionLocal, Conversation, Message

# --------------------
# Initialization
# --------------------
load_dotenv()
create_db_and_tables()

app = FastAPI()

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# --------------------
# Lazy-loaded globals
# --------------------
_retriever_model = None
_faiss_index = None
_corpus_chunks = None
_llm = None


def load_rag_components():
    global _retriever_model, _faiss_index, _corpus_chunks, _llm

    if _retriever_model is None:
        from sentence_transformers import SentenceTransformer
        _retriever_model = SentenceTransformer("all-MiniLM-L6-v2")

    if _faiss_index is None:
        import faiss
        _faiss_index = faiss.read_index("knowledge_base.index")

    if _corpus_chunks is None:
        with open("corpus_chunks.json", "r", encoding="utf-8") as f:
            _corpus_chunks = json.load(f)

    if _llm is None:
        import google.generativeai as genai
        genai.configure(api_key=os.environ["GOOGLE_API_KEY"])
        _llm = genai.GenerativeModel("gemini-pro-latest")

    return _retriever_model, _faiss_index, _corpus_chunks, _llm


# --------------------
# Pydantic models
# --------------------
class Query(BaseModel):
    query: str
    session_id: str | None = None


# --------------------
# DB dependency
# --------------------
def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


# --------------------
# Health check
# --------------------
@app.get("/")
def read_root():
    return {"status": "Backend is running"}


# --------------------
# Chat endpoint (Streaming RAG)
# --------------------
@app.post("/api/chat")
async def chat_endpoint(query: Query, db: Session = Depends(get_db)):
    retriever_model, faiss_index, corpus_chunks, llm = load_rag_components()

    user_query = query.query
    session_id = query.session_id

    if not session_id:
        session_id = str(uuid.uuid4())
        db.add(Conversation(session_id=session_id))
        db.commit()

    conversation = db.query(Conversation).filter(
        Conversation.session_id == session_id
    ).first()

    if not conversation:
        raise HTTPException(status_code=404, detail="Conversation not found")

    db.add(
        Message(
            conversation_id=conversation.id,
            sender="user",
            text=user_query,
        )
    )
    db.commit()

    query_embedding = retriever_model.encode([user_query])
    D, I = faiss_index.search(
        np.array(query_embedding, dtype=np.float32), k=3
    )

    retrieved_chunks = [corpus_chunks[i] for i in I[0]]

    history = (
        db.query(Message)
        .filter(Message.conversation_id == conversation.id)
        .order_by(Message.timestamp.desc())
        .limit(5)
        .all()
    )
    history.reverse()

    chat_history_text = "\n".join(
        f"{msg.sender}: {msg.text}" for msg in history
    )

    context_str = ""
    if retrieved_chunks:
        context_str = " ".join(map(str, retrieved_chunks))

    prompt = f"""
You are a friendly Python tutor. Based on the following context, answer the user's question.

Chat History:
{chat_history_text}

Context:
{context_str}

User Question:
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

            db.add(
                Message(
                    conversation_id=conversation.id,
                    sender="bot",
                    text=full_response_text,
                )
            )
            db.commit()
        except Exception as e:
            print(f"Streaming error: {e}")
            yield "Sorry, I ran into an error."

    return StreamingResponse(
        stream_generator(),
        media_type="text/plain",
        headers={"X-Session-Id": session_id},
    )


# --------------------
# PDF processing
# --------------------
def process_pdf(
    file_bytes: bytes,
    chunk_size: int = 1000,
    chunk_overlap: int = 200,
) -> list[str]:
    text_chunks = []
    try:
        reader = PdfReader(io.BytesIO(file_bytes))
        full_text = "".join(
            page.extract_text() or "" for page in reader.pages
        )

        start = 0
        while start < len(full_text):
            end = start + chunk_size
            text_chunks.append(full_text[start:end])
            start += chunk_size - chunk_overlap

    except Exception as e:
        print(f"PDF error: {e}")

    return text_chunks


# --------------------
# Upload endpoint
# --------------------
@app.post("/api/upload")
async def upload_document(file: UploadFile = File(...)):
    if not file.filename:
        raise HTTPException(status_code=400, detail="No file uploaded")

    if file.content_type != "application/pdf":
        raise HTTPException(
            status_code=400,
            detail="Only PDF files are supported",
        )

    file_bytes = await file.read()
    text_chunks = process_pdf(file_bytes)

    if not text_chunks:
        raise HTTPException(
            status_code=500,
            detail="Could not extract text from PDF",
        )

    output_dir = "uploaded_data"
    os.makedirs(output_dir, exist_ok=True)

    output_path = os.path.join(
        output_dir, f"{file.filename}.json"
    )

    with open(output_path, "w", encoding="utf-8") as f:
        json.dump(
            {"source": file.filename, "chunks": text_chunks},
            f,
            indent=2,
        )

    return {
        "message": f"File '{file.filename}' processed successfully"
    }
