import anthropic

client = anthropic.Anthropic(api_key="***REMOVED***")

# Direct message request to extract first page of blue_book.pdf using Files API
response = client.beta.messages.create(
    model="claude-sonnet-4-20250514",
    betas=["files-api-2025-04-14"],
    max_tokens=8192,
    messages=[{
        "role": "user",
        "content": [
            {"type": "text", "text": "You are a PDF table text extractor. Please extract all text content from the first page only of the blue_book.pdf file using OCR tools. Output the results in a csv. Extract only the text that is contained within the tables. note that the extra large headers are state names. they should apply to all colleges until the next state is reached. for bold headers without numbers, these classify the type of college. these should be used for the succeeding colleges until the next bold header or state name is reached. there should be no rows in the table that are blank except for the first column. make sure to verify that you are always outputting the text to the correct column as there are sometimes nested headers. You do not need to include any text in your response except for the csv."},
            {"type": "document", "source": {"type": "file", "file_id": "file_011CTRySCHwGfk5VuLuzytjz"}}
        ]
    }]
)

print("Extraction completed!")
extracted_text = response.content[0].text
print("Extracted text:")
print(extracted_text)

# Save to text file
with open("blue_book_first_page.txt", "w", encoding="utf-8") as f:
    f.write(extracted_text)
print(f"Text saved to blue_book_first_page.txt")