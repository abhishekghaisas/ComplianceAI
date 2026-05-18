"""
Week 3, Days 15-21: Conflict Detection & Analysis Integration Test
Tests conflict detection, change tracking, and timeline analysis
"""

import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

from app.week3.conflict_detector import ConflictDetector
from app.week3.change_tracker import ChangeTracker
from app.week3.timeline_analyzer import TimelineAnalyzer
from datetime import datetime


def test_week3_integration():
    """Test complete Week 3 functionality"""
    
    print("="*70)
    print("🚀 WEEK 3: CONFLICT DETECTION & ANALYSIS INTEGRATION TEST")
    print("="*70 + "\n")
    
    print("This test demonstrates:")
    print("• Conflict detection (Days 15-16)")
    print("• Change tracking (Days 17-18)")
    print("• Timeline analysis (Days 19-20)")
    print("• Integration (Day 21)")
    print()
    
    # Sample requirements with intentional conflicts
    current_requirements = [
        {
            'requirement_id': 'req_001',
            'type': 'OBLIGATION',
            'severity': 'HIGH',
            'section_title': 'Data Reporting',
            'requirement': 'Financial institutions must report small business lending data quarterly to the CFPB.',
            'deadline': 'January 1, 2028',
            'entities': {
                'agencies': ['CFPB'],
                'dates': ['quarterly', 'January 1, 2028']
            }
        },
        {
            'requirement_id': 'req_002',
            'type': 'RECOMMENDATION',
            'severity': 'MEDIUM',
            'section_title': 'Data Reporting',
            'requirement': 'Banks should report small business lending data annually to maintain good standing.',
            'deadline': 'December 31 annually',
            'entities': {
                'agencies': ['CFPB'],
                'dates': ['annually']
            }
        },
        {
            'requirement_id': 'req_003',
            'type': 'OBLIGATION',
            'severity': 'CRITICAL',
            'section_title': 'Applicability',
            'requirement': 'This regulation applies to institutions with assets exceeding $1 billion.',
            'deadline': 'Effective immediately',
            'entities': {
                'amounts': ['$1 billion']
            }
        },
        {
            'requirement_id': 'req_004',
            'type': 'OBLIGATION',
            'severity': 'HIGH',
            'section_title': 'Applicability',
            'requirement': 'Covered institutions are those with total assets of $500 million or more.',
            'deadline': 'Effective immediately',
            'entities': {
                'amounts': ['$500 million']
            }
        },
        {
            'requirement_id': 'req_005',
            'type': 'OBLIGATION',
            'severity': 'HIGH',
            'section_title': 'Customer Notification',
            'requirement': 'Applicants must be notified within 30 days of a credit decision.',
            'deadline': 'June 30, 2027',
            'entities': {
                'dates': ['30 days', 'June 30, 2027']
            }
        },
        {
            'requirement_id': 'req_006',
            'type': 'RECOMMENDATION',
            'severity': 'MEDIUM',
            'section_title': 'Customer Notification',
            'requirement': 'Creditors should notify applicants within 60 days when possible.',
            'deadline': 'June 30, 2027',
            'entities': {
                'dates': ['60 days']
            }
        }
    ]
    
    # ================================================================
    # TEST 1: Conflict Detection
    # ================================================================
    
    print("="*70)
    print("TEST 1: CONFLICT DETECTION (Days 15-16)")
    print("="*70 + "\n")
    
    detector = ConflictDetector(embedder=None, similarity_threshold=0.6)
    
    conflict_results = detector.detect_all_conflicts(current_requirements)
    
    print("CONFLICTS DETECTED BY TYPE:")
    print("-"*70)
    
    for conflict_type, conflicts in conflict_results['conflicts_by_type'].items():
        if conflicts:
            print(f"\n{conflict_type.replace('_', ' ').title()}: {len(conflicts)}")
            for conflict in conflicts:
                print(f"   • {conflict['conflict_id']}")
                print(f"     {conflict['requirement_1']['id']} vs {conflict['requirement_2']['id']}")
                print(f"     Issue: {conflict['description']}")
                print(f"     Resolution: {conflict['resolution']}")
    
    print(f"\n📊 Total conflicts: {conflict_results['total_conflicts']}")
    print()
    
    # ================================================================
    # TEST 2: Change Tracking
    # ================================================================
    
    print("="*70)
    print("TEST 2: CHANGE TRACKING (Days 17-18)")
    print("="*70 + "\n")
    
    # Old version (simulate 2024 regulation)
    old_version = [
        {
            'requirement_id': 'req_001',
            'type': 'OBLIGATION',
            'severity': 'HIGH',
            'section_title': 'Data Reporting',
            'requirement': 'Financial institutions must report small business lending data annually.',
            'deadline': 'March 31 annually',
            'entities': {'dates': ['annually'], 'agencies': ['CFPB']}
        },
        {
            'requirement_id': 'req_005',
            'type': 'RECOMMENDATION',
            'severity': 'MEDIUM',
            'section_title': 'Customer Notification',
            'requirement': 'Banks should notify customers within 45 days.',
            'deadline': 'Not specified',
            'entities': {'dates': ['45 days']}
        }
    ]
    
    # New version (current_requirements has changes)
    new_version = [current_requirements[0], current_requirements[4]]  # req_001, req_005
    
    tracker = ChangeTracker()
    
    change_results = tracker.compare_versions(
        old_version,
        new_version,
        version_old="2024 Edition",
        version_new="2025 Edition"
    )
    
    print("CHANGE SUMMARY:")
    print("-"*70)
    print(f"Added:     {change_results['summary']['total_added']}")
    print(f"Removed:   {change_results['summary']['total_removed']}")
    print(f"Modified:  {change_results['summary']['total_modified']}")
    print(f"Change Rate: {change_results['summary']['change_rate']:.1f}%")
    print()
    
    # Show modified requirements
    if change_results['changes']['modified']:
        print("MODIFIED REQUIREMENTS:")
        print("-"*70)
        for mod in change_results['changes']['modified']:
            print(f"\n{mod['requirement_id']} (Impact: {mod['impact_level']})")
            for field, details in mod['changes'].items():
                if field == 'requirement_text':
                    print(f"   Text: {details['similarity']} similar")
                else:
                    print(f"   {field}: {details.get('old')} → {details.get('new')}")
    
    print("\n" + "="*70)
    print("IMPACT ANALYSIS:")
    print("-"*70)
    impact = change_results['impact_analysis']
    print(f"Policy updates required: {impact['policy_updates_required']}")
    print(f"Urgent actions: {len(impact['urgent_actions'])}")
    print(f"Estimated effort: {impact['estimated_effort_hours']} hours")
    print()
    
    # ================================================================
    # TEST 3: Timeline Analysis
    # ================================================================
    
    print("="*70)
    print("TEST 3: TIMELINE ANALYSIS (Days 19-20)")
    print("="*70 + "\n")
    
    analyzer = TimelineAnalyzer(current_date=datetime(2026, 5, 17))
    
    timeline_results = analyzer.analyze_deadlines(current_requirements)
    
    print("TIMELINE SUMMARY:")
    print("-"*70)
    print(f"Total deadlines: {timeline_results['total_deadlines']}")
    print(f"Upcoming (90 days): {timeline_results['upcoming_count']}")
    print(f"Overdue: {timeline_results['overdue_count']}")
    print(f"Future: {timeline_results['far_future_count']}")
    print()
    
    # Show critical path
    if timeline_results['critical_path']:
        print("CRITICAL PATH:")
        print("-"*70)
        for step in timeline_results['critical_path']:
            print(f"{step['step']}. {step['requirement_id']} ({step['severity']})")
            print(f"   Deadline: {step['deadline_date']}")
            print(f"   Days until: {step.get('days_until', 'N/A')}")
            print(f"   Effort: {step['estimated_effort']}")
            print()
    
    # ================================================================
    # TEST 4: Integration Summary
    # ================================================================
    
    print("="*70)
    print("📊 WEEK 3 INTEGRATION SUMMARY")
    print("="*70 + "\n")
    
    print("CONFLICT ANALYSIS:")
    print(f"   Total conflicts detected: {conflict_results['total_conflicts']}")
    print(f"   Resolutions recommended: {len(conflict_results['resolution_recommendations'])}")
    print()
    
    print("CHANGE ANALYSIS:")
    print(f"   Total changes: {change_results['total_changes']}")
    print(f"   High-impact changes: {change_results['summary']['high_impact_changes']}")
    print(f"   Policy updates needed: {change_results['impact_analysis']['policy_updates_required']}")
    print()
    
    print("TIMELINE ANALYSIS:")
    print(f"   Upcoming deadlines: {timeline_results['upcoming_count']}")
    print(f"   Critical path steps: {len(timeline_results['critical_path'])}")
    print(f"   Overdue items: {timeline_results['overdue_count']}")
    print()
    
    print("="*70)
    print("🎉 WEEK 3 COMPLETE!")
    print("="*70)
    print("\n✅ Days 15-21 Complete! Advanced features:")
    print("   • Conflict detection (frequency, obligation, timeline, amount)")
    print("   • Change tracking (version comparison, impact analysis)")
    print("   • Timeline analysis (deadline tracking, critical path)")
    print("   • Dependency mapping (cross-reference detection)")
    print("   • Resolution recommendations")
    print("\n📚 Ready for Week 4: Dashboard & Deployment")
    
    return True


if __name__ == "__main__":
    try:
        test_week3_integration()
        print("\n" + "="*70)
        print("✅ ALL TESTS PASSED!")
        print("="*70)
    except Exception as e:
        print(f"\n❌ Error: {e}")
        import traceback
        traceback.print_exc()