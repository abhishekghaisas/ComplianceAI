"""
RAG Query Engine - Week 2, Day 9
Advanced search with query expansion, hybrid search, and re-ranking
"""

from typing import List, Dict, Any, Optional, Tuple
from collections import defaultdict
import re
from .rag_embedder import EmbeddingGenerator
from .rag_store import VectorStore


class QueryEngine:
    """Advanced query engine for RAG system"""
    
    def __init__(
        self,
        vector_store: VectorStore,
        embedder: EmbeddingGenerator
    ):
        """
        Initialize query engine
        
        Args:
            vector_store: VectorStore instance
            embedder: EmbeddingGenerator instance
        """
        self.store = vector_store
        self.embedder = embedder
    
    def simple_search(
        self,
        query: str,
        collection: str = "regulations",
        n_results: int = 5,
        filters: Optional[Dict] = None
    ) -> Dict[str, Any]:
        """
        Basic semantic search
        
        Args:
            query: Search query
            collection: 'regulations' or 'policies'
            n_results: Number of results
            filters: Metadata filters
            
        Returns:
            Search results with documents, distances, metadata
        """
        # Embed query
        query_embedding = self.embedder.embed_text(query)
        
        # Search appropriate collection
        if collection == "regulations":
            results = self.store.query_regulations(
                query_embedding,
                n_results=n_results,
                filters=filters
            )
        else:
            results = self.store.query_policies(
                query_embedding,
                n_results=n_results,
                filters=filters
            )
        
        return results
    
    def expand_query(self, query: str) -> List[str]:
        """
        Expand query with related terms and variations
        
        Args:
            query: Original query
            
        Returns:
            List of expanded queries including original
        """
        expanded = [query]  # Always include original
        
        # Banking/compliance synonyms
        synonyms = {
            'data collection': ['information gathering', 'record keeping', 'data tracking'],
            'requirement': ['obligation', 'mandate', 'rule'],
            'bank': ['financial institution', 'lender', 'credit union'],
            'report': ['disclose', 'submit', 'provide information'],
            'customer': ['client', 'borrower', 'applicant'],
            'loan': ['credit', 'lending', 'financing'],
            'discrimination': ['bias', 'unfair treatment', 'disparate impact'],
            'deadline': ['due date', 'compliance date', 'effective date'],
            'penalty': ['fine', 'sanction', 'enforcement action'],
        }
        
        # Find and expand matching terms
        query_lower = query.lower()
        for term, alternatives in synonyms.items():
            if term in query_lower:
                for alt in alternatives:
                    expanded_query = query_lower.replace(term, alt)
                    if expanded_query not in expanded:
                        expanded.append(expanded_query)
        
        return expanded[:4]  # Limit to 4 variations to avoid overwhelming
    
    def multi_query_search(
        self,
        queries: List[str],
        collection: str = "regulations",
        n_results: int = 10,
        filters: Optional[Dict] = None,
        aggregate: bool = True
    ) -> Dict[str, Any]:
        """
        Search with multiple queries and aggregate results
        
        Args:
            queries: List of query strings
            collection: 'regulations' or 'policies'
            n_results: Results per query
            filters: Metadata filters
            aggregate: If True, deduplicate and merge results
            
        Returns:
            Aggregated search results
        """
        all_results = {
            'documents': [],
            'distances': [],
            'metadatas': [],
            'ids': []
        }
        
        seen_ids = set()
        
        for query in queries:
            results = self.simple_search(
                query,
                collection=collection,
                n_results=n_results,
                filters=filters
            )
            
            if aggregate:
                # Deduplicate by document ID
                for i, doc_id in enumerate(results['ids'][0]):
                    if doc_id not in seen_ids:
                        seen_ids.add(doc_id)
                        all_results['documents'].append(results['documents'][0][i])
                        all_results['distances'].append(results['distances'][0][i])
                        all_results['metadatas'].append(results['metadatas'][0][i])
                        all_results['ids'].append(doc_id)
            else:
                # Keep all results
                all_results['documents'].extend(results['documents'][0])
                all_results['distances'].extend(results['distances'][0])
                all_results['metadatas'].extend(results['metadatas'][0])
                all_results['ids'].extend(results['ids'][0])
        
        # Sort by distance (lower = more similar)
        if aggregate and all_results['documents']:
            sorted_indices = sorted(
                range(len(all_results['distances'])),
                key=lambda i: all_results['distances'][i]
            )
            
            all_results['documents'] = [all_results['documents'][i] for i in sorted_indices]
            all_results['distances'] = [all_results['distances'][i] for i in sorted_indices]
            all_results['metadatas'] = [all_results['metadatas'][i] for i in sorted_indices]
            all_results['ids'] = [all_results['ids'][i] for i in sorted_indices]
        
        return all_results
    
    def advanced_search(
        self,
        query: str,
        collection: str = "regulations",
        expand_query: bool = True,
        n_results: int = 10,
        filters: Optional[Dict] = None,
        min_similarity: float = 0.0
    ) -> List[Dict[str, Any]]:
        """
        Advanced search with query expansion and filtering
        
        Args:
            query: Search query
            collection: 'regulations' or 'policies'
            expand_query: If True, use query expansion
            n_results: Number of results
            filters: Metadata filters
            min_similarity: Minimum similarity threshold (0-1)
            
        Returns:
            List of result dictionaries with enhanced metadata
        """
        # Expand query if requested
        if expand_query:
            queries = self.expand_query(query)
            print(f"🔍 Expanded query into {len(queries)} variations")
        else:
            queries = [query]
        
        # Multi-query search
        raw_results = self.multi_query_search(
            queries,
            collection=collection,
            n_results=n_results,
            filters=filters,
            aggregate=True
        )
        
        # Format results with similarity scores
        formatted_results = []
        for i in range(len(raw_results['documents'])):
            distance = raw_results['distances'][i]
            similarity = 1 - distance  # Convert distance to similarity
            
            # Apply similarity threshold
            if similarity >= min_similarity:
                formatted_results.append({
                    'id': raw_results['ids'][i],
                    'document': raw_results['documents'][i],
                    'metadata': raw_results['metadatas'][i],
                    'distance': distance,
                    'similarity': similarity,
                    'similarity_percent': f"{similarity * 100:.1f}%"
                })
        
        return formatted_results[:n_results]
    
    def keyword_score(self, text: str, keywords: List[str]) -> float:
        """
        Calculate keyword overlap score
        
        Args:
            text: Document text
            keywords: List of keywords to match
            
        Returns:
            Score between 0-1
        """
        if not keywords:
            return 0.0
        
        text_lower = text.lower()
        matches = sum(1 for kw in keywords if kw.lower() in text_lower)
        return matches / len(keywords)
    
    def hybrid_search(
        self,
        query: str,
        keywords: List[str] = None,
        collection: str = "regulations",
        semantic_weight: float = 0.7,
        n_results: int = 10,
        filters: Optional[Dict] = None
    ) -> List[Dict[str, Any]]:
        """
        Hybrid search combining semantic and keyword matching
        
        Args:
            query: Search query
            keywords: Additional keywords to boost
            collection: 'regulations' or 'policies'
            semantic_weight: Weight for semantic score (0-1)
            n_results: Number of results
            filters: Metadata filters
            
        Returns:
            Hybrid-scored results
        """
        # Get semantic results
        semantic_results = self.advanced_search(
            query,
            collection=collection,
            expand_query=True,
            n_results=n_results * 2,  # Get more for re-ranking
            filters=filters
        )
        
        # Calculate hybrid scores
        keyword_weight = 1 - semantic_weight
        
        for result in semantic_results:
            semantic_score = result['similarity']
            
            # Calculate keyword score if keywords provided
            if keywords:
                kw_score = self.keyword_score(result['document'], keywords)
            else:
                kw_score = 0.0
            
            # Hybrid score
            hybrid_score = (semantic_weight * semantic_score) + (keyword_weight * kw_score)
            
            result['keyword_score'] = kw_score
            result['hybrid_score'] = hybrid_score
            result['hybrid_percent'] = f"{hybrid_score * 100:.1f}%"
        
        # Sort by hybrid score
        semantic_results.sort(key=lambda x: x['hybrid_score'], reverse=True)
        
        return semantic_results[:n_results]
    
    def search_with_context(
        self,
        query: str,
        collection: str = "regulations",
        n_results: int = 5,
        context_window: int = 1
    ) -> List[Dict[str, Any]]:
        """
        Search and include surrounding chunks for context
        
        Args:
            query: Search query
            collection: 'regulations' or 'policies'
            n_results: Number of results
            context_window: Number of adjacent chunks to include
            
        Returns:
            Results with context chunks
        """
        # Get base results
        results = self.advanced_search(
            query,
            collection=collection,
            n_results=n_results
        )
        
        # For each result, try to find adjacent chunks
        for result in results:
            metadata = result['metadata']
            
            # If we have chunk index info, note what context to fetch
            if 'chunk_index' in metadata and 'total_chunks' in metadata:
                chunk_idx = int(metadata['chunk_index'])
                total = int(metadata['total_chunks'])
                
                result['has_context'] = True
                result['context_info'] = {
                    'current_chunk': chunk_idx,
                    'total_chunks': total,
                    'can_expand': chunk_idx > 0 or chunk_idx < total - 1
                }
            else:
                result['has_context'] = False
        
        return results


def test_query_engine():
    """Test the query engine"""
    print("="*70)
    print("🧪 TESTING QUERY ENGINE")
    print("="*70 + "\n")
    
    # Initialize components
    from .rag_store import VectorStore
    from .rag_embedder import EmbeddingGenerator
    
    embedder = EmbeddingGenerator()
    store = VectorStore(persist_directory="./test_query_db")
    
    # Create test data
    from .rag_chunker import DocumentChunker
    
    chunker = DocumentChunker()
    
    test_requirements = [
        {
            "requirement_id": "req_001",
            "type": "OBLIGATION",
            "severity": "HIGH",
            "requirement": "Financial institutions must collect and report small business lending data quarterly.",
            "entities": {"agencies": ["CFPB"]}
        },
        {
            "requirement_id": "req_002",
            "type": "PROHIBITION",
            "severity": "CRITICAL",
            "requirement": "Lenders are prohibited from discriminating based on protected characteristics.",
            "entities": {"agencies": ["CFPB", "DOJ"]}
        }
    ]
    
    # Chunk and embed
    chunks = []
    for req in test_requirements:
        chunks.extend(chunker.chunk_requirement(req, "test.pdf"))
    
    embedded_chunks = embedder.embed_chunks(chunks)
    
    # Store
    store.create_regulations_collection(reset=True)
    store.add_chunks(embedded_chunks, collection_type="regulations")
    
    # Initialize query engine
    query_engine = QueryEngine(store, embedder)
    
    print("✅ Query engine initialized with test data\n")
    
    # Test 1: Simple search
    print("="*70)
    print("TEST 1: Simple Search\n")
    
    results = query_engine.simple_search("data collection requirements")
    print(f"✅ Found {len(results['documents'][0])} results")
    print(f"   Top result: {results['documents'][0][0][:80]}...\n")
    
    # Test 2: Query expansion
    print("="*70)
    print("TEST 2: Query Expansion\n")
    
    query = "data collection requirements"
    expanded = query_engine.expand_query(query)
    print(f"Original query: {query}")
    print(f"Expanded to {len(expanded)} queries:")
    for i, q in enumerate(expanded, 1):
        print(f"   {i}. {q}")
    print()
    
    # Test 3: Advanced search with expansion
    print("="*70)
    print("TEST 3: Advanced Search (with expansion)\n")
    
    results = query_engine.advanced_search(
        "data collection requirements",
        expand_query=True,
        n_results=5
    )
    
    print(f"✅ Found {len(results)} results")
    for i, result in enumerate(results, 1):
        print(f"\n   Result {i}:")
        print(f"   Similarity: {result['similarity_percent']}")
        print(f"   Text: {result['document'][:80]}...")
    
    # Test 4: Hybrid search
    print("\n" + "="*70)
    print("TEST 4: Hybrid Search (semantic + keywords)\n")
    
    results = query_engine.hybrid_search(
        query="lending requirements",
        keywords=["CFPB", "quarterly", "data"],
        semantic_weight=0.7
    )
    
    print(f"✅ Found {len(results)} results with hybrid scoring")
    for i, result in enumerate(results, 1):
        print(f"\n   Result {i}:")
        print(f"   Semantic: {result['similarity_percent']}")
        print(f"   Keyword: {result['keyword_score']:.1%}")
        print(f"   Hybrid: {result['hybrid_percent']}")
        print(f"   Text: {result['document'][:80]}...")
    
    print("\n" + "="*70)
    print("✅ ALL QUERY ENGINE TESTS PASSED!")
    print("="*70)


if __name__ == "__main__":
    test_query_engine()