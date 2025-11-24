import json
import os
import faiss
from sentence_transformers import SentenceTransformer

def create_search_index():
    """
    This function reads the corpus, generates text embeddings,
    and builds a searchable FAISS index.
    """
    print("Starting index creation process...")

    # Define the path to the corpus file
    corpus_path = os.path.join('..', 'corpus', 'corpus.json')

    # --- 1. Load the Corpus ---
    print(f"Loading corpus from: {corpus_path}")
    try:
        with open(corpus_path, 'r', encoding='utf-8') as f:
            corpus_data = json.load(f)
    except FileNotFoundError:
        print(f"Error: Corpus file not found at {corpus_path}")
        return
    
    # --- 2. Prepare Text Chunks for Embedding ---
    # We combine the relevant text fields into a single string for each item.
    # This provides more context for the embedding model.
    print("Preparing text chunks for embedding...")
    corpus_chunks = []
    for item in corpus_data:
        chunk = f"Topic: {item['topic']}. Question: {' '.join(item['question_variations'])}. Answer: {item['answer_text']}. Code: {item['code_example']}. Best Practice: {item['best_practice_tip']}"
        corpus_chunks.append(chunk)
    
    print(f"Created {len(corpus_chunks)} text chunks.")

    # --- 3. Load a Pre-trained Sentence-Transformer Model ---
    # 'all-MiniLM-L6-v2' is a great model for this task: fast and effective.
    print("Loading the sentence-transformer model...")
    model = SentenceTransformer('all-MiniLM-L6-v2')

    # --- 4. Generate Embeddings ---
    # The model converts our text chunks into numerical vectors (embeddings).
    print("Generating embeddings for the corpus... (This may take a moment)")
    embeddings = model.encode(corpus_chunks, show_progress_bar=True)

    # The dimension of the embeddings (e.g., 384 for 'all-MiniLM-L6-v2')
    embedding_dim = embeddings.shape[1]
    
    # --- 5. Build the FAISS Index ---
    # We use IndexFlatL2, a standard and effective index for similarity search.
    print(f"Building FAISS index with dimension: {embedding_dim}")
    index = faiss.IndexFlatL2(embedding_dim)
    index.add(embeddings)
    
    print(f"Index built successfully. Total vectors in index: {index.ntotal}")

    # --- 6. Save the Index and the Corpus Chunks ---
    index_path = 'knowledge_base.index'
    chunks_path = 'corpus_chunks.json'

    print(f"Saving FAISS index to: {index_path}")
    faiss.write_index(index, index_path)

    print(f"Saving corpus chunks to: {chunks_path}")
    with open(chunks_path, 'w', encoding='utf-8') as f:
        json.dump(corpus_chunks, f, indent=2)

    print("\nIndex creation complete!")
    print(f"Files created: {index_path}, {chunks_path}")


if __name__ == "__main__":
    create_search_index()