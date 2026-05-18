"""
Entity Extractor - Extract specific entities from regulatory text

Extracts:
- Dates (effective dates, deadlines, comment periods)
- Dollar amounts (thresholds, penalties, fees)
- Percentages and numbers (25%, 1,000 transactions)
- Agency names (CFPB, FinCEN, FDIC, OCC)
- Legal citations (12 CFR 1002, 15 U.S.C. 1691)
- Thresholds and numerical criteria
"""

import re
import logging
from typing import Dict, List, Optional, Tuple
from datetime import datetime
from dateutil import parser as date_parser

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class EntityExtractor:
    """
    Extract structured entities from regulatory text.
    
    Uses regex patterns and NLP techniques to identify:
    - Temporal entities (dates, deadlines)
    - Monetary entities (dollar amounts, penalties)
    - Numerical entities (percentages, thresholds)
    - Named entities (agencies, legal citations)
    """
    
    def __init__(self):
        # Agency patterns
        self.agency_patterns = {
            'CFPB': r'\b(?:Consumer Financial Protection Bureau|CFPB)\b',
            'FinCEN': r'\b(?:Financial Crimes Enforcement Network|FinCEN)\b',
            'FDIC': r'\b(?:Federal Deposit Insurance Corporation|FDIC)\b',
            'OCC': r'\b(?:Office of the Comptroller of the Currency|OCC)\b',
            'Federal Reserve': r'\b(?:Federal Reserve|Board of Governors)\b',
            'SEC': r'\b(?:Securities and Exchange Commission|SEC)\b',
            'NCUA': r'\b(?:National Credit Union Administration|NCUA)\b',
            'FCA': r'\b(?:Farm Credit Administration|FCA)\b',
            'SBA': r'\b(?:Small Business Administration|SBA)\b'
        }
        
        # Legal citation patterns
        self.citation_patterns = {
            'CFR': r'\b\d+\s+CFR\s+(?:Part\s+)?\d+(?:\.\d+)*\b',
            'USC': r'\b\d+\s+U\.?S\.?C\.?\s+§?\s*\d+[a-z]?(?:-\d+)*\b',
            'Public_Law': r'\bPublic Law\s+\d+-\d+\b',
            'Executive_Order': r'\b(?:Executive Order|E\.O\.)\s+\d+\b'
        }
    
    def extract_all_entities(self, text: str) -> Dict:
        """
        Extract all entities from text.
        
        Args:
            text: Regulatory text to analyze
            
        Returns:
            Dictionary with all extracted entities
        """
        return {
            'dates': self.extract_dates(text),
            'dollar_amounts': self.extract_dollar_amounts(text),
            'percentages': self.extract_percentages(text),
            'numbers': self.extract_numbers(text),
            'agencies': self.extract_agencies(text),
            'legal_citations': self.extract_legal_citations(text),
            'thresholds': self.extract_thresholds(text)
        }
    
    def extract_dates(self, text: str) -> List[Dict]:
        """
        Extract dates from text.
        
        Finds patterns like:
        - "January 1, 2028"
        - "2026-06-30"
        - "June 30, 2026"
        - "effective on July 1, 2027"
        
        Returns:
            List of date dictionaries with context
        """
        dates = []
        
        # Common date patterns
        patterns = [
            # Month Day, Year
            r'\b(?:January|February|March|April|May|June|July|August|September|October|November|December)\s+\d{1,2},?\s+\d{4}\b',
            # YYYY-MM-DD
            r'\b\d{4}-\d{2}-\d{2}\b',
            # MM/DD/YYYY
            r'\b\d{1,2}/\d{1,2}/\d{4}\b'
        ]
        
        for pattern in patterns:
            matches = re.finditer(pattern, text, re.IGNORECASE)
            
            for match in matches:
                date_str = match.group()
                
                # Try to parse to validate
                try:
                    parsed_date = date_parser.parse(date_str)
                    
                    # Get context (50 chars before and after)
                    start = max(0, match.start() - 50)
                    end = min(len(text), match.end() + 50)
                    context = text[start:end].strip()
                    
                    # Classify type of date
                    date_type = self._classify_date_type(context)
                    
                    dates.append({
                        'date': parsed_date.strftime('%Y-%m-%d'),
                        'original_format': date_str,
                        'type': date_type,
                        'context': context,
                        'position': match.start()
                    })
                    
                except Exception as e:
                    logger.debug(f"Could not parse date: {date_str}")
                    continue
        
        # Remove duplicates (same date, similar position)
        dates = self._deduplicate_dates(dates)
        
        return dates
    
    def _classify_date_type(self, context: str) -> str:
        """Classify what type of date this is based on context."""
        context_lower = context.lower()
        
        if any(word in context_lower for word in ['effective', 'takes effect']):
            return 'effective_date'
        elif any(word in context_lower for word in ['compliance', 'comply by', 'must comply']):
            return 'compliance_date'
        elif any(word in context_lower for word in ['deadline', 'due by', 'by when']):
            return 'deadline'
        elif any(word in context_lower for word in ['comment', 'comments close']):
            return 'comment_deadline'
        elif any(word in context_lower for word in ['publish', 'released', 'issued']):
            return 'publication_date'
        else:
            return 'general_date'
    
    def _deduplicate_dates(self, dates: List[Dict]) -> List[Dict]:
        """Remove duplicate dates that are close together in text."""
        if not dates:
            return []
        
        # Sort by position
        dates = sorted(dates, key=lambda x: x['position'])
        
        unique_dates = []
        for date in dates:
            # Check if similar date already exists
            is_duplicate = False
            for existing in unique_dates:
                # Same date within 100 characters = duplicate
                if (existing['date'] == date['date'] and 
                    abs(existing['position'] - date['position']) < 100):
                    is_duplicate = True
                    break
            
            if not is_duplicate:
                unique_dates.append(date)
        
        return unique_dates
    
    def extract_dollar_amounts(self, text: str) -> List[Dict]:
        """
        Extract dollar amounts from text.
        
        Finds patterns like:
        - "$1 million"
        - "$500,000"
        - "$10 billion"
        - "500K penalty"
        
        Returns:
            List of dollar amount dictionaries
        """
        amounts = []
        
        # Patterns for dollar amounts
        patterns = [
            # $X million/billion/trillion
            (r'\$\s*(\d+(?:\.\d+)?)\s*(million|billion|trillion)', 'word_suffix'),
            # $XXX,XXX or $XXX,XXX.XX
            (r'\$\s*(\d{1,3}(?:,\d{3})*(?:\.\d{2})?)', 'numeric'),
            # XXX million dollars
            (r'(\d+(?:\.\d+)?)\s*(million|billion|trillion)\s+dollars?', 'word_suffix')
        ]
        
        for pattern, pattern_type in patterns:
            matches = re.finditer(pattern, text, re.IGNORECASE)
            
            for match in matches:
                # Get context
                start = max(0, match.start() - 60)
                end = min(len(text), match.end() + 60)
                context = text[start:end].strip()
                
                # Parse amount
                if pattern_type == 'word_suffix':
                    number = float(match.group(1))
                    suffix = match.group(2).lower()
                    
                    multipliers = {
                        'million': 1_000_000,
                        'billion': 1_000_000_000,
                        'trillion': 1_000_000_000_000
                    }
                    
                    amount_value = number * multipliers[suffix]
                    amount_str = match.group()
                    
                elif pattern_type == 'numeric':
                    # Remove commas and parse
                    amount_str = match.group()
                    amount_value = float(match.group(1).replace(',', ''))
                
                # Classify amount type
                amount_type = self._classify_amount_type(context)
                
                amounts.append({
                    'amount': amount_value,
                    'formatted': amount_str,
                    'type': amount_type,
                    'context': context,
                    'position': match.start()
                })
        
        # Deduplicate
        amounts = self._deduplicate_amounts(amounts)
        
        return amounts
    
    def _classify_amount_type(self, context: str) -> str:
        """Classify what type of dollar amount this is."""
        context_lower = context.lower()
        
        if any(word in context_lower for word in ['penalty', 'fine', 'violation']):
            return 'penalty'
        elif any(word in context_lower for word in ['threshold', 'limit', 'maximum', 'minimum']):
            return 'threshold'
        elif any(word in context_lower for word in ['revenue', 'gross annual revenue']):
            return 'revenue_threshold'
        elif any(word in context_lower for word in ['asset', 'total assets']):
            return 'asset_threshold'
        elif any(word in context_lower for word in ['cost', 'expense', 'fee']):
            return 'cost'
        else:
            return 'amount'
    
    def _deduplicate_amounts(self, amounts: List[Dict]) -> List[Dict]:
        """Remove duplicate amounts close together."""
        if not amounts:
            return []
        
        amounts = sorted(amounts, key=lambda x: x['position'])
        
        unique_amounts = []
        for amount in amounts:
            is_duplicate = False
            for existing in unique_amounts:
                # Same amount within 50 characters = duplicate
                if (existing['amount'] == amount['amount'] and 
                    abs(existing['position'] - amount['position']) < 50):
                    is_duplicate = True
                    break
            
            if not is_duplicate:
                unique_amounts.append(amount)
        
        return unique_amounts
    
    def extract_percentages(self, text: str) -> List[Dict]:
        """
        Extract percentages from text.
        
        Finds: "25%", "50 percent", "3.5%"
        """
        percentages = []
        
        # Pattern for percentages
        pattern = r'\b(\d+(?:\.\d+)?)\s*(?:%|percent)\b'
        
        matches = re.finditer(pattern, text, re.IGNORECASE)
        
        for match in matches:
            # Get context
            start = max(0, match.start() - 60)
            end = min(len(text), match.end() + 60)
            context = text[start:end].strip()
            
            percentages.append({
                'percentage': float(match.group(1)),
                'formatted': match.group(),
                'context': context,
                'position': match.start()
            })
        
        return percentages
    
    def extract_numbers(self, text: str) -> List[Dict]:
        """
        Extract significant numbers (transaction counts, thresholds).
        
        Finds: "1,000 transactions", "100 loans", "500 applications"
        """
        numbers = []
        
        # Pattern for numbers with context
        pattern = r'\b(\d{1,3}(?:,\d{3})*)\s+(transactions?|loans?|applications?|originations?|institutions?)\b'
        
        matches = re.finditer(pattern, text, re.IGNORECASE)
        
        for match in matches:
            number_str = match.group(1)
            number_value = int(number_str.replace(',', ''))
            unit = match.group(2)
            
            # Get context
            start = max(0, match.start() - 60)
            end = min(len(text), match.end() + 60)
            context = text[start:end].strip()
            
            numbers.append({
                'number': number_value,
                'formatted': f"{number_str} {unit}",
                'unit': unit,
                'context': context,
                'position': match.start()
            })
        
        return numbers
    
    def extract_agencies(self, text: str) -> List[Dict]:
        """
        Extract agency names and count their occurrences.
        
        Returns:
            List of agencies with their frequency
        """
        agency_counts = {}
        agency_positions = {}
        
        for agency_name, pattern in self.agency_patterns.items():
            matches = list(re.finditer(pattern, text, re.IGNORECASE))
            
            if matches:
                agency_counts[agency_name] = len(matches)
                agency_positions[agency_name] = [m.start() for m in matches]
        
        # Convert to list
        agencies = []
        for agency, count in agency_counts.items():
            agencies.append({
                'agency': agency,
                'count': count,
                'first_mention': agency_positions[agency][0] if agency_positions[agency] else None
            })
        
        # Sort by first mention
        agencies = sorted(agencies, key=lambda x: x['first_mention'] or float('inf'))
        
        return agencies
    
    def extract_legal_citations(self, text: str) -> List[Dict]:
        """
        Extract legal citations (CFR, USC, Public Laws, Executive Orders).
        
        Examples:
        - "12 CFR 1002"
        - "15 U.S.C. 1691"
        - "Public Law 111-203"
        - "Executive Order 14168"
        """
        citations = []
        
        for citation_type, pattern in self.citation_patterns.items():
            matches = re.finditer(pattern, text, re.IGNORECASE)
            
            for match in matches:
                citation_text = match.group()
                
                # Get context
                start = max(0, match.start() - 80)
                end = min(len(text), match.end() + 80)
                context = text[start:end].strip()
                
                citations.append({
                    'citation': citation_text,
                    'type': citation_type,
                    'context': context,
                    'position': match.start()
                })
        
        # Deduplicate
        citations = self._deduplicate_citations(citations)
        
        return citations
    
    def _deduplicate_citations(self, citations: List[Dict]) -> List[Dict]:
        """Remove duplicate citations."""
        seen = set()
        unique = []
        
        for citation in citations:
            # Normalize citation text
            norm = citation['citation'].replace(' ', '').lower()
            
            if norm not in seen:
                seen.add(norm)
                unique.append(citation)
        
        return unique
    
    def extract_thresholds(self, text: str) -> List[Dict]:
        """
        Extract regulatory thresholds.
        
        Examples:
        - "at least 1,000 covered credit transactions"
        - "gross annual revenue of $1 million or less"
        - "25 percent or more of the equity"
        """
        thresholds = []
        
        # Pattern for "at least/more than X"
        patterns = [
            r'(?:at least|more than|fewer than|less than|exceeds?|below)\s+(\d{1,3}(?:,\d{3})*)\s+([a-z\s]+?)(?:\.|,|;|\n)',
            r'(\d{1,3}(?:,\d{3})*)\s+or (?:more|less|fewer)',
            r'(?:threshold of|limit of)\s+(\d{1,3}(?:,\d{3})*)'
        ]
        
        for pattern in patterns:
            matches = re.finditer(pattern, text, re.IGNORECASE)
            
            for match in matches:
                # Extract number
                try:
                    number_str = match.group(1)
                    number_value = int(number_str.replace(',', ''))
                    
                    # Get full match
                    full_text = match.group()
                    
                    # Get context
                    start = max(0, match.start() - 100)
                    end = min(len(text), match.end() + 100)
                    context = text[start:end].strip()
                    
                    thresholds.append({
                        'threshold_value': number_value,
                        'threshold_text': full_text,
                        'context': context,
                        'position': match.start()
                    })
                    
                except Exception as e:
                    logger.debug(f"Could not parse threshold: {match.group()}")
                    continue
        
        return thresholds
    
    def extract_key_dates_from_requirements(self, requirements: Dict) -> Dict:
        """
        Extract and organize key dates from requirement extraction output.
        
        Args:
            requirements: Output from RequirementExtractor
            
        Returns:
            Organized dict of key dates
        """
        all_dates = {
            'effective_dates': [],
            'compliance_dates': [],
            'deadlines': [],
            'publication_dates': []
        }
        
        # Extract from each section
        for section in requirements:
            # Get deadlines from deadline section
            for deadline in section.get('deadlines', []):
                date_entry = {
                    'date': deadline['date'],
                    'action': deadline['action'],
                    'who': deadline['who'],
                    'consequence': deadline.get('consequence', 'N/A')
                }
                
                # Classify
                action_lower = deadline['action'].lower()
                if 'effective' in action_lower:
                    all_dates['effective_dates'].append(date_entry)
                elif 'compliance' in action_lower or 'comply' in action_lower:
                    all_dates['compliance_dates'].append(date_entry)
                elif 'publish' in action_lower:
                    all_dates['publication_dates'].append(date_entry)
                else:
                    all_dates['deadlines'].append(date_entry)
        
        # Sort each category by date
        for category in all_dates:
            all_dates[category] = sorted(
                all_dates[category], 
                key=lambda x: x['date'] if x['date'] else '9999-99-99'
            )
        
        return all_dates
    
    def generate_entity_summary(self, entities: Dict) -> str:
        """
        Generate human-readable summary of extracted entities.
        
        Args:
            entities: Output from extract_all_entities()
            
        Returns:
            Formatted summary string
        """
        summary = []
        summary.append("📊 ENTITY EXTRACTION SUMMARY")
        summary.append("=" * 60)
        
        # Dates
        if entities.get('dates'):
            summary.append(f"\n📅 DATES: {len(entities['dates'])} found")
            
            # Group by type
            by_type = {}
            for date in entities['dates']:
                date_type = date['type']
                if date_type not in by_type:
                    by_type[date_type] = []
                by_type[date_type].append(date)
            
            for date_type, dates in sorted(by_type.items()):
                summary.append(f"   {date_type}: {len(dates)}")
                for d in dates[:3]:  # Show first 3
                    summary.append(f"      • {d['date']}: {d['context'][:60]}...")
        
        # Dollar amounts
        if entities.get('dollar_amounts'):
            summary.append(f"\n💰 DOLLAR AMOUNTS: {len(entities['dollar_amounts'])} found")
            
            # Show largest amounts
            sorted_amounts = sorted(
                entities['dollar_amounts'], 
                key=lambda x: x['amount'], 
                reverse=True
            )[:5]
            
            for amt in sorted_amounts:
                summary.append(f"   • {amt['formatted']} ({amt['type']})")
                summary.append(f"      {amt['context'][:70]}...")
        
        # Percentages
        if entities.get('percentages'):
            summary.append(f"\n📊 PERCENTAGES: {len(entities['percentages'])} found")
            for pct in entities['percentages'][:5]:
                summary.append(f"   • {pct['formatted']}")
        
        # Agencies
        if entities.get('agencies'):
            summary.append(f"\n🏛️ AGENCIES: {len(entities['agencies'])} found")
            for agency in entities['agencies']:
                summary.append(f"   • {agency['agency']}: {agency['count']} mentions")
        
        # Legal citations
        if entities.get('legal_citations'):
            summary.append(f"\n📖 LEGAL CITATIONS: {len(entities['legal_citations'])} found")
            
            # Group by type
            by_type = {}
            for citation in entities['legal_citations']:
                ctype = citation['type']
                if ctype not in by_type:
                    by_type[ctype] = []
                by_type[ctype].append(citation['citation'])
            
            for ctype, cites in sorted(by_type.items()):
                summary.append(f"   {ctype}: {len(cites)}")
                for c in list(set(cites))[:3]:  # Unique, first 3
                    summary.append(f"      • {c}")
        
        summary.append("\n" + "=" * 60)
        
        return "\n".join(summary)


def main():
    """Test the entity extractor."""
    
    # Sample regulatory text
    sample_text = """
    The compliance date for the rule is January 1, 2028. This final rule is 
    effective on June 30, 2026.
    
    Financial institutions that originated at least 1,000 covered credit transactions 
    for small businesses in each of the two preceding calendar years must comply.
    
    The Bureau is changing the gross annual revenue threshold from $5 million or 
    less to $1 million or less. Violations may result in penalties up to $500,000.
    
    This implements section 1071 of the Dodd-Frank Act, codified at 15 U.S.C. 1691c-2, 
    and amends 12 CFR Part 1002 (Regulation B).
    
    The CFPB consulted with the Federal Reserve, FDIC, and OCC regarding this rule.
    An individual who owns 25 percent or more of the equity is a principal owner.
    """
    
    print("\n🧪 Testing Entity Extractor\n")
    print("=" * 70)
    
    extractor = EntityExtractor()
    
    # Extract all entities
    entities = extractor.extract_all_entities(sample_text)
    
    # Print summary
    summary = extractor.generate_entity_summary(entities)
    print(summary)
    
    print("\n" + "=" * 70)
    print("✅ Entity extraction test complete!")
    print("\nTo use with real documents:")
    print("  from entity_extractor import EntityExtractor")
    print("  extractor = EntityExtractor()")
    print("  entities = extractor.extract_all_entities(document_text)")


if __name__ == "__main__":
    main()