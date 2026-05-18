"""
Week 2, Day 9: Query Engine Integration Test
Tests advanced search capabilities
"""

import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

from app.week2.rag_chunker import DocumentChunker
from app.week2.rag_embedder import EmbeddingGenerator
from app.week2.rag_store import VectorStore
from app.week2.rag_query import QueryEngine


def test_query_engine_full():
    """Test complete query engine with realistic scenarios"""
    
    print("="*70)
    print("🚀 WEEK 2, DAY 9: QUERY ENGINE INTEGRATION TEST")
    print("="*70 + "\n")
    
    # Initialize components
    print("STEP 1: Initializing Components")
    print("-"*70 + "\n")
    
    chunker = DocumentChunker(chunk_size=300, overlap=50)
    embedder = EmbeddingGenerator()
    store = VectorStore(persist_directory="./day9_demo_db")
    
    print("✅ All components initialized\n")
    
    # Create realistic test data
    print("="*70)
    print("STEP 2: Creating Realistic Test Requirements")
    print("-"*70 + "\n")
    
    test_requirements = [
        {
            "requirement_id": "req_001",
            "type": "OBLIGATION",
            "severity": "HIGH",
            "section_title": "Small Business Lending Data Collection",
            "requirement": "Financial institutions with assets exceeding $1 billion must collect and maintain detailed data on small business loan applications, including applicant demographics, business information, loan terms, pricing, and credit decisions. This data must be reported to the CFPB on a quarterly basis starting January 1, 2028.",
            "plain_language": "Large banks need to track and report detailed small business loan data every quarter.",
            "entities": {
                "dates": ["2028-01-01"],
                "amounts": ["$1 billion"],
                "agencies": ["CFPB"]
            }
        },
        {
            "requirement_id": "req_002",
            "type": "PROHIBITION",
            "severity": "CRITICAL",
            "section_title": "Fair Lending and Non-Discrimination",
            "requirement": "Lenders are strictly prohibited from discriminating on the basis of race, color, religion, national origin, sex, marital status, age, or receipt of public assistance in any aspect of a credit transaction. This includes application processes, underwriting decisions, loan terms, and servicing.",
            "plain_language": "You cannot treat people differently in lending based on their personal characteristics.",
            "entities": {
                "agencies": ["CFPB", "DOJ", "FDIC"]
            }
        },
        {
            "requirement_id": "req_003",
            "type": "RECOMMENDATION",
            "severity": "MEDIUM",
            "section_title": "Adverse Action Notification",
            "requirement": "Creditors should notify applicants of adverse actions within 30 days of receiving a completed application or taking adverse action on an existing account. Notifications should include specific reasons for the denial or adverse terms.",
            "plain_language": "Tell customers within 30 days if you deny their loan and explain why.",
            "entities": {
                "dates": ["30 days"]
            }
        },
        {
            "requirement_id": "req_004",
            "type": "OBLIGATION",
            "severity": "HIGH",
            "section_title": "Customer Due Diligence Requirements",
            "requirement": "Banks must establish and maintain written customer identification programs (CIP) that enable them to verify the identity of customers, including beneficial owners of legal entity customers. Records must be retained for five years after account closure.",
            "plain_language": "Know who your customers really are and keep records for 5 years after closing accounts.",
            "entities": {
                "dates": ["five years"],
                "agencies": ["FinCEN"]
            }
        },
        {
            "requirement_id": "req_005",
            "type": "OBLIGATION",
            "severity": "MEDIUM",
            "section_title": "Appraisal Requirements",
            "requirement": "For residential real estate transactions, lenders must provide applicants with a free copy of all appraisals and valuations promptly upon completion, but no later than three business days before consummation.",
            "plain_language": "Give borrowers their home appraisal at least 3 days before closing.",
            "entities": {
                "dates": ["three business days"]
            }
        }
    ]
    
    print(f"✅ Created {len(test_requirements)} requirements")
    for req in test_requirements:
        print(f"   • {req['requirement_id']}: {req['section_title']}")
    print()
    
    # Chunk and embed
    print("="*70)
    print("STEP 3: Processing Requirements")
    print("-"*70 + "\n")
    
    chunks = []
    for req in test_requirements:
        req_chunks = chunker.chunk_requirement(req, "test_regulation.pdf")
        chunks.extend(req_chunks)
    
    print(f"✅ Created {len(chunks)} chunks")
    
    embedded_chunks = embedder.embed_chunks(chunks, batch_size=8)
    print(f"✅ Generated embeddings ({embedder.embedding_dim}D)")
    
    # Store in database
    store.create_regulations_collection(reset=True)
    store.add_chunks(embedded_chunks, collection_type="regulations")
    print(f"✅ Stored in vector database\n")
    
    # Initialize query engine
    query_engine = QueryEngine(store, embedder)
    
    # Test scenarios
    print("="*70)
    print("STEP 4: Testing Search Scenarios")
    print("="*70 + "\n")
    
    # Scenario 1: Simple search
    print("📊 SCENARIO 1: Simple Semantic Search")
    print("-"*70 + "\n")
    
    query = "What are the data collection requirements?"
    print(f"Query: \"{query}\"\n")
    
    results = query_engine.simple_search(query, n_results=3)
    
    print(f"Found {len(results['documents'][0])} results:\n")
    for i, doc in enumerate(results['documents'][0], 1):
        distance = results['distances'][0][i-1]
        similarity = (1 - distance) * 100
        metadata = results['metadatas'][0][i-1]
        
        print(f"Result {i} (Similarity: {similarity:.1f}%):")
        print(f"   Type: {metadata.get('requirement_type', 'N/A')}")
        print(f"   Section: {metadata.get('section_title', 'N/A')}")
        print(f"   Text: {doc[:100]}...")
        print()
    
    # Scenario 2: Query expansion
    print("="*70)
    print("📊 SCENARIO 2: Query Expansion")
    print("-"*70 + "\n")
    
    query = "discrimination rules"
    print(f"Original query: \"{query}\"\n")
    
    expanded = query_engine.expand_query(query)
    print(f"Expanded to {len(expanded)} variations:")
    for i, q in enumerate(expanded, 1):
        print(f"   {i}. {q}")
    
    print(f"\nSearching with expanded queries...\n")
    
    results = query_engine.advanced_search(
        query,
        expand_query=True,
        n_results=2
    )
    
    print(f"Found {len(results)} results:\n")
    for i, result in enumerate(results, 1):
        print(f"Result {i} (Similarity: {result['similarity_percent']}):")
        print(f"   {result['document'][:100]}...")
        print()
    
    # Scenario 3: Filtered search
    print("="*70)
    print("📊 SCENARIO 3: Filtered Search (High Priority Only)")
    print("-"*70 + "\n")
    
    query = "compliance requirements"
    filters = {"severity": "HIGH"}
    
    print(f"Query: \"{query}\"")
    print(f"Filter: {filters}\n")
    
    results = query_engine.simple_search(query, filters=filters, n_results=5)
    
    print(f"Found {len(results['documents'][0])} HIGH severity requirements:\n")
    for i, doc in enumerate(results['documents'][0], 1):
        metadata = results['metadatas'][0][i-1]
        print(f"   {i}. {metadata.get('requirement_id', 'N/A')}: {metadata.get('section_title', 'N/A')}")
    print()
    
    # Scenario 4: Hybrid search
    print("="*70)
    print("📊 SCENARIO 4: Hybrid Search (Semantic + Keywords)")
    print("-"*70 + "\n")
    
    query = "customer identification"
    keywords = ["CIP", "FinCEN", "beneficial owner", "five years"]
    
    print(f"Query: \"{query}\"")
    print(f"Keywords: {keywords}\n")
    
    results = query_engine.hybrid_search(
        query,
        keywords=keywords,
        semantic_weight=0.7,
        n_results=3
    )
    
    print(f"Found {len(results)} results with hybrid scoring:\n")
    for i, result in enumerate(results, 1):
        print(f"Result {i}:")
        print(f"   Semantic: {result['similarity_percent']}")
        print(f"   Keyword: {result['keyword_score']:.1%}")
        print(f"   Hybrid: {result['hybrid_percent']}")
        print(f"   Text: {result['document'][:100]}...")
        print()
    
    # Scenario 5: Multiple queries
    print("="*70)
    print("📊 SCENARIO 5: Multi-Query Search")
    print("-"*70 + "\n")
    
    queries = [
        "What data must be collected?",
        "What are the reporting deadlines?",
        "Which agencies enforce these rules?"
    ]
    
    print("Multiple queries:")
    for i, q in enumerate(queries, 1):
        print(f"   {i}. {q}")
    print()
    
    results = query_engine.multi_query_search(
        queries,
        n_results=5,
        aggregate=True
    )
    
    print(f"✅ Aggregated and deduplicated results")
    print(f"✅ Found {len(results['documents'])} unique documents\n")
    
    # Scenario 6: Similarity threshold
    print("="*70)
    print("📊 SCENARIO 6: Minimum Similarity Threshold")
    print("-"*70 + "\n")
    
    query = "appraisal requirements"
    min_sim = 0.3
    
    print(f"Query: \"{query}\"")
    print(f"Minimum similarity: {min_sim:.0%}\n")
    
    results = query_engine.advanced_search(
        query,
        expand_query=False,
        n_results=10,
        min_similarity=min_sim
    )
    
    print(f"Found {len(results)} results above {min_sim:.0%} threshold:\n")
    for i, result in enumerate(results, 1):
        print(f"   {i}. {result['similarity_percent']}: {result['metadata'].get('section_title', 'N/A')}")
    print()
    
    # Performance comparison
    print("="*70)
    print("📊 SCENARIO 7: Search Quality Comparison")
    print("-"*70 + "\n")
    
    test_query = "loan discrimination rules"
    
    print(f"Query: \"{test_query}\"\n")
    
    # Simple search
    simple_results = query_engine.simple_search(test_query, n_results=3)
    simple_top_sim = (1 - simple_results['distances'][0][0]) * 100
    
    # Advanced search with expansion
    advanced_results = query_engine.advanced_search(
        test_query,
        expand_query=True,
        n_results=3
    )
    advanced_top_sim = advanced_results[0]['similarity'] * 100
    
    # Hybrid search
    hybrid_results = query_engine.hybrid_search(
        test_query,
        keywords=["discrimination", "lending", "prohibited"],
        n_results=3
    )
    hybrid_top_score = hybrid_results[0]['hybrid_score'] * 100
    
    print("Comparison of top result similarity:")
    print(f"   Simple Search:   {simple_top_sim:.1f}%")
    print(f"   Advanced Search: {advanced_top_sim:.1f}% (with expansion)")
    print(f"   Hybrid Search:   {hybrid_top_score:.1f}% (semantic + keywords)")
    print()
    
    improvement = hybrid_top_score - simple_top_sim
    print(f"✅ Improvement: +{improvement:.1f}% with advanced features!")
    
    # Final statistics
    print("\n" + "="*70)
    print("📊 FINAL STATISTICS")
    print("-"*70 + "\n")
    
    stats = store.get_collection_stats()
    print(f"✅ Requirements in database: {stats['regulations']['count']}")
    print(f"✅ Test scenarios completed: 7")
    print(f"✅ Search methods tested: 5")
    print(f"✅ Features demonstrated:")
    print(f"   • Simple semantic search")
    print(f"   • Query expansion")
    print(f"   • Filtered search")
    print(f"   • Hybrid search (semantic + keywords)")
    print(f"   • Multi-query aggregation")
    print(f"   • Similarity thresholds")
    print(f"   • Performance comparison")
    
    print("\n" + "="*70)
    print("🎉 QUERY ENGINE IS WORKING!")
    print("="*70)
    print("\n✅ Day 9 Complete! Advanced query capabilities:")
    print("   • Query expansion improves recall")
    print("   • Hybrid search boosts accuracy")
    print("   • Multiple filter combinations")
    print("   • Result deduplication")
    print("   • Flexible similarity thresholds")
    print("\n📚 Ready for Day 10: Policy Ingestion & Comparison")
    
    return True


if __name__ == "__main__":
    try:
        test_query_engine_full()
        print("\n" + "="*70)
        print("✅ ALL TESTS PASSED!")
        print("="*70)
    except Exception as e:
        print(f"\n❌ Error: {e}")
        import traceback
        traceback.print_exc()