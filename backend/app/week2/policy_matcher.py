"""
Policy Matcher - Week 2, Day 10
Matches regulatory requirements to bank policy sections
"""

from typing import Dict, Any, List, Tuple
from .rag_query import QueryEngine
from .rag_embedder import EmbeddingGenerator
from .rag_store import VectorStore


class PolicyMatcher:
    """Match regulatory requirements to bank policies"""
    
    def __init__(
        self,
        query_engine: QueryEngine,
        coverage_threshold: float = 0.5,
        partial_threshold: float = 0.3
    ):
        """
        Initialize policy matcher
        
        Args:
            query_engine: QueryEngine instance with both collections
            coverage_threshold: Minimum score for COVERED status
            partial_threshold: Minimum score for PARTIAL status
        """
        self.query_engine = query_engine
        self.coverage_threshold = coverage_threshold
        self.partial_threshold = partial_threshold
    
    def match_requirement_to_policies(
        self,
        requirement: Dict[str, Any],
        n_results: int = 5
    ) -> Dict[str, Any]:
        """
        Find policy sections that address a requirement
        
        Args:
            requirement: Requirement dict with 'requirement' text
            n_results: Number of policy matches to return
            
        Returns:
            Match result with coverage status and policy matches
        """
        # Build search query from requirement
        query_text = self._build_query_from_requirement(requirement)
        
        # Search policies collection
        policy_results = self.query_engine.advanced_search(
            query=query_text,
            collection="policies",
            expand_query=True,
            n_results=n_results,
            min_similarity=0.2  # Cast wide net
        )
        
        # Score matches
        matches = []
        for result in policy_results:
            match_score = self._calculate_match_score(
                requirement,
                result
            )
            
            matches.append({
                'policy_section': result['metadata'].get('section_title', 'Unknown'),
                'policy_text': result['document'],
                'similarity': result['similarity'],
                'match_score': match_score,
                'match_percent': f"{match_score * 100:.1f}%",
                'metadata': result['metadata']
            })
        
        # Sort by match score
        matches.sort(key=lambda x: x['match_score'], reverse=True)
        
        # Determine coverage status
        best_score = matches[0]['match_score'] if matches else 0.0
        
        if best_score >= self.coverage_threshold:
            status = "COVERED"
            confidence = "HIGH" if best_score >= 0.7 else "MEDIUM"
        elif best_score >= self.partial_threshold:
            status = "PARTIAL"
            confidence = "MEDIUM" if best_score >= 0.4 else "LOW"
        else:
            status = "MISSING"
            confidence = "N/A"
        
        return {
            'requirement_id': requirement.get('requirement_id', 'unknown'),
            'requirement_text': requirement.get('requirement', ''),
            'requirement_type': requirement.get('type', 'UNKNOWN'),
            'severity': requirement.get('severity', 'UNKNOWN'),
            'coverage_status': status,
            'confidence': confidence,
            'best_match_score': best_score,
            'match_percent': f"{best_score * 100:.1f}%",  # Add formatted percentage
            'policy_matches': matches[:3],  # Top 3 matches
            'all_matches': matches
        }
    
    def _build_query_from_requirement(self, requirement: Dict[str, Any]) -> str:
        """
        Build search query from requirement
        
        Args:
            requirement: Requirement dict
            
        Returns:
            Query string
        """
        parts = []
        
        # Main requirement text
        if requirement.get('requirement'):
            parts.append(requirement['requirement'])
        
        # Plain language explanation
        if requirement.get('plain_language'):
            parts.append(requirement['plain_language'])
        
        # Section title
        if requirement.get('section_title'):
            parts.append(requirement['section_title'])
        
        return ' '.join(parts)
    
    def _calculate_match_score(
        self,
        requirement: Dict[str, Any],
        policy_result: Dict[str, Any]
    ) -> float:
        """
        Calculate comprehensive match score
        
        Args:
            requirement: Requirement dict
            policy_result: Policy search result
            
        Returns:
            Match score (0-1)
        """
        # Base score: semantic similarity
        semantic_score = policy_result['similarity']
        
        # Keyword overlap bonus
        keyword_score = self._keyword_overlap(
            requirement.get('requirement', ''),
            policy_result['document']
        )
        
        # Entity match bonus
        entity_score = self._entity_match(
            requirement.get('entities', {}),
            policy_result['document']
        )
        
        # Weighted combination
        final_score = (
            0.6 * semantic_score +
            0.25 * keyword_score +
            0.15 * entity_score
        )
        
        return min(final_score, 1.0)  # Cap at 1.0
    
    def _keyword_overlap(self, req_text: str, policy_text: str) -> float:
        """Calculate keyword overlap between requirement and policy"""
        # Extract important keywords (nouns, verbs)
        req_words = set(req_text.lower().split())
        policy_words = set(policy_text.lower().split())
        
        # Remove common words
        stop_words = {'the', 'a', 'an', 'and', 'or', 'but', 'is', 'are', 'was', 'were', 
                      'be', 'been', 'being', 'have', 'has', 'had', 'do', 'does', 'did',
                      'will', 'would', 'should', 'could', 'may', 'might', 'must', 'can',
                      'to', 'of', 'in', 'for', 'on', 'with', 'at', 'by', 'from', 'as'}
        
        req_words = {w for w in req_words if w not in stop_words and len(w) > 3}
        policy_words = {w for w in policy_words if w not in stop_words and len(w) > 3}
        
        if not req_words:
            return 0.0
        
        overlap = len(req_words & policy_words)
        return overlap / len(req_words)
    
    def _entity_match(self, req_entities: Dict, policy_text: str) -> float:
        """Check if requirement entities appear in policy"""
        if not req_entities:
            return 0.0
        
        policy_lower = policy_text.lower()
        matches = 0
        total = 0
        
        # Check dates
        if req_entities.get('dates'):
            total += len(req_entities['dates'])
            for date in req_entities['dates']:
                if date.lower() in policy_lower:
                    matches += 1
        
        # Check amounts
        if req_entities.get('amounts'):
            total += len(req_entities['amounts'])
            for amount in req_entities['amounts']:
                # Extract just the number
                import re
                numbers = re.findall(r'\d+', amount)
                if numbers and any(num in policy_lower for num in numbers):
                    matches += 1
        
        # Check agencies
        if req_entities.get('agencies'):
            total += len(req_entities['agencies'])
            for agency in req_entities['agencies']:
                if agency.lower() in policy_lower:
                    matches += 1
        
        if total == 0:
            return 0.0
        
        return matches / total
    
    def batch_match_requirements(
        self,
        requirements: List[Dict[str, Any]],
        show_progress: bool = True
    ) -> List[Dict[str, Any]]:
        """
        Match multiple requirements to policies
        
        Args:
            requirements: List of requirement dicts
            show_progress: Show progress during matching
            
        Returns:
            List of match results
        """
        results = []
        
        for i, req in enumerate(requirements, 1):
            if show_progress:
                print(f"🔍 Matching requirement {i}/{len(requirements)}: {req.get('requirement_id', 'unknown')}")
            
            match_result = self.match_requirement_to_policies(req)
            results.append(match_result)
        
        return results
    
    def generate_gap_report(
        self,
        match_results: List[Dict[str, Any]]
    ) -> Dict[str, Any]:
        """
        Generate compliance gap report from match results
        
        Args:
            match_results: List of requirement match results
            
        Returns:
            Gap report summary
        """
        total = len(match_results)
        
        covered = sum(1 for r in match_results if r['coverage_status'] == 'COVERED')
        partial = sum(1 for r in match_results if r['coverage_status'] == 'PARTIAL')
        missing = sum(1 for r in match_results if r['coverage_status'] == 'MISSING')
        
        coverage_pct = (covered / total * 100) if total > 0 else 0
        
        # Group by severity
        by_severity = {}
        for result in match_results:
            severity = result['severity']
            if severity not in by_severity:
                by_severity[severity] = {'covered': 0, 'partial': 0, 'missing': 0}
            
            status = result['coverage_status'].lower()
            by_severity[severity][status] += 1
        
        # Identify gaps
        gaps = [r for r in match_results if r['coverage_status'] in ['MISSING', 'PARTIAL']]
        critical_gaps = [g for g in gaps if g['severity'] in ['CRITICAL', 'HIGH']]
        
        return {
            'total_requirements': total,
            'covered': covered,
            'partial': partial,
            'missing': missing,
            'coverage_percentage': coverage_pct,
            'by_severity': by_severity,
            'gaps': gaps,
            'critical_gaps': critical_gaps,
            'critical_gap_count': len(critical_gaps),
            'recommendation': self._generate_recommendation(coverage_pct, critical_gaps)
        }
    
    def _generate_recommendation(
        self,
        coverage_pct: float,
        critical_gaps: List[Dict]
    ) -> str:
        """Generate recommendation based on gap analysis"""
        if coverage_pct >= 90 and len(critical_gaps) == 0:
            return "EXCELLENT: Policy coverage is comprehensive. Minor updates may be needed."
        elif coverage_pct >= 75 and len(critical_gaps) == 0:
            return "GOOD: Policy coverage is adequate. Review partial matches for improvement."
        elif coverage_pct >= 60:
            return "FAIR: Policy coverage has gaps. Address partial matches and missing items."
        elif len(critical_gaps) > 0:
            return f"URGENT: {len(critical_gaps)} critical gaps identified. Immediate policy updates required."
        else:
            return "POOR: Significant policy gaps. Comprehensive policy review recommended."


def test_policy_matcher():
    """Test policy matcher with sample data"""
    print("="*70)
    print("🧪 TESTING POLICY MATCHER")
    print("="*70 + "\n")
    
    from .rag_chunker import DocumentChunker
    from .rag_embedder import EmbeddingGenerator
    from .rag_store import VectorStore
    from .rag_query import QueryEngine
    
    # Initialize components
    chunker = DocumentChunker()
    embedder = EmbeddingGenerator()
    store = VectorStore(persist_directory="./test_matcher_db")
    query_engine = QueryEngine(store, embedder)
    
    # Sample requirement
    requirement = {
        'requirement_id': 'req_001',
        'type': 'OBLIGATION',
        'severity': 'HIGH',
        'requirement': 'Banks must collect and report small business lending data quarterly.',
        'plain_language': 'Track and report business loan data every quarter.',
        'entities': {
            'dates': ['quarterly'],
            'agencies': ['CFPB']
        }
    }
    
    # Sample policy
    policy_text = """
    Section 3: Data Collection
    
    The bank collects comprehensive data on all small business loan applications.
    This includes applicant information, loan terms, and decision outcomes.
    
    Data is reported to the CFPB on a quarterly basis as required by regulation.
    """
    
    # Create policy chunks
    policy_chunks = chunker.chunk_policy(
        policy_text,
        "lending_policy.pdf",
        metadata={'policy_area': 'lending'}
    )
    
    # Embed and store
    embedded_chunks = embedder.embed_chunks(policy_chunks)
    store.create_policies_collection(reset=True)
    store.add_chunks(embedded_chunks, collection_type="policies")
    
    print("✅ Test data prepared\n")
    
    # Initialize matcher
    matcher = PolicyMatcher(query_engine)
    
    # Match requirement to policy
    print("🔍 Matching requirement to policy...\n")
    result = matcher.match_requirement_to_policies(requirement)
    
    print(f"Requirement: {result['requirement_text'][:80]}...")
    print(f"\nCoverage Status: {result['coverage_status']}")
    print(f"Confidence: {result['confidence']}")
    print(f"Best Match Score: {result['match_percent']}")
    
    if result['policy_matches']:
        print(f"\nTop Policy Match:")
        match = result['policy_matches'][0]
        print(f"   Section: {match['policy_section']}")
        print(f"   Score: {match['match_percent']}")
        print(f"   Text: {match['policy_text'][:100]}...")
    
    print("\n" + "="*70)
    print("✅ POLICY MATCHER TEST PASSED!")
    print("="*70)


if __name__ == "__main__":
    test_policy_matcher()