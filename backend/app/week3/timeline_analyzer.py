"""
Timeline Analyzer - Week 3, Days 19-20
Analyzes compliance deadlines and creates timeline visualizations
"""

from typing import List, Dict, Any, Optional
from datetime import datetime, timedelta
from dateutil import parser
from collections import defaultdict
import re


class TimelineAnalyzer:
    """Analyze compliance timelines and deadlines"""
    
    def __init__(self, current_date: Optional[datetime] = None):
        """
        Initialize timeline analyzer
        
        Args:
            current_date: Reference date (defaults to today)
        """
        self.current_date = current_date or datetime.now()
    
    def analyze_deadlines(
        self,
        requirements: List[Dict[str, Any]]
    ) -> Dict[str, Any]:
        """
        Analyze all deadlines in requirements
        
        Args:
            requirements: List of requirement dicts
            
        Returns:
            Timeline analysis with upcoming, overdue, and critical deadlines
        """
        print(f"📅 Analyzing deadlines (Reference date: {self.current_date.strftime('%Y-%m-%d')})\n")
        
        deadlines = []
        
        for req in requirements:
            deadline_info = self._extract_deadline_info(req)
            if deadline_info:
                deadlines.append(deadline_info)
        
        print(f"✅ Found {len(deadlines)} requirements with deadlines\n")
        
        # Categorize deadlines
        upcoming = []
        overdue = []
        far_future = []
        
        for deadline in deadlines:
            if deadline['parsed_date']:
                days_until = (deadline['parsed_date'] - self.current_date).days
                deadline['days_until'] = days_until
                
                if days_until < 0:
                    overdue.append(deadline)
                elif days_until <= 90:  # Next 90 days
                    upcoming.append(deadline)
                else:
                    far_future.append(deadline)
            else:
                far_future.append(deadline)  # Can't parse date
        
        # Sort by date
        upcoming.sort(key=lambda x: x.get('days_until', 9999))
        overdue.sort(key=lambda x: x.get('days_until', -9999))
        
        # Build calendar
        calendar = self._build_calendar(upcoming)
        
        # Identify critical path
        critical_path = self._identify_critical_path(upcoming)
        
        return {
            'total_deadlines': len(deadlines),
            'upcoming_count': len(upcoming),
            'overdue_count': len(overdue),
            'far_future_count': len(far_future),
            'upcoming': upcoming,
            'overdue': overdue,
            'far_future': far_future,
            'calendar': calendar,
            'critical_path': critical_path,
            'analysis_date': self.current_date.isoformat()
        }
    
    def _extract_deadline_info(self, requirement: Dict) -> Optional[Dict]:
        """Extract deadline information from requirement"""
        deadline_text = requirement.get('deadline', '')
        
        if not deadline_text or deadline_text.lower() in ['none', 'n/a', 'not specified']:
            return None
        
        # Try to parse date
        parsed_date = self._parse_deadline(deadline_text)
        
        return {
            'requirement_id': requirement.get('requirement_id'),
            'requirement_text': requirement.get('requirement', '')[:100],
            'section_title': requirement.get('section_title', 'Unknown'),
            'severity': requirement.get('severity', 'MEDIUM'),
            'type': requirement.get('type', 'UNKNOWN'),
            'deadline_text': deadline_text,
            'parsed_date': parsed_date,
            'entities': requirement.get('entities', {})
        }
    
    def _parse_deadline(self, deadline_text: str) -> Optional[datetime]:
        """Parse deadline text to datetime"""
        # Common patterns
        date_patterns = [
            r'(\d{4}-\d{2}-\d{2})',  # ISO format
            r'(\w+ \d{1,2},? \d{4})',  # "January 1, 2028"
            r'(\d{1,2}/\d{1,2}/\d{4})',  # "01/01/2028"
        ]
        
        for pattern in date_patterns:
            match = re.search(pattern, deadline_text)
            if match:
                try:
                    return parser.parse(match.group(1))
                except:
                    continue
        
        # Relative dates
        relative_patterns = {
            r'(\d+)\s*days?': lambda n: self.current_date + timedelta(days=int(n)),
            r'(\d+)\s*months?': lambda n: self.current_date + timedelta(days=int(n)*30),
            r'(\d+)\s*years?': lambda n: self.current_date + timedelta(days=int(n)*365),
        }
        
        for pattern, converter in relative_patterns.items():
            match = re.search(pattern, deadline_text.lower())
            if match:
                try:
                    return converter(match.group(1))
                except:
                    continue
        
        return None
    
    def _build_calendar(self, upcoming: List[Dict]) -> Dict[str, List[Dict]]:
        """Build compliance calendar by quarter"""
        calendar = defaultdict(list)
        
        for deadline in upcoming:
            if deadline.get('parsed_date'):
                quarter = f"Q{(deadline['parsed_date'].month - 1) // 3 + 1} {deadline['parsed_date'].year}"
                calendar[quarter].append(deadline)
        
        return dict(calendar)
    
    def _identify_critical_path(self, upcoming: List[Dict]) -> List[Dict]:
        """Identify critical path - highest priority deadlines in order"""
        # Filter for CRITICAL and HIGH severity
        critical = [d for d in upcoming if d.get('severity') in ['CRITICAL', 'HIGH']]
        
        # Sort by date
        critical.sort(key=lambda x: x.get('days_until', 9999))
        
        # Build critical path with dependencies
        critical_path = []
        
        for i, deadline in enumerate(critical, 1):
            critical_path.append({
                'step': i,
                'requirement_id': deadline['requirement_id'],
                'description': deadline['requirement_text'][:80],
                'deadline_date': deadline['parsed_date'].strftime('%Y-%m-%d') if deadline.get('parsed_date') else 'TBD',
                'days_until': deadline.get('days_until'),
                'severity': deadline['severity'],
                'estimated_effort': self._estimate_effort(deadline)
            })
        
        return critical_path
    
    def _estimate_effort(self, deadline: Dict) -> str:
        """Estimate effort required for compliance"""
        severity = deadline.get('severity', 'MEDIUM')
        req_type = deadline.get('type', 'UNKNOWN')
        
        effort_hours = {
            ('CRITICAL', 'OBLIGATION'): 40,
            ('HIGH', 'OBLIGATION'): 20,
            ('MEDIUM', 'OBLIGATION'): 10,
            ('CRITICAL', 'PROHIBITION'): 30,
            ('HIGH', 'PROHIBITION'): 15,
        }
        
        hours = effort_hours.get((severity, req_type), 8)
        
        if hours >= 40:
            return f"{hours} hours (5+ days)"
        elif hours >= 20:
            return f"{hours} hours (2-3 days)"
        else:
            return f"{hours} hours (1 day)"
    
    def generate_timeline_report(
        self,
        timeline_analysis: Dict[str, Any]
    ) -> str:
        """Generate formatted timeline report"""
        report = []
        
        report.append("="*70)
        report.append("📅 COMPLIANCE TIMELINE ANALYSIS")
        report.append("="*70)
        report.append("")
        
        report.append(f"Analysis Date: {datetime.fromisoformat(timeline_analysis['analysis_date']).strftime('%B %d, %Y')}")
        report.append("")
        
        report.append("📊 DEADLINE SUMMARY")
        report.append("-"*70)
        report.append(f"Total Deadlines: {timeline_analysis['total_deadlines']}")
        report.append(f"Upcoming (next 90 days): {timeline_analysis['upcoming_count']}")
        report.append(f"Overdue: {timeline_analysis['overdue_count']}")
        report.append(f"Future (>90 days): {timeline_analysis['far_future_count']}")
        report.append("")
        
        # Overdue deadlines
        if timeline_analysis['overdue']:
            report.append("="*70)
            report.append("🚨 OVERDUE DEADLINES")
            report.append("-"*70)
            report.append("")
            
            for deadline in timeline_analysis['overdue'][:5]:
                report.append(f"• {deadline['requirement_id']} ({deadline['severity']})")
                report.append(f"  Deadline: {deadline['deadline_text']}")
                report.append(f"  Days overdue: {abs(deadline['days_until'])}")
                report.append(f"  {deadline['requirement_text'][:80]}...")
                report.append("")
        
        # Upcoming deadlines
        if timeline_analysis['upcoming']:
            report.append("="*70)
            report.append("📅 UPCOMING DEADLINES (Next 90 Days)")
            report.append("-"*70)
            report.append("")
            
            for deadline in timeline_analysis['upcoming'][:10]:
                report.append(f"• {deadline['requirement_id']} ({deadline['severity']})")
                report.append(f"  Deadline: {deadline['deadline_text']}")
                report.append(f"  Days until: {deadline['days_until']}")
                report.append(f"  {deadline['requirement_text'][:80]}...")
                report.append("")
        
        # Calendar view
        if timeline_analysis['calendar']:
            report.append("="*70)
            report.append("📆 COMPLIANCE CALENDAR")
            report.append("-"*70)
            report.append("")
            
            for quarter, deadlines in sorted(timeline_analysis['calendar'].items()):
                report.append(f"{quarter}: {len(deadlines)} deadline(s)")
                
                critical_count = sum(1 for d in deadlines if d['severity'] in ['CRITICAL', 'HIGH'])
                if critical_count > 0:
                    report.append(f"   ⚠️  {critical_count} CRITICAL/HIGH priority")
                
                report.append("")
        
        # Critical path
        if timeline_analysis['critical_path']:
            report.append("="*70)
            report.append("🎯 CRITICAL PATH (High Priority Deadlines)")
            report.append("-"*70)
            report.append("")
            
            for step in timeline_analysis['critical_path']:
                report.append(f"Step {step['step']}: {step['requirement_id']}")
                report.append(f"   Deadline: {step['deadline_date']}")
                report.append(f"   Days until: {step['days_until']}")
                report.append(f"   Effort: {step['estimated_effort']}")
                report.append(f"   {step['description'][:70]}...")
                report.append("")
        
        report.append("="*70)
        
        return "\n".join(report)


def test_timeline_analyzer():
    """Test timeline analysis"""
    print("="*70)
    print("🧪 TESTING TIMELINE ANALYZER")
    print("="*70 + "\n")
    
    # Test requirements with various deadline formats
    test_requirements = [
        {
            'requirement_id': 'req_001',
            'type': 'OBLIGATION',
            'severity': 'CRITICAL',
            'section_title': 'Data Reporting',
            'requirement': 'Submit initial report by January 1, 2028.',
            'deadline': 'January 1, 2028',
            'entities': {'dates': ['January 1, 2028']}
        },
        {
            'requirement_id': 'req_002',
            'type': 'OBLIGATION',
            'severity': 'HIGH',
            'section_title': 'System Implementation',
            'requirement': 'Implement data collection system within 180 days.',
            'deadline': '180 days from effective date',
            'entities': {'dates': ['180 days']}
        },
        {
            'requirement_id': 'req_003',
            'type': 'OBLIGATION',
            'severity': 'HIGH',
            'section_title': 'Staff Training',
            'requirement': 'Complete staff training by June 30, 2027.',
            'deadline': 'June 30, 2027',
            'entities': {'dates': ['June 30, 2027']}
        },
        {
            'requirement_id': 'req_004',
            'type': 'OBLIGATION',
            'severity': 'MEDIUM',
            'section_title': 'Policy Updates',
            'requirement': 'Update internal policies within 90 days.',
            'deadline': '90 days from publication',
            'entities': {'dates': ['90 days']}
        },
        {
            'requirement_id': 'req_005',
            'type': 'RECOMMENDATION',
            'severity': 'LOW',
            'section_title': 'Best Practices',
            'requirement': 'Review procedures annually.',
            'deadline': 'Ongoing',
            'entities': {'dates': ['annually']}
        }
    ]
    
    # Initialize analyzer
    analyzer = TimelineAnalyzer(current_date=datetime(2026, 5, 17))  # Use current date
    
    # Analyze deadlines
    results = analyzer.analyze_deadlines(test_requirements)
    
    # Generate report
    print("\n" + analyzer.generate_timeline_report(results))
    
    # Test calendar building
    print("\n" + "="*70)
    print("CALENDAR VISUALIZATION")
    print("="*70 + "\n")
    
    if results['calendar']:
        for quarter, deadlines in sorted(results['calendar'].items()):
            print(f"📆 {quarter}")
            for deadline in deadlines:
                status = "🚨" if deadline['severity'] in ['CRITICAL', 'HIGH'] else "📌"
                print(f"   {status} {deadline['requirement_id']}: {deadline['deadline_text']}")
            print()
    
    print("="*70)
    print("✅ TIMELINE ANALYZER TESTS PASSED!")
    print("="*70)


if __name__ == "__main__":
    test_timeline_analyzer()