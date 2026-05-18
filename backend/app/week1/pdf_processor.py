"""
PDF Processor for Regulatory Documents

Handles extraction of text, tables, and structure from regulatory PDFs.
Supports both text-based and scanned (OCR) documents.
"""

import os
import json
from pathlib import Path
from typing import Dict, List, Optional
import logging

import pdfplumber
from pypdf import PdfReader
import pytesseract
from PIL import Image

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class RegulatoryPDFProcessor:
    """
    Process regulatory PDFs to extract text, structure, and metadata.
    
    Handles:
    - Text-based PDFs (direct extraction)
    - Scanned PDFs (OCR)
    - Mixed PDFs (text + images)
    - Table extraction
    - Structure detection
    """
    
    def __init__(self):
        self.min_text_threshold = 100  # Minimum chars to consider text-based
        
    def process_pdf(self, pdf_path: str) -> Dict:
        """
        Main processing function for regulatory PDFs.
        
        Args:
            pdf_path: Path to PDF file
            
        Returns:
            Dictionary containing:
            - text: Full extracted text
            - metadata: PDF metadata (pages, size, etc.)
            - sections: Detected document sections
            - tables: Extracted tables
            - pages: List of page texts
        """
        logger.info(f"Processing PDF: {pdf_path}")
        
        if not os.path.exists(pdf_path):
            raise FileNotFoundError(f"PDF not found: {pdf_path}")
        
        # Get basic metadata
        metadata = self._extract_basic_metadata(pdf_path)
        logger.info(f"PDF has {metadata['page_count']} pages")
        
        # Extract text
        text, pages = self._extract_text(pdf_path)
        
        # If mostly empty, try OCR
        if len(text.strip()) < self.min_text_threshold:
            logger.warning("PDF appears to be scanned. Attempting OCR...")
            text, pages = self._ocr_pdf(pdf_path)
        
        logger.info(f"Extracted {len(text)} characters of text")
        
        # Extract tables
        tables = self._extract_tables(pdf_path)
        logger.info(f"Found {len(tables)} tables")
        
        # Detect structure (sections, headings)
        sections = self._detect_structure(text)
        logger.info(f"Detected {len(sections)} sections")
        
        return {
            'text': text,
            'metadata': metadata,
            'sections': sections,
            'tables': tables,
            'pages': pages,
            'pdf_path': pdf_path
        }
    
    def _extract_basic_metadata(self, pdf_path: str) -> Dict:
        """Extract basic PDF metadata."""
        try:
            with open(pdf_path, 'rb') as file:
                reader = PdfReader(file)
                metadata = reader.metadata
                
                return {
                    'page_count': len(reader.pages),
                    'file_size_mb': os.path.getsize(pdf_path) / (1024 * 1024),
                    'title': metadata.get('/Title', '') if metadata else '',
                    'author': metadata.get('/Author', '') if metadata else '',
                    'creation_date': metadata.get('/CreationDate', '') if metadata else '',
                    'file_name': os.path.basename(pdf_path)
                }
        except Exception as e:
            logger.error(f"Error extracting metadata: {e}")
            return {
                'page_count': 0,
                'file_size_mb': 0,
                'error': str(e)
            }
    
    def _extract_text(self, pdf_path: str) -> tuple[str, List[str]]:
        """
        Extract text from PDF using pdfplumber.
        
        Returns:
            Tuple of (full_text, list_of_page_texts)
        """
        full_text = ""
        pages = []
        
        try:
            with pdfplumber.open(pdf_path) as pdf:
                for page_num, page in enumerate(pdf.pages, 1):
                    try:
                        page_text = page.extract_text() or ""
                        pages.append(page_text)
                        full_text += f"\n\n--- Page {page_num} ---\n\n{page_text}"
                    except Exception as e:
                        logger.warning(f"Error extracting page {page_num}: {e}")
                        pages.append("")
        except Exception as e:
            logger.error(f"Error opening PDF: {e}")
            raise
        
        return full_text, pages
    
    def _ocr_pdf(self, pdf_path: str) -> tuple[str, List[str]]:
        """
        OCR scanned PDF using pytesseract.
        
        Note: Requires tesseract-ocr installed on system.
        Mac: brew install tesseract
        Ubuntu: sudo apt-get install tesseract-ocr
        """
        logger.info("Running OCR (this may take a while)...")
        
        # This is a simplified version
        # In production, you'd use pdf2image to convert pages to images first
        full_text = ""
        pages = []
        
        try:
            # For now, just indicate OCR would be needed
            logger.warning("OCR not fully implemented. Install pdf2image and implement if needed.")
            return "OCR_REQUIRED: This PDF needs OCR processing", []
        except Exception as e:
            logger.error(f"OCR error: {e}")
            return f"OCR_ERROR: {str(e)}", []
    
    def _extract_tables(self, pdf_path: str) -> List[Dict]:
        """
        Extract tables from PDF.
        
        Returns list of tables with their page numbers and data.
        """
        tables = []
        
        try:
            with pdfplumber.open(pdf_path) as pdf:
                for page_num, page in enumerate(pdf.pages, 1):
                    page_tables = page.extract_tables()
                    
                    if page_tables:
                        for table_num, table in enumerate(page_tables, 1):
                            tables.append({
                                'page': page_num,
                                'table_number': table_num,
                                'rows': len(table),
                                'columns': len(table[0]) if table else 0,
                                'data': table
                            })
        except Exception as e:
            logger.error(f"Error extracting tables: {e}")
        
        return tables
    
    def _detect_structure(self, text: str) -> List[Dict]:
        """
        Detect document structure (sections, headings).
        
        Looks for common regulatory document patterns:
        - "SECTION I.", "SECTION II.", etc.
        - "I. Background", "II. Analysis", etc.
        - Numbered sections (1.0, 1.1, 2.0, etc.)
        """
        sections = []
        lines = text.split('\n')
        
        current_section = None
        section_patterns = [
            r'SECTION\s+[IVXLCDM]+',  # SECTION I, SECTION II
            r'[IVXLCDM]+\.\s+[A-Z]',   # I. Background, II. Analysis
            r'\d+\.\d+\s+[A-Z]',        # 1.0 Overview, 2.1 Requirements
        ]
        
        for line_num, line in enumerate(lines):
            line = line.strip()
            
            # Simple heuristic: Lines that are all caps and short might be headers
            if line and line.isupper() and len(line) < 100 and len(line) > 5:
                if current_section:
                    sections.append(current_section)
                
                current_section = {
                    'title': line,
                    'line_number': line_num,
                    'text': ""
                }
            elif current_section:
                current_section['text'] += line + "\n"
        
        # Add the last section
        if current_section:
            sections.append(current_section)
        
        return sections
    
    def get_first_pages(self, pdf_path: str, num_pages: int = 3) -> str:
        """
        Extract just the first N pages (useful for metadata extraction).
        
        Args:
            pdf_path: Path to PDF
            num_pages: Number of pages to extract (default 3)
            
        Returns:
            Text from first N pages
        """
        try:
            with pdfplumber.open(pdf_path) as pdf:
                text = ""
                for page in pdf.pages[:num_pages]:
                    text += page.extract_text() or ""
                    text += "\n\n"
                return text
        except Exception as e:
            logger.error(f"Error extracting first pages: {e}")
            return ""
    
    def save_extracted_data(self, extracted_data: Dict, output_path: str):
        """Save extracted data to JSON file."""
        # Remove large text fields for summary
        summary = {
            'metadata': extracted_data['metadata'],
            'sections_count': len(extracted_data['sections']),
            'tables_count': len(extracted_data['tables']),
            'text_length': len(extracted_data['text']),
            'pages_count': len(extracted_data['pages'])
        }
        
        output_file = Path(output_path)
        output_file.parent.mkdir(parents=True, exist_ok=True)
        
        with open(output_file, 'w', encoding='utf-8') as f:
            json.dump(summary, f, indent=2)
        
        logger.info(f"Saved extraction summary to: {output_path}")


def main():
    """Example usage"""
    processor = RegulatoryPDFProcessor()
    
    # Example: process a PDF
    pdf_path = "path/to/your/regulation.pdf"
    
    if os.path.exists(pdf_path):
        result = processor.process_pdf(pdf_path)
        
        print(f"\n✅ Successfully processed PDF:")
        print(f"   Pages: {result['metadata']['page_count']}")
        print(f"   Text length: {len(result['text'])} characters")
        print(f"   Sections: {len(result['sections'])}")
        print(f"   Tables: {len(result['tables'])}")
        
        # Show first 500 characters
        print(f"\nFirst 500 characters:")
        print(result['text'][:500])
    else:
        print(f"❌ PDF not found: {pdf_path}")
        print("\nTo test:")
        print("1. Download a regulatory PDF from CFPB, FinCEN, or FDIC")
        print("2. Update the pdf_path variable above")
        print("3. Run: python pdf_processor.py")


if __name__ == "__main__":
    main()