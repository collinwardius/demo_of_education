import anthropic
import os

# Read API key from config file
with open(os.path.expanduser('~/Documents/.claude_api_key'), 'r') as f:
    api_key = f.read().strip()

client = anthropic.Anthropic(api_key=api_key)
client.beta.files.upload(
    file=("public_funding.pdf", open('/Users/cjwardius/Library/CloudStorage/OneDrive-UCSanDiego/demo of education/scans/funding_tables/select_bi_survey1920_1922_funding_tables.pdf', "rb"), "application/pdf"),
)