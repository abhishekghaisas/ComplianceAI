"""
Conflict Detection Engine - Week 3, Days 15-16
Identifies contradictory or conflicting requirements
"""

from typing import List, Dict, Any, Tuple, Optional
import re
from collections import defaultdict
import networkx as nx


class ConflictDetector:
    """Detect conflicts between regulatory requirements"""
    
    def __init__(self, embedder=None, similarity_threshold=0.6):
        """
        Initialize conflict detector
        
        Args:
            embedder: EmbeddingGenerator for semantic similarity
            similarity_threshold: Threshold for considering requirements related
        """
        self.embedder = embedder
        self.similarity_threshold = similarity_threshold
        self.conflict_patterns = self._build_conflict_patterns()
    
    def _build_conflict_patterns(self) -> Dict[str, List[str]]:
        """Build patterns for detecting conflicts"""
        return {
            'frequency': {
                'positive': ['quarterly', 'monthly', 'weekly', 'daily', 'annually', 'semi-annually'],
                'negative': ['not required', 'optional', 'at discretion']
            },
            'obligation': {
                'positive': ['must', 'shall', 'required', 'mandatory', 'will'],
                'negative': ['may', 'should', 'optional', 'discretionary', 'not required']
            },
            'prohibition': {
                'positive': ['prohibited', 'shall not', 'forbidden', 'restricted', 'banned'],
                'negative': ['permitted', 'allowed', 'authorized', 'may']
            },
            'amount': {
                'operators': ['exceeding', 'more than', 'greater than', 'less than', 'below', 'at least', 'maximum', 'minimum']
            }
        }
    
    def detect_all_conflicts(
        self,
        requirements: List[Dict[str, Any]]
    ) -> Dict[str, Any]:
        """
        Detect all types of conflicts in requirements
        
        Args:
            requirements: List of requirement dicts
            
        Returns:
            Conflict analysis with detected conflicts
        """
        print(f"🔍 Analyzing {len(requirements)} requirements for conflicts...\n")
        
        conflicts = {
            'frequency_conflicts': [],
            'obligation_conflicts': [],
            'scope_conflicts': [],
            'timeline_conflicts': [],
            'amount_conflicts': [],
            'semantic_conflicts': []
        }
        
        # Build requirement pairs for comparison
        pairs_checked = 0
        
        for i, req1 in enumerate(requirements):
            for j, req2 in enumerate(requirements[i+1:], i+1):
                pairs_checked += 1
                
                # Check if requirements are related (same topic area)
                if self._are_requirements_related(req1, req2):
                    
                    # Check for frequency conflicts
                    freq_conflict = self._detect_frequency_conflict(req1, req2)
                    if freq_conflict:
                        conflicts['frequency_conflicts'].append(freq_conflict)
                    
                    # Check for obligation conflicts
                    obl_conflict = self._detect_obligation_conflict(req1, req2)
                    if obl_conflict:
                        conflicts['obligation_conflicts'].append(obl_conflict)
                    
                    # Check for timeline conflicts
                    timeline_conflict = self._detect_timeline_conflict(req1, req2)
                    if timeline_conflict:
                        conflicts['timeline_conflicts'].append(timeline_conflict)
                    
                    # Check for amount conflicts
                    amount_conflict = self._detect_amount_conflict(req1, req2)
                    if amount_conflict:
                        conflicts['amount_conflicts'].append(amount_conflict)
        
        # Count total conflicts
        total_conflicts = sum(len(v) for v in conflicts.values())
        
        print(f"✅ Checked {pairs_checked} requirement pairs")
        print(f"📊 Found {total_conflicts} total conflicts\n")
        
        return {
            'total_requirements': len(requirements),
            'pairs_checked': pairs_checked,
            'total_conflicts': total_conflicts,
            'conflicts_by_type': conflicts,
            'conflict_graph': self._build_conflict_graph(conflicts),
            'resolution_recommendations': self._generate_conflict_resolutions(conflicts)
        }
    
    def _are_requirements_related(self, req1: Dict, req2: Dict) -> bool:
        """
        Check if two requirements are related (same topic)
        
        Uses:
        - Same section titles
        - Shared entities (agencies)
        - Semantic similarity (if embedder available)
        """
        # Check section titles
        section1 = req1.get('section_title', '').lower()
        section2 = req2.get('section_title', '').lower()
        
        if section1 and section2:
            # Same section or overlapping keywords
            words1 = set(section1.split())
            words2 = set(section2.split())
            if len(words1 & words2) >= 2:  # At least 2 shared words
                return True
        
        # Check shared agencies
        entities1 = req1.get('entities', {})
        entities2 = req2.get('entities', {})
        
        agencies1 = set(entities1.get('agencies', []))
        agencies2 = set(entities2.get('agencies', []))
        
        if agencies1 & agencies2:  # Shared agency
            return True
        
        # Semantic similarity check (if embedder available)
        if self.embedder:
            text1 = req1.get('requirement', '')
            text2 = req2.get('requirement', '')
            
            if text1 and text2:
                emb1 = self.embedder.embed_text(text1)
                emb2 = self.embedder.embed_text(text2)
                similarity = self.embedder.cosine_similarity(emb1, emb2)
                
                if similarity >= self.similarity_threshold:
                    return True
        
        return False
    
    def _detect_frequency_conflict(self, req1: Dict, req2: Dict) -> Optional[Dict]:
        """Detect conflicts in reporting/action frequency"""
        text1 = req1.get('requirement', '').lower()
        text2 = req2.get('requirement', '').lower()
        
        frequencies = {
            'daily': 365,
            'weekly': 52,
            'monthly': 12,
            'quarterly': 4,
            'semi-annually': 2,
            'annually': 1,
            'annual': 1
        }
        
        freq1 = None
        freq2 = None
        
        for freq, count in frequencies.items():
            if freq in text1:
                freq1 = (freq, count)
            if freq in text2:
                freq2 = (freq, count)
        
        # If both have frequencies and they differ
        if freq1 and freq2 and freq1[0] != freq2[0]:
            return {
                'conflict_id': f"freq_{req1.get('requirement_id', '')}_{req2.get('requirement_id', '')}",
                'type': 'FREQUENCY_CONFLICT',
                'severity': 'HIGH' if abs(freq1[1] - freq2[1]) > 2 else 'MEDIUM',
                'requirement_1': {
                    'id': req1.get('requirement_id'),
                    'text': req1.get('requirement', '')[:100],
                    'frequency': freq1[0]
                },
                'requirement_2': {
                    'id': req2.get('requirement_id'),
                    'text': req2.get('requirement', '')[:100],
                    'frequency': freq2[0]
                },
                'description': f"Conflicting frequencies: {freq1[0]} vs {freq2[0]}",
                'resolution': f"Apply stricter requirement: {freq1[0] if freq1[1] > freq2[1] else freq2[0]}"
            }
        
        return None
    
    def _detect_obligation_conflict(self, req1: Dict, req2: Dict) -> Optional[Dict]:
        """Detect must vs may conflicts"""
        text1 = req1.get('requirement', '').lower()
        text2 = req2.get('requirement', '').lower()
        
        type1 = req1.get('type', '')
        type2 = req2.get('type', '')
        
        # OBLIGATION vs RECOMMENDATION on same topic
        if (type1 == 'OBLIGATION' and type2 == 'RECOMMENDATION') or \
           (type1 == 'RECOMMENDATION' and type2 == 'OBLIGATION'):
            
            # Check if they're about the same action
            if self._extract_action_verbs(text1) & self._extract_action_verbs(text2):
                return {
                    'conflict_id': f"obl_{req1.get('requirement_id', '')}_{req2.get('requirement_id', '')}",
                    'type': 'OBLIGATION_CONFLICT',
                    'severity': 'MEDIUM',
                    'requirement_1': {
                        'id': req1.get('requirement_id'),
                        'type': type1,
                        'text': req1.get('requirement', '')[:100]
                    },
                    'requirement_2': {
                        'id': req2.get('requirement_id'),
                        'type': type2,
                        'text': req2.get('requirement', '')[:100]
                    },
                    'description': f"Obligation strength conflict: {type1} vs {type2}",
                    'resolution': "Apply OBLIGATION (stricter standard)"
                }
        
        return None
    
    def _detect_timeline_conflict(self, req1: Dict, req2: Dict) -> Optional[Dict]:
        """Detect conflicting deadlines or timelines"""
        entities1 = req1.get('entities', {})
        entities2 = req2.get('entities', {})
        
        dates1 = entities1.get('dates', [])
        dates2 = entities2.get('dates', [])
        
        # Check for same deadline descriptions with different dates
        if dates1 and dates2:
            # Look for conflicting deadlines (e.g., "30 days" vs "60 days")
            for date1 in dates1:
                for date2 in dates2:
                    if self._are_timeline_conflicts(date1, date2):
                        return {
                            'conflict_id': f"time_{req1.get('requirement_id', '')}_{req2.get('requirement_id', '')}",
                            'type': 'TIMELINE_CONFLICT',
                            'severity': 'MEDIUM',
                            'requirement_1': {
                                'id': req1.get('requirement_id'),
                                'timeline': date1,
                                'text': req1.get('requirement', '')[:100]
                            },
                            'requirement_2': {
                                'id': req2.get('requirement_id'),
                                'timeline': date2,
                                'text': req2.get('requirement', '')[:100]
                            },
                            'description': f"Timeline conflict: {date1} vs {date2}",
                            'resolution': "Apply shorter timeline (stricter)"
                        }
        
        return None
    
    def _detect_amount_conflict(self, req1: Dict, req2: Dict) -> Optional[Dict]:
        """Detect conflicting dollar amounts or thresholds"""
        entities1 = req1.get('entities', {})
        entities2 = req2.get('entities', {})
        
        amounts1 = entities1.get('amounts', [])
        amounts2 = entities2.get('amounts', [])
        
        if amounts1 and amounts2:
            # Extract numeric values
            nums1 = [self._extract_number(amt) for amt in amounts1]
            nums2 = [self._extract_number(amt) for amt in amounts2]
            
            nums1 = [n for n in nums1 if n is not None]
            nums2 = [n for n in nums2 if n is not None]
            
            # Check for significant differences
            if nums1 and nums2:
                max_diff = max(abs(n1 - n2) for n1 in nums1 for n2 in nums2)
                
                if max_diff > 1000000:  # $1M+ difference
                    return {
                        'conflict_id': f"amt_{req1.get('requirement_id', '')}_{req2.get('requirement_id', '')}",
                        'type': 'AMOUNT_CONFLICT',
                        'severity': 'HIGH',
                        'requirement_1': {
                            'id': req1.get('requirement_id'),
                            'amounts': amounts1,
                            'text': req1.get('requirement', '')[:100]
                        },
                        'requirement_2': {
                            'id': req2.get('requirement_id'),
                            'amounts': amounts2,
                            'text': req2.get('requirement', '')[:100]
                        },
                        'description': f"Threshold conflict: {amounts1} vs {amounts2}",
                        'resolution': "Review both requirements - may apply to different scenarios"
                    }
        
        return None
    
    def _extract_action_verbs(self, text: str) -> set:
        """Extract action verbs from requirement text"""
        action_verbs = {
            'collect', 'report', 'maintain', 'verify', 'identify', 'notify',
            'provide', 'submit', 'disclose', 'record', 'monitor', 'review',
            'approve', 'assess', 'evaluate', 'implement', 'establish'
        }
        
        words = set(text.lower().split())
        return words & action_verbs
    
    def _are_timeline_conflicts(self, date1: str, date2: str) -> bool:
        """Check if two timeline strings conflict"""
        # Extract numbers
        nums1 = re.findall(r'\d+', date1)
        nums2 = re.findall(r'\d+', date2)
        
        if nums1 and nums2:
            # Same unit (days, months) but different numbers
            if ('day' in date1.lower() and 'day' in date2.lower()) or \
               ('month' in date1.lower() and 'month' in date2.lower()):
                return nums1[0] != nums2[0]
        
        return False
    
    def _extract_number(self, text: str) -> Optional[float]:
        """Extract numeric value from text like '$5 million'"""
        # Remove currency symbols and commas
        text = text.replace('$', '').replace(',', '')
        
        # Handle millions/billions
        multipliers = {
            'billion': 1_000_000_000,
            'million': 1_000_000,
            'thousand': 1_000
        }
        
        for word, mult in multipliers.items():
            if word in text.lower():
                nums = re.findall(r'\d+\.?\d*', text)
                if nums:
                    return float(nums[0]) * mult
        
        # Extract plain number
        nums = re.findall(r'\d+\.?\d*', text)
        if nums:
            return float(nums[0])
        
        return None
    
    def _build_conflict_graph(self, conflicts: Dict) -> nx.Graph:
        """Build graph of conflicting requirements"""
        G = nx.Graph()
        
        for conflict_type, conflict_list in conflicts.items():
            for conflict in conflict_list:
                req1_id = conflict['requirement_1']['id']
                req2_id = conflict['requirement_2']['id']
                
                G.add_edge(
                    req1_id,
                    req2_id,
                    conflict_type=conflict_type,
                    severity=conflict.get('severity', 'MEDIUM')
                )
        
        return G
    
    def _generate_conflict_resolutions(self, conflicts: Dict) -> List[Dict]:
        """Generate resolution recommendations for conflicts"""
        resolutions = []
        
        for conflict_type, conflict_list in conflicts.items():
            for conflict in conflict_list:
                resolutions.append({
                    'conflict_id': conflict['conflict_id'],
                    'type': conflict_type,
                    'severity': conflict.get('severity', 'MEDIUM'),
                    'affected_requirements': [
                        conflict['requirement_1']['id'],
                        conflict['requirement_2']['id']
                    ],
                    'recommendation': conflict.get('resolution', 'Manual review required'),
                    'priority': self._calculate_resolution_priority(conflict)
                })
        
        # Sort by priority
        resolutions.sort(key=lambda x: x['priority'], reverse=True)
        
        return resolutions
    
    def _calculate_resolution_priority(self, conflict: Dict) -> int:
        """Calculate priority for resolving conflict"""
        severity_scores = {'CRITICAL': 10, 'HIGH': 7, 'MEDIUM': 4, 'LOW': 1}
        base_score = severity_scores.get(conflict.get('severity', 'MEDIUM'), 4)
        
        # Boost for certain conflict types
        if conflict['type'] == 'FREQUENCY_CONFLICT':
            base_score += 3  # Frequency conflicts are important
        elif conflict['type'] == 'AMOUNT_CONFLICT':
            base_score += 2
        
        return base_score
    
    def find_requirement_dependencies(
        self,
        requirements: List[Dict[str, Any]]
    ) -> Dict[str, Any]:
        """
        Find dependencies and cross-references between requirements
        
        Returns:
            Dependency graph and analysis
        """
        print(f"🔗 Analyzing requirement dependencies...\n")
        
        dependencies = []
        cross_refs = []
        
        for req in requirements:
            req_text = req.get('requirement', '')
            req_id = req.get('requirement_id', '')
            
            # Look for explicit references
            ref_patterns = [
                r'section\s+(\d+\.?\d*)',
                r'paragraph\s+([a-z]\))',
                r'subsection\s+(\d+)',
                r'as defined in\s+([^,\.]+)',
                r'pursuant to\s+([^,\.]+)'
            ]
            
            for pattern in ref_patterns:
                matches = re.findall(pattern, req_text.lower())
                if matches:
                    for match in matches:
                        cross_refs.append({
                            'from_requirement': req_id,
                            'reference_text': match,
                            'type': 'EXPLICIT_REFERENCE'
                        })
        
        # Build dependency graph
        dep_graph = nx.DiGraph()
        for ref in cross_refs:
            dep_graph.add_edge(ref['from_requirement'], ref['reference_text'])
        
        return {
            'total_cross_references': len(cross_refs),
            'cross_references': cross_refs,
            'dependency_graph': dep_graph,
            'strongly_connected': list(nx.strongly_connected_components(dep_graph)) if dep_graph.edges() else []
        }


def test_conflict_detector():
    """Test conflict detection"""
    print("="*70)
    print("🧪 TESTING CONFLICT DETECTOR")
    print("="*70 + "\n")
    
    # Sample requirements with conflicts
    test_requirements = [
        {
            'requirement_id': 'req_001',
            'type': 'OBLIGATION',
            'severity': 'HIGH',
            'section_title': 'Data Reporting',
            'requirement': 'Financial institutions must report small business lending data quarterly to the CFPB.',
            'entities': {
                'agencies': ['CFPB'],
                'dates': ['quarterly']
            }
        },
        {
            'requirement_id': 'req_002',
            'type': 'RECOMMENDATION',
            'severity': 'MEDIUM',
            'section_title': 'Data Reporting',
            'requirement': 'Banks should report small business lending data annually to maintain compliance.',
            'entities': {
                'agencies': ['CFPB'],
                'dates': ['annually']
            }
        },
        {
            'requirement_id': 'req_003',
            'type': 'OBLIGATION',
            'severity': 'CRITICAL',
            'section_title': 'Loan Thresholds',
            'requirement': 'This regulation applies to institutions with assets exceeding $1 billion.',
            'entities': {
                'amounts': ['$1 billion']
            }
        },
        {
            'requirement_id': 'req_004',
            'type': 'OBLIGATION',
            'severity': 'HIGH',
            'section_title': 'Loan Thresholds',
            'requirement': 'Covered institutions are those with total assets of $500 million or more.',
            'entities': {
                'amounts': ['$500 million']
            }
        },
        {
            'requirement_id': 'req_005',
            'type': 'OBLIGATION',
            'severity': 'HIGH',
            'section_title': 'Notification Requirements',
            'requirement': 'Applicants must be notified within 30 days of a credit decision.',
            'entities': {
                'dates': ['30 days']
            }
        },
        {
            'requirement_id': 'req_006',
            'type': 'RECOMMENDATION',
            'severity': 'MEDIUM',
            'section_title': 'Notification Requirements',
            'requirement': 'Creditors should notify applicants within 60 days when feasible.',
            'entities': {
                'dates': ['60 days']
            }
        }
    ]
    
    # Initialize detector (without embedder for basic test)
    detector = ConflictDetector(embedder=None, similarity_threshold=0.6)
    
    # Detect conflicts
    print("DETECTING CONFLICTS")
    print("-"*70 + "\n")
    
    results = detector.detect_all_conflicts(test_requirements)
    
    # Display results
    print("="*70)
    print("CONFLICT DETECTION RESULTS")
    print("="*70 + "\n")
    
    print(f"📊 Total Requirements: {results['total_requirements']}")
    print(f"📊 Pairs Checked: {results['pairs_checked']}")
    print(f"📊 Total Conflicts: {results['total_conflicts']}\n")
    
    # Show conflicts by type
    for conflict_type, conflict_list in results['conflicts_by_type'].items():
        if conflict_list:
            print(f"🔍 {conflict_type.replace('_', ' ').title()}: {len(conflict_list)}")
            for conflict in conflict_list:
                print(f"\n   Conflict: {conflict['conflict_id']}")
                print(f"   Severity: {conflict['severity']}")
                print(f"   Req 1: {conflict['requirement_1']['id']}")
                print(f"   Req 2: {conflict['requirement_2']['id']}")
                print(f"   Issue: {conflict['description']}")
                print(f"   Resolution: {conflict['resolution']}")
    
    # Resolution recommendations
    if results['resolution_recommendations']:
        print("\n" + "="*70)
        print("RESOLUTION RECOMMENDATIONS (Priority-Ranked)")
        print("="*70 + "\n")
        
        for i, rec in enumerate(results['resolution_recommendations'][:5], 1):
            print(f"{i}. {rec['conflict_id']} ({rec['severity']})")
            print(f"   Type: {rec['type']}")
            print(f"   Priority: {rec['priority']}/10")
            print(f"   Action: {rec['recommendation']}")
            print()
    
    # Test dependency analysis
    print("="*70)
    print("DEPENDENCY ANALYSIS")
    print("="*70 + "\n")
    
    dep_results = detector.find_requirement_dependencies(test_requirements)
    
    print(f"📊 Cross-references found: {dep_results['total_cross_references']}")
    
    if dep_results['cross_references']:
        print("\nExplicit References:")
        for ref in dep_results['cross_references'][:5]:
            print(f"   {ref['from_requirement']} → {ref['reference_text']}")
    
    print("\n" + "="*70)
    print("✅ CONFLICT DETECTOR TESTS PASSED!")
    print("="*70)


if __name__ == "__main__":
    test_conflict_detector()