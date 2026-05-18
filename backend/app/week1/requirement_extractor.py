"""
Requirement Extractor using Claude API

Extracts structured requirements from regulatory documents:
- Obligations (what banks MUST do)
- Prohibitions (what banks MUST NOT do)
- Deadlines
- Exemptions
- Definitions
"""

import os
import json
import logging
from typing import Dict, List, Optional
from datetime import datetime

import anthropic
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class RequirementExtractor:
    """
    Extract structured requirements from regulatory text using Claude API.
    
    Uses different models for different tasks:
    - Haiku: Fast metadata extraction
    - Sonnet: Deep requirement analysis
    """
    
    def __init__(self):
        api_key = os.getenv("ANTHROPIC_API_KEY")
        if not api_key:
            raise ValueError("ANTHROPIC_API_KEY not found in environment")
        
        self.client = anthropic.Anthropic(api_key=api_key)
        self.model_metadata = "claude-haiku-4-5-20251001"  # Fast for metadata
        self.model_analysis = "claude-haiku-4-5-20251001"  # Better for complex analysis
    
    def extract_metadata(self, document_text: str) -> Dict:
        """
        Extract metadata from regulatory document.
        
        Uses first 2-3 pages to identify:
        - Agency (CFPB, FinCEN, FDIC, OCC, etc.)
        - Document type (Final Rule, Proposed Rule, Guidance, etc.)
        - Regulation number
        - Dates (publication, effective, comment deadline)
        - Topics/categories
        - Summary
        
        Args:
            document_text: First few pages of document
            
        Returns:
            Dictionary with metadata fields
        """
        logger.info("Extracting metadata with Claude Haiku...")
        
        # Take first 3000 characters (roughly 2-3 pages)
        sample = document_text[:3000]
        
        prompt = f"""Extract metadata from this regulatory document.

DOCUMENT TEXT (first 2-3 pages):
{sample}

Extract in this EXACT JSON format (no deviation):
{{
  "agency": "CFPB|FinCEN|FDIC|OCC|Federal Reserve|SEC|Other",
  "document_type": "Final Rule|Proposed Rule|Guidance|Advisory|Examination Manual|Notice",
  "regulation_number": "CFR citation or rule number (e.g., '12 CFR 1002', 'Section 1071')",
  "title": "full document title",
  "publication_date": "YYYY-MM-DD or null",
  "effective_date": "YYYY-MM-DD or null",
  "comment_deadline": "YYYY-MM-DD or null (for proposed rules)",
  "topics": ["topic1", "topic2", "topic3"],
  "affected_entities": ["banks", "credit unions", "broker-dealers", etc.],
  "summary": "one sentence summary of what this regulation does"
}}

Be precise. If a field cannot be determined, use null.
Output ONLY valid JSON, no markdown, no preamble, no explanation."""

        try:
            message = self.client.messages.create(
                model=self.model_metadata,
                max_tokens=500,
                temperature=0.0,  # Deterministic
                messages=[{"role": "user", "content": prompt}]
            )
            
            response_text = message.content[0].text.strip()
            
            # Remove markdown code blocks if present
            if response_text.startswith("```"):
                # Remove opening ```json or ```
                lines = response_text.split('\n')
                if lines[0].startswith("```"):
                    lines = lines[1:]
                # Remove closing ```
                if lines and lines[-1].strip() == "```":
                    lines = lines[:-1]
                response_text = '\n'.join(lines).strip()
            
            # Parse JSON
            metadata = json.loads(response_text)
            
            logger.info(f"✅ Extracted metadata: {metadata.get('title', 'Unknown')[:50]}...")
            
            return metadata
            
        except json.JSONDecodeError as e:
            logger.error(f"Failed to parse JSON: {e}")
            logger.error(f"Response was: {response_text}")
            return self._empty_metadata()
        except Exception as e:
            logger.error(f"Error extracting metadata: {e}")
            return self._empty_metadata()
    
    def extract_requirements(self, section_text: str, document_metadata: Dict) -> Dict:
        """
        Extract specific requirements from a document section.
        
        Identifies:
        - Obligations (MUST do)
        - Prohibitions (MUST NOT do)
        - Deadlines
        - Exemptions
        - Definitions
        
        Args:
            section_text: Text of document section to analyze
            document_metadata: Context about the document
            
        Returns:
            Dictionary with categorized requirements
        """
        logger.info("Extracting requirements with Claude Sonnet...")
        
        prompt = f"""You are a banking compliance expert analyzing a regulatory document.

DOCUMENT CONTEXT:
- Title: {document_metadata.get('title', 'Unknown')}
- Agency: {document_metadata.get('agency', 'Unknown')}
- Effective Date: {document_metadata.get('effective_date', 'Unknown')}

SECTION TEXT TO ANALYZE:
{section_text[:4000]}  

Extract ALL specific requirements in this EXACT JSON format:

{{
  "obligations": [
    {{
      "text": "exact text of requirement",
      "plain_language": "simple one-sentence explanation",
      "who_must_comply": "banks|credit unions|all financial institutions|specific subset",
      "action_required": "what specifically must be done",
      "deadline": "YYYY-MM-DD or null",
      "trigger_condition": "when/if this applies",
      "exemptions": "who is exempt, if any",
      "penalty": "consequence of non-compliance",
      "severity": "low|medium|high|critical",
      "section_reference": "section number or paragraph"
    }}
  ],
  "prohibitions": [
    {{
      "text": "exact text of prohibition",
      "plain_language": "simple explanation",
      "prohibited_action": "what is forbidden",
      "scope": "who/what this applies to",
      "penalty": "consequence if violated",
      "severity": "low|medium|high|critical",
      "section_reference": "section number"
    }}
  ],
  "deadlines": [
    {{
      "date": "YYYY-MM-DD",
      "action": "what must be done by this date",
      "who": "who must comply",
      "consequence": "what happens if missed"
    }}
  ],
  "exemptions": [
    {{
      "who": "who is exempt",
      "condition": "under what conditions",
      "section_reference": "where exemption is defined"
    }}
  ],
  "definitions": [
    {{
      "term": "defined term",
      "definition": "the definition",
      "relevance": "why this matters for compliance"
    }}
  ]
}}

Be EXHAUSTIVE - extract every requirement you find.
Be PRECISE - use exact regulatory language.
If a category has no items, use an empty array [].

Output ONLY valid JSON, no markdown, no preamble."""

        try:
            message = self.client.messages.create(
                model=self.model_analysis,
                max_tokens=2000,
                temperature=0.0,
                messages=[{"role": "user", "content": prompt}]
            )
            
            response_text = message.content[0].text.strip()
            
            # Remove markdown code blocks if present
            if response_text.startswith("```"):
                # Remove opening ```json or ```
                lines = response_text.split('\n')
                if lines[0].startswith("```"):
                    lines = lines[1:]
                # Remove closing ```
                if lines and lines[-1].strip() == "```":
                    lines = lines[:-1]
                response_text = '\n'.join(lines).strip()
            
            requirements = json.loads(response_text)
            
            # Log summary
            num_obligations = len(requirements.get('obligations', []))
            num_prohibitions = len(requirements.get('prohibitions', []))
            num_deadlines = len(requirements.get('deadlines', []))
            
            logger.info(f"✅ Found {num_obligations} obligations, {num_prohibitions} prohibitions, {num_deadlines} deadlines")
            
            return requirements
            
        except json.JSONDecodeError as e:
            logger.error(f"Failed to parse JSON: {e}")
            logger.error(f"Response was: {response_text[:500]}...")
            return self._empty_requirements()
        except Exception as e:
            logger.error(f"Error extracting requirements: {e}")
            return self._empty_requirements()
    
    def extract_full_document_requirements(
        self, 
        document_text: str, 
        metadata: Dict,
        max_sections: int = 10
    ) -> List[Dict]:
        """
        Extract requirements from entire document by processing sections.
        
        Args:
            document_text: Full document text
            metadata: Document metadata
            max_sections: Maximum number of sections to process
            
        Returns:
            List of requirement dictionaries, one per section
        """
        logger.info("Processing full document...")
        
        # Split into sections (simple chunking for now)
        # In production, use the section detection from PDF processor
        sections = self._chunk_document(document_text, chunk_size=3000)
        
        all_requirements = []
        
        for i, section in enumerate(sections[:max_sections], 1):
            logger.info(f"Processing section {i}/{min(len(sections), max_sections)}...")
            
            requirements = self.extract_requirements(section, metadata)
            requirements['section_number'] = i
            all_requirements.append(requirements)
        
        return all_requirements
    
    def _chunk_document(self, text: str, chunk_size: int = 3000) -> List[str]:
        """Simple chunking by character count."""
        chunks = []
        words = text.split()
        current_chunk = []
        current_length = 0
        
        for word in words:
            current_chunk.append(word)
            current_length += len(word) + 1
            
            if current_length >= chunk_size:
                chunks.append(' '.join(current_chunk))
                current_chunk = []
                current_length = 0
        
        if current_chunk:
            chunks.append(' '.join(current_chunk))
        
        return chunks
    
    def _empty_metadata(self) -> Dict:
        """Return empty metadata structure."""
        return {
            "agency": None,
            "document_type": None,
            "regulation_number": None,
            "title": None,
            "publication_date": None,
            "effective_date": None,
            "comment_deadline": None,
            "topics": [],
            "affected_entities": [],
            "summary": None
        }
    
    def _empty_requirements(self) -> Dict:
        """Return empty requirements structure."""
        return {
            "obligations": [],
            "prohibitions": [],
            "deadlines": [],
            "exemptions": [],
            "definitions": []
        }
    
    def save_requirements(self, requirements: List[Dict], output_path: str):
        """Save extracted requirements to JSON file."""
        with open(output_path, 'w', encoding='utf-8') as f:
            json.dump(requirements, f, indent=2, ensure_ascii=False)
        
        logger.info(f"💾 Saved requirements to: {output_path}")


def main():
    """Example usage"""
    
    # Check for API key
    if not os.getenv("ANTHROPIC_API_KEY"):
        print("❌ Error: ANTHROPIC_API_KEY not found in environment")
        print("Please create a .env file with your API key:")
        print("ANTHROPIC_API_KEY=your_key_here")
        return
    
    extractor = RequirementExtractor()
    
    # Example document text (simulated)
    sample_text = """
    DEPARTMENT OF THE TREASURY
    Financial Crimes Enforcement Network
    31 CFR Chapter X

    Customer Due Diligence Requirements for Financial Institutions

    AGENCY: Financial Crimes Enforcement Network (FinCEN), Treasury.

    ACTION: Final rule.

    EFFECTIVE DATE: This rule is effective July 11, 2016. The compliance date 
    is May 11, 2018.

    SUMMARY: The Financial Crimes Enforcement Network (FinCEN) is issuing 
    this final rule to clarify and strengthen customer due diligence (CDD) 
    requirements for banks, securities broker-dealers, mutual funds, and 
    futures commission merchants and introducing brokers in commodities.

    Financial institutions must establish and maintain written procedures that 
    are reasonably designed to identify and verify the beneficial owners of 
    legal entity customers at the time a new account is opened.

    The procedures must enable the financial institution to identify the 
    beneficial owners of each legal entity customer at the time a new account 
    is opened, unless the customer is excluded pursuant to paragraph (e) or 
    the account is excluded pursuant to paragraph (f).
    """
    
    print("\n🔍 Testing Requirement Extractor\n")
    print("=" * 60)
    
    # Test 1: Extract metadata
    print("\n1️⃣  Extracting metadata...")
    metadata = extractor.extract_metadata(sample_text)
    print(json.dumps(metadata, indent=2))
    
    # Test 2: Extract requirements
    print("\n2️⃣  Extracting requirements...")
    requirements = extractor.extract_requirements(sample_text, metadata)
    
    print(f"\n   Found:")
    print(f"   • {len(requirements['obligations'])} obligations")
    print(f"   • {len(requirements['prohibitions'])} prohibitions")
    print(f"   • {len(requirements['deadlines'])} deadlines")
    print(f"   • {len(requirements['definitions'])} definitions")
    
    if requirements['obligations']:
        print(f"\n   Example obligation:")
        print(f"   {requirements['obligations'][0].get('plain_language', 'N/A')}")
    
    print("\n" + "=" * 60)
    print("✅ Test complete!")
    print("\nTo process a real PDF:")
    print("1. Use pdf_processor.py to extract text")
    print("2. Pass the text to extract_requirements()")


if __name__ == "__main__":
    main()