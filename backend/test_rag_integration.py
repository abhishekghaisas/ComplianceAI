"""
Week 2, Day 8: RAG System Integration Test
Tests all modules working together
"""

import sys
import json
from app.week2.rag_chunker import DocumentChunker
from app.week2.rag_embedder import EmbeddingGenerator
from app.week2.rag_store import VectorStore


def test_full_pipeline():
    """Test the complete RAG pipeline"""
    print("="*70)
    print("🚀 WEEK 2, DAY 8: RAG SYSTEM INTEGRATION TEST")
    print("="*70 + "\n")
    
    # Step 1: Initialize components
    print("STEP 1: Initializing Components\n")
    print("-" * 70)
    
    chunker = DocumentChunker(chunk_size=300, overlap=50)
    embedder = EmbeddingGenerator()
    store = VectorStore(persist_directory="./demo_chroma_db")
    
    print("\n✅ All components initialized!\n")
    
    # Step 2: Create sample requirements (simulating Week 1 output)
    print("="*70)
    print("STEP 2: Creating Sample Requirements\n")
    print("-" * 70)
    
    sample_requirements = [
        {
            "requirement_id": "req_001",
            "type": "OBLIGATION",
            "severity": "HIGH",
            "section_title": "Small Business Lending Data Collection",
            "requirement": "Financial institutions must collect and maintain data on small business loan applications, including applicant demographics, loan amounts, interest rates, and approval decisions. This data must be reported quarterly to the CFPB.",
            "plain_language": "Banks need to track detailed information about every small business loan application and report it to regulators every quarter.",
            "deadline": "January 1, 2028",
            "entities": {
                "dates": ["2028-01-01"],
                "amounts": ["$5 million threshold"],
                "agencies": ["CFPB"]
            }
        },
        {
            "requirement_id": "req_002",
            "type": "PROHIBITION",
            "severity": "CRITICAL",
            "section_title": "Discriminatory Lending Practices",
            "requirement": "Lenders are strictly prohibited from discriminating on the basis of race, gender, ethnicity, or other protected characteristics in any lending decision.",
            "plain_language": "You cannot deny loans or charge different rates based on someone's race, gender, or similar protected characteristics.",
            "deadline": "Effective immediately",
            "entities": {
                "agencies": ["CFPB", "DOJ"]
            }
        },
        {
            "requirement_id": "req_003",
            "type": "RECOMMENDATION",
            "severity": "MEDIUM",
            "section_title": "Customer Notification",
            "requirement": "Banks should notify applicants of lending decisions within 30 days of receiving a complete application.",
            "plain_language": "Try to let customers know about loan decisions within a month of getting their full application.",
            "deadline": "Best practice",
            "entities": {
                "dates": ["30 days"]
            }
        }
    ]
    
    print(f"✅ Created {len(sample_requirements)} sample requirements\n")
    for req in sample_requirements:
        print(f"   • {req['requirement_id']}: {req['type']} - {req['section_title']}")
    
    # Step 3: Chunk requirements
    print("\n" + "="*70)
    print("STEP 3: Chunking Requirements\n")
    print("-" * 70)
    
    all_chunks = []
    for req in sample_requirements:
        req_chunks = chunker.chunk_requirement(req, "cfpb_section_1071.pdf")
        all_chunks.extend(req_chunks)
        print(f"✅ {req['requirement_id']}: {len(req_chunks)} chunk(s)")
    
    print(f"\n📦 Total chunks created: {len(all_chunks)}")
    
    # Step 4: Generate embeddings
    print("\n" + "="*70)
    print("STEP 4: Generating Embeddings\n")
    print("-" * 70)
    
    embedded_chunks = embedder.embed_chunks(all_chunks, batch_size=8)
    
    print(f"\n✅ Generated {len(embedded_chunks)} embeddings")
    print(f"✅ Embedding dimension: {len(embedded_chunks[0]['embedding'])}")
    
    # Step 5: Store in ChromaDB
    print("\n" + "="*70)
    print("STEP 5: Storing in Vector Database\n")
    print("-" * 70)
    
    store.create_regulations_collection(reset=True)
    store.add_chunks(embedded_chunks, collection_type="regulations")
    
    # Step 6: Test semantic search
    print("\n" + "="*70)
    print("STEP 6: Testing Semantic Search\n")
    print("-" * 70)
    
    test_queries = [
        "What are the requirements for collecting loan data?",
        "Are there rules against discrimination in lending?",
        "How quickly should I notify loan applicants?"
    ]
    
    for i, query in enumerate(test_queries):
        print(f"\n🔍 Query {i + 1}: \"{query}\"\n")
        
        # Embed query
        query_embedding = embedder.embed_text(query)
        
        # Search
        results = store.query_regulations(query_embedding, n_results=2)
        
        print(f"   Top {len(results['documents'][0])} Results:")
        for j, doc in enumerate(results['documents'][0]):
            distance = results['distances'][0][j]
            similarity = 1 - distance  # Convert distance to similarity
            metadata = results['metadatas'][0][j]
            
            print(f"\n   📄 Result {j + 1} (Similarity: {similarity:.2%}):")
            print(f"      Type: {metadata.get('requirement_type', 'N/A')}")
            print(f"      Severity: {metadata.get('severity', 'N/A')}")
            print(f"      Text: {doc[:100]}...")
    
    # Step 7: Test filtered search
    print("\n" + "="*70)
    print("STEP 7: Testing Filtered Search\n")
    print("-" * 70)
    
    print("🔍 Find all HIGH severity OBLIGATIONS:\n")
    
    query_embedding = embedder.embed_text("compliance requirements")
    results = store.query_regulations(
        query_embedding,
        n_results=5,
        filters={"severity": "HIGH", "requirement_type": "OBLIGATION"}
    )
    
    print(f"   Found {len(results['documents'][0])} matching requirements:")
    for j, doc in enumerate(results['documents'][0]):
        metadata = results['metadatas'][0][j]
        print(f"\n   📄 {metadata.get('requirement_id', 'N/A')}:")
        print(f"      {doc[:80]}...")
    
    # Final stats
    print("\n" + "="*70)
    print("📊 FINAL STATISTICS\n")
    print("-" * 70)
    
    stats = store.get_collection_stats()
    print(f"✅ Requirements in database: {stats['regulations']['count']}")
    print(f"✅ Policies in database: {stats['policies']['count']}")
    print(f"✅ Total chunks processed: {len(all_chunks)}")
    print(f"✅ Embedding dimension: {embedder.embedding_dim}")
    
    print("\n" + "="*70)
    print("🎉 RAG SYSTEM IS WORKING!")
    print("="*70)
    print("\n✅ Day 8 Complete! You now have:")
    print("   • Document chunking with semantic boundaries")
    print("   • Fast embedding generation (384D vectors)")
    print("   • ChromaDB vector database")
    print("   • Semantic search with filtering")
    print("   • Foundation for policy matching!")
    print("\n📚 Ready for Day 9: Query Engine & Search Interface")


def save_sample_output():
    """Save a sample output for reference"""
    output = {
        "day": 8,
        "title": "RAG Foundation Complete",
        "components": {
            "chunker": "DocumentChunker - smart semantic chunking",
            "embedder": "EmbeddingGenerator - sentence-transformers",
            "store": "VectorStore - ChromaDB with persistence"
        },
        "capabilities": [
            "Chunk requirements and policies",
            "Generate 384D embeddings",
            "Store in vector database",
            "Semantic search",
            "Filtered search by metadata"
        ],
        "next_steps": [
            "Build query engine (Day 9)",
            "Add policy ingestion (Day 10)",
            "Create policy matcher (Day 11)",
            "Gap analysis (Day 12-13)"
        ]
    }
    
    with open("day8_completion_summary.json", "w") as f:
        json.dump(output, f, indent=2)
    
    print("\n💾 Saved completion summary to day8_completion_summary.json")


if __name__ == "__main__":
    try:
        test_full_pipeline()
        save_sample_output()
        
        print("\n" + "="*70)
        print("✅ ALL TESTS PASSED!")
        print("="*70)
        
    except Exception as e:
        print(f"\n❌ Error: {e}")
        import traceback
        traceback.print_exc()