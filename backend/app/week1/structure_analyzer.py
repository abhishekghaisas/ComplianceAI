"""
Document Structure Analyzer - Days 5-6

Advanced section detection and document intelligence:
- Build hierarchical table of contents
- Detect section numbering schemes (I, II, III or 1.0, 1.1, 2.0)
- Link cross-references
- Create navigable document map
- Identify key sections (Summary, Requirements, Effective Date)
"""

import re
import logging
from typing import Dict, List, Optional, Tuple
from dataclasses import dataclass

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


@dataclass
class DocumentSection:
    """Represents a document section with hierarchy."""
    number: str
    title: str
    level: int  # 0=main section, 1=subsection, 2=sub-subsection
    page: Optional[int]
    start_pos: int
    end_pos: Optional[int]
    text: str
    parent: Optional[str]  # Parent section number
    children: List[str]  # Child section numbers


class DocumentStructureAnalyzer:
    """
    Analyze and extract document structure from regulatory text.
    
    Capabilities:
    - Detect section hierarchy (I, I.A, I.A.1, etc.)
    - Build table of contents
    - Identify key sections
    - Link cross-references
    - Create searchable document map
    """
    
    def __init__(self):
        # Common regulatory section patterns
        self.section_patterns = [
            # Roman numerals: "I. Background", "II. Analysis"
            (r'^([IVXLCDM]+)\.\s+([A-Z][^\n]{0,100})', 'roman'),
            # Decimal: "1.0 Overview", "2.1 Requirements"
            (r'^(\d+\.\d+)\s+([A-Z][^\n]{0,100})', 'decimal'),
            # Letter subsections: "A. General", "B. Specific"  
            (r'^([A-Z])\.\s+([A-Z][^\n]{0,100})', 'letter'),
            # Numbered: "Section 1", "Section II"
            (r'^Section\s+([IVXLCDM]+|[0-9]+)[:\.]?\s+([A-Z][^\n]{0,100})', 'named_section')
        ]
        
        # Key section identifiers
        self.key_sections = {
            'summary': ['summary', 'executive summary', 'overview'],
            'background': ['background', 'introduction', 'context'],
            'requirements': ['requirements', 'obligations', 'must', 'shall'],
            'effective_date': ['effective date', 'compliance date', 'deadlines'],
            'definitions': ['definitions', 'terms', 'glossary'],
            'exemptions': ['exemptions', 'exclusions', 'exceptions'],
            'penalties': ['penalties', 'enforcement', 'violations']
        }
    
    def analyze_structure(self, text: str, pages: List[str] = None) -> Dict:
        """
        Analyze complete document structure.
        
        Args:
            text: Full document text
            pages: Optional list of page texts
            
        Returns:
            Dictionary with structure analysis
        """
        logger.info("Analyzing document structure...")
        
        # Detect sections
        sections = self.detect_sections(text)
        logger.info(f"Found {len(sections)} sections")
        
        # Build hierarchy
        hierarchy = self.build_hierarchy(sections)
        logger.info(f"Built {len(hierarchy)} top-level sections")
        
        # Build table of contents
        toc = self.build_toc(sections)
        
        # Identify key sections
        key_sections = self.identify_key_sections(sections)
        logger.info(f"Identified {len(key_sections)} key sections")
        
        # Extract cross-references
        cross_refs = self.extract_cross_references(text)
        logger.info(f"Found {len(cross_refs)} cross-references")
        
        return {
            'sections': sections,
            'hierarchy': hierarchy,
            'table_of_contents': toc,
            'key_sections': key_sections,
            'cross_references': cross_refs,
            'statistics': {
                'total_sections': len(sections),
                'max_depth': self._calculate_max_depth(hierarchy),
                'avg_section_length': sum(len(s.text) for s in sections) / len(sections) if sections else 0
            }
        }
    
    def detect_sections(self, text: str) -> List[DocumentSection]:
        """
        Detect all sections in document using multiple patterns.
        
        Returns:
            List of DocumentSection objects
        """
        sections = []
        lines = text.split('\n')
        
        current_section = None
        accumulated_text = []
        
        for line_num, line in enumerate(lines):
            line_stripped = line.strip()
            
            # Try each pattern
            for pattern, pattern_type in self.section_patterns:
                match = re.match(pattern, line_stripped)
                
                if match:
                    # Save previous section
                    if current_section:
                        current_section.text = '\n'.join(accumulated_text)
                        current_section.end_pos = sum(len(l) + 1 for l in lines[:line_num])
                        sections.append(current_section)
                    
                    # Start new section
                    section_number = match.group(1)
                    section_title = match.group(2).strip()
                    
                    current_section = DocumentSection(
                        number=section_number,
                        title=section_title,
                        level=self._determine_level(section_number, pattern_type),
                        page=None,  # Would need page mapping
                        start_pos=sum(len(l) + 1 for l in lines[:line_num]),
                        end_pos=None,
                        text="",
                        parent=None,
                        children=[]
                    )
                    
                    accumulated_text = []
                    break
            else:
                # Not a section header, accumulate text
                if current_section:
                    accumulated_text.append(line)
                # Check if this might be a HEADING (all caps, short)
                elif (line_stripped and 
                      line_stripped.isupper() and 
                      5 < len(line_stripped) < 100 and
                      not line_stripped.endswith(':')):
                    
                    # Save previous
                    if current_section:
                        current_section.text = '\n'.join(accumulated_text)
                        current_section.end_pos = sum(len(l) + 1 for l in lines[:line_num])
                        sections.append(current_section)
                    
                    # Create section from heading
                    current_section = DocumentSection(
                        number=f"H{len(sections)+1}",  # Heading number
                        title=line_stripped.title(),
                        level=0,
                        page=None,
                        start_pos=sum(len(l) + 1 for l in lines[:line_num]),
                        end_pos=None,
                        text="",
                        parent=None,
                        children=[]
                    )
                    accumulated_text = []
        
        # Save last section
        if current_section:
            current_section.text = '\n'.join(accumulated_text)
            sections.append(current_section)
        
        return sections
    
    def _determine_level(self, section_number: str, pattern_type: str) -> int:
        """Determine hierarchy level of section."""
        if pattern_type == 'roman':
            return 0  # Top level
        elif pattern_type == 'decimal':
            # Count dots: "1.0" = level 0, "1.1" = level 1, "1.1.1" = level 2
            return section_number.count('.')
        elif pattern_type == 'letter':
            return 1  # Subsection
        else:
            return 0
    
    def build_hierarchy(self, sections: List[DocumentSection]) -> Dict:
        """
        Build hierarchical structure of sections.
        
        Returns:
            Nested dictionary representing document hierarchy
        """
        hierarchy = {}
        section_stack = []
        
        for section in sections:
            # Determine parent based on level
            while section_stack and section_stack[-1].level >= section.level:
                section_stack.pop()
            
            if section_stack:
                parent = section_stack[-1]
                section.parent = parent.number
                parent.children.append(section.number)
            
            section_stack.append(section)
            
            # Add to hierarchy
            if section.level == 0:
                hierarchy[section.number] = {
                    'title': section.title,
                    'subsections': []
                }
        
        return hierarchy
    
    def build_toc(self, sections: List[DocumentSection]) -> List[Dict]:
        """
        Build table of contents.
        
        Returns:
            List of TOC entries
        """
        toc = []
        
        for section in sections:
            toc.append({
                'number': section.number,
                'title': section.title,
                'level': section.level,
                'page': section.page,
                'length': len(section.text),
                'has_subsections': len(section.children) > 0
            })
        
        return toc
    
    def identify_key_sections(self, sections: List[DocumentSection]) -> Dict[str, List[str]]:
        """
        Identify key sections by content type.
        
        Returns:
            Dictionary mapping section type to section numbers
        """
        key_sections = {category: [] for category in self.key_sections.keys()}
        
        for section in sections:
            # Check title and text
            combined = (section.title + " " + section.text[:500]).lower()
            
            for category, keywords in self.key_sections.items():
                if any(keyword in combined for keyword in keywords):
                    key_sections[category].append({
                        'section_number': section.number,
                        'title': section.title,
                        'preview': section.text[:200]
                    })
        
        return key_sections
    
    def extract_cross_references(self, text: str) -> List[Dict]:
        """
        Extract cross-references to other sections.
        
        Finds: "See Section II.A", "as discussed in paragraph (b)"
        """
        cross_refs = []
        
        patterns = [
            r'(?:see|See)\s+(?:Section|section)\s+([IVXLCDM]+(?:\.[A-Z])?)',
            r'(?:pursuant to|under)\s+(?:§|section)\s+(\d+\.\d+(?:\.\d+)*)',
            r'(?:paragraph|para\.?)\s+\(([a-z0-9]+)\)',
            r'(?:comment|Comment)\s+(\d+\([a-z]\)-\d+)'
        ]
        
        for pattern in patterns:
            matches = re.finditer(pattern, text)
            
            for match in matches:
                reference = match.group(1)
                
                # Get context
                start = max(0, match.start() - 60)
                end = min(len(text), match.end() + 60)
                context = text[start:end].strip()
                
                cross_refs.append({
                    'reference': reference,
                    'full_text': match.group(),
                    'context': context,
                    'position': match.start()
                })
        
        return cross_refs
    
    def _calculate_max_depth(self, hierarchy: Dict) -> int:
        """Calculate maximum depth of section hierarchy."""
        max_depth = 0
        
        def traverse(node, depth):
            nonlocal max_depth
            max_depth = max(max_depth, depth)
            
            if isinstance(node, dict):
                for key, value in node.items():
                    if key == 'subsections' and value:
                        for subsection in value:
                            traverse(subsection, depth + 1)
        
        traverse(hierarchy, 0)
        return max_depth
    
    def get_section_by_number(self, sections: List[DocumentSection], section_number: str) -> Optional[DocumentSection]:
        """Find section by number."""
        for section in sections:
            if section.number == section_number:
                return section
        return None
    
    def get_sections_by_keyword(self, sections: List[DocumentSection], keyword: str) -> List[DocumentSection]:
        """Find sections containing keyword in title or text."""
        matches = []
        keyword_lower = keyword.lower()
        
        for section in sections:
            if keyword_lower in section.title.lower() or keyword_lower in section.text.lower():
                matches.append(section)
        
        return matches


def main():
    """Test the document structure analyzer."""
    
    # Sample regulatory text with structure
    sample_text = """
CONSUMER FINANCIAL PROTECTION BUREAU

12 CFR Part 1002

Small Business Lending Under the Equal Credit Opportunity Act

I. BACKGROUND

The Bureau worked toward a section 1071 rulemaking for a number of years.
This section provides background on the regulatory history.

A. Legislative History

Congress passed the Dodd-Frank Act in 2010. Section 1071 amended ECOA.

B. Previous Rulemakings

The Bureau published a proposed rule in 2021. See Section II for details.

II. SUMMARY OF THE FINAL RULE

This final rule amends certain provisions of the 2023 final rule.

A. Covered Credit Transactions

The Bureau is excluding merchant cash advances from coverage.

B. Covered Financial Institutions  

The threshold is raised from 100 to 1,000 transactions.

III. EFFECTIVE DATE

This rule is effective on June 30, 2026. The compliance date is January 1, 2028.

DEFINITIONS

For purposes of this rule, the following definitions apply:

Small business means a business with gross annual revenue of $1 million or less.
"""
    
    print("\n🧪 Testing Document Structure Analyzer\n")
    print("=" * 70)
    
    analyzer = DocumentStructureAnalyzer()
    
    # Analyze structure
    structure = analyzer.analyze_structure(sample_text)
    
    print(f"\n📋 STRUCTURE ANALYSIS")
    print(f"=" * 70)
    print(f"\nSections found: {structure['statistics']['total_sections']}")
    print(f"Max depth: {structure['statistics']['max_depth']}")
    print(f"Avg section length: {structure['statistics']['avg_section_length']:.0f} characters")
    
    print(f"\n📚 TABLE OF CONTENTS:")
    print("-" * 70)
    for entry in structure['table_of_contents']:
        indent = "  " * entry['level']
        print(f"{indent}{entry['number']}. {entry['title']}")
        print(f"{indent}   ({entry['length']:,} chars)")
    
    print(f"\n🎯 KEY SECTIONS IDENTIFIED:")
    print("-" * 70)
    for category, sections in structure['key_sections'].items():
        if sections:
            print(f"\n{category.upper()}:")
            for sec in sections:
                print(f"   • Section {sec['section_number']}: {sec['title']}")
                print(f"     Preview: {sec['preview'][:100]}...")
    
    print(f"\n🔗 CROSS-REFERENCES:")
    print("-" * 70)
    for ref in structure['cross_references'][:5]:
        print(f"   • {ref['full_text']}")
        print(f"     Context: {ref['context'][:80]}...")
    
    print("\n" + "=" * 70)
    print("✅ Structure analysis test complete!")
    print("\nTo use with real documents:")
    print("  from structure_analyzer import DocumentStructureAnalyzer")
    print("  analyzer = DocumentStructureAnalyzer()")
    print("  structure = analyzer.analyze_structure(document_text)")


if __name__ == "__main__":
    main()