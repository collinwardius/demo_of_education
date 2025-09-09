import pandas as pd
import numpy as np
import re
from typing import List, Dict, Optional
import json

class UniversityDataCleaner:
    """Pipeline for cleaning Amazon Textract output of university data tables."""
    
    def __init__(self):
        self.column_mapping = {
            # Based on the column numbers in row 2
            0: 'location',
            1: 'institution_name',
            2: 'gender_type',  # coeducational, men, women
            3: 'control',  # State, Private, etc.
            4: 'year_founded',
            5: 'faculty_men',
            6: 'faculty_women',
            7: 'faculty_total_men',
            8: 'faculty_total_women',
            9: 'students_men',
            10: 'students_women',
            11: 'students_total_men',
            12: 'students_total_women',
            13: 'first_degrees_men',
            14: 'first_degrees_women',
            15: 'first_degrees_total_men',
            16: 'first_degrees_total_women',
            17: 'graduate_degrees_men',
            18: 'graduate_degrees_women',
            19: 'graduate_degrees_total_men',
            20: 'graduate_degrees_total_women',
            21: 'honorary_degrees'
        }
        
    def clean_csv_from_textract(self, filepath: str) -> pd.DataFrame:
        """Main pipeline to clean CSV output from Amazon Textract."""
        
        # Step 1: Read and parse the raw CSV
        df_raw = self._read_raw_csv(filepath)
        
        # Step 2: Clean cell values (remove quotes, handle OCR errors)
        df_cleaned = self._clean_cell_values(df_raw)
        
        # Step 3: Identify and structure hierarchical data
        df_structured = self._structure_hierarchical_data(df_cleaned)
        
        # Step 4: Validate and fix data types
        df_typed = self._fix_data_types(df_structured)
        
        # Step 5: Add calculated fields and quality checks
        df_final = self._add_validation_fields(df_typed)
        
        return df_final
    
    def _read_raw_csv(self, filepath: str) -> pd.DataFrame:
        """Read CSV with proper handling of Textract quirks."""
        # Read without headers since they're multi-row
        df = pd.read_csv(filepath, header=None, dtype=str)
        
        # Remove apostrophes and quotes that Textract adds
        df = df.map(lambda x: x.strip("'\"") if isinstance(x, str) else x)
        
        return df
    
    def _clean_cell_values(self, df: pd.DataFrame) -> pd.DataFrame:
        """Clean individual cell values from OCR errors."""
        df_clean = df.copy()
        
        # Common OCR corrections
        ocr_corrections = {
            'fessors': 'Professors',
            'struc-': 'instruc-',
            'tors': 'tors',
            'de- grees': 'degrees',
            'gradu- ate': 'graduate',
            'coeduca- tional': 'coeducational'
        }
        
        for col in df_clean.columns:
            df_clean[col] = df_clean[col].apply(lambda x: self._apply_ocr_corrections(x, ocr_corrections))
        
        # Remove periods from headers
        df_clean = df_clean.map(lambda x: x.rstrip('.') if isinstance(x, str) else x)
        
        # Replace empty strings with NaN
        df_clean = df_clean.replace('', np.nan)
        
        return df_clean
    
    def _apply_ocr_corrections(self, text: str, corrections: dict) -> str:
        """Apply OCR corrections to text."""
        if pd.isna(text):
            return text
        
        result = str(text)
        for wrong, right in corrections.items():
            result = result.replace(wrong, right)
        
        # Fix hyphenated words
        result = re.sub(r'(\w+)- (\w+)', r'\1\2', result)
        
        return result
    
    def _structure_hierarchical_data(self, df: pd.DataFrame) -> pd.DataFrame:
        """Convert hierarchical table structure to flat panel data."""
        
        # Skip header rows (0-2) and state header rows
        data_rows = []
        current_state = None
        current_institution = None
        
        for idx in range(3, len(df)):
            row = df.iloc[idx]
            
            # Check if it's a state header (all caps in first column)
            if pd.notna(row[0]) and row[0].isupper() and all(pd.isna(row[i]) or row[i] == '' for i in range(1, len(row))):
                current_state = row[0].replace('.', '')
                continue
            
            # Check if it's an institution (has location and institution name)
            if pd.notna(row[0]) and pd.notna(row[1]):
                current_institution = {
                    'state': current_state,
                    'city': row[0],
                    'institution': row[1],
                    'parent_institution': row[1],
                    'department': 'Total',
                    'gender_type': row[2],
                    'control': row[3],
                    'year_founded': row[4]
                }
                
                # Add numeric data
                for col_idx, col_name in self.column_mapping.items():
                    if col_idx >= 5:  # Numeric columns start at index 5
                        current_institution[col_name] = row[col_idx] if col_idx < len(row) else None
                
                data_rows.append(current_institution)
            
            # Check if it's a department/program row
            elif pd.notna(row[1]) and current_institution:
                dept_row = current_institution.copy()
                dept_row['department'] = row[1]
                
                # Update numeric data for this department
                for col_idx, col_name in self.column_mapping.items():
                    if col_idx >= 5:
                        dept_row[col_name] = row[col_idx] if col_idx < len(row) else None
                
                data_rows.append(dept_row)
        
        return pd.DataFrame(data_rows)
    
    def _fix_data_types(self, df: pd.DataFrame) -> pd.DataFrame:
        """Convert columns to appropriate data types."""
        df_typed = df.copy()
        
        # Numeric columns
        numeric_cols = [col for col in df_typed.columns if any(
            keyword in col for keyword in ['faculty', 'students', 'degrees', 'year']
        )]
        
        for col in numeric_cols:
            df_typed[col] = pd.to_numeric(df_typed[col], errors='coerce')
        
        # Clean up gender_type values
        gender_map = {
            'Coed': 'Coeducational',
            'Men': 'Men only',
            'Women': 'Women only'
        }
        df_typed['gender_type'] = df_typed['gender_type'].map(lambda x: gender_map.get(x, x))
        
        return df_typed
    
    def _add_validation_fields(self, df: pd.DataFrame) -> pd.DataFrame:
        """Add calculated fields and data quality indicators."""
        df_final = df.copy()
        
        # Calculate totals where both components exist
        if 'faculty_men' in df_final.columns and 'faculty_women' in df_final.columns:
            df_final['faculty_total_calculated'] = df_final['faculty_men'].fillna(0) + df_final['faculty_women'].fillna(0)
            
        if 'students_men' in df_final.columns and 'students_women' in df_final.columns:
            df_final['students_total_calculated'] = df_final['students_men'].fillna(0) + df_final['students_women'].fillna(0)
        
        # Add data quality flags
        df_final['has_faculty_data'] = (df_final['faculty_men'].notna()) | (df_final['faculty_women'].notna())
        df_final['has_student_data'] = (df_final['students_men'].notna()) | (df_final['students_women'].notna())
        df_final['has_degree_data'] = (df_final['first_degrees_men'].notna()) | (df_final['first_degrees_women'].notna())
        
        # Flag potential OCR errors (e.g., unusually high numbers)
        df_final['potential_ocr_error'] = False
        for col in ['students_men', 'students_women', 'faculty_men', 'faculty_women']:
            if col in df_final.columns:
                df_final.loc[df_final[col] > 10000, 'potential_ocr_error'] = True
        
        # Add completeness score
        data_cols = [col for col in df_final.columns if any(
            keyword in col for keyword in ['faculty', 'students', 'degrees']
        ) and '_calculated' not in col and 'has_' not in col]
        
        df_final['completeness_score'] = df_final[data_cols].notna().sum(axis=1) / len(data_cols)
        
        return df_final
    
    def export_clean_data(self, df: pd.DataFrame, output_format: str = 'csv', filepath: str = None):
        """Export cleaned data in various formats."""
        if output_format == 'csv':
            df.to_csv(filepath or 'cleaned_university_data.csv', index=False)
        elif output_format == 'json':
            df.to_json(filepath or 'cleaned_university_data.json', orient='records', indent=2)
        elif output_format == 'parquet':
            df.to_parquet(filepath or 'cleaned_university_data.parquet', index=False)
        else:
            raise ValueError(f"Unsupported format: {output_format}")
    
    def generate_quality_report(self, df: pd.DataFrame) -> Dict:
        """Generate a data quality report."""
        report = {
            'total_records': int(len(df)),
            'unique_institutions': int(df['parent_institution'].nunique()),
            'unique_departments': int(df[df['department'] != 'Total']['department'].nunique()),
            'states_covered': int(df['state'].nunique()),
            'completeness': {
                'mean': float(df['completeness_score'].mean()),
                'median': float(df['completeness_score'].median()),
                'records_above_80pct': int((df['completeness_score'] > 0.8).sum())
            },
            'potential_errors': int(df['potential_ocr_error'].sum()),
            'missing_data': {
                'faculty': int((~df['has_faculty_data']).sum()),
                'students': int((~df['has_student_data']).sum()),
                'degrees': int((~df['has_degree_data']).sum())
            }
        }
        
        return report


# Example usage
if __name__ == "__main__":
    # Initialize the cleaner
    cleaner = UniversityDataCleaner()
    
    # Clean the data
    cleaned_df = cleaner.clean_csv_from_textract('bi_survey1916_1918 (1)/table-1.csv')
    
    # Generate quality report
    quality_report = cleaner.generate_quality_report(cleaned_df)
    print("Data Quality Report:")
    print(json.dumps(quality_report, indent=2))
    
    # Export cleaned data
    cleaner.export_clean_data(cleaned_df, 'csv', 'cleaned_university_panel.csv')
    cleaner.export_clean_data(cleaned_df, 'json', 'cleaned_university_panel.json')
    
    # Show sample of cleaned data
    print("\nSample of cleaned data:")
    print(cleaned_df.head(10))
    
    # Show data by department for first institution
    first_inst = cleaned_df['parent_institution'].iloc[0]
    print(f"\nDepartments for {first_inst}:")
    inst_data = cleaned_df[cleaned_df['parent_institution'] == first_inst][
        ['department', 'students_men', 'students_women', 'first_degrees_men', 'first_degrees_women']
    ]
    print(inst_data)