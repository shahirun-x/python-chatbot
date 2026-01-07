import pandas as pd
import json
import faiss
import numpy as np
from sentence_transformers import SentenceTransformer
import os

# Configuration
MODEL_NAME = 'all-MiniLM-L6-v2'
INDEX_FILE = "knowledge_base.index"
CHUNKS_FILE = "corpus_chunks.json"

def load_csv_datasets():
    documents = []
    
    # 1. Load the "Gold Mine" (13k rows)
    if os.path.exists('Python Programming Questions Dataset.csv'):
        print("Loading 13k Dataset... (This is the big one)")
        df_big = pd.read_csv('Python Programming Questions Dataset.csv')
        # We process all rows. It might take time but it's worth it.
        for _, row in df_big.iterrows():
            # Format: Instruction -> Input (if any) -> Output
            entry = f"User Request: {row['Instruction']}\n"
            if pd.notna(row['Input']):
                entry += f"Input Data: {row['Input']}\n"
            entry += f"Python Solution:\n{row['Output']}"
            documents.append(entry)
            
    # 2. Load the Chatbot Dataset
    if os.path.exists('python_programming_chatbot_dataset.csv'):
        print("Loading Chatbot QA Dataset...")
        df_chat = pd.read_csv('python_programming_chatbot_dataset.csv')
        for _, row in df_chat.iterrows():
            entry = f"Question: {row['question']}\nAnswer: {row['answer']}"
            if pd.notna(row['code']):
                entry += f"\nCode Example:\n{row['code']}"
            documents.append(entry)

    # 3. Load the Syntax QA Dataset
    if os.path.exists('python_queries_QA_dataset FINAL.csv'):
        print("Loading Syntax QA Dataset...")
        df_syntax = pd.read_csv('python_queries_QA_dataset FINAL.csv')
        for _, row in df_syntax.iterrows():
            entry = f"Question: {row['question']}\nAnswer: {row['answer']}"
            documents.append(entry)

    print(f"Total knowledge chunks collected: {len(documents)}")
    return documents

def build_index():
    # 1. Get text data
    chunks = load_csv_datasets()
    if not chunks:
        print("No CSV files found! Please upload them to the backend folder.")
        return

    # 2. Load AI Model
    print("Loading AI Model (Sentence Transformers)...")
    model = SentenceTransformer(MODEL_NAME)

    # 3. Create Embeddings (This takes the longest time)
    print("Generating embeddings... (Go grab a coffee, this takes ~5-10 mins)")
    embeddings = model.encode(chunks, show_progress_bar=True)

    # 4. Create FAISS Index
    print("Building FAISS Index...")
    dimension = embeddings.shape[1]
    index = faiss.IndexFlatL2(dimension)
    index.add(np.array(embeddings).astype('float32'))

    # 5. Save everything
    faiss.write_index(index, INDEX_FILE)
    with open(CHUNKS_FILE, 'w') as f:
        json.dump(chunks, f)

    print("Success! Knowledge base updated.")

if __name__ == "__main__":
    build_index()