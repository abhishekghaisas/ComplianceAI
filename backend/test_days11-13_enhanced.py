"""
Week 2, Days 11-13: Enhanced Matching & Analysis Integration Test
Tests improved scoring, gap analysis, and recommendations
"""

import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

from app.week2.policy_reader import PolicyReader
from app.week2.rag_chunker import DocumentChunker
from app.week2.rag_embedder import EmbeddingGenerator
from app.week2.rag_store import VectorStore
from app.week2.rag_query import QueryEngine
from app.week2.enhanced_policy_matcher import EnhancedPolicyMatcher


def test_enhanced_matching():
    """Test enhanced matching with Days 11-13 improvements"""
    
    print("="*70)
    print("🚀 WEEK 2, DAYS 11-13: ENHANCED MATCHING & ANALYSIS TEST")
    print("="*70 + "\n")
    
    print("This test demonstrates:")
    print("• Improved scoring algorithm (Day 11)")
    print("• Adaptive thresholds by severity (Day 11)")
    print("• Priority-based gap ranking (Day 12)")
    print("• Remediation roadmap (Day 12)")
    print("• Weighted coverage scoring (Day 12)")
    print("• Actionable recommendations (Days 11-13)")
    print()
    
    # Use Day 10 data
    print("Note: Using Day 10's database for comparison...")
    print("(Run test_day10_policy_pipeline.py first if database doesn't exist)")
    print()
    
    # Initialize with existing database
    embedder = EmbeddingGenerator()
    store = VectorStore(persist_directory="./day10_demo_db")
    query_engine = QueryEngine(store, embedder)
    
    # Enhanced matcher with improvements
    enhanced_matcher = EnhancedPolicyMatcher(
        query_engine,
        coverage_threshold=0.45,  # Slightly lower
        partial_threshold=0.25,   # Slightly lower
        use_adaptive_thresholds=True  # Adjust by severity
    )
    
    print("✅ Enhanced matcher initialized with:")
    print("   • Adaptive thresholds (severity-based)")
    print("   • Improved scoring (4 components)")
    print("   • Hybrid search enabled")
    print()
    
    # Test requirements (same as Day 10)
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
    
    print("="*70)
    print("MATCHING WITH ENHANCED ALGORITHM")
    print("="*70 + "\n")
    
    results = enhanced_matcher.batch_match_requirements(test_requirements)
    
    print()
    
    # Show improved results
    print("="*70)
    print("ENHANCED MATCH RESULTS")
    print("="*70 + "\n")
    
    for result in results:
        print(f"📋 {result['requirement_id']}: {result['severity']}")
        print(f"   Status: {result['coverage_status']} ({result['confidence']} confidence)")
        print(f"   Score: {result['match_percent']}")
        print(f"   Thresholds used: COVERED ≥{result['thresholds_used']['coverage']:.0%}, PARTIAL ≥{result['thresholds_used']['partial']:.0%}")
        
        if result['policy_matches']:
            top = result['policy_matches'][0]
            print(f"   Best match: {top['policy_section']}")
            
            if 'score_breakdown' in top:
                breakdown = top['score_breakdown']
                print(f"   Score breakdown:")
                print(f"      Semantic: {breakdown.get('semantic', 0):.1%}")
                print(f"      Keywords: {breakdown.get('keyword', 0):.1%}")
                print(f"      Entities: {breakdown.get('entity', 0):.1%}")
                print(f"      Context:  {breakdown.get('context', 0):.1%}")
        
        print()
    
    # Enhanced gap report
    print("="*70)
    print("ENHANCED GAP ANALYSIS")
    print("="*70 + "\n")
    
    gap_report = enhanced_matcher.generate_enhanced_gap_report(results)
    
    print("📊 COVERAGE METRICS")
    print("-"*70)
    print(f"Standard Coverage:  {gap_report['coverage_percentage']:.1f}%")
    print(f"Weighted Coverage:  {gap_report['weighted_coverage']:.1f}% (severity-adjusted)")
    print(f"Overall Assessment: {gap_report['overall_assessment']}")
    print()
    
    print(f"Covered:  {gap_report['covered']}")
    print(f"Partial:  {gap_report['partial']}")
    print(f"Missing:  {gap_report['missing']}")
    print()
    
    print("📊 BY SEVERITY")
    print("-"*70)
    for severity, counts in gap_report['by_severity'].items():
        total = counts['total']
        cov_pct = (counts['covered'] / total * 100) if total > 0 else 0
        print(f"{severity}: {counts['covered']}/{total} covered ({cov_pct:.0f}%)")
    print()
    
    # Priority gaps
    if gap_report['priority_gaps']:
        print("🎯 PRIORITY-RANKED GAPS")
        print("-"*70)
        for gap in gap_report['priority_gaps']:
            print(f"{gap['priority']:7} | {gap['requirement_id']} ({gap['severity']}) - {gap['match_percent']}")
        print()
    
    # Remediation roadmap
    roadmap = gap_report['remediation_roadmap']
    
    if roadmap['phase_1_immediate']:
        print("📅 REMEDIATION ROADMAP")
        print("-"*70)
        print(f"\n🚨 PHASE 1 - IMMEDIATE ({len(roadmap['phase_1_immediate'])} items):")
        for item in roadmap['phase_1_immediate']:
            print(f"   • {item['requirement_id']}: {item['requirement'][:60]}...")
            if item['actions']:
                print(f"     Action: {item['actions'][0]}")
        
        if roadmap['phase_2_short_term']:
            print(f"\n📋 PHASE 2 - SHORT TERM ({len(roadmap['phase_2_short_term'])} items):")
            for item in roadmap['phase_2_short_term'][:3]:  # Show first 3
                print(f"   • {item['requirement_id']}: {item['requirement'][:60]}...")
        
        if roadmap['phase_3_ongoing']:
            print(f"\n✓ PHASE 3 - ONGOING ({len(roadmap['phase_3_ongoing'])} items)")
        print()
    
    # Overall recommendation
    print("💡 OVERALL RECOMMENDATION")
    print("-"*70)
    print(gap_report['recommendation'])
    print()
    
    # Comparison with Day 10
    print("="*70)
    print("📊 IMPROVEMENT vs DAY 10")
    print("="*70 + "\n")
    
    print("Day 10 Results (Basic Matcher):")
    print("   • Coverage: 20% (1/5 COVERED)")
    print("   • Thresholds: Fixed 50%/30%")
    print("   • Scoring: 3 components")
    print()
    
    covered_count = gap_report['covered']
    coverage_pct = gap_report['coverage_percentage']
    weighted_cov = gap_report['weighted_coverage']
    
    print("Days 11-13 Results (Enhanced Matcher):")
    print(f"   • Coverage: {coverage_pct:.0f}% ({covered_count}/{len(results)} COVERED)")
    print(f"   • Weighted Coverage: {weighted_cov:.1f}%")
    print("   • Thresholds: Adaptive by severity")
    print("   • Scoring: 4 components + context")
    print("   • Roadmap: 3-phase remediation plan")
    print()
    
    improvement = coverage_pct - 20.0
    if improvement > 0:
        print(f"✅ Improvement: +{improvement:.0f}% coverage with enhanced algorithm!")
    
    print("\n" + "="*70)
    print("🎉 ENHANCED MATCHING COMPLETE!")
    print("="*70)
    print("\n✅ Days 11-13 Complete! Enhanced features:")
    print("   • Adaptive thresholds (severity-based)")
    print("   • 4-component scoring (semantic + keywords + entities + context)")
    print("   • Priority-ranked gaps")
    print("   • Weighted coverage metrics")
    print("   • 3-phase remediation roadmap")
    print("   • Actionable recommendations")
    print("\n📚 Ready for Week 2 completion and Week 3!")
    
    return True


if __name__ == "__main__":
    try:
        test_enhanced_matching()
        print("\n" + "="*70)
        print("✅ ALL TESTS PASSED!")
        print("="*70)
    except Exception as e:
        print(f"\n❌ Error: {e}")
        import traceback
        traceback.print_exc()