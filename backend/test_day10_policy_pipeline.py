"""
Week 2, Day 10: Policy Ingestion & Matching Integration Test
Complete pipeline from policy reading to gap analysis
"""

import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

from app.week2.policy_reader import PolicyReader
from app.week2.rag_chunker import DocumentChunker
from app.week2.rag_embedder import EmbeddingGenerator
from app.week2.rag_store import VectorStore
from app.week2.rag_query import QueryEngine
from app.week2.policy_matcher import PolicyMatcher


def test_full_policy_pipeline():
    """Test complete policy ingestion and matching pipeline"""
    
    print("="*70)
    print("🚀 WEEK 2, DAY 10: POLICY INGESTION & MATCHING TEST")
    print("="*70 + "\n")
    
    # Step 1: Initialize components
    print("STEP 1: Initializing Components")
    print("-"*70 + "\n")
    
    policy_reader = PolicyReader()
    chunker = DocumentChunker(chunk_size=400, overlap=50)
    embedder = EmbeddingGenerator()
    store = VectorStore(persist_directory="./day10_demo_db")
    query_engine = QueryEngine(store, embedder)
    
    print("✅ All components initialized\n")
    
    # Step 2: Create sample bank policy
    print("="*70)
    print("STEP 2: Creating Sample Bank Policy")
    print("-"*70 + "\n")
    
    sample_policy = """
COMMUNITY BANK LENDING POLICY

Version 3.2
Effective Date: January 15, 2024

1. PURPOSE AND SCOPE

This policy establishes comprehensive guidelines for all lending activities 
at Community Bank to ensure compliance with federal and state regulations 
while maintaining sound lending practices.

2. SMALL BUSINESS LENDING DATA COLLECTION

2.1 Data Collection Requirements

The bank shall collect the following information for all small business 
loan applications:

- Business demographic information including NAICS code
- Ownership demographics (race, ethnicity, gender of principal owners)
- Gross annual revenue
- Loan amount requested and approved
- Loan type and purpose
- Pricing information (interest rate, fees)
- Credit decision and action taken
- Reasons for denial if applicable

2.2 Reporting Requirements

All collected data must be compiled and reported to the Consumer Financial 
Protection Bureau (CFPB) on a quarterly basis. Reports are due within 30 
days following the end of each calendar quarter.

The bank maintains a dedicated compliance team responsible for data quality 
and timely submission of required reports.

3. FAIR LENDING AND NON-DISCRIMINATION

3.1 Prohibited Basis

The bank strictly prohibits discrimination in lending on the basis of:
- Race or color
- Religion
- National origin
- Sex or gender
- Marital status
- Age (provided applicant has capacity to contract)
- Receipt of public assistance

3.2 Equal Treatment

All applicants shall be evaluated using the same underwriting criteria 
and standards. Loan officers must document all credit decisions with 
objective, verifiable factors.

Any deviation from standard terms must be justified with business reasons 
documented in the loan file.

4. CUSTOMER DUE DILIGENCE

4.1 Customer Identification Program (CIP)

All new customers must be properly identified and verified before 
establishing a banking relationship. Required identification includes:
- Full legal name
- Date of birth
- Physical address (not PO Box)
- Government-issued identification number

4.2 Beneficial Ownership

For legal entity customers, the bank must identify and verify beneficial 
owners who own 25% or more of the entity or who exercise control.

4.3 Record Retention

Customer identification records must be maintained for five years after 
account closure. This includes copies of identification documents and 
verification procedures performed.

5. ADVERSE ACTION NOTIFICATIONS

When the bank takes adverse action on a credit application, the applicant 
must be notified within 30 days. The notice must include:
- Statement of action taken
- Specific reasons for the decision
- ECOA notice of rights
- Credit bureau information if credit report was used

All adverse action notices are reviewed by compliance before sending.

6. APPRAISAL REQUIREMENTS

For residential real estate secured loans, the bank provides applicants 
with a free copy of all appraisals and written valuations.

Appraisals must be provided at least three business days before loan 
consummation to allow borrower review.

7. COMPLIANCE MONITORING

7.1 Internal Audits

The compliance department conducts quarterly audits of lending activities 
to ensure adherence to this policy and applicable regulations.

7.2 Training

All lending personnel must complete annual fair lending and compliance 
training. New hires receive training within 30 days of employment.

7.3 Policy Review

This policy is reviewed annually and updated as needed to reflect changes 
in regulations, business practices, or identified deficiencies.

8. APPROVAL AND AUTHORITY

Loan approval authority is delegated based on loan amount and risk rating:
- Loans up to $100,000: Senior loan officers
- Loans $100,000 to $500,000: Lending managers
- Loans over $500,000: Senior credit committee

9. EXCEPTIONS

Any exceptions to this policy must be approved by the Chief Credit Officer 
and documented with business justification.
"""
    
    # Save to temp file
    import tempfile
    with tempfile.NamedTemporaryFile(mode='w', suffix='.txt', delete=False, dir='.') as f:
        f.write(sample_policy)
        policy_file = f.name
    
    print(f"✅ Created sample policy file: {policy_file}\n")
    
    # Step 3: Read and parse policy
    print("="*70)
    print("STEP 3: Reading and Parsing Policy")
    print("-"*70 + "\n")
    
    policy_doc = policy_reader.read_policy(policy_file)
    
    print(f"✅ Policy parsed:")
    print(f"   Title: {policy_doc['metadata']['title']}")
    print(f"   Words: {policy_doc['word_count']}")
    print(f"   Sections: {len(policy_doc['sections'])}")
    print(f"   Areas: {', '.join(policy_doc['metadata']['policy_areas'])}\n")
    
    # Step 4: Chunk and embed policy
    print("="*70)
    print("STEP 4: Chunking and Embedding Policy")
    print("-"*70 + "\n")
    
    policy_chunks = []
    for section in policy_doc['sections']:
        section_chunks = chunker.chunk_policy(
            section['content'],
            policy_doc['file_name'],
            metadata={
                'section_title': section['title'],
                'policy_area': ', '.join(policy_doc['metadata']['policy_areas'])
            }
        )
        policy_chunks.extend(section_chunks)
    
    print(f"✅ Created {len(policy_chunks)} policy chunks")
    
    embedded_policy_chunks = embedder.embed_chunks(policy_chunks)
    
    print(f"✅ Generated embeddings ({embedder.embedding_dim}D)\n")
    
    # Step 5: Store policies in ChromaDB
    print("="*70)
    print("STEP 5: Storing Policies in Database")
    print("-"*70 + "\n")
    
    store.create_policies_collection(reset=True)
    store.add_chunks(embedded_policy_chunks, collection_type="policies")
    
    print(f"✅ Policies stored in ChromaDB\n")
    
    # Step 6: Create test requirements
    print("="*70)
    print("STEP 6: Creating Test Requirements")
    print("-"*70 + "\n")
    
    test_requirements = [
        {
            'requirement_id': 'req_001',
            'type': 'OBLIGATION',
            'severity': 'HIGH',
            'section_title': 'Small Business Lending Data Collection',
            'requirement': 'Financial institutions must collect and report small business lending data quarterly to the CFPB.',
            'plain_language': 'Banks must track business loan data and report it to CFPB every quarter.',
            'entities': {
                'dates': ['quarterly'],
                'agencies': ['CFPB']
            }
        },
        {
            'requirement_id': 'req_002',
            'type': 'PROHIBITION',
            'severity': 'CRITICAL',
            'section_title': 'Fair Lending',
            'requirement': 'Lenders are prohibited from discriminating based on race, color, religion, national origin, sex, marital status, or age.',
            'plain_language': 'Cannot discriminate based on protected characteristics.',
            'entities': {
                'agencies': ['CFPB', 'DOJ']
            }
        },
        {
            'requirement_id': 'req_003',
            'type': 'OBLIGATION',
            'severity': 'HIGH',
            'section_title': 'Customer Due Diligence',
            'requirement': 'Banks must maintain customer identification programs and verify beneficial owners of legal entities.',
            'plain_language': 'Know your customers and keep their info on file.',
            'entities': {
                'agencies': ['FinCEN']
            }
        },
        {
            'requirement_id': 'req_004',
            'type': 'RECOMMENDATION',
            'severity': 'MEDIUM',
            'section_title': 'Adverse Action Notification',
            'requirement': 'Creditors should notify applicants of adverse credit decisions within 30 days.',
            'plain_language': 'Tell customers about loan denials within 30 days.',
            'entities': {
                'dates': ['30 days']
            }
        },
        {
            'requirement_id': 'req_005',
            'type': 'OBLIGATION',
            'severity': 'MEDIUM',
            'section_title': 'Appraisal Delivery',
            'requirement': 'Lenders must provide appraisal copies at least three business days before consummation.',
            'plain_language': 'Give borrowers appraisals 3 days before closing.',
            'entities': {
                'dates': ['three business days']
            }
        }
    ]
    
    print(f"✅ Created {len(test_requirements)} test requirements\n")
    for req in test_requirements:
        print(f"   • {req['requirement_id']}: {req['section_title']} ({req['severity']})")
    
    # Step 7: Match requirements to policies
    print("\n" + "="*70)
    print("STEP 7: Matching Requirements to Policies")
    print("="*70 + "\n")
    
    matcher = PolicyMatcher(query_engine, coverage_threshold=0.5, partial_threshold=0.3)
    
    match_results = matcher.batch_match_requirements(test_requirements, show_progress=True)
    
    print()
    
    # Step 8: Display match results
    print("="*70)
    print("STEP 8: Match Results")
    print("="*70 + "\n")
    
    for result in match_results:
        print(f"📋 {result['requirement_id']}: {result['requirement_text'][:60]}...")
        print(f"   Status: {result['coverage_status']} ({result['confidence']} confidence)")
        print(f"   Best Match: {result['match_percent']}")
        
        if result['policy_matches']:
            top_match = result['policy_matches'][0]
            print(f"   Policy Section: {top_match['policy_section']}")
            print(f"   Match Score: {top_match['match_percent']}")
        print()
    
    # Step 9: Generate gap report
    print("="*70)
    print("STEP 9: Compliance Gap Analysis")
    print("="*70 + "\n")
    
    gap_report = matcher.generate_gap_report(match_results)
    
    print("📊 COVERAGE SUMMARY")
    print("-"*70)
    print(f"Total Requirements: {gap_report['total_requirements']}")
    print(f"Covered: {gap_report['covered']} ({gap_report['coverage_percentage']:.1f}%)")
    print(f"Partial: {gap_report['partial']}")
    print(f"Missing: {gap_report['missing']}")
    print()
    
    print("📊 BY SEVERITY")
    print("-"*70)
    for severity, counts in gap_report['by_severity'].items():
        print(f"{severity}:")
        print(f"   Covered: {counts['covered']}")
        print(f"   Partial: {counts['partial']}")
        print(f"   Missing: {counts['missing']}")
    print()
    
    if gap_report['critical_gaps']:
        print(f"⚠️  CRITICAL GAPS: {gap_report['critical_gap_count']}")
        print("-"*70)
        for gap in gap_report['critical_gaps']:
            print(f"   • {gap['requirement_id']}: {gap['requirement_text'][:60]}...")
        print()
    
    print("💡 RECOMMENDATION")
    print("-"*70)
    print(f"{gap_report['recommendation']}")
    print()
    
    # Final statistics
    print("="*70)
    print("📊 FINAL STATISTICS")
    print("-"*70 + "\n")
    
    stats = store.get_collection_stats()
    print(f"✅ Policies in database: {stats['policies']['count']}")
    print(f"✅ Requirements matched: {len(match_results)}")
    print(f"✅ Coverage rate: {gap_report['coverage_percentage']:.1f}%")
    print(f"✅ Critical gaps: {gap_report['critical_gap_count']}")
    
    # Cleanup
    print()
    os.unlink(policy_file)
    print("🗑️  Cleaned up temp files")
    
    print("\n" + "="*70)
    print("🎉 POLICY INGESTION & MATCHING COMPLETE!")
    print("="*70)
    print("\n✅ Day 10 Complete! You now have:")
    print("   • Policy reading and parsing")
    print("   • Policy chunking and embedding")
    print("   • Requirement-to-policy matching")
    print("   • Coverage scoring and gap detection")
    print("   • Automated gap analysis reports")
    print("\n📚 Ready for Days 11-13: Enhanced Matching & Gap Analysis")
    
    return True


if __name__ == "__main__":
    try:
        test_full_policy_pipeline()
        print("\n" + "="*70)
        print("✅ ALL TESTS PASSED!")
        print("="*70)
    except Exception as e:
        print(f"\n❌ Error: {e}")
        import traceback
        traceback.print_exc()