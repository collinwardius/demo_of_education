# Table Orientation Guidelines

## Critical Requirement: TABLE TEXT ONLY

**IMPORTANT**: We only care about the orientation of TABLE content, not other text on the page.

## Key Points

- **Focus**: Table text readability for OCR extraction
- **Ignore**: Headers, footers, page numbers, annotations, or other non-table text
- **Goal**: Ensure table data (rows, columns, cell values) are correctly oriented

## Implementation Guidelines

### For Textract Analysis
- Extract `OrientationCorrection` from TABLE blocks specifically
- Do NOT use page-level or general text block orientation
- Each table block may have different orientation needs

### For Rotation Decisions
- Only rotate pages when TABLE blocks indicate incorrect orientation
- Preserve pages where tables are already correctly oriented (OrientationCorrection = 0°)
- Apply the exact rotation angle needed for table readability

### Mixed Content Pages
- Historical documents often have:
  - Correctly oriented page headers/text
  - Rotated table content (common in landscape tables)
- **Always prioritize table orientation over other page elements**

## Why This Matters
- Historical education tables are often in landscape format
- Page text might be portrait while tables need landscape orientation
- OCR accuracy depends on correct table text orientation, not page decoration text

---
*This guideline ensures consistent table-focused orientation handling across all processing.*