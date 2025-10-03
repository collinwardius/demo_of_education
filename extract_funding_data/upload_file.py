import anthropic

client = anthropic.Anthropic(api_key="***REMOVED***")
client.beta.files.upload(
    file=("public_funding.pdf", open('/Users/cjwardius/Library/CloudStorage/OneDrive-UCSanDiego/demo of education/scans/funding_tables/select_bi_survey1920_1922_funding_tables.pdf', "rb"), "application/pdf"),
)