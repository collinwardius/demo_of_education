#!/usr/bin/env python3
"""
Header Reconstruction Module for Historical Education Data
Reconstructs proper column headers from fragmented Textract output
"""

import pandas as pd
import numpy as np
import re
from typing import List, Dict, Tuple, Optional
import logging
from pathlib import Path

class HeaderReconstructor:
    def __init__(self):
        """Initialize header reconstructor with historical education patterns."""
        self.setup_logging()
        
        # Common header patterns in historical education data
        self.header_patterns = {
            # Geographic
            'state_region': ['state', 'region', 'area', 'territory', 'outlying', 'part'],
            
            # Institution counts
            'institutions': ['institution', 'number', 'reporting', 'colleges', 'universities'],
            
            # Faculty data
            'faculty': ['faculty', 'teachers', 'staff', 'instructors', 'professors'],
            'faculty_male': ['men', 'male', 'faculty'],
            'faculty_female': ['women', 'female', 'faculty'],
            'faculty_full_time': ['full', 'time', 'basis', 'reduced'],
            
            # Student data
            'students': ['students', 'enrollment', 'enrolled', 'attendance'],
            'resident': ['resident', 'regular', 'session'],
            'summer': ['summer', 'session'],
            'undergraduate': ['undergraduate', 'undergrad', 'college'],
            'graduate': ['graduate', 'grad', 'advanced'],
            'freshmen': ['freshmen', 'first', 'year'],
            
            # Degree data
            'degrees': ['degrees', 'graduated', 'completion'],
            'bachelors': ['bachelor', 'baccalau', 'ba', 'bs'],
            'masters': ['master', 'ma', 'ms', 'including'],
            'doctorate': ['doctor', 'phd', 'doctoral'],
            'professional': ['professional', 'first', 'law', 'medicine'],
            'honorary': ['honorary'],
            
            # School types
            'arts_sciences': ['arts', 'sciences', 'liberal'],
            'professional_schools': ['professional', 'schools', 'technical'],
            'engineering': ['engineering', 'engineer']
        }
        
        # Common text fragments that should be joined
        self.join_fragments = {
            'baccalau-': 'baccalaureate',
            'undergrad-': 'undergraduate', 
            'grad-': 'graduate',
            'engineer-': 'engineering',
            'pro-': 'professional',
            'ses-': 'session',
            'institu-': 'institution'
        }
    
    def setup_logging(self):
        """Setup logging for header reconstruction."""
        logging.basicConfig(level=logging.INFO, format='%(levelname)s: %(message)s')
        self.logger = logging.getLogger(__name__)
    
    def reconstruct_headers(self, df: pd.DataFrame, header_rows: int = 4) -> pd.DataFrame:
        """
        Reconstruct proper headers from multi-row fragmented headers.
        
        Args:
            df: DataFrame with fragmented headers
            header_rows: Number of rows containing header information
            
        Returns:
            DataFrame with reconstructed single-row headers
        """
        self.logger.info(f"Reconstructing headers from {header_rows} header rows...")
        
        # Extract potential header rows
        header_data = df.head(header_rows)
        data_rows = df.iloc[header_rows:].reset_index(drop=True)
        
        # Reconstruct column headers
        new_headers = self._merge_header_fragments(header_data)
        
        # Apply to data
        data_rows.columns = new_headers
        
        self.logger.info(f"Reconstructed {len(new_headers)} column headers")
        return data_rows
    
    def _merge_header_fragments(self, header_rows: pd.DataFrame) -> List[str]:
        """Merge fragmented header text into coherent column names."""
        
        num_cols = len(header_rows.columns)
        merged_headers = []
        
        for col_idx in range(num_cols):
            # Collect all text fragments for this column
            fragments = []
            
            for row_idx in range(len(header_rows)):
                cell_value = str(header_rows.iloc[row_idx, col_idx]).strip()
                if cell_value and cell_value != 'nan' and cell_value != '':
                    fragments.append(cell_value)
            
            # Merge fragments into coherent header
            merged_header = self._create_coherent_header(fragments, col_idx)
            merged_headers.append(merged_header)
        
        # Post-process to ensure unique headers
        merged_headers = self._ensure_unique_headers(merged_headers)
        
        return merged_headers
    
    def _create_coherent_header(self, fragments: List[str], col_idx: int) -> str:
        """Create a coherent header from text fragments."""
        
        if not fragments:
            return f"column_{col_idx + 1}"
        
        # Join fragments and clean
        combined_text = " ".join(fragments).lower()
        
        # Fix common fragmentation issues
        for fragment, replacement in self.join_fragments.items():
            combined_text = combined_text.replace(fragment, replacement)
        
        # Remove extra spaces and punctuation
        combined_text = re.sub(r'[^\w\s]', ' ', combined_text)
        combined_text = re.sub(r'\s+', ' ', combined_text).strip()
        
        # Try to classify header type
        classified_header = self._classify_header(combined_text, fragments)
        
        if classified_header:
            return classified_header
        
        # Fallback: clean up the combined text
        return self._clean_header_text(combined_text) or f"column_{col_idx + 1}"
    
    def _classify_header(self, combined_text: str, original_fragments: List[str]) -> Optional[str]:
        """Classify header based on content patterns."""
        
        words = combined_text.split()
        
        # Check for specific patterns
        for category, keywords in self.header_patterns.items():
            matches = sum(1 for word in words if any(keyword in word for keyword in keywords))
            
            if matches >= 2 or (matches >= 1 and len(words) <= 2):
                # Found a strong match, create descriptive name
                return self._generate_descriptive_name(category, combined_text, original_fragments)
        
        return None
    
    def _generate_descriptive_name(self, category: str, text: str, fragments: List[str]) -> str:
        """Generate descriptive column name based on category and content."""
        
        # Look for gender indicators
        gender = ""
        if any(word in text for word in ['men', 'male']):
            gender = "_male"
        elif any(word in text for word in ['women', 'female']):
            gender = "_female"
        
        # Look for level indicators
        level = ""
        if any(word in text for word in ['undergraduate', 'undergrad']):
            level = "_undergraduate"
        elif any(word in text for word in ['graduate', 'grad']):
            level = "_graduate"
        elif any(word in text for word in ['freshmen', 'first']):
            level = "_freshmen"
        
        # Look for session type
        session = ""
        if any(word in text for word in ['summer']):
            session = "_summer"
        elif any(word in text for word in ['regular', 'session']):
            session = "_regular"
        
        # Generate base name from category
        base_names = {
            'state_region': 'state',
            'institutions': 'institutions_count',
            'faculty': 'faculty_total',
            'faculty_male': 'faculty_male',
            'faculty_female': 'faculty_female', 
            'faculty_full_time': 'faculty_full_time',
            'students': 'students_total',
            'resident': 'resident_students',
            'summer': 'summer_students',
            'undergraduate': 'undergraduate_students',
            'graduate': 'graduate_students',
            'freshmen': 'freshmen_students',
            'degrees': 'degrees_total',
            'bachelors': 'bachelors_degrees',
            'masters': 'masters_degrees',
            'doctorate': 'doctorate_degrees',
            'professional': 'professional_degrees',
            'honorary': 'honorary_degrees',
            'arts_sciences': 'arts_sciences',
            'professional_schools': 'professional_schools',
            'engineering': 'engineering'
        }
        
        base_name = base_names.get(category, category)
        return base_name + level + gender + session
    
    def _clean_header_text(self, text: str) -> str:
        """Clean header text for use as column name."""
        
        # Convert to lowercase and replace spaces with underscores
        clean = text.lower().replace(' ', '_')
        
        # Remove special characters except underscores
        clean = re.sub(r'[^\w_]', '', clean)
        
        # Remove multiple underscores
        clean = re.sub(r'_+', '_', clean)
        
        # Remove leading/trailing underscores
        clean = clean.strip('_')
        
        # Truncate if too long
        if len(clean) > 50:
            clean = clean[:50].rstrip('_')
        
        return clean
    
    def _ensure_unique_headers(self, headers: List[str]) -> List[str]:
        """Ensure all headers are unique by adding suffixes if needed."""
        
        seen = {}
        unique_headers = []
        
        for header in headers:
            if header not in seen:
                seen[header] = 0
                unique_headers.append(header)
            else:
                seen[header] += 1
                unique_headers.append(f"{header}_{seen[header]}")
        
        return unique_headers
    
    def auto_detect_header_rows(self, df: pd.DataFrame, max_header_rows: int = 6) -> int:
        """
        Automatically detect how many rows contain header information.
        
        Args:
            df: Input DataFrame
            max_header_rows: Maximum rows to consider as headers
            
        Returns:
            Number of header rows detected
        """
        
        # Look for patterns that indicate data vs headers
        for row_idx in range(min(max_header_rows, len(df))):
            row_data = df.iloc[row_idx].astype(str)
            
            # Check if this row looks like data
            numeric_cells = sum(1 for cell in row_data if self._looks_like_number(cell))
            text_cells = sum(1 for cell in row_data if self._looks_like_text(cell))
            empty_cells = sum(1 for cell in row_data if not cell.strip() or cell == 'nan')
            
            # If mostly numeric with some text, likely start of data
            if numeric_cells > len(row_data) * 0.6 and text_cells > 0:
                self.logger.info(f"Auto-detected {row_idx} header rows")
                return row_idx
        
        # Default fallback
        return 4
    
    def _looks_like_number(self, text: str) -> bool:
        """Check if text looks like a number."""
        text = text.strip()
        if not text or text == 'nan':
            return False
        
        # Remove commas and check if it's a number
        clean_text = text.replace(',', '').replace('.', '')
        return clean_text.isdigit()
    
    def _looks_like_text(self, text: str) -> bool:
        """Check if text looks like descriptive text (not numbers)."""
        text = text.strip()
        if not text or text == 'nan':
            return False
        
        return not self._looks_like_number(text) and len(text) > 1
    
    def create_manual_header_template(self, df: pd.DataFrame, output_path: str):
        """
        Create a template CSV file for manual header specification.
        Research assistants can fill this out for complex cases.
        """
        
        num_cols = len(df.columns)
        
        # Extract first few rows for reference
        header_preview = df.head(6)
        
        # Create template structure
        template_data = {
            'column_index': list(range(1, num_cols + 1)),
            'suggested_header': [''] * num_cols,
            'manual_header': [''] * num_cols,  # For research assistant to fill
            'notes': [''] * num_cols
        }
        
        # Add preview rows as reference columns
        for i in range(min(6, len(header_preview))):
            col_name = f'row_{i+1}_preview'
            template_data[col_name] = [str(cell) for cell in header_preview.iloc[i]]
        
        # Try to suggest headers
        temp_headers = self._merge_header_fragments(header_preview.head(4))
        template_data['suggested_header'] = temp_headers[:num_cols] + [''] * (num_cols - len(temp_headers))
        
        # Save template
        template_df = pd.DataFrame(template_data)
        template_df.to_csv(output_path, index=False)
        
        self.logger.info(f"Manual header template created: {output_path}")
        self.logger.info("Instructions: Fill in 'manual_header' column with desired column names")
        
        return template_df
    
    def apply_manual_headers(self, df: pd.DataFrame, template_path: str) -> pd.DataFrame:
        """Apply manually specified headers from template file."""
        
        template_df = pd.read_csv(template_path)
        
        # Extract manual headers
        manual_headers = template_df['manual_header'].fillna('').tolist()
        
        # Filter out empty headers and ensure we have enough
        manual_headers = [h if h.strip() else f"column_{i+1}" 
                         for i, h in enumerate(manual_headers)]
        
        # Apply to DataFrame
        num_cols = len(df.columns)
        if len(manual_headers) < num_cols:
            # Extend with default names if needed
            manual_headers.extend([f"column_{i+1}" for i in range(len(manual_headers), num_cols)])
        
        # Detect header rows automatically
        header_rows = self.auto_detect_header_rows(df)
        
        # Apply headers to data
        result_df = df.iloc[header_rows:].reset_index(drop=True)
        result_df.columns = manual_headers[:num_cols]
        
        self.logger.info(f"Applied manual headers from template: {template_path}")
        return result_df

def main():
    """Example usage of header reconstructor."""
    import argparse
    
    parser = argparse.ArgumentParser(description='Reconstruct headers from fragmented Textract output')
    parser.add_argument('input_file', help='Path to CSV with fragmented headers')
    parser.add_argument('--output', '-o', help='Output file path')
    parser.add_argument('--header-rows', type=int, default=0, 
                       help='Number of header rows (0 for auto-detect)')
    parser.add_argument('--create-template', action='store_true',
                       help='Create manual header template for research assistants')
    parser.add_argument('--apply-template', 
                       help='Apply headers from manual template file')
    
    args = parser.parse_args()
    
    # Load data
    df = pd.read_csv(args.input_file)
    reconstructor = HeaderReconstructor()
    
    # Generate output path if not provided
    if not args.output:
        input_path = Path(args.input_file)
        args.output = input_path.parent / f"{input_path.stem}_fixed_headers.csv"
    
    if args.create_template:
        # Create manual header template
        template_path = str(args.output).replace('.csv', '_header_template.csv')
        reconstructor.create_manual_header_template(df, template_path)
        print(f"✅ Header template created: {template_path}")
        print(f"📝 Edit the 'manual_header' column and use --apply-template to apply")
        
    elif args.apply_template:
        # Apply manual headers
        result_df = reconstructor.apply_manual_headers(df, args.apply_template)
        result_df.to_csv(args.output, index=False)
        print(f"✅ Headers applied from template: {args.output}")
        
    else:
        # Auto-reconstruct headers
        if args.header_rows == 0:
            header_rows = reconstructor.auto_detect_header_rows(df)
        else:
            header_rows = args.header_rows
        
        result_df = reconstructor.reconstruct_headers(df, header_rows)
        result_df.to_csv(args.output, index=False)
        print(f"✅ Headers reconstructed: {args.output}")
        print(f"   Used {header_rows} header rows")
        print(f"   Generated {len(result_df.columns)} column headers")

if __name__ == "__main__":
    main()