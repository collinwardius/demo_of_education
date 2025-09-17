Here are instructions for cleaning text extracted from historical tables on universites

Data Structure & Organization

  - Check page numbering: Verify pages are in correct range and sequence
  - Remove page headers: Use consistent logic to drop header rows (e.g.,
  first 3 rows per page)
  - Standardize missing values: Look for variations like "Do", "Do (May",
  "Do." that mean "ditto"

  Geographic & Institutional Assignment

  - Forward-fill state names: States appear once then apply to subsequent
  rows until next state
  - Handle state name truncation: Watch for abbreviated names like "NORTH
  CARO" → "NORTH CAROLINA"
  - Remove periods from state names: Clean formatting inconsistencies
  - Forward-fill town names: Towns follow same pattern as states

  Institution Name Cleaning

  - Flexible institution detection: Use partial matches ("col", "inst",
  "uni") not just full words
  - Forward-fill institution names: College names apply to subsequent
  department rows
  - Remove parenthetical information: Strip anything in parentheses from
  college names
  - Clean Unicode/special characters: Remove non-ASCII characters that OCR
  introduces
  - Standardize spacing: Remove extra spaces and trim whitespace
  - Remove leading/trailing punctuation: Clean up dots and dashes

  Numeric Variable Processing

  - Remove currency symbols: Strip "$" from all numeric fields
  - Remove thousands separators: Strip "," from numeric values
  - Apply to all numeric vars at once: Use loops for efficiency
  - Use destring with force: Handle remaining non-numeric characters
  gracefully
  - Document expected missingness: Note when missing values are legitimate
  vs. OCR errors

  Quality Checks to Perform

  - Verify geographic consistency: Check that institutions are in correct
  states
  - Look for split institution names: Watch for names broken across multiple
   rows
  - Check for reasonable numeric ranges: Flag outliers that might be OCR
  errors
  - Compare missing value patterns: Ensure missingness makes logical sense
  - Spot-check total vs. detail rows: Verify totals match sum of components

  General OCR/Textract Considerations

  - Expect inconsistent formatting: OCR introduces random spacing and
  characters
  - Plan for split text: Important information may span multiple rows
  - Be flexible with pattern matching: Use partial matches rather than exact
   strings
  - Document assumptions: Note decisions about ambiguous cases
  - Keep original data: Preserve raw extracted data for reference