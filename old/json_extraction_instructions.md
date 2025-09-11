  You are an agent tasked with extracting json data to a csv to be used for data analysis. Please use extract_table_improved.py as a template for performing this task.
  
  Mandatory Workflow

  1. Test with 5-10 pages first
  2. Examine headers with examine_headers_from_page()
  3. Customize is_header_row() patterns for your document
  4. Create domain-specific headers in create_meaningful_headers()
  5. Handle column mismatches and report problem pages
  6. Scale to full document once working

  Key Principles

  - Always preserve page numbers as last column
  - Use page 1 as column count reference
  - Report which pages have issues
  - Start small, debug, then scale