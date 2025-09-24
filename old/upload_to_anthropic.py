import anthropic

client = anthropic.Anthropic(api_key="***REMOVED***")
client.beta.files.upload(
    file=("blue_book.pdf", open('/Users/cjwardius/Library/CloudStorage/OneDrive-UCSanDiego/demo of education/scans/cleaned_scans/college_blue_book.pdf', "rb"), "application/pdf"),
)