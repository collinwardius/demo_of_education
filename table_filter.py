#!/usr/bin/env python3
"""
Table Content Filter for Education Data
Advanced filtering and scoring of detected tables based on content relevance
"""

import re
import json
import pandas as pd
from pathlib import Path
from typing import Dict, List, Tuple, Any
import logging
from dataclasses import dataclass
import argparse

@dataclass
class TableScore:
    """Score breakdown for a table's education relevance."""
    content_score: float
    structure_score: float
    keyword_score: float
    numeric_score: float
    total_score: float
    confidence: float
    reasons: List[str]

class EducationTableFilter:
    def __init__(self):
        """Initialize education table filter with scoring criteria."""
        
        # Education keyword categories with different weights
        self.keyword_categories = {
            'primary_education': {
                'weight': 1.0,
                'keywords': [
                    'school', 'schools', 'pupils', 'students', 'enrollment', 'enrolled',
                    'attendance', 'teachers', 'education', 'educational'
                ]
            },
            'institutional': {
                'weight': 0.9,
                'keywords': [
                    'university', 'college', 'academy', 'institute', 'seminary',
                    'normal school', 'common school', 'public school', 'private school'
                ]
            },
            'administrative': {
                'weight': 0.8,
                'keywords': [
                    'superintendent', 'principal', 'commissioner', 'board of education',
                    'school district', 'county', 'state', 'department of education'
                ]
            },
            'demographics': {
                'weight': 0.7,
                'keywords': [
                    'male', 'female', 'white', 'colored', 'negro', 'age', 'ages',
                    'population', 'census', 'total', 'number'
                ]
            },
            'academic': {
                'weight': 0.8,
                'keywords': [
                    'graduate', 'graduation', 'grade', 'grades', 'class', 'classes',
                    'examination', 'certificate', 'diploma', 'degree'
                ]
            },
            'statistics': {
                'weight': 0.6,
                'keywords': [
                    'percent', 'per cent', 'percentage', 'ratio', 'average', 'total',
                    'sum', 'statistics', 'data', 'report', 'annual'
                ]
            }
        }
        
        # Patterns that indicate tabular data structure
        self.structure_patterns = {
            'header_indicators': [
                r'name of school', r'district', r'county', r'state',
                r'number of', r'total', r'male', r'female',
                r'enrollment', r'attendance', r'teachers'
            ],
            'numeric_patterns': [
                r'\b\d+\b',  # Simple numbers
                r'\b\d+,\d+\b',  # Numbers with commas
                r'\b\d+\.\d+\b',  # Decimals
                r'\b\d+\s*%\b',  # Percentages
                r'\$\d+',  # Dollar amounts
            ],
            'geographic_patterns': [
                r'\b[A-Z][a-z]+ County\b',
                r'\b[A-Z][a-z]+ District\b',
                r'\bState of [A-Z][a-z]+\b'
            ]
        }
        
        # Historical context patterns (1890s education)
        self.historical_patterns = [
            r'school year \d{4}[-–]\d{2,4}',
            r'annual report',
            r'commissioner of education',
            r'state superintendent',
            r'normal schools?',
            r'common schools?',
            r'graded schools?',
            r'ungraded schools?'
        ]
        
    def filter_scan_results(self, scan_results: Dict, 
                          min_score: float = 0.5,
                          max_pages: int = None) -> Dict:
        """
        Filter and rank scan results based on education relevance.
        
        Args:
            scan_results: Results from page scanner
            min_score: Minimum score threshold for inclusion
            max_pages: Maximum number of pages to return (top-ranked)
            
        Returns:
            Filtered and ranked results
        """
        filtered_pages = []
        
        for page in scan_results['pages_with_tables']:
            # Score this page for education relevance
            score = self._score_page_content(page)
            
            if score.total_score >= min_score:
                page_with_score = page.copy()
                page_with_score['education_score'] = score.total_score
                page_with_score['score_breakdown'] = {
                    'content': score.content_score,
                    'structure': score.structure_score,
                    'keywords': score.keyword_score,
                    'numeric': score.numeric_score,
                    'reasons': score.reasons
                }
                filtered_pages.append(page_with_score)
        
        # Sort by education score (descending)
        filtered_pages.sort(key=lambda x: x['education_score'], reverse=True)
        
        # Limit number of pages if specified
        if max_pages:
            filtered_pages = filtered_pages[:max_pages]
        
        # Create filtered results
        filtered_results = scan_results.copy()
        filtered_results['pages_with_tables'] = filtered_pages
        filtered_results['filter_applied'] = {
            'min_score': min_score,
            'max_pages': max_pages,
            'pages_before_filtering': len(scan_results['pages_with_tables']),
            'pages_after_filtering': len(filtered_pages)
        }
        
        return filtered_results
    
    def _score_page_content(self, page: Dict) -> TableScore:
        """Score a page for education data relevance."""
        text = page.get('text_content', '').lower()
        
        # Initialize scores
        content_score = 0.0
        structure_score = 0.0
        keyword_score = 0.0
        numeric_score = 0.0
        reasons = []
        
        # 1. Score based on education keywords
        for category, info in self.keyword_categories.items():
            category_matches = 0
            for keyword in info['keywords']:
                if keyword.lower() in text:
                    category_matches += 1
            
            if category_matches > 0:
                category_score = min(1.0, category_matches * 0.1) * info['weight']
                keyword_score += category_score
                reasons.append(f"{category}: {category_matches} keywords")
        
        keyword_score = min(1.0, keyword_score)
        
        # 2. Score table structure indicators
        structure_matches = 0
        
        # Check for header-like patterns
        for pattern in self.structure_patterns['header_indicators']:
            if re.search(pattern, text, re.IGNORECASE):
                structure_matches += 1
        
        # Check for geographic patterns
        for pattern in self.structure_patterns['geographic_patterns']:
            if re.search(pattern, text, re.IGNORECASE):
                structure_matches += 1
        
        if structure_matches > 0:
            structure_score = min(1.0, structure_matches * 0.15)
            reasons.append(f"Structure indicators: {structure_matches}")
        
        # 3. Score numeric content density
        total_numbers = 0
        for pattern in self.structure_patterns['numeric_patterns']:
            matches = re.findall(pattern, text)
            total_numbers += len(matches)
        
        if total_numbers > 5:  # Threshold for "data-heavy" content
            numeric_score = min(1.0, total_numbers / 50.0)  # Normalize
            reasons.append(f"Numeric content: {total_numbers} numbers")
        
        # 4. Historical context bonus
        historical_matches = 0
        for pattern in self.historical_patterns:
            if re.search(pattern, text, re.IGNORECASE):
                historical_matches += 1
        
        historical_bonus = min(0.2, historical_matches * 0.05)
        
        # 5. Calculate content score (combination of factors)
        content_score = (
            keyword_score * 0.4 +
            structure_score * 0.3 +
            numeric_score * 0.2 +
            historical_bonus
        )
        
        # 6. Factor in table detection confidence from original scan
        base_confidence = page.get('confidence', 0.0)
        
        # Total score combines content relevance with detection confidence
        total_score = (content_score * 0.7) + (base_confidence * 0.3)
        
        # Final confidence is average of content and detection confidence
        final_confidence = (content_score + base_confidence) / 2.0
        
        if historical_matches > 0:
            reasons.append(f"Historical context: {historical_matches} matches")
        
        return TableScore(
            content_score=content_score,
            structure_score=structure_score,
            keyword_score=keyword_score,
            numeric_score=numeric_score,
            total_score=total_score,
            confidence=final_confidence,
            reasons=reasons
        )
    
    def analyze_text_sample(self, text: str) -> Dict:
        """Analyze a text sample for education content indicators."""
        
        analysis = {
            'keyword_analysis': {},
            'structure_indicators': [],
            'numeric_content': {},
            'historical_indicators': [],
            'overall_score': 0.0
        }
        
        text_lower = text.lower()
        
        # Analyze keywords by category
        total_keyword_score = 0.0
        for category, info in self.keyword_categories.items():
            matches = []
            for keyword in info['keywords']:
                if keyword in text_lower:
                    matches.append(keyword)
            
            category_score = min(1.0, len(matches) * 0.1) * info['weight']
            total_keyword_score += category_score
            
            analysis['keyword_analysis'][category] = {
                'matches': matches,
                'count': len(matches),
                'score': category_score
            }
        
        # Check structure indicators
        for pattern in self.structure_patterns['header_indicators']:
            if re.search(pattern, text, re.IGNORECASE):
                analysis['structure_indicators'].append(pattern)
        
        # Analyze numeric content
        for pattern_name, pattern in self.structure_patterns['numeric_patterns'].items():
            matches = re.findall(pattern, text)
            if matches:
                analysis['numeric_content'][pattern_name] = len(matches)
        
        # Check historical patterns
        for pattern in self.historical_patterns:
            if re.search(pattern, text, re.IGNORECASE):
                analysis['historical_indicators'].append(pattern)
        
        # Calculate overall score
        keyword_score = min(1.0, total_keyword_score)
        structure_score = min(1.0, len(analysis['structure_indicators']) * 0.15)
        numeric_score = min(1.0, sum(analysis['numeric_content'].values()) / 50.0)
        historical_bonus = min(0.2, len(analysis['historical_indicators']) * 0.05)
        
        analysis['overall_score'] = (
            keyword_score * 0.4 +
            structure_score * 0.3 +
            numeric_score * 0.2 +
            historical_bonus
        )
        
        return analysis
    
    def save_filtered_results(self, filtered_results: Dict, output_dir: str, 
                            pdf_name: str) -> str:
        """Save filtered results with detailed scoring information."""
        output_path = Path(output_dir)
        output_path.mkdir(exist_ok=True)
        
        # Save complete filtered results
        json_file = output_path / f"{pdf_name}_filtered_results.json"
        with open(json_file, 'w') as f:
            json.dump(filtered_results, f, indent=2, default=str)
        
        # Create detailed CSV for analysis
        if filtered_results['pages_with_tables']:
            csv_data = []
            for page in filtered_results['pages_with_tables']:
                csv_data.append({
                    'page_number': page['page_number'],
                    'education_score': page['education_score'],
                    'original_confidence': page['confidence'],
                    'tables_detected': len(page['detected_tables']),
                    'content_score': page['score_breakdown']['content'],
                    'structure_score': page['score_breakdown']['structure'],
                    'keyword_score': page['score_breakdown']['keywords'],
                    'numeric_score': page['score_breakdown']['numeric'],
                    'education_keywords': len(page['education_keywords']),
                    'reasons': '; '.join(page['score_breakdown']['reasons'])
                })
            
            csv_df = pd.DataFrame(csv_data)
            csv_file = output_path / f"{pdf_name}_filtered_pages.csv"
            csv_df.to_csv(csv_file, index=False)
        
        return str(json_file)
    
    def create_priority_list(self, filtered_results: Dict, 
                           output_dir: str, pdf_name: str) -> str:
        """Create a priority list of pages for extraction."""
        
        if not filtered_results['pages_with_tables']:
            return None
        
        # Sort pages by score and create priority tiers
        pages = filtered_results['pages_with_tables']
        
        priority_tiers = {
            'high_priority': [p for p in pages if p['education_score'] > 0.8],
            'medium_priority': [p for p in pages if 0.6 <= p['education_score'] <= 0.8],
            'low_priority': [p for p in pages if 0.4 <= p['education_score'] < 0.6],
            'review_needed': [p for p in pages if p['education_score'] < 0.4]
        }
        
        # Create HTML priority report
        html_content = f"""
        <!DOCTYPE html>
        <html>
        <head>
            <title>Extraction Priority List - {pdf_name}</title>
            <style>
                body {{ font-family: Arial, sans-serif; margin: 20px; }}
                .container {{ max-width: 1200px; margin: 0 auto; }}
                .tier {{ margin-bottom: 30px; border-radius: 8px; padding: 20px; }}
                .high {{ background: #d4edda; border-left: 5px solid #28a745; }}
                .medium {{ background: #fff3cd; border-left: 5px solid #ffc107; }}
                .low {{ background: #f8d7da; border-left: 5px solid #dc3545; }}
                .review {{ background: #e2e3e5; border-left: 5px solid #6c757d; }}
                .page-item {{ margin: 10px 0; padding: 15px; background: white; border-radius: 4px; }}
                .score {{ font-weight: bold; color: #007bff; }}
                .reasons {{ font-size: 0.9em; color: #666; margin-top: 5px; }}
            </style>
        </head>
        <body>
            <div class="container">
                <h1>🎯 Extraction Priority List</h1>
                <h2>{pdf_name}</h2>
        """
        
        for tier_name, tier_pages in priority_tiers.items():
            if not tier_pages:
                continue
                
            tier_display = tier_name.replace('_', ' ').title()
            tier_class = tier_name.split('_')[0]
            
            html_content += f"""
                <div class="tier {tier_class}">
                    <h3>{tier_display} ({len(tier_pages)} pages)</h3>
            """
            
            for page in tier_pages:
                reasons = ', '.join(page['score_breakdown']['reasons'][:3])
                html_content += f"""
                    <div class="page-item">
                        <strong>Page {page['page_number']}</strong> 
                        <span class="score">(Score: {page['education_score']:.2f})</span>
                        <div>Tables: {len(page['detected_tables'])}, Keywords: {len(page['education_keywords'])}</div>
                        <div class="reasons">{reasons}</div>
                    </div>
                """
            
            html_content += "</div>"
        
        html_content += """
                <div style="margin-top: 30px; padding: 15px; background: #f9f9f9; border-radius: 4px;">
                    <h4>🚀 Recommended Extraction Order</h4>
                    <ol>
                        <li><strong>High Priority:</strong> Extract these pages first - highest confidence for education data</li>
                        <li><strong>Medium Priority:</strong> Good candidates with solid education indicators</li>
                        <li><strong>Low Priority:</strong> May contain relevant data but lower confidence</li>
                        <li><strong>Review Needed:</strong> Manual review recommended before extraction</li>
                    </ol>
                </div>
            </div>
        </body>
        </html>
        """
        
        output_path = Path(output_dir)
        priority_file = output_path / f"{pdf_name}_priority_list.html"
        with open(priority_file, 'w', encoding='utf-8') as f:
            f.write(html_content)
        
        return str(priority_file)


def main():
    parser = argparse.ArgumentParser(description='Filter scan results for education relevance')
    parser.add_argument('scan_results', help='Path to scan results JSON file')
    parser.add_argument('--min-score', type=float, default=0.5,
                       help='Minimum education relevance score (default: 0.5)')
    parser.add_argument('--max-pages', type=int,
                       help='Maximum number of pages to return')
    parser.add_argument('--output-dir', '-o', default='filtered_results',
                       help='Output directory for filtered results')
    parser.add_argument('--create-priority-list', action='store_true',
                       help='Create HTML priority list for extraction')
    
    args = parser.parse_args()
    
    # Load scan results
    with open(args.scan_results, 'r') as f:
        scan_results = json.load(f)
    
    # Initialize filter
    filter_engine = EducationTableFilter()
    
    try:
        print(f"🔍 Filtering scan results with min score: {args.min_score}")
        
        # Apply filtering
        filtered_results = filter_engine.filter_scan_results(
            scan_results, 
            min_score=args.min_score,
            max_pages=args.max_pages
        )
        
        pdf_name = Path(scan_results['pdf_path']).stem
        
        # Save filtered results
        output_file = filter_engine.save_filtered_results(
            filtered_results, args.output_dir, pdf_name
        )
        
        # Create priority list if requested
        priority_file = None
        if args.create_priority_list:
            priority_file = filter_engine.create_priority_list(
                filtered_results, args.output_dir, pdf_name
            )
        
        print(f"✅ Filtering complete!")
        print(f"   📄 Pages before filtering: {filtered_results['filter_applied']['pages_before_filtering']}")
        print(f"   📄 Pages after filtering: {filtered_results['filter_applied']['pages_after_filtering']}")
        print(f"   💾 Results saved: {output_file}")
        
        if priority_file:
            print(f"   🎯 Priority list: {priority_file}")
        
        # Show top recommendations
        if filtered_results['pages_with_tables']:
            print(f"\n🏆 Top 3 recommended pages:")
            for i, page in enumerate(filtered_results['pages_with_tables'][:3], 1):
                print(f"   {i}. Page {page['page_number']} (score: {page['education_score']:.2f})")
        
    except Exception as e:
        print(f"❌ Error: {e}")
        return 1
    
    return 0


if __name__ == "__main__":
    exit(main())