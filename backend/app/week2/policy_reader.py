"""
Policy Reader - Week 2, Day 10
Reads bank policy documents (PDF, DOCX) and extracts structured content
"""

import pdfplumber
from pathlib import Path
from typing import Dict, Any, List, Optional
import re


class PolicyReader:
    """Read and parse bank policy documents"""
    
    def __init__(self):
        """Initialize policy reader"""
        self.supported_formats = ['.pdf', '.docx', '.txt']
    
    def read_policy(self, file_path: str) -> Dict[str, Any]:
        """
        Read a policy document and extract content
        
        Args:
            file_path: Path to policy file
            
        Returns:
            Dict with policy content and metadata
        """
        path = Path(file_path)
        
        if not path.exists():
            raise FileNotFoundError(f"Policy file not found: {file_path}")
        
        file_ext = path.suffix.lower()
        
        if file_ext not in self.supported_formats:
            raise ValueError(f"Unsupported format: {file_ext}. Supported: {self.supported_formats}")
        
        print(f"📖 Reading policy: {path.name}")
        
        # Read based on format
        if file_ext == '.pdf':
            content = self._read_pdf(file_path)
        elif file_ext == '.docx':
            content = self._read_docx(file_path)
        else:  # .txt
            content = self._read_txt(file_path)
        
        # Extract metadata
        metadata = self._extract_metadata(content, path.name)
        
        # Detect sections
        sections = self._detect_sections(content)
        
        result = {
            'file_name': path.name,
            'file_path': str(path),
            'format': file_ext[1:],
            'content': content,
            'metadata': metadata,
            'sections': sections,
            'word_count': len(content.split()),
            'char_count': len(content)
        }
        
        print(f"✅ Extracted {result['word_count']} words, {len(sections)} sections")
        
        return result
    
    def _read_pdf(self, file_path: str) -> str:
        """Read PDF file"""
        text_parts = []
        
        with pdfplumber.open(file_path) as pdf:
            for page in pdf.pages:
                text = page.extract_text()
                if text:
                    text_parts.append(text)
        
        return '\n\n'.join(text_parts)
    
    def _read_docx(self, file_path: str) -> str:
        """Read DOCX file"""
        try:
            from docx import Document
            
            doc = Document(file_path)
            text_parts = []
            
            for paragraph in doc.paragraphs:
                if paragraph.text.strip():
                    text_parts.append(paragraph.text)
            
            return '\n\n'.join(text_parts)
            
        except ImportError:
            raise ImportError("python-docx not installed. Install with: pip install python-docx")
    
    def _read_txt(self, file_path: str) -> str:
        """Read text file"""
        with open(file_path, 'r', encoding='utf-8') as f:
            return f.read()
    
    def _extract_metadata(self, content: str, filename: str) -> Dict[str, Any]:
        """
        Extract metadata from policy content
        
        Args:
            content: Policy text
            filename: Original filename
            
        Returns:
            Metadata dictionary
        """
        metadata = {
            'title': self._extract_title(content, filename),
            'policy_areas': self._identify_policy_areas(content),
            'version': self._extract_version(content),
            'effective_date': self._extract_dates(content)
        }
        
        return metadata
    
    def _extract_title(self, content: str, filename: str) -> str:
        """Extract policy title from content or filename"""
        # Look for title in first few lines
        lines = content.split('\n')[:10]
        
        for line in lines:
            line = line.strip()
            # Title usually all caps or title case and longer than 10 chars
            if len(line) > 10 and len(line) < 100:
                if line.isupper() or line.istitle():
                    return line
        
        # Fallback to cleaned filename
        return filename.replace('_', ' ').replace('.pdf', '').replace('.docx', '').title()
    
    def _identify_policy_areas(self, content: str) -> List[str]:
        """Identify policy areas mentioned in document"""
        content_lower = content.lower()
        
        areas = {
            'lending': ['lending', 'loan', 'credit'],
            'compliance': ['compliance', 'regulatory', 'regulation'],
            'risk_management': ['risk management', 'risk assessment'],
            'anti_money_laundering': ['aml', 'anti-money laundering', 'suspicious activity'],
            'customer_due_diligence': ['cdd', 'customer due diligence', 'know your customer', 'kyc'],
            'fair_lending': ['fair lending', 'ecoa', 'equal credit'],
            'data_privacy': ['privacy', 'data protection', 'confidential'],
            'consumer_protection': ['consumer protection', 'cfpb'],
        }
        
        found_areas = []
        for area, keywords in areas.items():
            if any(kw in content_lower for kw in keywords):
                found_areas.append(area)
        
        return found_areas if found_areas else ['general']
    
    def _extract_version(self, content: str) -> Optional[str]:
        """Extract version number from content"""
        # Look for version patterns
        version_patterns = [
            r'version[:\s]+(\d+\.?\d*)',
            r'v(\d+\.?\d*)',
            r'revision[:\s]+(\d+)',
        ]
        
        content_lower = content.lower()
        
        for pattern in version_patterns:
            match = re.search(pattern, content_lower)
            if match:
                return match.group(1)
        
        return None
    
    def _extract_dates(self, content: str) -> Optional[str]:
        """Extract effective date from content"""
        # Look for date patterns
        date_patterns = [
            r'effective\s+date[:\s]+([A-Za-z]+\s+\d{1,2},?\s+\d{4})',
            r'effective[:\s]+([A-Za-z]+\s+\d{1,2},?\s+\d{4})',
            r'last\s+updated[:\s]+([A-Za-z]+\s+\d{1,2},?\s+\d{4})',
        ]
        
        for pattern in date_patterns:
            match = re.search(pattern, content, re.IGNORECASE)
            if match:
                return match.group(1)
        
        return None
    
    def _detect_sections(self, content: str) -> List[Dict[str, str]]:
        """
        Detect sections in policy document
        
        Args:
            content: Policy text
            
        Returns:
            List of section dicts with title and content
        """
        sections = []
        
        # Common section patterns
        section_patterns = [
            r'^(\d+\.?\d*\.?\s+[A-Z][^\n]{10,80})$',  # "1.1 Section Title"
            r'^([A-Z][A-Z\s]{5,50})$',                 # "SECTION TITLE"
            r'^([IVX]+\.\s+[A-Z][^\n]{10,80})$',      # "I. Section Title"
        ]
        
        lines = content.split('\n')
        current_section = None
        current_content = []
        
        for line in lines:
            line_stripped = line.strip()
            
            # Check if line is a section header
            is_header = False
            for pattern in section_patterns:
                if re.match(pattern, line_stripped):
                    is_header = True
                    
                    # Save previous section
                    if current_section:
                        sections.append({
                            'title': current_section,
                            'content': '\n'.join(current_content).strip()
                        })
                    
                    # Start new section
                    current_section = line_stripped
                    current_content = []
                    break
            
            if not is_header and current_section:
                current_content.append(line)
        
        # Add last section
        if current_section:
            sections.append({
                'title': current_section,
                'content': '\n'.join(current_content).strip()
            })
        
        # If no sections detected, treat whole document as one section
        if not sections:
            sections.append({
                'title': 'Policy Document',
                'content': content
            })
        
        return sections


def test_policy_reader():
    """Test the policy reader"""
    print("="*70)
    print("🧪 TESTING POLICY READER")
    print("="*70 + "\n")
    
    # Create a sample policy as text
    sample_policy = """
BANK XYZ LENDING POLICY

Version 2.1
Effective Date: January 1, 2024

1. PURPOSE

This policy establishes guidelines for lending activities at Bank XYZ to ensure 
compliance with applicable regulations and sound lending practices.

2. SCOPE

This policy applies to all lending personnel and covers all types of loans including:
- Commercial loans
- Consumer loans
- Small business loans

3. DATA COLLECTION REQUIREMENTS

3.1 Small Business Lending Data

The bank shall collect the following data for all small business loan applications:
- Business name and address
- Business demographics
- Loan amount requested
- Purpose of loan
- Action taken (approved, denied, etc.)

This data must be reported to the CFPB on a quarterly basis.

3.2 Fair Lending Compliance

The bank prohibits discrimination in lending based on race, color, religion, 
national origin, sex, marital status, age, or receipt of public assistance.

All lending decisions must be based on objective creditworthiness criteria.

4. CUSTOMER IDENTIFICATION

All customers must be properly identified and verified according to our 
Customer Identification Program (CIP) requirements. Records must be 
maintained for five years after account closure.

5. APPROVAL AUTHORITY

Lending authority is delegated as follows:
- Loans up to $50,000: Loan officers
- Loans $50,000 - $500,000: Branch managers
- Loans over $500,000: Credit committee

6. REVIEW AND UPDATES

This policy shall be reviewed annually and updated as needed to reflect 
changes in regulations and business needs.
"""
    
    # Save sample policy
    import tempfile
    with tempfile.NamedTemporaryFile(mode='w', suffix='.txt', delete=False) as f:
        f.write(sample_policy)
        temp_file = f.name
    
    # Test reading
    reader = PolicyReader()
    
    try:
        result = reader.read_policy(temp_file)
        
        print("✅ Policy read successfully!\n")
        print(f"Title: {result['metadata']['title']}")
        print(f"Word count: {result['word_count']}")
        print(f"Sections detected: {len(result['sections'])}")
        print(f"Policy areas: {', '.join(result['metadata']['policy_areas'])}")
        
        if result['metadata']['version']:
            print(f"Version: {result['metadata']['version']}")
        if result['metadata']['effective_date']:
            print(f"Effective date: {result['metadata']['effective_date']}")
        
        print("\n📑 Sections:")
        for i, section in enumerate(result['sections'], 1):
            print(f"   {i}. {section['title']}")
            print(f"      ({len(section['content'])} chars)")
        
        print("\n" + "="*70)
        print("✅ POLICY READER TEST PASSED!")
        print("="*70)
        
    finally:
        # Cleanup
        import os
        os.unlink(temp_file)


if __name__ == "__main__":
    test_policy_reader()