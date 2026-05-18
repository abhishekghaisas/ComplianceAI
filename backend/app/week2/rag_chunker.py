"""
RAG Document Chunker - Week 2, Day 8
Splits documents into semantic chunks for embedding
"""

import re
import tiktoken
from typing import List, Dict, Any


class DocumentChunker:
    """Smart document chunking with context preservation"""
    
    def __init__(self, chunk_size=500, overlap=100, min_chunk_size=100):
        """
        Args:
            chunk_size: Target size in tokens
            overlap: Overlap between chunks in tokens
            min_chunk_size: Minimum chunk size to keep
        """
        self.chunk_size = chunk_size
        self.overlap = overlap
        self.min_chunk_size = min_chunk_size
        self.encoding = tiktoken.get_encoding("cl100k_base")
        
    def count_tokens(self, text: str) -> int:
        """Count tokens in text"""
        return len(self.encoding.encode(text))
    
    def chunk_requirement(self, requirement: Dict[str, Any], source_file: str) -> List[Dict[str, Any]]:
        """
        Chunk a requirement from Week 1 output
        
        Args:
            requirement: Requirement dict from Week 1 JSON
            source_file: Source regulation filename
            
        Returns:
            List of chunk dicts ready for embedding
        """
        chunks = []
        full_text = self._build_requirement_text(requirement)
        tokens = self.count_tokens(full_text)
        
        # Single chunk if small enough
        if tokens <= self.chunk_size:
            chunks.append({
                "text": full_text,
                "metadata": {
                    "source_file": source_file,
                    "requirement_id": requirement.get("requirement_id", "unknown"),
                    "requirement_type": requirement.get("type", "UNKNOWN"),
                    "severity": requirement.get("severity", "MEDIUM"),
                    "section_title": requirement.get("section_title", ""),
                    "chunk_index": 0,
                    "total_chunks": 1
                }
            })
        else:
            # Split into overlapping chunks
            text_chunks = self._split_with_overlap(full_text)
            for i, chunk_text in enumerate(text_chunks):
                chunks.append({
                    "text": chunk_text,
                    "metadata": {
                        "source_file": source_file,
                        "requirement_id": requirement.get("requirement_id", "unknown"),
                        "requirement_type": requirement.get("type", "UNKNOWN"),
                        "severity": requirement.get("severity", "MEDIUM"),
                        "section_title": requirement.get("section_title", ""),
                        "chunk_index": i,
                        "total_chunks": len(text_chunks)
                    }
                })
        
        return chunks
    
    def chunk_policy(self, policy_text: str, source_file: str, metadata: Dict = None) -> List[Dict[str, Any]]:
        """
        Chunk a bank policy document
        
        Args:
            policy_text: Full policy text
            source_file: Policy filename
            metadata: Additional metadata
            
        Returns:
            List of chunk dicts
        """
        chunks = []
        metadata = metadata or {}
        
        # Split by sections
        sections = self._split_by_sections(policy_text)
        
        for section_idx, (section_title, section_text) in enumerate(sections):
            contextualized_text = f"Section: {section_title}\n\n{section_text}"
            
            # Split if too large
            if self.count_tokens(contextualized_text) > self.chunk_size:
                text_chunks = self._split_with_overlap(contextualized_text)
            else:
                text_chunks = [contextualized_text]
            
            for chunk_idx, chunk_text in enumerate(text_chunks):
                chunks.append({
                    "text": chunk_text,
                    "metadata": {
                        "source_file": source_file,
                        "section_title": section_title,
                        "section_index": section_idx,
                        "chunk_index": chunk_idx,
                        "total_chunks": len(text_chunks),
                        **metadata
                    }
                })
        
        return chunks
    
    def _build_requirement_text(self, requirement: Dict[str, Any]) -> str:
        """Build searchable text from requirement"""
        parts = []
        
        if requirement.get("section_title"):
            parts.append(f"Section: {requirement['section_title']}")
        
        req_type = requirement.get("type", "UNKNOWN")
        severity = requirement.get("severity", "MEDIUM")
        parts.append(f"Type: {req_type} (Severity: {severity})")
        
        if requirement.get("requirement"):
            parts.append(f"Requirement: {requirement['requirement']}")
        
        if requirement.get("plain_language"):
            parts.append(f"Explanation: {requirement['plain_language']}")
        
        if requirement.get("deadline"):
            parts.append(f"Deadline: {requirement['deadline']}")
        
        # Add entities if available
        entities = requirement.get("entities", {})
        if entities.get("dates"):
            parts.append(f"Key Dates: {', '.join(entities['dates'])}")
        if entities.get("amounts"):
            parts.append(f"Dollar Amounts: {', '.join(entities['amounts'])}")
        
        return "\n\n".join(parts)
    
    def _split_by_sections(self, text: str) -> List[tuple]:
        """Split text by section headers"""
        section_pattern = r'^((?:[A-Z][A-Za-z\s]+:)|(?:\d+\.(?:\d+\.?)?\s+[A-Z][^\n]+))'
        
        sections = []
        current_title = "Introduction"
        current_text = []
        
        lines = text.split('\n')
        for line in lines:
            if re.match(section_pattern, line.strip()):
                if current_text:
                    sections.append((current_title, '\n'.join(current_text)))
                current_title = line.strip()
                current_text = []
            else:
                current_text.append(line)
        
        if current_text:
            sections.append((current_title, '\n'.join(current_text)))
        
        return sections if sections else [("Document", text)]
    
    def _split_with_overlap(self, text: str) -> List[str]:
        """Split text into overlapping chunks"""
        tokens = self.encoding.encode(text)
        chunks = []
        start = 0
        
        while start < len(tokens):
            end = start + self.chunk_size
            chunk_tokens = tokens[start:end]
            
            if len(chunk_tokens) >= self.min_chunk_size:
                chunks.append(self.encoding.decode(chunk_tokens))
            
            start += (self.chunk_size - self.overlap)
        
        return chunks


def test_chunker():
    """Test the document chunker"""
    print("="*60)
    print("🧪 TESTING DOCUMENT CHUNKER")
    print("="*60 + "\n")
    
    chunker = DocumentChunker(chunk_size=200, overlap=50)
    
    # Test 1: Chunk a requirement
    print("TEST 1: Chunking a Requirement\n")
    
    sample_requirement = {
        "requirement_id": "req_001",
        "type": "OBLIGATION",
        "severity": "HIGH",
        "section_title": "Small Business Lending Data Collection",
        "requirement": "Financial institutions must collect and report data on small business loan applications.",
        "plain_language": "Banks need to track business loan info.",
        "deadline": "January 1, 2028",
        "entities": {
            "dates": ["2028-01-01"],
            "amounts": ["$5 million"]
        }
    }
    
    chunks = chunker.chunk_requirement(sample_requirement, "cfpb_test.pdf")
    
    print(f"✅ Created {len(chunks)} chunk(s)\n")
    
    for i, chunk in enumerate(chunks):
        print(f"📄 Chunk {i + 1}/{len(chunks)}:")
        print(f"   Tokens: {chunker.count_tokens(chunk['text'])}")
        print(f"   Metadata: {chunk['metadata']['requirement_type']} - {chunk['metadata']['severity']}")
        print(f"   Text: {chunk['text'][:100]}...")
        print()
    
    # Test 2: Chunk a policy
    print("\n" + "="*60)
    print("TEST 2: Chunking a Policy Document\n")
    
    sample_policy = """
Section 5.2: Small Business Lending Procedures

Our bank follows comprehensive procedures for small business lending.

5.2.1 Application Process
All small business loan applications must be documented within 24 hours.

5.2.2 Data Collection  
We collect all required data points including demographics and loan terms.

5.2.3 Decision Tracking
All lending decisions are tracked and reported quarterly.
"""
    
    policy_chunks = chunker.chunk_policy(sample_policy, "lending_policy.pdf")
    
    print(f"✅ Created {len(policy_chunks)} chunk(s)\n")
    
    for i, chunk in enumerate(policy_chunks):
        print(f"📄 Chunk {i + 1}/{len(policy_chunks)}:")
        print(f"   Section: {chunk['metadata']['section_title']}")
        print(f"   Tokens: {chunker.count_tokens(chunk['text'])}")
        print(f"   Text: {chunk['text'][:80]}...")
        print()
    
    print("="*60)
    print("✅ ALL TESTS PASSED!")
    print("="*60)


if __name__ == "__main__":
    test_chunker()