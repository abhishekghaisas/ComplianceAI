"""
Week 2: RAG (Retrieval-Augmented Generation) System

This package implements semantic search and policy comparison capabilities
for the ComplianceAI system.

Modules:
    rag_chunker: Smart document chunking with semantic boundaries
    rag_embedder: Vector embedding generation using sentence-transformers
    rag_store: ChromaDB vector database for persistent storage
    rag_query: Advanced query engine with hybrid search (Day 9)
    policy_matcher: Requirement-to-policy matching (Days 10-11)

Usage:
    from app.week2 import DocumentChunker, EmbeddingGenerator, VectorStore
    
    # Initialize components
    chunker = DocumentChunker(chunk_size=500, overlap=100)
    embedder = EmbeddingGenerator()
    store = VectorStore(persist_directory="./chroma_db")
    
    # Chunk documents
    chunks = chunker.chunk_requirement(requirement, "source.pdf")
    
    # Generate embeddings
    embedded_chunks = embedder.embed_chunks(chunks)
    
    # Store in vector database
    store.create_regulations_collection()
    store.add_chunks(embedded_chunks, collection_type="regulations")
    
    # Search semantically
    query_embedding = embedder.embed_text("data collection requirements")
    results = store.query_regulations(query_embedding, n_results=5)
"""

__version__ = "0.1.0"
__author__ = "ComplianceAI Team"

# Import main classes
from .rag_chunker import DocumentChunker
from .rag_embedder import EmbeddingGenerator
from .rag_store import VectorStore
from .rag_query import QueryEngine
from .policy_reader import PolicyReader
from .policy_matcher import PolicyMatcher
from .enhanced_policy_matcher import EnhancedPolicyMatcher

# Define public API
__all__ = [
    "DocumentChunker",
    "EmbeddingGenerator",
    "VectorStore",
    "QueryEngine",
    "PolicyReader",
    "PolicyMatcher",
    "EnhancedPolicyMatcher"
]

# Version info
VERSION_INFO = {
    "week": 2,
    "days_complete": 8,
    "status": "Day 8 Complete - RAG Foundation",
    "components": [
        "DocumentChunker - Smart semantic chunking",
        "EmbeddingGenerator - 384D vector embeddings",
        "VectorStore - ChromaDB integration",
    ],
    "coming_soon": [
        "QueryEngine - Advanced search (Day 9)",
        "PolicyMatcher - Requirement matching (Days 10-11)",
        "GapAnalyzer - Compliance gap detection (Days 12-13)",
    ]
}


def get_version_info():
    """Print version information"""
    print(f"ComplianceAI Week 2 - Version {__version__}")
    print(f"Status: {VERSION_INFO['status']}")
    print("\nComponents:")
    for component in VERSION_INFO['components']:
        print(f"  ✅ {component}")
    print("\nComing Soon:")
    for component in VERSION_INFO['coming_soon']:
        print(f"  ⏳ {component}")


# Quick test function
def test_imports():
    """Test that all modules can be imported"""
    print("Testing Week 2 imports...\n")
    
    try:
        print("✅ DocumentChunker imported")
    except Exception as e:
        print(f"❌ DocumentChunker: {e}")
    
    try:
        print("✅ EmbeddingGenerator imported")
    except Exception as e:
        print(f"❌ EmbeddingGenerator: {e}")
    
    try:
        print("✅ VectorStore imported")
    except Exception as e:
        print(f"❌ VectorStore: {e}")
    
    print("\n✅ All Week 2 modules imported successfully!")


if __name__ == "__main__":
    get_version_info()