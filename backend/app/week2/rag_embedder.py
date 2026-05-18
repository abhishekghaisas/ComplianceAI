"""
RAG Embedding Generator - Week 2, Day 8
Generates vector embeddings for semantic search
"""

from sentence_transformers import SentenceTransformer
from typing import List, Dict, Any
import numpy as np


class EmbeddingGenerator:
    """Generate embeddings using sentence-transformers"""
    
    def __init__(self, model_name="all-MiniLM-L6-v2"):
        """
        Initialize embedding model
        
        Args:
            model_name: HuggingFace model name
                       Default: all-MiniLM-L6-v2 (384 dims, fast, good quality)
        """
        print(f"📥 Loading embedding model: {model_name}...")
        self.model = SentenceTransformer(model_name)
        self.model_name = model_name
        self.embedding_dim = self.model.get_sentence_embedding_dimension()
        print(f"✅ Model loaded! Embedding dimension: {self.embedding_dim}")
    
    def embed_text(self, text: str) -> List[float]:
        """
        Generate embedding for single text
        
        Args:
            text: Text to embed
            
        Returns:
            Embedding vector as list of floats
        """
        embedding = self.model.encode(text, convert_to_numpy=True)
        return embedding.tolist()
    
    def embed_batch(self, texts: List[str], batch_size=32, show_progress=True) -> List[List[float]]:
        """
        Generate embeddings for batch of texts
        
        Args:
            texts: List of texts to embed
            batch_size: Batch size for encoding
            show_progress: Show progress bar
            
        Returns:
            List of embedding vectors
        """
        embeddings = self.model.encode(
            texts,
            batch_size=batch_size,
            show_progress_bar=show_progress,
            convert_to_numpy=True
        )
        return embeddings.tolist()
    
    def embed_chunks(self, chunks: List[Dict[str, Any]], batch_size=32) -> List[Dict[str, Any]]:
        """
        Add embeddings to chunk dictionaries
        
        Args:
            chunks: List of chunk dicts with 'text' field
            batch_size: Batch size for encoding
            
        Returns:
            Chunks with 'embedding' field added
        """
        print(f"\n🔢 Embedding {len(chunks)} chunks...")
        
        # Extract texts
        texts = [chunk["text"] for chunk in chunks]
        
        # Generate embeddings
        embeddings = self.embed_batch(texts, batch_size=batch_size)
        
        # Add to chunks
        for chunk, embedding in zip(chunks, embeddings):
            chunk["embedding"] = embedding
        
        print(f"✅ Embedded {len(chunks)} chunks ({self.embedding_dim}D vectors)")
        
        return chunks
    
    def cosine_similarity(self, vec1: List[float], vec2: List[float]) -> float:
        """
        Calculate cosine similarity between two vectors
        
        Args:
            vec1, vec2: Embedding vectors
            
        Returns:
            Similarity score (0-1, higher = more similar)
        """
        vec1 = np.array(vec1)
        vec2 = np.array(vec2)
        
        dot_product = np.dot(vec1, vec2)
        norm1 = np.linalg.norm(vec1)
        norm2 = np.linalg.norm(vec2)
        
        if norm1 == 0 or norm2 == 0:
            return 0.0
        
        return float(dot_product / (norm1 * norm2))


def test_embedder():
    """Test the embedding generator"""
    print("="*60)
    print("🧪 TESTING EMBEDDING GENERATOR")
    print("="*60 + "\n")
    
    # Initialize
    embedder = EmbeddingGenerator()
    
    # Test 1: Single text embedding
    print("\nTEST 1: Single Text Embedding\n")
    
    text = "Banks must collect small business lending data."
    embedding = embedder.embed_text(text)
    
    print(f"✅ Text: {text}")
    print(f"✅ Embedding dimension: {len(embedding)}")
    print(f"✅ First 5 values: {embedding[:5]}")
    
    # Test 2: Batch embedding
    print("\n" + "="*60)
    print("TEST 2: Batch Embedding\n")
    
    texts = [
        "Financial institutions must report data quarterly.",
        "Banks need to track loan applications.",
        "Compliance deadlines are strictly enforced."
    ]
    
    embeddings = embedder.embed_batch(texts, show_progress=False)
    
    print(f"✅ Embedded {len(embeddings)} texts")
    print(f"✅ Each embedding: {len(embeddings[0])} dimensions")
    
    # Test 3: Similarity
    print("\n" + "="*60)
    print("TEST 3: Semantic Similarity\n")
    
    text1 = "Banks must collect data on small business loans."
    text2 = "Financial institutions need to gather information about small business lending."
    text3 = "The weather is sunny today."
    
    emb1 = embedder.embed_text(text1)
    emb2 = embedder.embed_text(text2)
    emb3 = embedder.embed_text(text3)
    
    sim_12 = embedder.cosine_similarity(emb1, emb2)
    sim_13 = embedder.cosine_similarity(emb1, emb3)
    
    print(f"Text 1: {text1}")
    print(f"Text 2: {text2}")
    print(f"Text 3: {text3}\n")
    
    print(f"✅ Similarity (1 vs 2): {sim_12:.3f} - Similar meaning!")
    print(f"✅ Similarity (1 vs 3): {sim_13:.3f} - Different meaning!")
    
    assert sim_12 > 0.6, "Similar texts should have high similarity"
    assert sim_13 < 0.3, "Different texts should have low similarity"
    
    # Test 4: Chunk embedding
    print("\n" + "="*60)
    print("TEST 4: Embedding Chunks\n")
    
    sample_chunks = [
        {
            "text": "Banks must maintain adequate capital reserves.",
            "metadata": {"type": "OBLIGATION", "severity": "HIGH"}
        },
        {
            "text": "Financial institutions should report annually.",
            "metadata": {"type": "RECOMMENDATION", "severity": "MEDIUM"}
        }
    ]
    
    embedded_chunks = embedder.embed_chunks(sample_chunks)
    
    for i, chunk in enumerate(embedded_chunks):
        print(f"\n📄 Chunk {i + 1}:")
        print(f"   Text: {chunk['text'][:50]}...")
        print(f"   Embedding size: {len(chunk['embedding'])}")
        print(f"   Metadata: {chunk['metadata']}")
    
    print("\n" + "="*60)
    print("✅ ALL TESTS PASSED!")
    print("="*60)
    
    return embedder


if __name__ == "__main__":
    test_embedder()