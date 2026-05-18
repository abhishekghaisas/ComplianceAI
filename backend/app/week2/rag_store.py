"""
RAG Vector Store - Week 2, Day 8
Manages ChromaDB collections for regulations and policies
"""

import chromadb
from chromadb.config import Settings
from typing import List, Dict, Any, Optional
import json


class VectorStore:
    """ChromaDB vector database for semantic search"""
    
    def __init__(self, persist_directory="./chroma_db"):
        """
        Initialize ChromaDB client
        
        Args:
            persist_directory: Where to save the database
        """
        print(f"📦 Initializing ChromaDB at {persist_directory}...")
        
        self.client = chromadb.PersistentClient(
            path=persist_directory,
            settings=Settings(anonymized_telemetry=False)
        )
        
        self.regulations_collection = None
        self.policies_collection = None
        
        print("✅ ChromaDB initialized!")
    
    def create_regulations_collection(self, reset=False):
        """
        Create or get regulations collection
        
        Args:
            reset: If True, delete and recreate collection
        """
        collection_name = "regulations"
        
        if reset:
            try:
                self.client.delete_collection(collection_name)
                print(f"🗑️  Deleted existing '{collection_name}' collection")
            except:
                pass
        
        self.regulations_collection = self.client.get_or_create_collection(
            name=collection_name,
            metadata={"description": "Banking regulations and requirements"}
        )
        
        print(f"✅ Regulations collection ready ({self.regulations_collection.count()} items)")
        return self.regulations_collection
    
    def create_policies_collection(self, reset=False):
        """
        Create or get policies collection
        
        Args:
            reset: If True, delete and recreate collection
        """
        collection_name = "policies"
        
        if reset:
            try:
                self.client.delete_collection(collection_name)
                print(f"🗑️  Deleted existing '{collection_name}' collection")
            except:
                pass
        
        self.policies_collection = self.client.get_or_create_collection(
            name=collection_name,
            metadata={"description": "Bank policies and procedures"}
        )
        
        print(f"✅ Policies collection ready ({self.policies_collection.count()} items)")
        return self.policies_collection
    
    def add_chunks(
        self,
        chunks: List[Dict[str, Any]],
        collection_type: str = "regulations"
    ):
        """
        Add chunks to collection
        
        Args:
            chunks: List of chunk dicts with 'text', 'embedding', 'metadata'
            collection_type: 'regulations' or 'policies'
        """
        # Select collection
        if collection_type == "regulations":
            if not self.regulations_collection:
                self.create_regulations_collection()
            collection = self.regulations_collection
        else:
            if not self.policies_collection:
                self.create_policies_collection()
            collection = self.policies_collection
        
        print(f"\n📥 Adding {len(chunks)} chunks to {collection_type} collection...")
        
        # Prepare data for ChromaDB
        ids = []
        documents = []
        embeddings = []
        metadatas = []
        
        for i, chunk in enumerate(chunks):
            # Generate unique ID
            chunk_id = f"{collection_type}_{i}_{hash(chunk['text'][:50]) % 100000}"
            ids.append(chunk_id)
            
            # Text
            documents.append(chunk["text"])
            
            # Embedding
            embeddings.append(chunk["embedding"])
            
            # Metadata (ChromaDB requires serializable metadata)
            metadata = chunk.get("metadata", {})
            # Convert nested dicts to JSON strings
            clean_metadata = {}
            for key, value in metadata.items():
                if isinstance(value, (dict, list)):
                    clean_metadata[key] = json.dumps(value)
                else:
                    clean_metadata[key] = str(value)
            
            metadatas.append(clean_metadata)
        
        # Add to collection in batches (ChromaDB has limits)
        batch_size = 100
        for i in range(0, len(ids), batch_size):
            batch_end = min(i + batch_size, len(ids))
            
            collection.add(
                ids=ids[i:batch_end],
                documents=documents[i:batch_end],
                embeddings=embeddings[i:batch_end],
                metadatas=metadatas[i:batch_end]
            )
        
        print(f"✅ Added {len(chunks)} chunks to {collection_type} collection")
        print(f"📊 Total items in collection: {collection.count()}")
    
    
    def _format_filters(self, filters: Dict) -> Dict:
        """
        Convert simple filter dict to ChromaDB WHERE syntax
        
        Args:
            filters: Simple dict like {'severity': 'HIGH', 'requirement_type': 'OBLIGATION'}
            
        Returns:
            ChromaDB-formatted filter:
            - Single filter: {'key': 'value'}
            - Multiple filters: {'$and': [{'key1': 'value1'}, {'key2': 'value2'}]}
        """
        # If already in ChromaDB format (has operators), return as-is
        if any(key.startswith('$') for key in filters.keys()):
            return filters
        
        # If single filter, return as-is
        if len(filters) == 1:
            return filters
        
        # Multiple filters: wrap in $and
        filter_list = [{key: value} for key, value in filters.items()]
        return {'$and': filter_list}
    
    def query_regulations(
        self,
        query_embedding: List[float],
        n_results: int = 5,
        filters: Optional[Dict] = None
    ) -> Dict[str, Any]:
        """
        Search regulations collection
        
        Args:
            query_embedding: Query vector
            n_results: Number of results to return
            filters: Metadata filters - use ChromaDB syntax:
                     Single filter: {'requirement_type': 'OBLIGATION'}
                     Multiple filters: {'$and': [{'severity': 'HIGH'}, {'requirement_type': 'OBLIGATION'}]}
            
        Returns:
            Query results with documents, distances, metadata
        """
        if not self.regulations_collection:
            self.create_regulations_collection()
        
        # Convert simple dict to ChromaDB format if needed
        where_clause = self._format_filters(filters) if filters else None
        
        results = self.regulations_collection.query(
            query_embeddings=[query_embedding],
            n_results=n_results,
            where=where_clause
        )
        
        return results
    
    def query_policies(
        self,
        query_embedding: List[float],
        n_results: int = 5,
        filters: Optional[Dict] = None
    ) -> Dict[str, Any]:
        """
        Search policies collection
        
        Args:
            query_embedding: Query vector
            n_results: Number of results to return
            filters: Metadata filters - use ChromaDB syntax
            
        Returns:
            Query results with documents, distances, metadata
        """
        if not self.policies_collection:
            self.create_policies_collection()
        
        # Convert simple dict to ChromaDB format if needed
        where_clause = self._format_filters(filters) if filters else None
        
        results = self.policies_collection.query(
            query_embeddings=[query_embedding],
            n_results=n_results,
            where=where_clause
        )
        
        return results
    
    def get_collection_stats(self):
        """Get statistics about both collections"""
        stats = {
            "regulations": {
                "count": self.regulations_collection.count() if self.regulations_collection else 0
            },
            "policies": {
                "count": self.policies_collection.count() if self.policies_collection else 0
            }
        }
        return stats


def test_vector_store():
    """Test the vector store"""
    print("="*60)
    print("🧪 TESTING VECTOR STORE")
    print("="*60 + "\n")
    
    # Initialize
    store = VectorStore(persist_directory="./test_chroma_db")
    
    # Test 1: Create collections
    print("TEST 1: Creating Collections\n")
    
    store.create_regulations_collection(reset=True)
    store.create_policies_collection(reset=True)
    
    print("✅ Collections created!")
    
    # Test 2: Add sample chunks
    print("\n" + "="*60)
    print("TEST 2: Adding Sample Chunks\n")
    
    # Create fake embeddings (normally from embedder)
    import random
    
    sample_chunks = [
        {
            "text": "Banks must collect small business lending data.",
            "embedding": [random.random() for _ in range(384)],
            "metadata": {
                "source_file": "cfpb_1071.pdf",
                "requirement_type": "OBLIGATION",
                "severity": "HIGH",
                "requirement_id": "req_001"
            }
        },
        {
            "text": "Financial institutions should report annually.",
            "embedding": [random.random() for _ in range(384)],
            "metadata": {
                "source_file": "cfpb_1071.pdf",
                "requirement_type": "RECOMMENDATION",
                "severity": "MEDIUM",
                "requirement_id": "req_002"
            }
        }
    ]
    
    store.add_chunks(sample_chunks, collection_type="regulations")
    
    # Test 3: Query
    print("\n" + "="*60)
    print("TEST 3: Querying Collection\n")
    
    query_embedding = [random.random() for _ in range(384)]
    results = store.query_regulations(query_embedding, n_results=2)
    
    print(f"✅ Found {len(results['documents'][0])} results")
    for i, doc in enumerate(results['documents'][0]):
        print(f"\n📄 Result {i + 1}:")
        print(f"   Text: {doc[:80]}...")
        print(f"   Distance: {results['distances'][0][i]:.4f}")
    
    # Test 4: Filtered query
    print("\n" + "="*60)
    print("TEST 4: Filtered Query\n")
    
    filtered_results = store.query_regulations(
        query_embedding,
        n_results=5,
        filters={"requirement_type": "OBLIGATION"}
    )
    
    print(f"✅ Found {len(filtered_results['documents'][0])} OBLIGATION results")
    
    # Stats
    print("\n" + "="*60)
    print("DATABASE STATISTICS\n")
    
    stats = store.get_collection_stats()
    print(f"📊 Regulations: {stats['regulations']['count']} items")
    print(f"📊 Policies: {stats['policies']['count']} items")
    
    print("\n" + "="*60)
    print("✅ ALL TESTS PASSED!")
    print("="*60)


if __name__ == "__main__":
    test_vector_store()