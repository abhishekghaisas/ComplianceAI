"""
Complete Week 1 Processor - Days 1-7 Integration

Full-featured regulatory document processor with:
✅ PDF processing (Days 1-2)
✅ Requirement extraction (Days 1-2)
✅ Entity extraction (Days 3-4)
✅ Quality validation (Days 3-4)
✅ Document structure analysis (Days 5-6)
✅ Multi-format export (Day 7)
"""

import os
import sys
import json
from pathlib import Path
from datetime import datetime
from typing import Dict, List, Optional

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from backend.app.week1.pdf_processor import RegulatoryPDFProcessor
from backend.app.week1.requirement_extractor import RequirementExtractor
from backend.app.week1.entity_extractor import EntityExtractor
from backend.app.week1.structure_analyzer import DocumentStructureAnalyzer
from backend.app.week1.export_utils import ReportExporter


def validate_extraction(metadata: Dict, requirements: List[Dict], entities: Dict) -> Dict:
    """
    Validate extraction quality and assign scores.
    
    Returns:
        Dictionary with quality scores and issues
    """
    issues = []
    
    # Metadata completeness (0-100)
    metadata_fields = ['agency', 'document_type', 'title', 'publication_date', 
                      'effective_date', 'topics', 'summary']
    filled_fields = sum(1 for f in metadata_fields if metadata.get(f))
    metadata_score = int((filled_fields / len(metadata_fields)) * 100)
    
    if not metadata.get('effective_date'):
        issues.append("Effective date not found in metadata")
    if not metadata.get('publication_date'):
        issues.append("Publication date not found")
    if not metadata.get('topics') or len(metadata.get('topics', [])) < 2:
        issues.append("Insufficient topics extracted (<2)")
    
    # Requirements quality (0-100)
    total_items = sum(
        len(r.get('obligations', [])) + 
        len(r.get('prohibitions', [])) + 
        len(r.get('deadlines', [])) 
        for r in requirements
    )
    
    # Base score on quantity (rough proxy for quality)
    if total_items >= 20:
        requirements_score = 100
    elif total_items >= 10:
        requirements_score = 80
    elif total_items >= 5:
        requirements_score = 60
    else:
        requirements_score = 40
        issues.append("Low number of requirements extracted (<5)")
    
    # Entity extraction richness (0-100)
    entity_counts = {
        'dates': len(entities.get('dates', [])),
        'amounts': len(entities.get('dollar_amounts', [])),
        'agencies': len(entities.get('agencies', [])),
        'citations': len(entities.get('legal_citations', []))
    }
    
    total_entities = sum(entity_counts.values())
    
    if total_entities >= 50:
        entity_score = 100
    elif total_entities >= 30:
        entity_score = 80
    elif total_entities >= 15:
        entity_score = 60
    else:
        entity_score = 40
        issues.append("Low entity extraction count (<15)")
    
    # Overall score (weighted average)
    overall_score = int(
        (metadata_score * 0.3) + 
        (requirements_score * 0.5) + 
        (entity_score * 0.2)
    )
    
    # Determine grade
    if overall_score >= 95:
        grade = "A+"
    elif overall_score >= 90:
        grade = "A"
    elif overall_score >= 85:
        grade = "A-"
    elif overall_score >= 80:
        grade = "B+"
    elif overall_score >= 75:
        grade = "B"
    else:
        grade = "B-"
    
    return {
        'overall_score': overall_score,
        'metadata_score': metadata_score,
        'requirements_score': requirements_score,
        'entity_score': entity_score,
        'details': {
            'metadata_fields_filled': f"{filled_fields}/{len(metadata_fields)}",
            'total_requirements': total_items,
            'total_entities': total_entities,
            'entity_breakdown': entity_counts
        },
        'issues': issues,
        'grade': grade
    }


def process_regulation_complete(pdf_path: str, output_dir: str = "./output_week1"):
    """
    Complete Week 1 processing pipeline.
    
    All features from Days 1-7:
    - PDF extraction
    - Metadata extraction (Claude)
    - Requirement extraction (Claude)
    - Entity extraction (Regex/NLP)
    - Structure analysis
    - Quality validation
    - Multi-format export (HTML, DOCX, MD)
    """
    
    print("\n" + "=" * 80)
    print("📄 COMPLIANCE AI - COMPLETE WEEK 1 PROCESSOR (Days 1-7)")
    print("=" * 80)
    
    if not os.path.exists(pdf_path):
        print(f"\n❌ Error: PDF not found at {pdf_path}")
        return
    
    # Create output directory
    output_path = Path(output_dir)
    output_path.mkdir(parents=True, exist_ok=True)
    
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    file_name = Path(pdf_path).stem
    
    print(f"\n📁 Input: {Path(pdf_path).name}")
    print(f"💾 Output: {output_dir}/")
    print(f"⏰ Started: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    
    results = {}
    
    # ========================================================================
    # STEP 1: PDF PROCESSING (Days 1-2)
    # ========================================================================
    print("\n" + "─" * 80)
    print("STEP 1/7: PDF Processing")
    print("─" * 80)
    
    processor = RegulatoryPDFProcessor()
    pdf_data = processor.process_pdf(pdf_path)
    
    print(f"\n✅ PDF extracted:")
    print(f"   • Pages: {pdf_data['metadata']['page_count']}")
    print(f"   • Characters: {len(pdf_data['text']):,}")
    print(f"   • Sections detected: {len(pdf_data['sections'])}")
    print(f"   • Tables found: {len(pdf_data['tables'])}")
    
    results['pdf_data'] = {
        'pages': pdf_data['metadata']['page_count'],
        'characters': len(pdf_data['text']),
        'sections': len(pdf_data['sections']),
        'tables': len(pdf_data['tables'])
    }
    
    # ========================================================================
    # STEP 2: METADATA EXTRACTION (Days 1-2)
    # ========================================================================
    print("\n" + "─" * 80)
    print("STEP 2/7: Metadata Extraction (Claude Haiku)")
    print("─" * 80)
    
    extractor = RequirementExtractor()
    first_pages = processor.get_first_pages(pdf_path, num_pages=3)
    metadata = extractor.extract_metadata(first_pages)
    
    if metadata and metadata.get('title'):
        print(f"\n✅ Metadata:")
        print(f"   • Title: {metadata.get('title', 'Unknown')[:65]}...")
        print(f"   • Agency: {metadata.get('agency', 'Unknown')}")
        print(f"   • Type: {metadata.get('document_type', 'Unknown')}")
        print(f"   • Published: {metadata.get('publication_date', 'Unknown')}")
        print(f"   • Effective: {metadata.get('effective_date', 'TBD')}")
    else:
        print("\n⚠️  Metadata extraction issues")
        metadata = {}
    
    results['metadata'] = metadata
    
    # ========================================================================
    # STEP 3: REQUIREMENT EXTRACTION (Days 1-2)
    # ========================================================================
    print("\n" + "─" * 80)
    print("STEP 3/7: Requirement Extraction (Claude Sonnet)")
    print("─" * 80)
    print("\nProcessing sections (limited to 5 for cost control)...")
    
    all_requirements = extractor.extract_full_document_requirements(
        pdf_data['text'],
        metadata,
        max_sections=5
    )
    
    total_obligations = sum(len(r['obligations']) for r in all_requirements)
    total_prohibitions = sum(len(r['prohibitions']) for r in all_requirements)
    total_deadlines = sum(len(r['deadlines']) for r in all_requirements)
    total_definitions = sum(len(r['definitions']) for r in all_requirements)
    
    print(f"\n✅ Requirements:")
    print(f"   • Obligations: {total_obligations}")
    print(f"   • Prohibitions: {total_prohibitions}")
    print(f"   • Deadlines: {total_deadlines}")
    print(f"   • Definitions: {total_definitions}")
    
    results['requirements'] = {
        'obligations': total_obligations,
        'prohibitions': total_prohibitions,
        'deadlines': total_deadlines,
        'definitions': total_definitions
    }
    
    # ========================================================================
    # STEP 4: ENTITY EXTRACTION (Days 3-4) ⭐
    # ========================================================================
    print("\n" + "─" * 80)
    print("STEP 4/7: Entity Extraction (Regex/NLP) ⭐ NEW")
    print("─" * 80)
    
    entity_extractor = EntityExtractor()
    entities = entity_extractor.extract_all_entities(pdf_data['text'])
    
    print(f"\n✅ Entities:")
    print(f"   • Dates: {len(entities['dates'])}")
    print(f"   • Dollar amounts: {len(entities['dollar_amounts'])}")
    print(f"   • Percentages: {len(entities['percentages'])}")
    print(f"   • Agencies: {len(entities['agencies'])}")
    print(f"   • Legal citations: {len(entities['legal_citations'])}")
    
    # Show highlights
    if entities['agencies']:
        print(f"\n   Top agencies:")
        for agency in sorted(entities['agencies'], key=lambda x: x['count'], reverse=True)[:3]:
            print(f"      • {agency['agency']}: {agency['count']} mentions")
    
    results['entities'] = {
        'dates': len(entities['dates']),
        'amounts': len(entities['dollar_amounts']),
        'agencies': len(entities['agencies']),
        'citations': len(entities['legal_citations'])
    }
    
    # ========================================================================
    # STEP 5: STRUCTURE ANALYSIS (Days 5-6) ⭐
    # ========================================================================
    print("\n" + "─" * 80)
    print("STEP 5/7: Document Structure Analysis ⭐ NEW")
    print("─" * 80)
    
    structure_analyzer = DocumentStructureAnalyzer()
    structure = structure_analyzer.analyze_structure(pdf_data['text'])
    
    print(f"\n✅ Structure:")
    print(f"   • Total sections: {structure['statistics']['total_sections']}")
    print(f"   • Max depth: {structure['statistics']['max_depth']}")
    print(f"   • Cross-references: {len(structure['cross_references'])}")
    
    # Show key sections
    print(f"\n   Key sections identified:")
    for category, sections in structure['key_sections'].items():
        if sections:
            print(f"      • {category}: {len(sections)} section(s)")
    
    results['structure'] = structure['statistics']
    
    # ========================================================================
    # STEP 6: QUALITY VALIDATION (Days 3-4) ⭐
    # ========================================================================
    print("\n" + "─" * 80)
    print("STEP 6/7: Quality Validation ⭐ NEW")
    print("─" * 80)
    
    quality = validate_extraction(metadata, all_requirements, entities)
    
    print(f"\n✅ Quality Assessment:")
    print(f"   • Overall Score: {quality['overall_score']}/100 ({quality['grade']})")
    print(f"   • Metadata: {quality['metadata_score']}/100")
    print(f"   • Requirements: {quality['requirements_score']}/100")
    print(f"   • Entities: {quality['entity_score']}/100")
    
    if quality['issues']:
        print(f"\n   ⚠️  Issues ({len(quality['issues'])}):")
        for issue in quality['issues'][:3]:
            print(f"      • {issue}")
    
    results['quality'] = quality
    
    # ========================================================================
    # STEP 7: EXPORT REPORTS (Day 7) ⭐
    # ========================================================================
    print("\n" + "─" * 80)
    print("STEP 7/7: Generating Reports ⭐ NEW")
    print("─" * 80)
    
    exporter = ReportExporter()
    
    # Generate HTML report
    print("\n📄 Generating HTML report...")
    html_file = output_path / f"{file_name}_report_{timestamp}.html"
    exporter.export_html_report(metadata, all_requirements, entities, str(html_file))
    print(f"   ✅ {html_file.name}")
    
    # Generate Markdown report
    print("\n📝 Generating Markdown report...")
    md_file = output_path / f"{file_name}_report_{timestamp}.md"
    exporter.export_markdown_report(metadata, all_requirements, entities, str(md_file))
    print(f"   ✅ {md_file.name}")
    
    # Generate DOCX executive summary
    print("\n📋 Generating Executive Summary (DOCX)...")
    docx_file = output_path / f"{file_name}_executive_summary_{timestamp}.docx"
    exporter.export_executive_summary_docx(metadata, all_requirements, entities, str(docx_file))
    print(f"   ✅ {docx_file.name}")
    
    # ========================================================================
    # SAVE JSON DATA
    # ========================================================================
    print("\n" + "─" * 80)
    print("Saving JSON Data Files")
    print("─" * 80)
    
    # Save metadata
    with open(output_path / f"{file_name}_metadata_{timestamp}.json", 'w') as f:
        json.dump(metadata, f, indent=2)
    print(f"\n💾 {file_name}_metadata_{timestamp}.json")
    
    # Save requirements
    with open(output_path / f"{file_name}_requirements_{timestamp}.json", 'w') as f:
        json.dump(all_requirements, f, indent=2)
    print(f"💾 {file_name}_requirements_{timestamp}.json")
    
    # Save entities
    with open(output_path / f"{file_name}_entities_{timestamp}.json", 'w') as f:
        json.dump(entities, f, indent=2)
    print(f"💾 {file_name}_entities_{timestamp}.json")
    
    # Save structure
    # Convert DocumentSection objects to dicts for JSON
    structure_json = {
        'table_of_contents': structure['table_of_contents'],
        'statistics': structure['statistics'],
        'key_sections': structure['key_sections']
    }
    with open(output_path / f"{file_name}_structure_{timestamp}.json", 'w') as f:
        json.dump(structure_json, f, indent=2)
    print(f"💾 {file_name}_structure_{timestamp}.json")
    
    # Save quality
    with open(output_path / f"{file_name}_quality_{timestamp}.json", 'w') as f:
        json.dump(quality, f, indent=2)
    print(f"💾 {file_name}_quality_{timestamp}.json")
    
    # Save comprehensive summary
    summary = {
        'document': {
            'file_name': Path(pdf_path).name,
            'processed_at': timestamp,
            **metadata
        },
        'analysis': {
            **results['pdf_data'],
            **results['requirements'],
            **results['entities'],
            **results['structure']
        },
        'quality': quality,
        'outputs': {
            'html_report': html_file.name,
            'markdown_report': md_file.name,
            'executive_summary': docx_file.name,
            'json_files': 5
        }
    }
    
    with open(output_path / f"{file_name}_COMPLETE_summary_{timestamp}.json", 'w') as f:
        json.dump(summary, f, indent=2)
    print(f"💾 {file_name}_COMPLETE_summary_{timestamp}.json")
    
    # ========================================================================
    # FINAL SUMMARY
    # ========================================================================
    print("\n" + "=" * 80)
    print("✅ WEEK 1 COMPLETE PROCESSING FINISHED!")
    print("=" * 80)
    
    print(f"\n📊 Analysis Results:")
    print(f"   Document: {metadata.get('title', 'Unknown')[:60]}...")
    print(f"   Agency: {metadata.get('agency', 'Unknown')}")
    print(f"   Pages: {pdf_data['metadata']['page_count']}")
    
    print(f"\n📈 Extracted:")
    print(f"   • {total_obligations} obligations")
    print(f"   • {total_prohibitions} prohibitions")
    print(f"   • {total_deadlines} deadlines")
    print(f"   • {len(entities['dates'])} dates")
    print(f"   • {len(entities['dollar_amounts'])} dollar amounts")
    print(f"   • {len(entities['agencies'])} agencies")
    
    print(f"\n⭐ Quality Score: {quality['overall_score']}/100 ({quality['grade']})")
    
    print(f"\n📁 Generated Files ({output_dir}/):")
    print(f"   JSON Data:")
    print(f"      • metadata, requirements, entities, structure, quality")
    print(f"   Reports:")
    print(f"      • HTML report (open in browser)")
    print(f"      • Markdown report (view in editor)")
    print(f"      • DOCX executive summary (open in Word)")
    
    print(f"\n💡 Next Steps:")
    print(f"   1. Review HTML report: open {html_file.name} in browser")
    print(f"   2. Check quality issues in quality JSON")
    print(f"   3. Verify accuracy against original PDF")
    print(f"   4. Ready for Week 2: RAG system!")
    
    print(f"\n🎉 Week 1 (Days 1-7) COMPLETE!")
    
    return {
        'metadata': metadata,
        'requirements': all_requirements,
        'entities': entities,
        'structure': structure,
        'quality': quality,
        'summary': summary
    }


def main():
    """Main entry point."""
    
    if len(sys.argv) > 1:
        pdf_path = sys.argv[1]
    else:
        pdf_path = "../data/regulations/cfpb_section_1071_2026.pdf"
        print(f"\n💡 Usage: python week1_complete_processor.py /path/to/regulation.pdf")
        print(f"   Using default: {pdf_path}")
    
    # Check API key
    if not os.getenv("ANTHROPIC_API_KEY"):
        print("\n❌ Error: ANTHROPIC_API_KEY not found!")
        return
    
    # Process
    try:
        start_time = datetime.now()
        
        result = process_regulation_complete(pdf_path)
        
        end_time = datetime.now()
        duration = (end_time - start_time).total_seconds()
        
        if result:
            print(f"\n⏱️  Processing time: {duration:.1f} seconds")
            print(f"💰 Estimated cost: ~$0.15-0.20")
            print(f"\n✨ All Week 1 features demonstrated!")
            
    except Exception as e:
        print(f"\n❌ Error: {e}")
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    main()