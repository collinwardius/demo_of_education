import anthropic
import os

# Read API key from config file
with open(os.path.expanduser('~/Documents/.claude_api_key'), 'r') as f:
    api_key = f.read().strip()

client = anthropic.Anthropic(api_key=api_key)

# Direct message request to extract first page of blue_book.pdf
response = client.beta.messages.create(
    model="claude-sonnet-4-20250514",
    betas=["files-api-2025-04-14"],
    max_tokens=8192,
    messages=[{
        "role": "user",
        "content": [
            {"type": "text", "text": "You are a PDF table text extractor that is extremely careful. Output the results in a csv. Extract only the text that is contained within the tables. make sure to verify that you are always outputting the text to the correct column as there are sometimes nested headers. You do not need to include any text in your response except for the csv. Ensure that if a cell is blank, leave it blank. Blank cells are sometimes filled with dashes or dots but are truly blank. Make sure the headers of the document are concise but also capture all the relevant information. There should be 14 total columns. All tables have the same number of columns. You should only output one header row at the top of the csv. All columns except for the first should be either numeric information or should be missing."},
            {"type": "document", "source": {"type": "file", "file_id": "file_011CThDTnh7dYwSUsgXRNfkB"}}
        ]
    }]
)

print("Extraction completed!")
extracted_text = response.content[0].text
print("Extracted text:")
print(extracted_text)

# Save to text file
with open("public_funding_1921_1922.txt", "w", encoding="utf-8") as f:
    f.write(extracted_text)
print(f"Text saved to public_funding_1921_1922.txt")