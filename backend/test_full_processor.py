"""
Complete Regulatory Document Processor

Integrates PDF processing and requirement extraction.
Run this to process a full regulatory document end-to-end.
"""

import os
import sys
import json
from pathlib import Path
from datetime import datetime

# Add parent directory to path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from app.pdf_processor import RegulatoryPDFProcessor
from app.requirement_extractor import RequirementExtractor


def process_regulation(pdf_path: str, output_dir: str = "./output"):
    """
    Process a regulatory PDF end-to-end.
    
    Steps:
    1. Extract text and structure from PDF
    2. Extract metadata using Claude
    3. Extract requirements section by section
    4. Save results
    
    Args:
        pdf_path: Path to regulatory PDF
        output_dir: Where to save results
    """
    
    print("\n" + "=" * 70)
    print("📄 COMPLIANCE AI - REGULATORY DOCUMENT PROCESSOR")
    print("=" * 70)
    
    # Verify file exists
    if not os.path.exists(pdf_path):
        print(f"\n❌ Error: PDF not found at {pdf_path}")
        print("\nTo get started:")
        print("1. Download a regulatory PDF from:")
        print("   - CFPB: https://www.consumerfinance.gov/policy-compliance/rulemaking/")
        print("   - FinCEN: https://www.fincen.gov/resources/statutes-and-regulations")
        print("   - FDIC: https://www.fdic.gov/regulations/laws/rules/")
        print("\n2. Save it and update the pdf_path in this script")
        return
    
    # Create output directory
    output_path = Path(output_dir)
    output_path.mkdir(parents=True, exist_ok=True)
    
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    file_name = Path(pdf_path).stem
    
    print(f"\n📁 Processing: {Path(pdf_path).name}")
    print(f"💾 Output directory: {output_dir}")
    
    # Step 1: Process PDF
    print("\n" + "-" * 70)
    print("STEP 1: PDF Processing")
    print("-" * 70)
    
    processor = RegulatoryPDFProcessor()
    pdf_data = processor.process_pdf(pdf_path)
    
    print(f"\n✅ PDF processed successfully:")
    print(f"   • Pages: {pdf_data['metadata']['page_count']}")
    print(f"   • Text length: {len(pdf_data['text']):,} characters")
    print(f"   • Sections detected: {len(pdf_data['sections'])}")
    print(f"   • Tables found: {len(pdf_data['tables'])}")
    
    # Step 2: Extract metadata
    print("\n" + "-" * 70)
    print("STEP 2: Metadata Extraction (Claude Haiku)")
    print("-" * 70)
    
    extractor = RequirementExtractor()
    
    # Use first few pages for metadata
    first_pages = processor.get_first_pages(pdf_path, num_pages=3)
    metadata = extractor.extract_metadata(first_pages)
    
    print(f"\n✅ Metadata extracted:")
    print(f"   • Title: {metadata.get('title', 'Unknown')[:60]}...")
    print(f"   • Agency: {metadata.get('agency', 'Unknown')}")
    print(f"   • Type: {metadata.get('document_type', 'Unknown')}")
    print(f"   • Effective Date: {metadata.get('effective_date', 'Unknown')}")
    print(f"   • Topics: {', '.join(metadata.get('topics', [])[:3])}")
    
    # Step 3: Extract requirements
    print("\n" + "-" * 70)
    print("STEP 3: Requirement Extraction (Claude Sonnet)")
    print("-" * 70)
    print("\nProcessing document sections...")
    
    # Process in chunks (limit to first 5 sections for demo to save costs)
    max_sections = 5
    all_requirements = extractor.extract_full_document_requirements(
        pdf_data['text'],
        metadata,
        max_sections=max_sections
    )
    
    # Aggregate statistics
    total_obligations = sum(len(r['obligations']) for r in all_requirements)
    total_prohibitions = sum(len(r['prohibitions']) for r in all_requirements)
    total_deadlines = sum(len(r['deadlines']) for r in all_requirements)
    total_definitions = sum(len(r['definitions']) for r in all_requirements)
    
    print(f"\n✅ Requirements extracted from {len(all_requirements)} sections:")
    print(f"   • Obligations (MUST): {total_obligations}")
    print(f"   • Prohibitions (MUST NOT): {total_prohibitions}")
    print(f"   • Deadlines: {total_deadlines}")
    print(f"   • Definitions: {total_definitions}")
    
    # Show sample obligation
    if total_obligations > 0:
        for reqs in all_requirements:
            if reqs['obligations']:
                sample = reqs['obligations'][0]
                print(f"\n   📋 Example obligation:")
                print(f"      {sample.get('plain_language', 'N/A')[:100]}...")
                break
    
    # Step 4: Save results
    print("\n" + "-" * 70)
    print("STEP 4: Saving Results")
    print("-" * 70)
    
    # Save metadata
    metadata_file = output_path / f"{file_name}_metadata_{timestamp}.json"
    with open(metadata_file, 'w') as f:
        json.dump(metadata, f, indent=2)
    print(f"\n💾 Saved metadata: {metadata_file.name}")
    
    # Save requirements
    requirements_file = output_path / f"{file_name}_requirements_{timestamp}.json"
    extractor.save_requirements(all_requirements, str(requirements_file))
    print(f"💾 Saved requirements: {requirements_file.name}")
    
    # Save summary report
    summary = {
        'document': {
            'file_name': Path(pdf_path).name,
            'processed_at': timestamp,
            **metadata
        },
        'statistics': {
            'pages': pdf_data['metadata']['page_count'],
            'text_length': len(pdf_data['text']),
            'sections_analyzed': len(all_requirements),
            'obligations': total_obligations,
            'prohibitions': total_prohibitions,
            'deadlines': total_deadlines,
            'definitions': total_definitions
        }
    }
    
    summary_file = output_path / f"{file_name}_summary_{timestamp}.json"
    with open(summary_file, 'w') as f:
        json.dump(summary, f, indent=2)
    print(f"💾 Saved summary: {summary_file.name}")
    
    # Final summary
    print("\n" + "=" * 70)
    print("✅ PROCESSING COMPLETE!")
    print("=" * 70)
    
    print(f"\n📊 Summary:")
    print(f"   Document: {metadata.get('title', 'Unknown')[:50]}...")
    print(f"   Agency: {metadata.get('agency', 'Unknown')}")
    print(f"   Analyzed: {len(all_requirements)} sections")
    print(f"   Found: {total_obligations} obligations, {total_prohibitions} prohibitions")
    
    print(f"\n💡 Next steps:")
    print(f"   1. Review the requirements in: {requirements_file.name}")
    print(f"   2. Next: Build the RAG system to compare against policies")
    print(f"   3. Then: Implement conflict detection")
    
    return {
        'metadata': metadata,
        'requirements': all_requirements,
        'summary': summary
    }


def main():
    """
    Main entry point.
    
    Usage:
        python test_full_processor.py /path/to/regulation.pdf
    """
    
    # Check for PDF path argument
    if len(sys.argv) > 1:
        pdf_path = sys.argv[1]
    else:
        # Default path (update this!)
        pdf_path = "./data/regulations/sample_regulation.pdf"
        
        print("\n💡 Usage: python test_full_processor.py /path/to/regulation.pdf")
        print(f"   Using default path: {pdf_path}")
    
    # Check for API key
    if not os.getenv("ANTHROPIC_API_KEY"):
        print("\n❌ Error: ANTHROPIC_API_KEY not found!")
        print("\nPlease:")
        print("1. Create a .env file in the project root")
        print("2. Add: ANTHROPIC_API_KEY=your_api_key_here")
        print("3. Get a key from: https://console.anthropic.com/")
        return
    
    # Process the regulation
    try:
        result = process_regulation(pdf_path)
        
        if result:
            print(f"\n🎉 Success! Check the output/ directory for results.")
            
    except Exception as e:
        print(f"\n❌ Error processing document: {e}")
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    main()