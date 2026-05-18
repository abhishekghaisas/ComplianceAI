"""
Report Generator - Week 4, Days 22-23
Generates professional compliance reports in multiple formats
"""

from typing import Dict, Any, List
from datetime import datetime
from pathlib import Path
import json


class ReportGenerator:
    """Generate professional compliance gap analysis reports"""
    
    def __init__(self, output_dir: str = "./reports"):
        """
        Initialize report generator
        
        Args:
            output_dir: Directory for generated reports
        """
        self.output_dir = Path(output_dir)
        self.output_dir.mkdir(exist_ok=True)
    
    def generate_executive_summary(
        self,
        gap_report: Dict[str, Any],
        regulation_name: str,
        policy_name: str
    ) -> str:
        """
        Generate executive summary text
        
        Returns:
            Formatted executive summary
        """
        summary = []
        
        # Header
        summary.append("EXECUTIVE SUMMARY")
        summary.append("=" * 70)
        summary.append("")
        
        # Overview
        summary.append(f"Regulation: {regulation_name}")
        summary.append(f"Policy: {policy_name}")
        summary.append(f"Analysis Date: {datetime.now().strftime('%B %d, %Y')}")
        summary.append("")
        
        # Key metrics
        summary.append("KEY METRICS")
        summary.append("-" * 70)
        summary.append(f"Total Requirements Analyzed: {gap_report['total_requirements']}")
        summary.append(f"Coverage Rate: {gap_report['coverage_percentage']:.1f}%")
        summary.append(f"Weighted Coverage: {gap_report.get('weighted_coverage', 0):.1f}%")
        summary.append(f"Overall Assessment: {gap_report.get('overall_assessment', 'N/A')}")
        summary.append("")
        
        # Coverage breakdown
        summary.append("COVERAGE BREAKDOWN")
        summary.append("-" * 70)
        summary.append(f"✅ Covered:  {gap_report['covered']} ({gap_report['covered']/gap_report['total_requirements']*100:.0f}%)")
        summary.append(f"⚠️  Partial:  {gap_report['partial']} ({gap_report['partial']/gap_report['total_requirements']*100:.0f}%)")
        summary.append(f"❌ Missing:  {gap_report['missing']} ({gap_report['missing']/gap_report['total_requirements']*100:.0f}%)")
        summary.append("")
        
        # Critical gaps
        critical_gaps = gap_report.get('priority_gaps', [])
        urgent_gaps = [g for g in critical_gaps if g.get('priority') == 'URGENT']
        
        if urgent_gaps:
            summary.append("🚨 URGENT ATTENTION REQUIRED")
            summary.append("-" * 70)
            summary.append(f"{len(urgent_gaps)} critical gap(s) require immediate action:")
            for gap in urgent_gaps[:5]:
                summary.append(f"   • {gap['requirement_id']}: {gap['requirement_text'][:60]}...")
            summary.append("")
        
        # Recommendation
        summary.append("RECOMMENDATION")
        summary.append("-" * 70)
        summary.append(gap_report.get('recommendation', 'Review required'))
        summary.append("")
        
        return "\n".join(summary)
    
    def generate_html_report(
        self,
        gap_report: Dict[str, Any],
        regulation_name: str,
        policy_name: str,
        match_results: List[Dict] = None
    ) -> str:
        """
        Generate HTML gap analysis report
        
        Returns:
            Path to generated HTML file
        """
        filename = f"gap_analysis_{datetime.now().strftime('%Y%m%d_%H%M%S')}.html"
        filepath = self.output_dir / filename
        
        html = self._build_html_report(gap_report, regulation_name, policy_name, match_results)
        
        with open(filepath, 'w', encoding='utf-8') as f:
            f.write(html)
        
        print(f"✅ HTML report saved: {filepath}")
        return str(filepath)
    
    def _build_html_report(
        self,
        gap_report: Dict[str, Any],
        regulation_name: str,
        policy_name: str,
        match_results: List[Dict] = None
    ) -> str:
        """Build HTML report content"""
        
        html = f"""<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Compliance Gap Analysis Report</title>
    <style>
        body {{
            font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Arial, sans-serif;
            line-height: 1.6;
            color: #333;
            max-width: 1200px;
            margin: 0 auto;
            padding: 20px;
            background: #f5f5f5;
        }}
        .container {{
            background: white;
            padding: 40px;
            border-radius: 8px;
            box-shadow: 0 2px 4px rgba(0,0,0,0.1);
        }}
        h1 {{
            color: #1a1a1a;
            border-bottom: 3px solid #0066cc;
            padding-bottom: 10px;
        }}
        h2 {{
            color: #0066cc;
            margin-top: 30px;
        }}
        .metric-card {{
            display: inline-block;
            background: #f8f9fa;
            padding: 20px;
            margin: 10px;
            border-radius: 6px;
            min-width: 200px;
            border-left: 4px solid #0066cc;
        }}
        .metric-value {{
            font-size: 2em;
            font-weight: bold;
            color: #0066cc;
        }}
        .metric-label {{
            color: #666;
            font-size: 0.9em;
        }}
        .status-covered {{
            background: #d4edda;
            color: #155724;
            padding: 4px 12px;
            border-radius: 4px;
            font-weight: bold;
        }}
        .status-partial {{
            background: #fff3cd;
            color: #856404;
            padding: 4px 12px;
            border-radius: 4px;
            font-weight: bold;
        }}
        .status-missing {{
            background: #f8d7da;
            color: #721c24;
            padding: 4px 12px;
            border-radius: 4px;
            font-weight: bold;
        }}
        .priority-urgent {{
            background: #dc3545;
            color: white;
            padding: 4px 12px;
            border-radius: 4px;
            font-weight: bold;
        }}
        .priority-high {{
            background: #fd7e14;
            color: white;
            padding: 4px 12px;
            border-radius: 4px;
            font-weight: bold;
        }}
        .priority-medium {{
            background: #ffc107;
            color: #333;
            padding: 4px 12px;
            border-radius: 4px;
            font-weight: bold;
        }}
        table {{
            width: 100%;
            border-collapse: collapse;
            margin: 20px 0;
        }}
        th, td {{
            padding: 12px;
            text-align: left;
            border-bottom: 1px solid #ddd;
        }}
        th {{
            background: #0066cc;
            color: white;
        }}
        tr:hover {{
            background: #f8f9fa;
        }}
        .recommendation {{
            background: #e7f3ff;
            padding: 20px;
            border-left: 4px solid #0066cc;
            border-radius: 4px;
            margin: 20px 0;
        }}
        .footer {{
            margin-top: 40px;
            padding-top: 20px;
            border-top: 1px solid #ddd;
            color: #666;
            font-size: 0.9em;
        }}
    </style>
</head>
<body>
    <div class="container">
        <h1>📊 Compliance Gap Analysis Report</h1>
        
        <div style="margin: 20px 0; color: #666;">
            <strong>Regulation:</strong> {regulation_name}<br>
            <strong>Policy:</strong> {policy_name}<br>
            <strong>Analysis Date:</strong> {datetime.now().strftime('%B %d, %Y')}<br>
            <strong>Generated by:</strong> ComplianceAI v3.0
        </div>
        
        <h2>📈 Key Metrics</h2>
        <div style="margin: 20px 0;">
            <div class="metric-card">
                <div class="metric-value">{gap_report['coverage_percentage']:.1f}%</div>
                <div class="metric-label">Standard Coverage</div>
            </div>
            <div class="metric-card">
                <div class="metric-value">{gap_report.get('weighted_coverage', 0):.1f}%</div>
                <div class="metric-label">Weighted Coverage</div>
            </div>
            <div class="metric-card">
                <div class="metric-value">{gap_report['total_requirements']}</div>
                <div class="metric-label">Total Requirements</div>
            </div>
            <div class="metric-card">
                <div class="metric-value">{len(gap_report.get('priority_gaps', []))}</div>
                <div class="metric-label">Gaps Identified</div>
            </div>
        </div>
        
        <h2>📊 Coverage Summary</h2>
        <table>
            <tr>
                <th>Status</th>
                <th>Count</th>
                <th>Percentage</th>
            </tr>
            <tr>
                <td><span class="status-covered">COVERED</span></td>
                <td>{gap_report['covered']}</td>
                <td>{gap_report['covered']/gap_report['total_requirements']*100:.1f}%</td>
            </tr>
            <tr>
                <td><span class="status-partial">PARTIAL</span></td>
                <td>{gap_report['partial']}</td>
                <td>{gap_report['partial']/gap_report['total_requirements']*100:.1f}%</td>
            </tr>
            <tr>
                <td><span class="status-missing">MISSING</span></td>
                <td>{gap_report['missing']}</td>
                <td>{gap_report['missing']/gap_report['total_requirements']*100:.1f}%</td>
            </tr>
        </table>
        
        <div class="recommendation">
            <h3>💡 Overall Recommendation</h3>
            <p><strong>Assessment:</strong> {gap_report.get('overall_assessment', 'N/A')}</p>
            <p>{gap_report.get('recommendation', 'Review required')}</p>
        </div>
        
        <h2>🎯 Priority Gaps</h2>
        {self._build_priority_gaps_html(gap_report.get('priority_gaps', []))}
        
        <h2>📅 Remediation Roadmap</h2>
        {self._build_roadmap_html(gap_report.get('remediation_roadmap', {}))}
        
        <div class="footer">
            <p>Generated by ComplianceAI - Automated Banking Compliance Gap Detection System</p>
            <p>Report ID: {datetime.now().strftime('%Y%m%d%H%M%S')} | Confidence: AI-Assisted Analysis</p>
        </div>
    </div>
</body>
</html>"""
        
        return html
    
    def _build_priority_gaps_html(self, priority_gaps: List[Dict]) -> str:
        """Build HTML for priority gaps section"""
        if not priority_gaps:
            return "<p>No gaps identified.</p>"
        
        html = "<table><tr><th>Priority</th><th>Requirement ID</th><th>Severity</th><th>Coverage</th><th>Score</th></tr>"
        
        for gap in priority_gaps[:10]:  # Top 10
            priority = gap.get('priority', 'MEDIUM')
            priority_class = f"priority-{priority.lower()}"
            
            html += f"""<tr>
                <td><span class="{priority_class}">{priority}</span></td>
                <td>{gap['requirement_id']}</td>
                <td>{gap['severity']}</td>
                <td><span class="status-{gap['coverage_status'].lower()}">{gap['coverage_status']}</span></td>
                <td>{gap['match_percent']}</td>
            </tr>"""
        
        html += "</table>"
        return html
    
    def _build_roadmap_html(self, roadmap: Dict) -> str:
        """Build HTML for remediation roadmap"""
        if not roadmap:
            return "<p>No remediation needed.</p>"
        
        html = []
        
        phases = [
            ('phase_1_immediate', '🚨 Phase 1: Immediate Actions (1-2 weeks)', '#dc3545'),
            ('phase_2_short_term', '📋 Phase 2: Short-term (1-3 months)', '#fd7e14'),
            ('phase_3_ongoing', '✓ Phase 3: Ongoing Improvements', '#28a745')
        ]
        
        for phase_key, phase_title, color in phases:
            items = roadmap.get(phase_key, [])
            if items:
                html.append(f"<h3 style='color: {color};'>{phase_title}</h3>")
                html.append("<ul>")
                for item in items[:5]:  # Top 5 per phase
                    html.append(f"<li><strong>{item['requirement_id']}</strong> ({item['severity']}): {item['requirement'][:80]}...</li>")
                html.append("</ul>")
        
        return "\n".join(html)
    
    def generate_markdown_report(
        self,
        gap_report: Dict[str, Any],
        regulation_name: str,
        policy_name: str,
        match_results: List[Dict] = None
    ) -> str:
        """Generate Markdown report"""
        filename = f"gap_analysis_{datetime.now().strftime('%Y%m%d_%H%M%S')}.md"
        filepath = self.output_dir / filename
        
        md = self._build_markdown_content(gap_report, regulation_name, policy_name, match_results)
        
        with open(filepath, 'w', encoding='utf-8') as f:
            f.write(md)
        
        print(f"✅ Markdown report saved: {filepath}")
        return str(filepath)
    
    def _build_markdown_content(
        self,
        gap_report: Dict[str, Any],
        regulation_name: str,
        policy_name: str,
        match_results: List[Dict] = None
    ) -> str:
        """Build markdown report content"""
        
        md = f"""# Compliance Gap Analysis Report

**Regulation:** {regulation_name}  
**Policy:** {policy_name}  
**Analysis Date:** {datetime.now().strftime('%B %d, %Y')}  
**Generated by:** ComplianceAI

---

## Executive Summary

### Key Metrics

| Metric | Value |
|--------|-------|
| Total Requirements | {gap_report['total_requirements']} |
| Coverage Rate | {gap_report['coverage_percentage']:.1f}% |
| Weighted Coverage | {gap_report.get('weighted_coverage', 0):.1f}% |
| Overall Assessment | {gap_report.get('overall_assessment', 'N/A')} |

### Coverage Breakdown

- ✅ **Covered:** {gap_report['covered']} ({gap_report['covered']/gap_report['total_requirements']*100:.0f}%)
- ⚠️ **Partial:** {gap_report['partial']} ({gap_report['partial']/gap_report['total_requirements']*100:.0f}%)
- ❌ **Missing:** {gap_report['missing']} ({gap_report['missing']/gap_report['total_requirements']*100:.0f}%)

---

## Overall Recommendation

**Assessment:** {gap_report.get('overall_assessment', 'N/A')}

{gap_report.get('recommendation', 'Review required')}

---

## Priority Gaps

{self._build_priority_gaps_markdown(gap_report.get('priority_gaps', []))}

---

## Remediation Roadmap

{self._build_roadmap_markdown(gap_report.get('remediation_roadmap', {}))}

---

## Detailed Results by Severity

{self._build_severity_breakdown_markdown(gap_report.get('by_severity', {}))}

---

## Analysis Metadata

- **Report ID:** {datetime.now().strftime('%Y%m%d%H%M%S')}
- **Analysis Method:** AI-Assisted (RAG + Semantic Search)
- **Confidence Level:** Medium-High
- **Recommended Action:** Human review of URGENT and HIGH priority gaps

---

*Generated by ComplianceAI - Automated Banking Compliance Gap Detection System*
"""
        
        return md
    
    def _build_priority_gaps_markdown(self, priority_gaps: List[Dict]) -> str:
        """Build markdown for priority gaps"""
        if not priority_gaps:
            return "No gaps identified."
        
        md = ["| Priority | Requirement | Severity | Status | Score |",
              "|----------|-------------|----------|--------|-------|"]
        
        for gap in priority_gaps[:15]:
            priority_emoji = {
                'URGENT': '🚨',
                'HIGH': '⚠️',
                'MEDIUM': '📋',
                'LOW': '✓'
            }.get(gap.get('priority', 'MEDIUM'), '📋')
            
            md.append(f"| {priority_emoji} {gap.get('priority', 'MEDIUM')} | {gap['requirement_id']} | {gap['severity']} | {gap['coverage_status']} | {gap['match_percent']} |")
        
        return "\n".join(md)
    
    def _build_roadmap_markdown(self, roadmap: Dict) -> str:
        """Build markdown for remediation roadmap"""
        if not roadmap:
            return "No remediation needed."
        
        md = []
        
        phases = [
            ('phase_1_immediate', '### 🚨 Phase 1: Immediate Actions (1-2 weeks)'),
            ('phase_2_short_term', '### 📋 Phase 2: Short-term (1-3 months)'),
            ('phase_3_ongoing', '### ✓ Phase 3: Ongoing Improvements')
        ]
        
        for phase_key, phase_title in phases:
            items = roadmap.get(phase_key, [])
            if items:
                md.append(phase_title)
                md.append("")
                for i, item in enumerate(items, 1):
                    md.append(f"{i}. **{item['requirement_id']}** ({item['severity']})")
                    md.append(f"   - {item['requirement'][:100]}...")
                    if item.get('actions'):
                        md.append(f"   - Action: {item['actions'][0]}")
                    md.append("")
        
        return "\n".join(md)
    
    def _build_severity_breakdown_markdown(self, by_severity: Dict) -> str:
        """Build markdown for severity breakdown"""
        if not by_severity:
            return "No severity data available."
        
        md = []
        
        for severity in ['CRITICAL', 'HIGH', 'MEDIUM', 'LOW']:
            if severity in by_severity:
                data = by_severity[severity]
                total = data['total']
                covered_pct = (data['covered'] / total * 100) if total > 0 else 0
                
                md.append(f"### {severity}")
                md.append(f"- Total: {total}")
                md.append(f"- Covered: {data['covered']} ({covered_pct:.0f}%)")
                md.append(f"- Partial: {data['partial']}")
                md.append(f"- Missing: {data['missing']}")
                md.append("")
        
        return "\n".join(md)
    
    def generate_json_report(
        self,
        gap_report: Dict[str, Any],
        match_results: List[Dict],
        conflicts: Dict = None,
        timeline: Dict = None
    ) -> str:
        """Generate comprehensive JSON report with all analysis data"""
        filename = f"full_analysis_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
        filepath = self.output_dir / filename
        
        full_report = {
            'metadata': {
                'generated_at': datetime.now().isoformat(),
                'report_version': '1.0',
                'system': 'ComplianceAI'
            },
            'gap_analysis': gap_report,
            'match_results': match_results if match_results else [],
            'conflicts': conflicts if conflicts else {},
            'timeline': timeline if timeline else {}
        }
        
        with open(filepath, 'w', encoding='utf-8') as f:
            json.dump(full_report, f, indent=2, default=str)
        
        print(f"✅ JSON report saved: {filepath}")
        return str(filepath)


def test_report_generator():
    """Test report generation"""
    print("="*70)
    print("🧪 TESTING REPORT GENERATOR")
    print("="*70 + "\n")
    
    # Sample gap report
    sample_gap_report = {
        'total_requirements': 5,
        'covered': 3,
        'partial': 1,
        'missing': 1,
        'coverage_percentage': 60.0,
        'weighted_coverage': 55.6,
        'overall_assessment': 'FAIR',
        'recommendation': '⚠️ MODERATE GAPS: 55.6% weighted coverage. Policy enhancement needed. Focus on 2 high-priority items.',
        'by_severity': {
            'CRITICAL': {'covered': 0, 'partial': 1, 'missing': 0, 'total': 1},
            'HIGH': {'covered': 1, 'partial': 1, 'missing': 0, 'total': 2},
            'MEDIUM': {'covered': 2, 'partial': 0, 'missing': 0, 'total': 2}
        },
        'priority_gaps': [
            {
                'requirement_id': 'req_002',
                'severity': 'CRITICAL',
                'coverage_status': 'PARTIAL',
                'match_percent': '34.9%',
                'priority': 'URGENT',
                'requirement_text': 'Lenders are prohibited from discriminating...'
            },
            {
                'requirement_id': 'req_003',
                'severity': 'HIGH',
                'coverage_status': 'PARTIAL',
                'match_percent': '39.8%',
                'priority': 'HIGH',
                'requirement_text': 'Banks must maintain customer identification programs...'
            }
        ],
        'remediation_roadmap': {
            'phase_1_immediate': [
                {
                    'requirement_id': 'req_002',
                    'severity': 'CRITICAL',
                    'requirement': 'Lenders are prohibited from discriminating based on protected characteristics',
                    'actions': ['Create comprehensive fair lending policy section']
                }
            ],
            'phase_2_short_term': [
                {
                    'requirement_id': 'req_003',
                    'severity': 'HIGH',
                    'requirement': 'Banks must maintain customer identification programs',
                    'actions': ['Enhance CDD section with FinCEN references']
                }
            ],
            'phase_3_ongoing': []
        }
    }
    
    # Initialize generator
    generator = ReportGenerator(output_dir="./test_reports")
    
    # Test 1: Executive summary
    print("TEST 1: Executive Summary")
    print("-"*70 + "\n")
    
    summary = generator.generate_executive_summary(
        sample_gap_report,
        "CFPB Section 1071",
        "Community Bank Lending Policy"
    )
    
    print(summary)
    print()
    
    # Test 2: HTML report
    print("="*70)
    print("TEST 2: HTML Report Generation")
    print("-"*70 + "\n")
    
    html_path = generator.generate_html_report(
        sample_gap_report,
        "CFPB Section 1071",
        "Community Bank Lending Policy"
    )
    
    print(f"✅ HTML report created at: {html_path}")
    print()
    
    # Test 3: Markdown report
    print("="*70)
    print("TEST 3: Markdown Report Generation")
    print("-"*70 + "\n")
    
    md_path = generator.generate_markdown_report(
        sample_gap_report,
        "CFPB Section 1071",
        "Community Bank Lending Policy"
    )
    
    print(f"✅ Markdown report created at: {md_path}")
    print()
    
    # Test 4: JSON report
    print("="*70)
    print("TEST 4: JSON Report Generation")
    print("-"*70 + "\n")
    
    json_path = generator.generate_json_report(
        sample_gap_report,
        match_results=[],
        conflicts={'total_conflicts': 3},
        timeline={'upcoming_count': 2}
    )
    
    print(f"✅ JSON report created at: {json_path}")
    print()
    
    print("="*70)
    print("✅ REPORT GENERATOR TESTS PASSED!")
    print("="*70)
    print("\nReports generated in ./test_reports/:")
    print("   • HTML (styled, professional)")
    print("   • Markdown (readable, GitHub-friendly)")
    print("   • JSON (machine-readable, complete data)")


if __name__ == "__main__":
    test_report_generator()