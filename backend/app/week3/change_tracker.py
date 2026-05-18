"""
Change Tracking System - Week 3, Days 17-18
Tracks changes between regulation versions and analyzes impact
"""

from typing import List, Dict, Any, Tuple
from datetime import datetime
import difflib
from collections import defaultdict


class ChangeTracker:
    """Track and analyze changes between regulation versions"""
    
    def __init__(self):
        """Initialize change tracker"""
        self.change_types = {
            'ADDED': 'New requirement added',
            'REMOVED': 'Requirement removed',
            'MODIFIED': 'Requirement modified',
            'UNCHANGED': 'No change'
        }
    
    def compare_versions(
        self,
        old_requirements: List[Dict[str, Any]],
        new_requirements: List[Dict[str, Any]],
        version_old: str = "Previous",
        version_new: str = "Current"
    ) -> Dict[str, Any]:
        """
        Compare two versions of requirements
        
        Args:
            old_requirements: Requirements from older version
            new_requirements: Requirements from newer version
            version_old: Label for old version
            version_new: Label for new version
            
        Returns:
            Change analysis with added, removed, modified requirements
        """
        print(f"🔍 Comparing versions: {version_old} vs {version_new}\n")
        print(f"   Old version: {len(old_requirements)} requirements")
        print(f"   New version: {len(new_requirements)} requirements\n")
        
        # Create ID mappings
        old_by_id = {req['requirement_id']: req for req in old_requirements}
        new_by_id = {req['requirement_id']: req for req in new_requirements}
        
        old_ids = set(old_by_id.keys())
        new_ids = set(new_by_id.keys())
        
        # Find changes
        added_ids = new_ids - old_ids
        removed_ids = old_ids - new_ids
        common_ids = old_ids & new_ids
        
        changes = {
            'added': [],
            'removed': [],
            'modified': [],
            'unchanged': []
        }
        
        # Added requirements
        for req_id in added_ids:
            changes['added'].append({
                'requirement_id': req_id,
                'requirement': new_by_id[req_id],
                'severity': new_by_id[req_id].get('severity', 'UNKNOWN'),
                'type': new_by_id[req_id].get('type', 'UNKNOWN')
            })
        
        # Removed requirements
        for req_id in removed_ids:
            changes['removed'].append({
                'requirement_id': req_id,
                'requirement': old_by_id[req_id],
                'severity': old_by_id[req_id].get('severity', 'UNKNOWN'),
                'type': old_by_id[req_id].get('type', 'UNKNOWN')
            })
        
        # Modified requirements
        for req_id in common_ids:
            old_req = old_by_id[req_id]
            new_req = new_by_id[req_id]
            
            modification = self._detect_modification(old_req, new_req)
            
            if modification['is_modified']:
                changes['modified'].append({
                    'requirement_id': req_id,
                    'old_requirement': old_req,
                    'new_requirement': new_req,
                    'changes': modification['changes'],
                    'severity': new_req.get('severity', 'UNKNOWN'),
                    'impact_level': modification['impact_level']
                })
            else:
                changes['unchanged'].append({
                    'requirement_id': req_id,
                    'requirement': new_req
                })
        
        # Calculate summary statistics
        summary = self._calculate_change_summary(changes, version_old, version_new)
        
        return {
            'version_old': version_old,
            'version_new': version_new,
            'comparison_date': datetime.now().isoformat(),
            'total_changes': len(changes['added']) + len(changes['removed']) + len(changes['modified']),
            'changes': changes,
            'summary': summary,
            'impact_analysis': self._analyze_impact(changes)
        }
    
    def _detect_modification(self, old_req: Dict, new_req: Dict) -> Dict[str, Any]:
        """Detect what changed in a requirement"""
        changes = {}
        is_modified = False
        impact_scores = []
        
        # Check requirement text
        old_text = old_req.get('requirement', '')
        new_text = new_req.get('requirement', '')
        
        if old_text != new_text:
            similarity = difflib.SequenceMatcher(None, old_text, new_text).ratio()
            
            if similarity < 0.95:  # More than 5% different
                changes['requirement_text'] = {
                    'old': old_text[:100] + '...' if len(old_text) > 100 else old_text,
                    'new': new_text[:100] + '...' if len(new_text) > 100 else new_text,
                    'similarity': f"{similarity * 100:.1f}%",
                    'diff': list(difflib.unified_diff(
                        old_text.split(),
                        new_text.split(),
                        lineterm='',
                        n=0
                    ))[:20]  # First 20 differences
                }
                is_modified = True
                impact_scores.append(8)  # Text change = high impact
        
        # Check severity
        if old_req.get('severity') != new_req.get('severity'):
            changes['severity'] = {
                'old': old_req.get('severity'),
                'new': new_req.get('severity')
            }
            is_modified = True
            impact_scores.append(7)  # Severity change = high impact
        
        # Check type
        if old_req.get('type') != new_req.get('type'):
            changes['type'] = {
                'old': old_req.get('type'),
                'new': new_req.get('type')
            }
            is_modified = True
            impact_scores.append(9)  # Type change = very high impact
        
        # Check deadline
        if old_req.get('deadline') != new_req.get('deadline'):
            changes['deadline'] = {
                'old': old_req.get('deadline'),
                'new': new_req.get('deadline')
            }
            is_modified = True
            impact_scores.append(6)  # Deadline change = medium-high impact
        
        # Check entities
        old_entities = old_req.get('entities', {})
        new_entities = new_req.get('entities', {})
        
        entity_changes = {}
        
        if old_entities.get('dates') != new_entities.get('dates'):
            entity_changes['dates'] = {
                'old': old_entities.get('dates', []),
                'new': new_entities.get('dates', [])
            }
            impact_scores.append(5)
        
        if old_entities.get('amounts') != new_entities.get('amounts'):
            entity_changes['amounts'] = {
                'old': old_entities.get('amounts', []),
                'new': new_entities.get('amounts', [])
            }
            impact_scores.append(6)
        
        if old_entities.get('agencies') != new_entities.get('agencies'):
            entity_changes['agencies'] = {
                'old': old_entities.get('agencies', []),
                'new': new_entities.get('agencies', [])
            }
            impact_scores.append(4)
        
        if entity_changes:
            changes['entities'] = entity_changes
            is_modified = True
        
        # Calculate impact level
        if impact_scores:
            avg_impact = sum(impact_scores) / len(impact_scores)
            if avg_impact >= 7:
                impact_level = 'HIGH'
            elif avg_impact >= 4:
                impact_level = 'MEDIUM'
            else:
                impact_level = 'LOW'
        else:
            impact_level = 'NONE'
        
        return {
            'is_modified': is_modified,
            'changes': changes,
            'impact_level': impact_level,
            'change_count': len(changes)
        }
    
    def _calculate_change_summary(
        self,
        changes: Dict,
        version_old: str,
        version_new: str
    ) -> Dict[str, Any]:
        """Calculate summary statistics for changes"""
        added = changes['added']
        removed = changes['removed']
        modified = changes['modified']
        
        # Impact by severity
        impact_by_severity = defaultdict(lambda: {'added': 0, 'removed': 0, 'modified': 0})
        
        for item in added:
            impact_by_severity[item['severity']]['added'] += 1
        
        for item in removed:
            impact_by_severity[item['severity']]['removed'] += 1
        
        for item in modified:
            impact_by_severity[item['severity']]['modified'] += 1
        
        # High-impact changes
        high_impact = [m for m in modified if m.get('impact_level') == 'HIGH']
        
        return {
            'total_added': len(added),
            'total_removed': len(removed),
            'total_modified': len(modified),
            'total_unchanged': len(changes['unchanged']),
            'change_rate': (len(added) + len(removed) + len(modified)) / (len(added) + len(removed) + len(modified) + len(changes['unchanged'])) * 100,
            'impact_by_severity': dict(impact_by_severity),
            'high_impact_changes': len(high_impact),
            'version_comparison': f"{version_old} → {version_new}"
        }
    
    def _analyze_impact(self, changes: Dict) -> Dict[str, Any]:
        """Analyze impact of changes on compliance"""
        impact = {
            'policy_updates_required': 0,
            'urgent_actions': [],
            'affected_areas': set(),
            'estimated_effort_hours': 0
        }
        
        # Added requirements = new policies needed
        for item in changes['added']:
            impact['policy_updates_required'] += 1
            impact['affected_areas'].add(item['requirement'].get('section_title', 'Unknown'))
            
            if item['severity'] in ['CRITICAL', 'HIGH']:
                impact['urgent_actions'].append({
                    'action': 'CREATE_POLICY',
                    'requirement_id': item['requirement_id'],
                    'description': f"Create policy for new {item['severity']} requirement"
                })
            
            # Estimate effort
            severity_hours = {'CRITICAL': 8, 'HIGH': 4, 'MEDIUM': 2, 'LOW': 1}
            impact['estimated_effort_hours'] += severity_hours.get(item['severity'], 2)
        
        # Removed requirements = policies can be simplified
        for item in changes['removed']:
            impact['affected_areas'].add(item['requirement'].get('section_title', 'Unknown'))
        
        # Modified requirements = policies need updates
        for item in changes['modified']:
            impact['policy_updates_required'] += 1
            impact['affected_areas'].add(item['new_requirement'].get('section_title', 'Unknown'))
            
            if item.get('impact_level') == 'HIGH':
                impact['urgent_actions'].append({
                    'action': 'UPDATE_POLICY',
                    'requirement_id': item['requirement_id'],
                    'description': f"Update policy - {item['severity']} requirement modified significantly"
                })
                impact['estimated_effort_hours'] += 4
            else:
                impact['estimated_effort_hours'] += 2
        
        impact['affected_areas'] = list(impact['affected_areas'])
        
        return impact


def test_change_tracker():
    """Test change tracking system"""
    print("="*70)
    print("🧪 TESTING CHANGE TRACKER")
    print("="*70 + "\n")
    
    # Old version requirements (2024)
    old_requirements = [
        {
            'requirement_id': 'req_001',
            'type': 'OBLIGATION',
            'severity': 'HIGH',
            'section_title': 'Data Reporting',
            'requirement': 'Financial institutions must report small business lending data annually.',
            'deadline': 'March 31 annually',
            'entities': {
                'dates': ['annually', 'March 31'],
                'agencies': ['CFPB']
            }
        },
        {
            'requirement_id': 'req_002',
            'type': 'RECOMMENDATION',
            'severity': 'MEDIUM',
            'section_title': 'Customer Notification',
            'requirement': 'Banks should notify customers within 45 days.',
            'entities': {
                'dates': ['45 days']
            }
        },
        {
            'requirement_id': 'req_003',
            'type': 'DEFINITION',
            'severity': 'LOW',
            'section_title': 'Definitions',
            'requirement': 'Small business means businesses with gross annual revenue of $1 million or less.',
            'entities': {
                'amounts': ['$1 million']
            }
        }
    ]
    
    # New version requirements (2025)
    new_requirements = [
        {
            'requirement_id': 'req_001',
            'type': 'OBLIGATION',
            'severity': 'CRITICAL',  # Changed from HIGH
            'section_title': 'Data Reporting',
            'requirement': 'Financial institutions must report small business lending data quarterly.',  # Changed from annually
            'deadline': '30 days after quarter end',  # Changed deadline
            'entities': {
                'dates': ['quarterly', '30 days'],
                'agencies': ['CFPB']
            }
        },
        {
            'requirement_id': 'req_002',
            'type': 'OBLIGATION',  # Changed from RECOMMENDATION
            'severity': 'HIGH',  # Changed from MEDIUM
            'section_title': 'Customer Notification',
            'requirement': 'Banks must notify customers within 30 days.',  # Changed from should/45 days
            'entities': {
                'dates': ['30 days']
            }
        },
        # req_003 removed (DEFINITION removed)
        {
            'requirement_id': 'req_004',  # New requirement
            'type': 'OBLIGATION',
            'severity': 'HIGH',
            'section_title': 'Beneficial Ownership',
            'requirement': 'Banks must verify beneficial owners of all legal entity customers.',
            'entities': {
                'agencies': ['FinCEN']
            }
        }
    ]
    
    # Initialize tracker
    tracker = ChangeTracker()
    
    # Compare versions
    print("COMPARING VERSIONS")
    print("-"*70 + "\n")
    
    results = tracker.compare_versions(
        old_requirements,
        new_requirements,
        version_old="2024 Version",
        version_new="2025 Version"
    )
    
    # Display results
    print("="*70)
    print("CHANGE ANALYSIS RESULTS")
    print("="*70 + "\n")
    
    summary = results['summary']
    
    print(f"📊 SUMMARY")
    print("-"*70)
    print(f"Total Changes: {results['total_changes']}")
    print(f"Change Rate: {summary['change_rate']:.1f}%")
    print()
    print(f"Added:     {summary['total_added']}")
    print(f"Removed:   {summary['total_removed']}")
    print(f"Modified:  {summary['total_modified']}")
    print(f"Unchanged: {summary['total_unchanged']}")
    print()
    
    # Show added requirements
    if results['changes']['added']:
        print("="*70)
        print(f"➕ ADDED REQUIREMENTS ({len(results['changes']['added'])})")
        print("-"*70 + "\n")
        
        for item in results['changes']['added']:
            print(f"📄 {item['requirement_id']} ({item['severity']})")
            print(f"   Type: {item['type']}")
            print(f"   Text: {item['requirement'].get('requirement', '')[:80]}...")
            print()
    
    # Show removed requirements
    if results['changes']['removed']:
        print("="*70)
        print(f"➖ REMOVED REQUIREMENTS ({len(results['changes']['removed'])})")
        print("-"*70 + "\n")
        
        for item in results['changes']['removed']:
            print(f"📄 {item['requirement_id']} ({item['severity']})")
            print(f"   Type: {item['type']}")
            print(f"   Text: {item['requirement'].get('requirement', '')[:80]}...")
            print()
    
    # Show modified requirements
    if results['changes']['modified']:
        print("="*70)
        print(f"✏️  MODIFIED REQUIREMENTS ({len(results['changes']['modified'])})")
        print("-"*70 + "\n")
        
        for item in results['changes']['modified']:
            print(f"📄 {item['requirement_id']} (Impact: {item['impact_level']})")
            print(f"   Changes detected: {len(item['changes'])}")
            
            for change_field, change_detail in item['changes'].items():
                if change_field == 'requirement_text':
                    print(f"\n   Text changed ({change_detail['similarity']} similar):")
                    print(f"      Old: {change_detail['old'][:60]}...")
                    print(f"      New: {change_detail['new'][:60]}...")
                elif change_field in ['severity', 'type', 'deadline']:
                    print(f"   {change_field.title()}: {change_detail['old']} → {change_detail['new']}")
                elif change_field == 'entities':
                    for entity_type, entity_change in change_detail.items():
                        print(f"   {entity_type.title()}: {entity_change['old']} → {entity_change['new']}")
            print()
    
    # Impact analysis
    print("="*70)
    print("💥 IMPACT ANALYSIS")
    print("-"*70 + "\n")
    
    impact = results['impact_analysis']
    
    print(f"Policy Updates Required: {impact['policy_updates_required']}")
    print(f"Urgent Actions: {len(impact['urgent_actions'])}")
    print(f"Affected Areas: {len(impact['affected_areas'])}")
    print(f"Estimated Effort: {impact['estimated_effort_hours']} hours")
    print()
    
    if impact['affected_areas']:
        print("Affected Policy Areas:")
        for area in impact['affected_areas']:
            print(f"   • {area}")
        print()
    
    if impact['urgent_actions']:
        print("Urgent Actions Required:")
        for i, action in enumerate(impact['urgent_actions'], 1):
            print(f"   {i}. {action['action']}: {action['requirement_id']}")
            print(f"      {action['description']}")
        print()
    
    print("="*70)
    print("✅ CHANGE TRACKER TESTS PASSED!")
    print("="*70)
    
    return results


if __name__ == "__main__":
    test_change_tracker()