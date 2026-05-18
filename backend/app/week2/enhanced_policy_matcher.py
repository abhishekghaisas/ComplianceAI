"""
Enhanced Policy Matcher - Week 2, Days 11-12
Improved scoring, context awareness, and gap analysis
"""

from typing import Dict, Any, List, Tuple, Optional
from datetime import datetime
import re
from .rag_query import QueryEngine


class EnhancedPolicyMatcher:
    """Enhanced matcher with improved scoring and analysis"""
    
    def __init__(
        self,
        query_engine: QueryEngine,
        coverage_threshold: float = 0.45,  # Lowered from 0.5
        partial_threshold: float = 0.25,   # Lowered from 0.3
        use_adaptive_thresholds: bool = True
    ):
        """
        Initialize enhanced matcher
        
        Args:
            query_engine: QueryEngine instance
            coverage_threshold: Base threshold for COVERED
            partial_threshold: Base threshold for PARTIAL
            use_adaptive_thresholds: Adjust thresholds by severity
        """
        self.query_engine = query_engine
        self.base_coverage_threshold = coverage_threshold
        self.base_partial_threshold = partial_threshold
        self.use_adaptive_thresholds = use_adaptive_thresholds
    
    def get_thresholds(self, severity: str) -> Tuple[float, float]:
        """
        Get adaptive thresholds based on severity
        
        Args:
            severity: Requirement severity
            
        Returns:
            (coverage_threshold, partial_threshold)
        """
        if not self.use_adaptive_thresholds:
            return (self.base_coverage_threshold, self.base_partial_threshold)
        
        # Higher standards for critical/high severity
        if severity in ['CRITICAL']:
            return (0.55, 0.35)  # Stricter
        elif severity in ['HIGH']:
            return (0.48, 0.28)  # Moderate
        else:  # MEDIUM, LOW
            return (0.42, 0.22)  # Lenient
    
    def match_requirement_to_policies(
        self,
        requirement: Dict[str, Any],
        n_results: int = 5,
        use_hybrid: bool = True
    ) -> Dict[str, Any]:
        """
        Enhanced requirement matching with hybrid search
        
        Args:
            requirement: Requirement dict
            n_results: Number of results
            use_hybrid: Use hybrid search (recommended)
            
        Returns:
            Enhanced match result
        """
        # Build query
        query_text = self._build_enhanced_query(requirement)
        keywords = self._extract_keywords(requirement)
        
        # Search policies with hybrid approach
        if use_hybrid and keywords:
            policy_results = self.query_engine.hybrid_search(
                query=query_text,
                keywords=keywords,
                collection="policies",
                semantic_weight=0.65,  # Balance semantic + keywords
                n_results=n_results
            )
        else:
            policy_results = self.query_engine.advanced_search(
                query=query_text,
                collection="policies",
                expand_query=True,
                n_results=n_results,
                min_similarity=0.15
            )
        
        # Enhanced scoring
        matches = []
        for result in policy_results:
            match_score = self._calculate_enhanced_score(requirement, result)
            
            matches.append({
                'policy_section': result.get('metadata', {}).get('section_title', 'Unknown'),
                'policy_text': result['document'] if isinstance(result, dict) and 'document' in result else result.get('policy_text', ''),
                'similarity': result.get('similarity', result.get('hybrid_score', 0)),
                'match_score': match_score,
                'match_percent': f"{match_score * 100:.1f}%",
                'metadata': result.get('metadata', {}),
                'score_breakdown': self._get_score_breakdown(requirement, result)
            })
        
        # Sort by match score
        matches.sort(key=lambda x: x['match_score'], reverse=True)
        
        # Get adaptive thresholds
        severity = requirement.get('severity', 'MEDIUM')
        coverage_thresh, partial_thresh = self.get_thresholds(severity)
        
        # Determine coverage with adaptive thresholds
        best_score = matches[0]['match_score'] if matches else 0.0
        
        if best_score >= coverage_thresh:
            status = "COVERED"
            confidence = "HIGH" if best_score >= 0.65 else "MEDIUM"
        elif best_score >= partial_thresh:
            status = "PARTIAL"
            confidence = "MEDIUM" if best_score >= 0.35 else "LOW"
        else:
            status = "MISSING"
            confidence = "N/A"
        
        # Generate recommendations
        recommendations = self._generate_recommendations(
            requirement, 
            matches[0] if matches else None,
            status,
            best_score
        )
        
        return {
            'requirement_id': requirement.get('requirement_id', 'unknown'),
            'requirement_text': requirement.get('requirement', ''),
            'requirement_type': requirement.get('type', 'UNKNOWN'),
            'severity': severity,
            'coverage_status': status,
            'confidence': confidence,
            'best_match_score': best_score,
            'match_percent': f"{best_score * 100:.1f}%",
            'thresholds_used': {
                'coverage': coverage_thresh,
                'partial': partial_thresh
            },
            'policy_matches': matches[:3],
            'all_matches': matches,
            'recommendations': recommendations
        }
    
    def _build_enhanced_query(self, requirement: Dict[str, Any]) -> str:
        """Build enhanced query with key terms emphasized"""
        parts = []
        
        # Main requirement (highest weight)
        if requirement.get('requirement'):
            parts.append(requirement['requirement'])
        
        # Plain language (medium weight)
        if requirement.get('plain_language'):
            parts.append(requirement['plain_language'])
        
        # Section context (lower weight)
        if requirement.get('section_title'):
            parts.append(requirement['section_title'])
        
        return ' '.join(parts)
    
    def _extract_keywords(self, requirement: Dict[str, Any]) -> List[str]:
        """Extract important keywords for hybrid search"""
        keywords = []
        
        # Add entities
        entities = requirement.get('entities', {})
        
        if entities.get('agencies'):
            keywords.extend(entities['agencies'])
        
        if entities.get('dates'):
            # Extract time periods (quarterly, monthly, etc.)
            for date in entities['dates']:
                if 'quarter' in date.lower():
                    keywords.append('quarterly')
                if 'month' in date.lower():
                    keywords.append('monthly')
                if 'annual' in date.lower():
                    keywords.append('annually')
        
        if entities.get('amounts'):
            keywords.extend(entities['amounts'])
        
        # Extract key action words
        req_text = requirement.get('requirement', '').lower()
        action_words = ['must', 'shall', 'required', 'prohibited', 'report', 'collect', 'maintain', 'verify']
        keywords.extend([word for word in action_words if word in req_text])
        
        return list(set(keywords))  # Deduplicate
    
    def _calculate_enhanced_score(
        self,
        requirement: Dict[str, Any],
        policy_result: Dict[str, Any]
    ) -> float:
        """
        Enhanced scoring with better component weighting
        
        Components:
        - Semantic similarity: 50%
        - Keyword overlap: 30%
        - Entity match: 15%
        - Context bonus: 5%
        """
        # Base semantic score
        if 'hybrid_score' in policy_result:
            semantic_score = policy_result['hybrid_score']
        else:
            semantic_score = policy_result.get('similarity', 0)
        
        # Keyword overlap
        policy_text = policy_result.get('document', policy_result.get('policy_text', ''))
        keyword_score = self._advanced_keyword_overlap(
            requirement.get('requirement', ''),
            policy_text
        )
        
        # Entity matching
        entity_score = self._enhanced_entity_match(
            requirement.get('entities', {}),
            policy_text
        )
        
        # Context bonus (if requirement type matches policy context)
        context_score = self._context_match(requirement, policy_result)
        
        # Weighted combination
        final_score = (
            0.50 * semantic_score +
            0.30 * keyword_score +
            0.15 * entity_score +
            0.05 * context_score
        )
        
        return min(final_score, 1.0)
    
    def _advanced_keyword_overlap(self, req_text: str, policy_text: str) -> float:
        """Advanced keyword matching with stemming-like behavior"""
        # Extract meaningful words
        req_words = set(self._extract_meaningful_words(req_text))
        policy_words = set(self._extract_meaningful_words(policy_text))
        
        if not req_words:
            return 0.0
        
        # Direct matches
        direct_matches = len(req_words & policy_words)
        
        # Fuzzy matches (partial word matching)
        fuzzy_matches = 0
        for req_word in req_words:
            if req_word not in policy_words:
                # Check if root form exists
                for policy_word in policy_words:
                    if (req_word in policy_word or policy_word in req_word) and len(req_word) > 4:
                        fuzzy_matches += 0.5
                        break
        
        total_matches = direct_matches + fuzzy_matches
        return min(total_matches / len(req_words), 1.0)
    
    def _extract_meaningful_words(self, text: str) -> List[str]:
        """Extract meaningful words (remove stop words)"""
        stop_words = {
            'the', 'a', 'an', 'and', 'or', 'but', 'is', 'are', 'was', 'were',
            'be', 'been', 'being', 'have', 'has', 'had', 'do', 'does', 'did',
            'will', 'would', 'should', 'could', 'may', 'might', 'must', 'can',
            'to', 'of', 'in', 'for', 'on', 'with', 'at', 'by', 'from', 'as',
            'that', 'this', 'these', 'those', 'it', 'its', 'all', 'each', 'any'
        }
        
        words = re.findall(r'\b[a-z]+\b', text.lower())
        return [w for w in words if w not in stop_words and len(w) > 3]
    
    def _enhanced_entity_match(self, req_entities: Dict, policy_text: str) -> float:
        """Enhanced entity matching"""
        if not req_entities:
            return 0.5  # Neutral score if no entities
        
        policy_lower = policy_text.lower()
        matches = 0
        total = 0
        
        # Agency matching (high weight)
        if req_entities.get('agencies'):
            for agency in req_entities['agencies']:
                total += 1
                if agency.lower() in policy_lower:
                    matches += 1
        
        # Date/period matching
        if req_entities.get('dates'):
            for date in req_entities['dates']:
                total += 1
                # Check for date or related terms
                if any(term in policy_lower for term in [date.lower(), 'quarter' if 'quarter' in date.lower() else '', 'annual' if 'annual' in date.lower() else '']):
                    matches += 0.75  # Partial credit for related terms
        
        # Amount matching
        if req_entities.get('amounts'):
            for amount in req_entities['amounts']:
                total += 1
                # Extract numbers
                numbers = re.findall(r'\d+', amount)
                if any(num in policy_lower for num in numbers):
                    matches += 0.5  # Partial credit
        
        return matches / total if total > 0 else 0.5
    
    def _context_match(self, requirement: Dict, policy_result: Dict) -> float:
        """Check if policy context matches requirement type"""
        req_type = requirement.get('type', '').upper()
        policy_text = policy_result.get('document', policy_result.get('policy_text', '')).lower()
        
        type_indicators = {
            'OBLIGATION': ['must', 'shall', 'required', 'will', 'ensure'],
            'PROHIBITION': ['prohibited', 'not', 'never', 'forbidden', 'restrict'],
            'RECOMMENDATION': ['should', 'recommend', 'consider', 'encouraged'],
            'DEFINITION': ['means', 'defined', 'refers to', 'includes']
        }
        
        if req_type in type_indicators:
            indicators = type_indicators[req_type]
            matches = sum(1 for indicator in indicators if indicator in policy_text)
            return min(matches / 3.0, 1.0)  # Cap at 1.0
        
        return 0.5  # Neutral if no type match
    
    def _get_score_breakdown(
        self,
        requirement: Dict,
        policy_result: Dict
    ) -> Dict[str, float]:
        """Get detailed score breakdown for transparency"""
        policy_text = policy_result.get('document', policy_result.get('policy_text', ''))
        
        return {
            'semantic': policy_result.get('similarity', policy_result.get('hybrid_score', 0)),
            'keyword': self._advanced_keyword_overlap(requirement.get('requirement', ''), policy_text),
            'entity': self._enhanced_entity_match(requirement.get('entities', {}), policy_text),
            'context': self._context_match(requirement, policy_result)
        }
    
    def _generate_recommendations(
        self,
        requirement: Dict,
        best_match: Optional[Dict],
        status: str,
        score: float
    ) -> List[str]:
        """Generate actionable recommendations"""
        recommendations = []
        
        if status == "COVERED":
            recommendations.append("✅ Policy adequately addresses this requirement.")
            if score < 0.70:
                recommendations.append("💡 Consider enhancing policy language to more closely match regulatory text.")
        
        elif status == "PARTIAL":
            recommendations.append("⚠️  Policy partially addresses this requirement.")
            
            if score >= 0.40:
                recommendations.append("📝 Minor policy updates needed - language alignment issue.")
                recommendations.append(f"   Add specific reference to: {requirement.get('section_title', 'requirement')}")
            else:
                recommendations.append("📝 Moderate policy updates needed - missing key details.")
                recommendations.append("   Consider adding section covering:")
                recommendations.append(f"   • {requirement.get('requirement', '')[:100]}...")
            
            # Specific suggestions based on entities
            entities = requirement.get('entities', {})
            if entities.get('agencies') and best_match:
                policy_text = best_match.get('policy_text', '').lower()
                missing_agencies = [a for a in entities['agencies'] if a.lower() not in policy_text]
                if missing_agencies:
                    recommendations.append(f"   • Reference to {', '.join(missing_agencies)}")
            
            if entities.get('dates'):
                recommendations.append(f"   • Timeline/deadline: {', '.join(entities['dates'])}")
        
        else:  # MISSING
            recommendations.append("❌ No policy found addressing this requirement.")
            recommendations.append("📝 URGENT: Create new policy section covering:")
            recommendations.append(f"   • {requirement.get('requirement', '')}")
            
            if requirement.get('plain_language'):
                recommendations.append(f"   In plain terms: {requirement.get('plain_language', '')}")
        
        return recommendations
    
    def batch_match_requirements(
        self,
        requirements: List[Dict[str, Any]],
        show_progress: bool = True
    ) -> List[Dict[str, Any]]:
        """Match multiple requirements with progress"""
        results = []
        
        for i, req in enumerate(requirements, 1):
            if show_progress:
                print(f"🔍 Matching {i}/{len(requirements)}: {req.get('requirement_id', 'unknown')} ({req.get('severity', 'UNKNOWN')})")
            
            match_result = self.match_requirement_to_policies(req)
            results.append(match_result)
        
        return results
    
    def generate_enhanced_gap_report(
        self,
        match_results: List[Dict[str, Any]]
    ) -> Dict[str, Any]:
        """
        Generate comprehensive gap report with priorities
        
        Returns enhanced report with:
        - Overall coverage
        - Severity breakdown
        - Priority-ranked gaps
        - Remediation roadmap
        """
        total = len(match_results)
        
        covered = sum(1 for r in match_results if r['coverage_status'] == 'COVERED')
        partial = sum(1 for r in match_results if r['coverage_status'] == 'PARTIAL')
        missing = sum(1 for r in match_results if r['coverage_status'] == 'MISSING')
        
        coverage_pct = (covered / total * 100) if total > 0 else 0
        
        # Weighted coverage (accounts for severity)
        weighted_score = self._calculate_weighted_coverage(match_results)
        
        # By severity
        by_severity = {}
        for result in match_results:
            severity = result['severity']
            if severity not in by_severity:
                by_severity[severity] = {'covered': 0, 'partial': 0, 'missing': 0, 'total': 0}
            
            status = result['coverage_status'].lower()
            by_severity[severity][status] += 1
            by_severity[severity]['total'] += 1
        
        # Identify gaps with priorities
        gaps = [r for r in match_results if r['coverage_status'] in ['MISSING', 'PARTIAL']]
        
        # Priority ranking
        priority_gaps = self._rank_gaps_by_priority(gaps)
        
        # Remediation roadmap
        roadmap = self._create_remediation_roadmap(priority_gaps)
        
        return {
            'generated_at': datetime.now().isoformat(),
            'total_requirements': total,
            'covered': covered,
            'partial': partial,
            'missing': missing,
            'coverage_percentage': coverage_pct,
            'weighted_coverage': weighted_score,
            'by_severity': by_severity,
            'gaps': gaps,
            'priority_gaps': priority_gaps,
            'remediation_roadmap': roadmap,
            'overall_assessment': self._assess_overall_compliance(coverage_pct, weighted_score, priority_gaps),
            'recommendation': self._generate_overall_recommendation(coverage_pct, weighted_score, priority_gaps)
        }
    
    def _calculate_weighted_coverage(self, results: List[Dict]) -> float:
        """Calculate severity-weighted coverage score"""
        severity_weights = {
            'CRITICAL': 3.0,
            'HIGH': 2.0,
            'MEDIUM': 1.0,
            'LOW': 0.5
        }
        
        status_scores = {
            'COVERED': 1.0,
            'PARTIAL': 0.5,
            'MISSING': 0.0
        }
        
        total_weight = 0
        total_score = 0
        
        for result in results:
            weight = severity_weights.get(result['severity'], 1.0)
            score = status_scores.get(result['coverage_status'], 0)
            
            total_weight += weight
            total_score += weight * score
        
        return (total_score / total_weight * 100) if total_weight > 0 else 0
    
    def _rank_gaps_by_priority(self, gaps: List[Dict]) -> List[Dict]:
        """Rank gaps by priority (severity + match score)"""
        severity_rank = {'CRITICAL': 4, 'HIGH': 3, 'MEDIUM': 2, 'LOW': 1, 'UNKNOWN': 1}
        
        for gap in gaps:
            # Priority score: higher severity + lower match = higher priority
            sev_score = severity_rank.get(gap['severity'], 1)
            match_score = gap['best_match_score']
            
            # Priority: high severity and low match score = urgent
            gap['priority_score'] = sev_score * (1 - match_score) * 10
            
            if gap['severity'] in ['CRITICAL', 'HIGH'] and gap['coverage_status'] == 'MISSING':
                gap['priority'] = 'URGENT'
            elif gap['severity'] == 'CRITICAL' or (gap['severity'] == 'HIGH' and match_score < 0.3):
                gap['priority'] = 'HIGH'
            elif gap['severity'] == 'HIGH' or (gap['severity'] == 'MEDIUM' and gap['coverage_status'] == 'MISSING'):
                gap['priority'] = 'MEDIUM'
            else:
                gap['priority'] = 'LOW'
        
        # Sort by priority score
        gaps.sort(key=lambda x: x['priority_score'], reverse=True)
        
        return gaps
    
    def _create_remediation_roadmap(self, priority_gaps: List[Dict]) -> Dict[str, List[Dict]]:
        """Create phased remediation roadmap"""
        roadmap = {
            'phase_1_immediate': [],  # URGENT + HIGH priority
            'phase_2_short_term': [],  # MEDIUM priority
            'phase_3_ongoing': []      # LOW priority
        }
        
        for gap in priority_gaps:
            item = {
                'requirement_id': gap['requirement_id'],
                'requirement': gap['requirement_text'][:100] + '...',
                'severity': gap['severity'],
                'status': gap['coverage_status'],
                'priority': gap['priority'],
                'actions': gap.get('recommendations', [])
            }
            
            if gap['priority'] in ['URGENT', 'HIGH']:
                roadmap['phase_1_immediate'].append(item)
            elif gap['priority'] == 'MEDIUM':
                roadmap['phase_2_short_term'].append(item)
            else:
                roadmap['phase_3_ongoing'].append(item)
        
        return roadmap
    
    def _assess_overall_compliance(
        self,
        coverage_pct: float,
        weighted_coverage: float,
        priority_gaps: List[Dict]
    ) -> str:
        """Assess overall compliance posture"""
        urgent_count = sum(1 for g in priority_gaps if g.get('priority') == 'URGENT')
        high_count = sum(1 for g in priority_gaps if g.get('priority') == 'HIGH')
        
        if weighted_coverage >= 85 and urgent_count == 0:
            return "EXCELLENT"
        elif weighted_coverage >= 70 and urgent_count == 0:
            return "GOOD"
        elif weighted_coverage >= 55 and urgent_count <= 2:
            return "FAIR"
        elif urgent_count > 0 or weighted_coverage < 55:
            return "NEEDS IMPROVEMENT"
        else:
            return "POOR"
    
    def _generate_overall_recommendation(
        self,
        coverage_pct: float,
        weighted_coverage: float,
        priority_gaps: List[Dict]
    ) -> str:
        """Generate overall recommendation"""
        urgent = sum(1 for g in priority_gaps if g.get('priority') == 'URGENT')
        high = sum(1 for g in priority_gaps if g.get('priority') == 'HIGH')
        
        if urgent > 0:
            return f"🚨 URGENT ACTION REQUIRED: {urgent} critical gap(s) identified. Immediate policy updates needed to address high-risk compliance gaps."
        elif weighted_coverage >= 80:
            return f"✅ STRONG COMPLIANCE: {weighted_coverage:.1f}% weighted coverage. Continue monitoring and refining policy language."
        elif weighted_coverage >= 65:
            return f"✓ ADEQUATE COMPLIANCE: {weighted_coverage:.1f}% weighted coverage. Address {high} high-priority gaps in next review cycle."
        elif weighted_coverage >= 50:
            return f"⚠️  MODERATE GAPS: {weighted_coverage:.1f}% weighted coverage. Policy enhancement needed. Focus on {high + urgent} high-priority items."
        else:
            return f"❌ SIGNIFICANT GAPS: {weighted_coverage:.1f}% weighted coverage. Comprehensive policy review and updates required."


if __name__ == "__main__":
    print("Enhanced Policy Matcher - Days 11-12")
    print("Import and use with QueryEngine for advanced gap analysis")